# 03 — How to Build a Harness

Two halves: **building** the scaffolding (a weekend of work) and **practicing** the improvement habit on it (ongoing). Every step below points to the matching file in this repo.

## Part A: Build the scaffolding

### Step 0: Make the model swappable — and fakeable

Hide the AI behind one tiny interface: `complete(system, messages, tools) → response`. Then write a **fake model** that just replays a script of pre-written responses.

Why bother? Because now your whole harness can be tested like normal software — no API key, no randomness, no cost. This one decision pays for itself immediately.
→ [`harness/model.py`](../harness/model.py)

### Step 1: Write the loop

The ~30-line loop from [doc 02](02-how-a-harness-works.md), with three properties every production loop shares:

- it stops when the model answers without asking for a tool;
- it checks budgets *before* each turn, not after;
- nothing a tool does can crash it — every failure becomes a message the model can read and react to.

→ [`harness/agent.py`](../harness/agent.py)

### Step 2: Build a few good tools

Start with four: **read, write, edit, run-a-command**. Then polish them:

- Write each description for the model: say *when* to use the tool, not just what it does.
- Make errors helpful: `"old string appears 3 times; make it unique"` beats a raw exception.
- Cap output size (this repo: 20,000 characters, keep the start and end) so one long log can't flood the agent's memory.
- Lock file tools to one working folder, and refuse any path that tries to escape it.

Resist adding more tools. Each one is text the model re-reads every turn.
→ [`harness/tools.py`](../harness/tools.py)

### Step 3: Add the brakes before you need them

- **Budgets**: max turns, max tool calls, max minutes. A confused agent should cost a bounded amount.
- **Block list**: ban the classic disasters outright — `rm -rf`, `sudo`, `curl ... | sh`, force-push.
- **Ask list**: gray-zone commands (`pip install`, `git push`) pause and ask a human "allow? y/n".
- **A real wall**: if the agent runs unattended, put it in a container. In-process "sandboxes" are conveniences, not walls.

→ [`harness/guardrails.py`](../harness/guardrails.py)

### Step 4: Manage the agent's memory

In order of value for effort:

1. **A notes file** (here `HARNESS.md`; in the wild, `CLAUDE.md` / `AGENTS.md`), added to the system prompt on every turn. Keep it under ~60 lines — every line competes for the model's attention.
2. **Stale-result cleanup**: keep only the last few tool outputs in full; replace older ones with "result removed — re-run if needed."
3. **Summarizing** (compaction): past a size limit, fold the oldest turns into a short summary. Two rules: never summarize away the original task, and never separate a tool call from its result (the API will reject that — easy to miss, annoying to debug).

→ [`harness/context.py`](../harness/context.py)

### Step 5: Log everything

Every event — model replies, tool calls and results, blocked commands, summaries — goes to one file, one JSON line each. This is your flight recorder; Part B runs on it.
→ [`harness/trace.py`](../harness/trace.py)

### Step 6: Test the harness, not the model

Using the fake model, write tests for the things that must always be true:

- the loop stops when the model finishes
- a dangerous command gets blocked *before* it runs
- a runaway agent hits the turn limit
- a path escape gets refused
- old results get cleaned up; summaries keep the task
- the notes file actually reaches the model

Eleven such tests in [`tests/test_harness.py`](../tests/test_harness.py) run in 50 milliseconds.

## Part B: Practice the habit

The scaffolding is table stakes. The real skill is a loop you run forever:

### The one habit

> "Every line in a good AGENTS.md should be traceable back to a specific thing that went wrong." — Addy Osmani

Mitchell Hashimoto's original version: every time the agent does something bad, change its world so *that exact thing* can't happen again. The fix climbs a ladder, weakest to strongest:

1. **A rule** in the notes file ("run pytest before saying done") — cheap, but only advice.
2. **A tool** that makes the right thing easy (a `run_tests` tool that knows the right flags) — the agent no longer has to figure it out.
3. **A check** that catches the mistake automatically (a test, a linter, a CI gate) — caught, not hoped against.
4. **A wall** that makes the mistake impossible (a banned command, a sandbox, a stricter tool) — deleted.

Climb as high as is proportionate. Rules get ignored. Walls don't.

### The working rhythm

1. Run a real task.
2. Read the log (and the code diff).
3. Find the **first** wrong step — not the last one.
4. Ask: what in the *environment* allowed this?
5. Fix it at the highest ladder level that makes sense.
6. Run it again.

Start with an empty notes file and let real failures fill it. Don't copy someone else's — "the right harness for your codebase is shaped by your failure history. You can't download it" (Osmani).

And keep a small fixed set of test tasks that you re-run after every harness change. If a change drops your pass rate, it was a regression, no matter how clever it felt.

### When you outgrow this repo

- **Very long tasks**: split into a "setup" agent (builds a task list and progress file) and a "worker" agent that does one item per session, committing to git each time — Anthropic's pattern for agents that run for days.
- **Parallel work**: helper agents with fresh memory that return only short summaries.
- **Fixed processes**: when steps must happen in a set order, encode the order in code (a workflow), don't ask the model to remember it.
- **Real isolation**: containers with both file and network walls.
- **A proper test suite of tasks**: your safety net for every future harness change.

Next: [04 — Sources](04-resources.md).
