# 02 — How a Harness Works

## The loop at the center

Remove the branding, and every major agent — Claude Code, OpenAI's agent SDK, Hugging Face smolagents, mini-swe-agent, OpenHands — runs the same core loop:

```python
messages = [system_prompt, user_task]
while True:
    response = model.complete(messages, tools)
    if not response.tool_calls:        # model gave a final answer — done
        break
    results = execute(response.tool_calls)
    messages += [response, results]    # show the model what happened
```

Ask the model. If it wants tools, run them, show it the results, ask again. Stop when it answers without asking for a tool — or when a budget (max turns, max cost, max time) runs out.

Anthropic describes the same loop in words: **gather context → take action → check the work → repeat.**

That's ~30 lines (see [`harness/agent.py`](../harness/agent.py)). Everything else is the harness, and it breaks into five parts.

## Part 1: Tools — the agent's hands

Tools are the only way the agent can touch the world. Designing them is like designing a user interface, except the user is a model. What matters:

- **Error messages are instructions.** Tool output goes straight back to the model, so `"ERROR: old string appears 3 times; make it unique"` teaches the agent to recover, while a raw stack trace leaves it guessing. Anthropic's famous example: their agent kept fumbling relative file paths, so they made the tools *require* full paths — that entire mistake category vanished, and it helped set a benchmark record.
- **Cut long outputs.** A single build log can be megabytes. Cap every tool result (this repo keeps the start and end, drops the middle) so one big output can't push the actual task out of the model's memory.
- **Never let a tool crash the loop.** Every failure becomes a message the model can react to.
- **Fewer tools is usually better.** Every tool description is text the model must re-read on every turn. mini-swe-agent works with *only* a shell tool; the pi agent uses exactly four (read, write, edit, shell). Claude Code has ~15. Nobody needs fifty.

→ In this repo: [`harness/tools.py`](../harness/tools.py)

## Part 2: Memory — deciding what the agent sees

A model can only see a limited amount of text at once (its **context window** — think of it as a desk). Worse, models get less accurate as the desk fills up — Anthropic calls this "context rot." The harness keeps the desk clean:

- **A notes file** — a short rules file shown to the agent at the start of every turn. Claude Code: `CLAUDE.md`. Open standard: `AGENTS.md` (60,000+ projects, now under the Linux Foundation). This repo: `HARNESS.md`. This is where your hard-won rules live, and it survives everything below.
- **Throw away stale results** — a file read 20 turns ago is old news; replace it with a stub. The agent can re-read if it needs to.
- **Summarize old history ("compaction")** — near the limit, fold the oldest turns into a short summary and continue. Claude Code does this automatically; OpenHands measured up to 2× lower API cost with no quality loss.
- **Fetch on demand** — instead of pre-loading everything, give the agent file names and let it open what it needs. OpenAI's phrasing: "Give Codex a map, not a 1,000-page instruction manual." Aider's "repo map" (an auto-generated outline of your codebase's key files and functions) is a smart version of the map.
- **Helper agents** — for a big side-quest ("find where auth is handled"), spawn a second agent with a fresh, empty desk. Only its short summary comes back — the main agent gets the answer without the 50,000 words of searching.

→ In this repo: [`harness/context.py`](../harness/context.py)

## Part 3: Guardrails — the part that says "no"

An agent spends your money and changes your files in a loop, so it needs brakes. Three kinds, softest to hardest:

1. **Budgets** — max turns, max tool calls, max minutes. Every serious harness has them: a confused agent should cost a bounded amount, then stop.
2. **Block / ask lists** — some commands are simply banned (`rm -rf`, `sudo`, `curl ... | sh`, force-push). Gray-zone commands (`pip install`, `git push`) pause and ask a human "allow? y/n". Block beats ask; ask beats allow.
3. **Real walls (sandboxing)** — for autonomous agents, run everything in a container that physically can't touch outside files or make arbitrary network calls. You need *both* walls — files and network — or a hijacked agent could read your secrets or send them out. Bonus from Anthropic: with real walls in place, they cut "allow this?" popups by 84%, because you don't have to ask about actions inside a boundary you trust.

Human-in-the-loop (a person approving risky steps) is the universal backstop.

→ In this repo: [`harness/guardrails.py`](../harness/guardrails.py)

## Part 4: Checking the work

An agent that can't check its work will confidently hand you broken code. Two ingredients, and you need both:

- **Guidance before acting** — the notes file, project conventions, types, docs. Steers the agent up front.
- **Checks after acting** — tests, linters, builds, review. Catches drift.

Böckeler's warning about using only one: "you get either an agent that keeps repeating the same mistakes… or an agent that encodes rules but never finds out whether they worked."

Which checks to trust, per Anthropic: automatic ones (tests, linters) are best; screenshots next; asking another AI to judge is weakest. OpenAI's version: don't write a doc *asking* agents to follow the architecture — write a lint rule that *fails the build* when they don't.

One rule to engrave, because agents under pressure really do cheat: **"It is unacceptable to remove or edit tests."**

## Part 5: The flight recorder

Log everything — every model reply, tool call, blocked command, and summary event — to a simple file, one event per line. When a long run fails, the real mistake usually happened many turns before the visible failure; the log is how you find it. OpenAI went further and gave their agents live access to app logs and browser state so the *agent* can debug the system it's changing.

→ In this repo: [`harness/trace.py`](../harness/trace.py)

## Big harnesses vs small harnesses

The field has two ends. **Big**: OpenHands and Google's ADK, with typed event logs, risk analyzers, and fixed step-by-step workflows. **Small**: mini-swe-agent (~100 lines, shell only) and Terminal-Bench's reference agent, which gets nothing but a raw terminal. As models improve, small harnesses keep closing the gap on the feature side — but the limits-and-checks side (budgets, blocks, sandboxes, tests, logs) stays essential at every size. As LangChain's Harrison Chase puts it: "Better models expand what harnesses need to do, not replace the need for them."

Next: [03 — How to build one](03-how-to-implement.md).
