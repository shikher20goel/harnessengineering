"""Run a real task with a real model (requires ANTHROPIC_API_KEY).

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python examples/run_task.py "Write a tested prime-sieve module in sieve.py"

The agent works inside ./sandbox (created if missing). A full trace of the
run is written to ./sandbox/.trace.jsonl — read it. The trace is where
harness engineering starts: find the failure, then fix the environment.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness import AnthropicModel, Guardrails, Harness, Trace

task = sys.argv[1] if len(sys.argv) > 1 else \
    "Write fizzbuzz.py printing FizzBuzz for 1..30, run it, and show the output."

workspace = Path("./sandbox")

harness = Harness(
    model=AnthropicModel(model="claude-sonnet-4-5"),
    workspace=workspace,
    guardrails=Guardrails(
        max_turns=25,
        max_tool_calls=60,
        max_seconds=600,
        # anything matching these patterns requires a human "y":
        bash_ask=[r"\bpip\s+install", r"\bgit\s+push"],
        approve=lambda tool, args: input(f"approve {tool} {args}? [y/N] ").lower() == "y",
    ),
    trace=Trace(path=workspace / ".trace.jsonl", echo=True),
)

result = harness.run(task)
print("\n--- final ---")
print(result.final_text)
print(f"({result.turns} turns, {result.tool_calls} tool calls, "
      f"stopped by {result.stopped_by})")
