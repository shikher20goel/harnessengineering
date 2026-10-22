"""The tool layer — how the agent touches the world.

Harness-engineering principles encoded here:

1. Tools are the agent's *only* effectors. If the agent can't do something,
   you add or improve a tool; you don't beg the model in prose.
2. Tool results are sanitized and TRUNCATED before they reach the context
   window (a 2 MB build log would otherwise evict everything else).
3. Errors are returned to the model as structured, readable feedback —
   an agent that sees "file not found: src/app.py (did you mean ls first?)"
   self-corrects; one that sees a stack trace flails.
4. Every tool is confined to a workspace directory. Path escapes are a
   guardrail violation, not an exception.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MAX_RESULT_CHARS = 20_000   # hard cap on what a single tool result may inject


def truncate(text: str, limit: int = MAX_RESULT_CHARS) -> str:
    """Keep head and tail; the middle of huge outputs is rarely load-bearing."""
    if len(text) <= limit:
        return text
    head, tail = text[: limit // 2], text[-limit // 2:]
    dropped = len(text) - limit
    return f"{head}\n... [{dropped} chars truncated by harness] ...\n{tail}"


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    fn: Callable[..., str]

    def spec(self) -> dict:
        """Schema in the shape the Anthropic API expects."""
        return {"name": self.name, "description": self.description,
                "input_schema": self.input_schema}


class ToolRegistry:
    """Holds the tools; executes calls; never lets an exception kill the loop."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def specs(self) -> list[dict]:
        return [t.spec() for t in self._tools.values()]

    def execute(self, name: str, arguments: dict) -> tuple[str, bool]:
        """Run a tool. Returns (result_text, is_error). Never raises."""
        tool = self._tools.get(name)
        if tool is None:
            return f"Unknown tool '{name}'. Available: {sorted(self._tools)}", True
        try:
            return truncate(tool.fn(**arguments)), False
        except TypeError as e:
            return f"Bad arguments for '{name}': {e}", True
        except Exception as e:  # noqa: BLE001 — the loop must survive any tool failure
            return truncate(f"{type(e).__name__}: {e}"), True


# --------------------------------------------------------------------------
# Built-in tools: bash + a minimal file suite. The file tools are confined to
# `workspace`; bash only *starts* there and runs with your user's permissions,
# so run untrusted tasks inside a container or VM.
# --------------------------------------------------------------------------

_SECRET_ENV = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|SESSION", re.IGNORECASE)


def _scrubbed_env() -> dict[str, str]:
    """The parent env minus anything that looks like a credential, so a
    prompt-injected `env` or `curl -d "$ANTHROPIC_API_KEY"` has nothing to leak."""
    return {k: v for k, v in os.environ.items() if not _SECRET_ENV.search(k)}

def _resolve_inside(workspace: Path, path: str) -> Path:
    """Resolve `path` and refuse anything outside the workspace (guardrail)."""
    p = (workspace / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if not p.is_relative_to(workspace.resolve()):
        raise PermissionError(f"path escapes the workspace: {path}")
    return p


def build_default_tools(workspace: Path, bash_timeout: int = 60) -> ToolRegistry:
    workspace = workspace.resolve()
    reg = ToolRegistry()

    def bash(command: str) -> str:
        proc = subprocess.run(
            command, shell=True, cwd=workspace, timeout=bash_timeout,
            capture_output=True, text=True, env=_scrubbed_env(),
        )
        out = proc.stdout + (("\n[stderr]\n" + proc.stderr) if proc.stderr else "")
        return f"exit_code={proc.returncode}\n{out or '(no output)'}"

    def read_file(path: str) -> str:
        return _resolve_inside(workspace, path).read_text()

    def write_file(path: str, content: str) -> str:
        p = _resolve_inside(workspace, path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"wrote {len(content)} chars to {p.relative_to(workspace)}"

    def edit_file(path: str, old: str, new: str) -> str:
        p = _resolve_inside(workspace, path)
        text = p.read_text()
        n = text.count(old)
        if n == 0:
            return f"ERROR: old string not found in {path}. Read the file first."
        if n > 1:
            return f"ERROR: old string appears {n} times in {path}; make it unique."
        p.write_text(text.replace(old, new, 1))
        return f"edited {p.relative_to(workspace)}"

    def list_files(pattern: str = "**/*") -> str:
        hits = [str(p.relative_to(workspace)) for p in sorted(workspace.glob(pattern))
                if p.is_file() and ".git/" not in str(p)]
        return "\n".join(hits[:500]) or "(no files match)"

    reg.register(Tool(
        "bash", "Run a shell command inside the workspace. Returns exit code and output.",
        {"type": "object", "properties": {"command": {"type": "string"}},
         "required": ["command"]}, bash))
    reg.register(Tool(
        "read_file", "Read a text file (path relative to the workspace).",
        {"type": "object", "properties": {"path": {"type": "string"}},
         "required": ["path"]}, read_file))
    reg.register(Tool(
        "write_file", "Create or overwrite a text file in the workspace.",
        {"type": "object", "properties": {"path": {"type": "string"},
                                          "content": {"type": "string"}},
         "required": ["path", "content"]}, write_file))
    reg.register(Tool(
        "edit_file", "Replace ONE exact occurrence of `old` with `new` in a file. "
                     "Fails loudly if `old` is missing or ambiguous.",
        {"type": "object", "properties": {"path": {"type": "string"},
                                          "old": {"type": "string"},
                                          "new": {"type": "string"}},
         "required": ["path", "old", "new"]}, edit_file))
    reg.register(Tool(
        "list_files", "List workspace files matching a glob pattern (default: all).",
        {"type": "object", "properties": {"pattern": {"type": "string"}}}, list_files))
    return reg
