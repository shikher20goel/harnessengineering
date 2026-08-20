"""Tracing — if you can't see what the agent did, you can't engineer the harness.

Every event in a run is appended to a JSONL file: model requests, tool calls,
guardrail decisions, compactions, and the final result. Harness engineering
is an empirical loop — observe a failure in the trace, add a rule or a tool,
re-run — and this file is where the observations come from.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path


class Trace:
    def __init__(self, path: Path | str | None = None, echo: bool = False):
        self.path = Path(path) if path else None
        self.echo = echo
        self.events: list[dict] = []
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, kind: str, **data) -> None:
        event = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "kind": kind,
            **data,
        }
        self.events.append(event)
        if self.path:
            with self.path.open("a") as f:
                f.write(json.dumps(event, default=str) + "\n")
        if self.echo:
            brief = {k: (str(v)[:200] + "…" if len(str(v)) > 200 else v)
                     for k, v in data.items()}
            print(f"[{kind}] {json.dumps(brief, default=str)}")
