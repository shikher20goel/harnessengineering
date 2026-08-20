# 02 — How a Harness Works

## The canonical loop

Strip away branding and every major agent system — Claude Code, the OpenAI Agents SDK, Hugging Face smolagents, mini-swe-agent, OpenHands — runs the same core loop:

```python
messages = [system_prompt, user_task]
while True:
    response = model.complete(messages, tools)
    if not response.tool_calls:        # model produced a final answer
        break
    results = execute(response.tool_calls)
    messages += [response, results]    # feed observations back
```

Anthropic frames the same thing conceptually as **gather context → take action → verify work → repeat**. The loop terminates when the model stops calling tools (Claude/OpenAI SDKs), emits a typed final output (OpenAI SDK), or a budget runs out (`max_turns`, cost, wall time — everyone).

That loop is ~30 lines (see [`harness/agent.py`](../harness/agent.py)). Everything else is the harness. It decomposes into six layers.

## Layer 1: The tool layer

Tools are the agent's only effectors, and tool *design* is interface design for a model. Anthropic's agent-computer-interface doctrine: document tools like you'd design a UI; keep formats close to what the model saw in training; make error messages actionable; "poka-yoke" the arguments so misuse is impossible (their example: requiring absolute paths eliminated an entire error class and helped push Claude 3.5 Sonnet to then-SOTA 49% on SWE-bench Verified).

Design spectrum in the wild: mini-swe-agent exposes *only bash* (no tool-calling API at all — actions are parsed from text, which makes it work with any model); pi uses exactly four tools (read/write/edit/bash); Claude Code has ~15 plus MCP; smolagents' `CodeAgent` has the model write Python that *composes* tools, cutting steps ~30% (the CodeAct result). Two universal rules: sanitize and **truncate** tool output before it enters the context, and never let a tool exception kill the loop — return it as feedback instead.
→ In this repo: [`harness/tools.py`](../harness/tools.py)

## Layer 2: Context management

The context window is a finite, degrading resource — Anthropic: "as token count increases, retrieval accuracy declines" (context rot). Production techniques:

- **Persistent memory files** — CLAUDE.md / AGENTS.md, re-injected every request, surviving compaction. AGENTS.md is now an open format used by 60k+ repos, stewarded under the Linux Foundation. This is where harness fixes accumulate.
- **Compaction** — when the window nears its limit, older history is summarized in place (Claude Code's auto-compact; OpenHands' `LLMSummarizingCondenser` cut API cost up to 2× with no performance loss).
- **Tool-result aging / truncation** — old tool outputs are stubbed out; the agent can re-read.
- **Just-in-time retrieval** — keep lightweight identifiers (file paths, queries) and fetch on demand rather than pre-loading ("progressive disclosure"; OpenAI: "Give Codex a map, not a 1,000-page instruction manual"). Aider's graph-ranked *repo map* is the precomputed variant.
- **Sub-agent isolation** — spawn a fresh-context agent for a subtask; only a distilled summary (Anthropic: typically 1,000–2,000 tokens) returns to the parent. HumanLayer calls sub-agents a "context firewall."
→ In this repo: [`harness/context.py`](../harness/context.py)

## Layer 3: Guardrails and permissions

Three escalating mechanisms:

1. **Budgets** — max turns, max cost, wall-clock limits. Every serious harness has them because autonomy means "higher costs, and the potential for compounding errors" (Anthropic).
2. **Policy** — allow/deny/ask rules over tool calls: Claude Code's parameterized permission rules (`Bash(npm *)`) and permission modes; OpenHands' `SecurityAnalyzer` risk-rates every call and a `ConfirmationPolicy` decides whether to pause for approval.
3. **Sandboxing** — OS-level isolation of filesystem *and* network (Anthropic uses bubblewrap/Seatbelt; "effective sandboxing requires both"; it cut permission prompts 84% because boundaries replace per-action questions). Docker-per-task is the benchmark-world standard. smolagents warns bluntly that its local executor "is not a security boundary" — real isolation needs E2B/Modal/Docker.

Human-in-the-loop is the backstop everywhere: plan modes, approval callbacks, review gates.
→ In this repo: [`harness/guardrails.py`](../harness/guardrails.py)

## Layer 4: Feedback and verification

Böckeler's control-theory framing is the cleanest: a harness needs **guides** (feedforward — conventions, docs, type systems, scripts) *and* **sensors** (feedback — linters, tests, review agents). "Separately, you get either an agent that keeps repeating the same mistakes… or an agent that encodes rules but never finds out whether they worked."

Anthropic's verification hierarchy: rules-based checks (lint, tests) beat visual feedback (screenshots) beat LLM-as-judge. OpenAI's version: mechanical enforcement over prescription — custom linters and CI that *validate* architecture rather than documents that request it. And from the long-running-agents work, one anti-reward-hacking rule worth engraving: "It is unacceptable to remove or edit tests."

## Layer 5: State and long-horizon structure

Agents outlive context windows, so durable state lives outside the model: git as memory and undo (Aider auto-commits; Anthropic's harness requires merge-ready commits per session), progress files (`claude-progress.txt`), JSON feature lists with pass/fail booleans, initializer-agent/executor-agent splits, and session-startup orientation checklists. Anthropic is blunt that "compaction isn't sufficient" for long-horizon work — you need externalized state.

## Layer 6: Observability

Traces of every model call, tool call, and policy decision. Not optional: harness engineering is empirical, and the trace is where you find out *why* a run failed before you fix the environment. OpenAI went as far as giving agents live access to logs (LogQL), metrics (PromQL), and browser state (CDP) so the *agent* can observe the system it's changing.
→ In this repo: [`harness/trace.py`](../harness/trace.py)

## Two design poles

The field spans **maximal harnesses** (OpenHands: typed event logs, condensers, security analyzers; Google ADK: deterministic Sequential/Parallel/Loop workflow agents) and **minimal harnesses** (mini-swe-agent, pi, Terminal-Bench's Terminus, which offers a model nothing but a tmux pane). The trend line: as models strengthen, minimal harnesses close the gap on bounded tasks — but the constraint-and-verification layers (guardrails, sensors, budgets) stay load-bearing at every point on the spectrum. Harrison Chase: "Better models expand what harnesses need to do, not replace the need for them."

Continue to [03 — How to implement one](03-how-to-implement.md).
