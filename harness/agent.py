"""The agent loop — the heart of every harness, and the smallest part of it.

The loop itself is ~30 lines and is essentially identical across Claude Code,
the OpenAI Agents SDK, smolagents, mini-swe-agent, and OpenHands:

    while True:
        response = model.complete(system, messages, tools)
        if not response.wants_tools:
            break                       # the model is done
        results = execute(response.tool_calls)
        messages += [response, results]

Everything AROUND that loop — the tool layer, guardrails, context management,
tracing — is what harness engineering is actually about. Notice how little of
this file is "AI" and how much is plain systems engineering.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .context import ContextManager
from .guardrails import Guardrails, GuardrailViolation
from .tools import ToolRegistry, build_default_tools
from .trace import Trace

DEFAULT_SYSTEM_PROMPT = """\
You are a careful software engineering agent operating inside a sandboxed
workspace via the tools provided. Work autonomously:

- Inspect before you act: list or read files before editing them.
- Prefer small, verifiable steps; run code or tests to check your work.
- When the task is complete, verify the result, then reply WITHOUT calling
  any tool, stating what you did and how you verified it.
- If you are blocked, say so plainly instead of guessing.
"""


@dataclass
class RunResult:
    final_text: str
    turns: int
    tool_calls: int
    stopped_by: str          # "model" | "guardrail"
    messages: list[dict]


class Harness:
    """Wires model + tools + guardrails + context + tracing into one runnable unit."""

    def __init__(self, model, workspace: str | Path,
                 tools: ToolRegistry | None = None,
                 guardrails: Guardrails | None = None,
                 context: ContextManager | None = None,
                 trace: Trace | None = None,
                 system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        self.model = model
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.tools = tools or build_default_tools(self.workspace)
        self.guardrails = guardrails or Guardrails()
        self.context = context or ContextManager(self.workspace)
        self.trace = trace or Trace()
        self.system_prompt = system_prompt

    def run(self, task: str) -> RunResult:
        messages: list[dict] = [{"role": "user", "content": task}]
        system = self.context.build_system_prompt(self.system_prompt)
        self.guardrails.start()
        self.trace.log("run_start", task=task, workspace=str(self.workspace))

        turns = tool_calls = 0
        final_text, stopped_by = "", "model"

        while True:
            # -- budgets --------------------------------------------------
            try:
                self.guardrails.on_turn()
            except GuardrailViolation as e:
                final_text, stopped_by = f"Run stopped by harness: {e}", "guardrail"
                self.trace.log("guardrail_stop", reason=str(e))
                break
            turns += 1

            # -- context discipline: prune/compact, then call the model ---
            prepared = self.context.prepare(messages)
            response = self.model.complete(system, prepared, self.tools.specs())
            self.trace.log("model_response", text=response.text,
                           n_tool_calls=len(response.tool_calls),
                           stop_reason=response.stop_reason)

            if not response.wants_tools:
                final_text = response.text          # the model decided it's done
                break

            # -- execute the requested tools, under policy -----------------
            assistant_blocks: list[dict] = []
            if response.text:
                assistant_blocks.append({"type": "text", "text": response.text})
            result_blocks: list[dict] = []

            for call in response.tool_calls:
                assistant_blocks.append({"type": "tool_use", "id": call.id,
                                         "name": call.name, "input": call.arguments})
                try:
                    self.guardrails.on_tool_call()
                except GuardrailViolation as e:
                    result_blocks.append(self._result(call.id, f"Blocked: {e}", True))
                    self.trace.log("guardrail_stop", reason=str(e))
                    stopped_by = "guardrail"
                    continue

                verdict = self.guardrails.check(call.name, call.arguments)
                if not verdict.allowed:
                    result_blocks.append(self._result(call.id, f"Blocked: {verdict.reason}", True))
                    self.trace.log("tool_blocked", tool=call.name,
                                   args=call.arguments, reason=verdict.reason)
                    continue

                output, is_error = self.tools.execute(call.name, call.arguments)
                tool_calls += 1
                self.trace.log("tool_result", tool=call.name, args=call.arguments,
                               is_error=is_error, output=output[:500])
                result_blocks.append(self._result(call.id, output, is_error))

            messages.append({"role": "assistant", "content": assistant_blocks})
            messages.append({"role": "user", "content": result_blocks})

        self.trace.log("run_end", turns=turns, tool_calls=tool_calls,
                       stopped_by=stopped_by)
        return RunResult(final_text=final_text, turns=turns,
                         tool_calls=tool_calls, stopped_by=stopped_by,
                         messages=messages)

    @staticmethod
    def _result(tool_use_id: str, content: str, is_error: bool) -> dict:
        return {"type": "tool_result", "tool_use_id": tool_use_id,
                "content": content, "is_error": is_error}
