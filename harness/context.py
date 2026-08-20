"""Context management — deciding what the model gets to see.

The context window is the scarcest resource in an agent system. This module
implements the three techniques almost every production harness converges on:

1. Persistent memory file (HARNESS.md) — durable project rules, injected
   into the system prompt every request, in the spirit of CLAUDE.md /
   AGENTS.md. This is where "engineer the harness" fixes accumulate: every
   time the agent makes a mistake, a rule lands here so it can't recur.
2. Tool-result aging — old tool results are collapsed to a stub once the
   history grows, because a `read_file` from 20 turns ago is stale anyway;
   the agent can always re-read.
3. Compaction — when the estimated token count still exceeds budget, the
   oldest turns are summarized into a single synthetic exchange. (Here the
   summary is mechanical; production harnesses use an LLM pass.)
"""

from __future__ import annotations

import json
from pathlib import Path

MEMORY_FILENAME = "HARNESS.md"


def estimate_tokens(messages: list[dict]) -> int:
    """Crude but monotonic: ~4 chars per token."""
    return len(json.dumps(messages)) // 4


class ContextManager:
    def __init__(self, workspace: Path, token_budget: int = 60_000,
                 keep_recent_results: int = 6):
        self.workspace = Path(workspace)
        self.token_budget = token_budget
        self.keep_recent_results = keep_recent_results

    # ---- persistent memory --------------------------------------------------

    def load_memory(self) -> str:
        """Project rules that survive across sessions (and compaction)."""
        f = self.workspace / MEMORY_FILENAME
        return f.read_text() if f.exists() else ""

    def build_system_prompt(self, base_prompt: str) -> str:
        memory = self.load_memory()
        if memory:
            return f"{base_prompt}\n\n# Project rules ({MEMORY_FILENAME})\n{memory}"
        return base_prompt

    # ---- pruning + compaction ------------------------------------------------

    def prepare(self, messages: list[dict]) -> list[dict]:
        """Return the message list actually sent to the model."""
        msgs = self._age_tool_results(messages)
        if estimate_tokens(msgs) > self.token_budget:
            msgs = self._compact(msgs)
        return msgs

    def _age_tool_results(self, messages: list[dict]) -> list[dict]:
        """Collapse all but the N most recent tool results to a stub."""
        result_positions = [
            i for i, m in enumerate(messages)
            if m["role"] == "user" and isinstance(m["content"], list)
            and any(b.get("type") == "tool_result" for b in m["content"])
        ]
        stale = set(result_positions[: -self.keep_recent_results or None]
                    if len(result_positions) > self.keep_recent_results else [])
        out = []
        for i, m in enumerate(messages):
            if i in stale:
                content = [
                    {**b, "content": "[result elided by harness — re-run the tool if needed]"}
                    if b.get("type") == "tool_result" else b
                    for b in m["content"]
                ]
                out.append({"role": "user", "content": content})
            else:
                out.append(m)
        return out

    @staticmethod
    def _is_tool_result(m: dict) -> bool:
        return (m["role"] == "user" and isinstance(m["content"], list)
                and any(b.get("type") == "tool_result" for b in m["content"]))

    def _compact(self, messages: list[dict]) -> list[dict]:
        """Fold the oldest half of the history into one synthetic summary turn.

        The first message (the task) and the recent half are preserved
        verbatim; the middle is replaced by a digest of what happened.
        """
        if len(messages) < 6:
            return messages
        # Pick a split point that does not orphan a tool_result from its
        # tool_use (the API rejects a tool_result whose call was dropped).
        split = len(messages) // 2
        while split < len(messages) and self._is_tool_result(messages[split]):
            split += 1
        head, mid, tail = messages[:1], messages[1:split], messages[split:]
        digest_lines = []
        for m in mid:
            if m["role"] == "assistant" and isinstance(m["content"], list):
                for b in m["content"]:
                    if b.get("type") == "tool_use":
                        digest_lines.append(f"- called {b['name']}({json.dumps(b['input'])[:120]})")
                    elif b.get("type") == "text" and b["text"].strip():
                        digest_lines.append(f"- said: {b['text'][:160]}")
            elif m["role"] == "assistant":
                digest_lines.append(f"- said: {str(m['content'])[:160]}")
        summary = ("[Earlier turns compacted by the harness]\n"
                   + "\n".join(digest_lines[-40:]))
        synthetic = [
            {"role": "assistant", "content": summary},
            {"role": "user", "content": "Understood — continue from where you left off."},
        ]
        return head + synthetic + tail
