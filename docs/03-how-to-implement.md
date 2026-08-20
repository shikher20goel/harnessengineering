# 03 — How to Implement a Harness

Two halves: **building** the initial scaffolding (a weekend), and **practicing** harness engineering on it (forever). The build below maps 1:1 to this repo's code.

## Part A: Build the scaffolding

### Step 0: Make the model swappable — and mockable

Define one narrow interface (`complete(system, messages, tools) → response`) and put every provider detail behind it. Then write a `MockModel` that replays scripted responses. This single decision makes the entire harness deterministic to test: you can unit-test guardrails, truncation, and compaction without an API key or a nondeterministic model in the loop.
→ [`harness/model.py`](../harness/model.py)

### Step 1: Write the loop

The ~30-line canonical loop from [doc 02](02-how-a-harness-works.md), with three properties production loops share: it terminates when the model stops calling tools; every iteration checks budgets *first*; and nothing a tool does can crash it — all failures become messages the model can react to.
→ [`harness/agent.py`](../harness/agent.py)

### Step 2: Build a small, sharp tool layer

Start with the four tools pi ships and mini-swe-agent approximates with bash alone: read, write, edit, bash. Then apply the ACI checklist:

- Descriptions written for the model, stating *when* to use the tool, not just what it does.
- Errors as guidance: `"old string appears 3 times; make it unique"` beats a `ValueError`.
- Hard truncation of outputs (this repo: 20k chars, keep head+tail) — one `cat` of a build log must not evict the task from context.
- Path confinement: file tools resolve against a workspace root and refuse escapes.

Resist tool sprawl. Anthropic warns against "bloated tool sets" with "ambiguous decision points"; every tool schema is context the model pays for on every request.
→ [`harness/tools.py`](../harness/tools.py)

### Step 3: Add guardrails before you need them

- **Budgets**: max turns, max tool calls, wall-clock. A confused agent should cost a bounded amount.
- **Policy**: regex deny-list for the classic regrets (`rm -rf`, `sudo`, `curl | sh`, force-push), an "ask" list routed to a human callback for the gray zone (`pip install`, `git push`). Deny beats ask beats allow.
- **Isolation**: run the workspace in a container or VM when the agent is autonomous. Treat in-process "sandboxes" as conveniences, not boundaries.
→ [`harness/guardrails.py`](../harness/guardrails.py)

### Step 4: Manage the context window

In order of value-per-line-of-code:

1. A **memory file** (`HARNESS.md` here; CLAUDE.md/AGENTS.md in production) injected into the system prompt every request. Keep it under ~60 lines — "every line is competing for attention" (Osmani).
2. **Tool-result aging**: stub out all but the N most recent tool results; the agent can re-read.
3. **Compaction**: over a token budget, fold the oldest turns into a summary — preserving the original task, and never orphaning a tool result from its tool call (an API-level constraint that's easy to miss).
→ [`harness/context.py`](../harness/context.py)

### Step 5: Trace everything

Append every event — model responses, tool calls and results, policy blocks, compactions — to a JSONL file. This is the flight recorder; Part B runs on it.
→ [`harness/trace.py`](../harness/trace.py)

### Step 6: Test the harness, not the model

With `MockModel`, assert the properties that matter: the loop terminates; dangerous commands are blocked *before* execution; a runaway agent hits `max_turns`; path escapes are refused; old results get elided; compaction preserves the task; the memory file reaches the system prompt. Eleven such tests in [`tests/test_harness.py`](../tests/test_harness.py) run in 50 ms.

## Part B: Practice the discipline

The scaffolding is table stakes. Harness engineering proper is a loop you run on top of it:

### The Ratchet Principle

> "Every line in a good AGENTS.md should be traceable back to a specific thing that went wrong." — Addy Osmani

Hashimoto's original formulation: every time the agent makes a mistake, don't hope it does better next time — change the environment so *that* mistake can't recur. The fix escalates through four levels:

1. **A rule** in the memory file ("run `pytest` before declaring done") — cheapest, weakest: it's advisory.
2. **A tool** that makes the right thing easy (a `run_tests` tool that already knows the right flags; a screenshot script) — the agent no longer has to figure it out.
3. **A sensor** that catches the failure mechanically (a linter, a test, a CI check, a review agent) — feedback instead of hope.
4. **A constraint** that makes the failure impossible (a deny rule, a sandbox boundary, a typed schema, dependency-direction lint) — OpenAI's "enforcement over prescription."

Prefer the highest level you can afford. Rules drift; constraints don't.

### The working rhythm

1. Run a real task. 2. Read the trace (and the diff). 3. Find the first place the agent went wrong. 4. Ask: what in the *environment* allowed that? 5. Fix at the highest ratchet level that's proportionate. 6. Re-run. Keep the memory file minimal and earned — start from an empty harness and let failures grow it, because "the right harness for your codebase is shaped by your failure history. You can't download it" (Osmani).

### Scaling up (when you outgrow this repo)

- **Long-horizon tasks**: initializer/executor agent split, JSON feature checklists, progress files, git-per-session (Anthropic's long-running-agents harness).
- **Parallelism and context isolation**: sub-agents returning distilled summaries.
- **Deterministic control flow**: workflow graphs (sequential/parallel/loop) instead of prompting the model to follow a process — ADK and LangGraph territory.
- **Real sandboxing**: containers with filesystem *and* network boundaries.
- **Evals**: a fixed task suite you re-run after every harness change, because a harness "improvement" that drops your pass rate is a regression, whatever it feels like.

Continue to [04 — Resources](04-resources.md).
