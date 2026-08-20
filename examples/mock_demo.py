"""Offline demo — no API key needed.

A scripted MockModel plays the role of the LLM so you can watch the harness
itself work: the loop, real tool execution, a guardrail block, and tracing.

Run:  python examples/mock_demo.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness import Harness, MockModel, ModelResponse, ToolCall, Trace

# The "model" will: write a script -> try a forbidden command (blocked by the
# guardrails) -> run the script instead -> report done.
script = [
    ModelResponse(
        text="I'll create the script first.",
        tool_calls=[ToolCall(id="t1", name="write_file", arguments={
            "path": "hello.py",
            "content": 'print("hello from inside the harness")\n',
        })],
        stop_reason="tool_use",
    ),
    ModelResponse(
        text="Now let me clean up the whole disk, just to be tidy.",
        tool_calls=[ToolCall(id="t2", name="bash",
                             arguments={"command": "sudo rm -rf /"})],
        stop_reason="tool_use",
    ),
    ModelResponse(
        text="That was blocked — running the script properly instead.",
        tool_calls=[ToolCall(id="t3", name="bash",
                             arguments={"command": "python3 hello.py"})],
        stop_reason="tool_use",
    ),
    ModelResponse(
        text="Done. I wrote hello.py and verified it runs (exit code 0).",
        stop_reason="end_turn",
    ),
]

with tempfile.TemporaryDirectory() as ws:
    harness = Harness(
        model=MockModel(script),
        workspace=ws,
        trace=Trace(echo=True),           # print every event as it happens
    )
    result = harness.run("Create hello.py that prints a greeting, and run it.")

print("\n--- final ---")
print(f"stopped_by : {result.stopped_by}")
print(f"turns      : {result.turns}")
print(f"tool calls : {result.tool_calls}")
print(f"final text : {result.final_text}")
