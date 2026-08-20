"""Tests for the harness — run with:  python -m pytest tests/ -q

Note what is being tested: NOT the model (it's mocked), but everything
around it. That separation — a harness you can test deterministically,
independent of the stochastic model — is itself a harness-engineering
principle.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from harness import (Guardrails, Harness, MockModel, ModelResponse, ToolCall,
                     build_default_tools)
from harness.context import ContextManager
from harness.tools import truncate


def make_harness(tmp_path, script, **guard_kwargs):
    return Harness(model=MockModel(script), workspace=tmp_path,
                   guardrails=Guardrails(**guard_kwargs))


# ---- the loop ---------------------------------------------------------------

def test_loop_terminates_when_model_stops(tmp_path):
    h = make_harness(tmp_path, [ModelResponse(text="all done")])
    r = h.run("do nothing")
    assert r.final_text == "all done"
    assert r.stopped_by == "model"
    assert r.turns == 1 and r.tool_calls == 0


def test_tools_execute_and_feed_back(tmp_path):
    script = [
        ModelResponse(tool_calls=[ToolCall("t1", "write_file",
                                           {"path": "a.txt", "content": "hi"})]),
        ModelResponse(text="done"),
    ]
    h = make_harness(tmp_path, script)
    r = h.run("write a file")
    assert (tmp_path / "a.txt").read_text() == "hi"
    # the tool result was appended to history for the model to see
    results = [b for m in r.messages if isinstance(m["content"], list)
               for b in m["content"] if b.get("type") == "tool_result"]
    assert results and not results[0]["is_error"]


def test_bad_tool_call_does_not_crash_loop(tmp_path):
    script = [
        ModelResponse(tool_calls=[ToolCall("t1", "no_such_tool", {})]),
        ModelResponse(tool_calls=[ToolCall("t2", "read_file", {"path": "missing.txt"})]),
        ModelResponse(text="recovered"),
    ]
    r = make_harness(tmp_path, script).run("survive errors")
    assert r.final_text == "recovered"
    assert r.stopped_by == "model"


# ---- guardrails -------------------------------------------------------------

def test_dangerous_bash_is_blocked(tmp_path):
    script = [
        ModelResponse(tool_calls=[ToolCall("t1", "bash", {"command": "sudo rm -rf /"})]),
        ModelResponse(text="ok"),
    ]
    r = make_harness(tmp_path, script).run("try something bad")
    blocked = [b for m in r.messages if isinstance(m["content"], list)
               for b in m["content"]
               if b.get("type") == "tool_result" and b["is_error"]]
    assert blocked and "Blocked" in blocked[0]["content"]
    assert r.tool_calls == 0            # nothing actually executed


def test_max_turns_stops_runaway_agent(tmp_path):
    looping = ModelResponse(tool_calls=[ToolCall("t", "bash", {"command": "true"})])
    script = [looping] * 50 + [ModelResponse(text="never reached")]
    r = make_harness(tmp_path, script, max_turns=5).run("loop forever")
    assert r.stopped_by == "guardrail"
    assert r.turns <= 5


def test_path_escape_is_refused(tmp_path):
    reg = build_default_tools(tmp_path)
    out, is_error = reg.execute("read_file", {"path": "../../etc/passwd"})
    assert is_error and "escapes the workspace" in out


def test_ask_pattern_requires_approver(tmp_path):
    script = [
        ModelResponse(tool_calls=[ToolCall("t1", "bash", {"command": "pip install x"})]),
        ModelResponse(text="done"),
    ]
    h = Harness(model=MockModel(script), workspace=tmp_path,
                guardrails=Guardrails(bash_ask=[r"pip install"], approve=None))
    r = h.run("install stuff")
    assert r.tool_calls == 0


# ---- context management -------------------------------------------------------

def test_tool_result_truncation():
    big = "x" * 100_000
    small = truncate(big, limit=1_000)
    assert len(small) < 2_000 and "truncated by harness" in small


def test_old_tool_results_are_elided(tmp_path):
    cm = ContextManager(tmp_path, keep_recent_results=1)
    msgs = []
    for i in range(4):
        msgs.append({"role": "assistant", "content": [
            {"type": "tool_use", "id": f"t{i}", "name": "bash", "input": {}}]})
        msgs.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": f"t{i}", "content": f"result {i}"}]})
    prepared = cm.prepare(msgs)
    texts = [b["content"] for m in prepared if isinstance(m["content"], list)
             for b in m["content"] if b.get("type") == "tool_result"]
    assert texts[-1] == "result 3"                      # newest kept
    assert all("elided" in t for t in texts[:-1])        # older stubbed


def test_compaction_kicks_in_over_budget(tmp_path):
    cm = ContextManager(tmp_path, token_budget=200, keep_recent_results=2)
    msgs = [{"role": "user", "content": "the task"}]
    for i in range(10):
        msgs.append({"role": "assistant", "content": f"thinking step {i} " + "pad " * 30})
        msgs.append({"role": "user", "content": f"feedback {i} " + "pad " * 30})
    prepared = cm.prepare(msgs)
    assert len(prepared) < len(msgs)
    assert prepared[0]["content"] == "the task"          # task always survives
    assert any("compacted by the harness" in str(m["content"]) for m in prepared)


def test_memory_file_lands_in_system_prompt(tmp_path):
    (tmp_path / "HARNESS.md").write_text("Never use tabs. Run pytest before finishing.")
    h = make_harness(tmp_path, [ModelResponse(text="ok")])
    h.run("anything")
    sent_system = h.model.calls[0]["system"]
    assert "Never use tabs" in sent_system


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
