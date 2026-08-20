# Harness Engineering

**Everything in an AI agent except the model — explained simply, with working code.**

An AI model just turns text into text. An **agent** is a model placed inside a loop and given tools, so it can actually do things: run commands, read files, write code. The **harness** is everything around the model that makes this work: the loop, the tools, the safety rules, the memory management, and the logs.

**Harness engineering** is the practice of building that scaffolding and improving it every time the agent makes a mistake — so the same mistake can never happen again.

```
Agent = Model + Harness
```
> "If you're not the model, you're the harness." — Vivek Trivedy, LangChain

## Why should you care?

Because the harness changes results as much as the model does. On the public Terminal-Bench benchmark, the *same* AI model scores anywhere from 58% to 76% depending only on which harness wraps it. That ~18-point gap is about the size of a full model-generation upgrade. The model is rented — everyone calls the same API. The harness is the part you own.

## What's in this repo

1. **Plain-English docs** (`docs/`) — what harness engineering is, how a harness works, and how to build one. Based on the original writings from OpenAI, Anthropic, Mitchell Hashimoto, LangChain, martinfowler.com, and Addy Osmani — with all sources linked.
2. **A small working harness** (`harness/`) — about 500 lines of plain Python, no libraries needed. It has all five parts of a real harness: the agent loop, tools, guardrails, memory management, and logging. Written to be read and learned from.
3. **A Medium article** (`article/`) — the whole story in one easy read.

## Try it in 30 seconds (no API key needed)

```bash
git clone https://github.com/shikher20goel/harnessengineering
cd harnessengineering

# Watch the harness work with a fake, scripted model:
# it writes a file, tries `sudo rm -rf /` (blocked!), then finishes properly.
python3 examples/mock_demo.py

# Run the tests (they test the harness, not the AI — so no key needed):
pip install pytest && python3 -m pytest tests/ -q

# Run a real task with a real model:
export ANTHROPIC_API_KEY=sk-ant-...
python3 examples/run_task.py "Write a tested prime sieve in sieve.py"
```

## The code, mapped to the ideas

```
harness/
├── agent.py       # the ~30-line loop every agent product uses, plus the wiring
├── model.py       # talks to the AI (Anthropic API), plus a fake model for testing
├── tools.py       # run commands + read/write/edit files, with safe limits
├── guardrails.py  # budgets, blocked commands, "ask a human first" rules
├── context.py     # notes file (HARNESS.md), cleanup of old results, summarizing
└── trace.py       # logs every event to a file — the agent's flight recorder
```

Each file starts with a short explanation of *why* it exists and which real products (Claude Code, OpenHands, Aider, mini-swe-agent) do the same thing at scale.

## The docs

| Doc | What it answers |
|---|---|
| [01 — What is harness engineering?](docs/01-what-is-harness-engineering.md) | What the term means, where it came from, and why it's not just "prompting" renamed |
| [02 — How a harness works](docs/02-how-a-harness-works.md) | The loop and the five parts, with examples from real products |
| [03 — How to build one](docs/03-how-to-implement.md) | A step-by-step guide matching this repo's code, plus the improvement habit |
| [04 — Sources](docs/04-resources.md) | Every article and project this repo is based on, with one-line summaries |

## The whole idea in one paragraph

An agent is a model in a `while` loop with tools. What decides whether it ships working code or burns money going in circles is the harness: which tools it gets and how their error messages read, what stays in its limited memory, which actions are blocked, what budgets stop a runaway loop, and what logs let you see why a run failed. Harness engineering is one habit applied forever: every time the agent messes up, change its environment — a rule, a tool, a test, or a wall — so that exact mistake can't happen again. Prompts ask nicely. Harnesses make sure.

## License

MIT — see [LICENSE](LICENSE).
