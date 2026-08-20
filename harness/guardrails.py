"""Guardrails — the part of the harness that says "no".

A harness constrains the agent along three axes:

1. Budgets  — hard limits on turns, tool calls, and wall-clock time, so a
              confused agent burns a bounded amount of money and time.
2. Policy   — pattern-based allow/deny rules over tool calls (deny wins),
              e.g. block `rm -rf`, `curl`, `sudo` in bash.
3. Approval — an optional human-in-the-loop callback for anything the
              policy marks as "ask" rather than "allow" or "deny".

The design mirrors what production harnesses (Claude Code permission rules,
OpenHands ConfirmationPolicy) do, reduced to its teachable core.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable

# Commands that a coding agent essentially never needs and that cause the
# most regret. Deny-by-default beats apology-by-default.
DEFAULT_BASH_DENY = [
    r"\brm\s+(-\w*\s+)*-\w*[rf]",   # rm -r / rm -f variants
    r"\bsudo\b",
    r"\bshutdown\b|\breboot\b",
    r"\bmkfs\b|\bdd\s+if=",
    r"\bgit\s+push\s+.*--force",
    r"curl[^|;&]*\|\s*(ba)?sh",     # curl ... | sh
]


class GuardrailViolation(Exception):
    """Raised when a hard limit is exceeded; ends the run."""


@dataclass
class Verdict:
    allowed: bool
    reason: str = ""


@dataclass
class Guardrails:
    max_turns: int = 30
    max_tool_calls: int = 100
    max_seconds: float = 600.0
    bash_deny: list[str] = field(default_factory=lambda: list(DEFAULT_BASH_DENY))
    bash_ask: list[str] = field(default_factory=list)   # patterns needing approval
    approve: Callable[[str, dict], bool] | None = None  # human-in-the-loop hook

    def start(self) -> None:
        self._t0 = time.monotonic()
        self._turns = 0
        self._tool_calls = 0

    # ---- budgets ----------------------------------------------------------

    def on_turn(self) -> None:
        self._turns += 1
        if self._turns > self.max_turns:
            raise GuardrailViolation(f"max_turns exceeded ({self.max_turns})")
        if time.monotonic() - self._t0 > self.max_seconds:
            raise GuardrailViolation(f"time budget exceeded ({self.max_seconds}s)")

    def on_tool_call(self) -> None:
        self._tool_calls += 1
        if self._tool_calls > self.max_tool_calls:
            raise GuardrailViolation(f"max_tool_calls exceeded ({self.max_tool_calls})")

    # ---- policy -----------------------------------------------------------

    def check(self, tool_name: str, arguments: dict) -> Verdict:
        """Policy check for a single tool call. Deny > ask > allow."""
        if tool_name == "bash":
            cmd = arguments.get("command", "")
            for pat in self.bash_deny:
                if re.search(pat, cmd):
                    return Verdict(False, f"blocked by policy: /{pat}/")
            for pat in self.bash_ask:
                if re.search(pat, cmd):
                    if self.approve is None:
                        return Verdict(False, "needs approval but no approver is configured")
                    if not self.approve(tool_name, arguments):
                        return Verdict(False, "denied by human reviewer")
                    return Verdict(True, "approved by human reviewer")
        return Verdict(True)
