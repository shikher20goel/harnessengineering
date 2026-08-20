# Harness Engineering

**Everything in an AI agent except the model.**

This repo is a study of *harness engineering* — the emerging discipline of designing the scaffolding around an LLM that turns raw model intelligence into a reliable working agent. It contains:

1. **Research notes** (`docs/`) — what harness engineering is, where the term came from, how a harness works, and how to practice the discipline, distilled from the primary sources (OpenAI, Anthropic, Mitchell Hashimoto, LangChain, Thoughtworks/martinfowler.com, Addy Osmani, and others).
2. **A minimal, runnable agent harness** (`harness/`) — ~500 lines of dependency-free Python that implements every core harness component: the agent loop, a tool layer, guardrails, context management, and tracing. Built to be read.
3. **A Medium article** (`article/`) — a practitioner deep-dive that ties it together.

```
Agent = Model + Harness
```
> "If you're not the model, you're the harness." — Vivek Trivedy, LangChain

## Why this matters

The same model produces wildly different results under different harnesses. On Terminal-Bench 2.0, one frontier model's score varies by ~18 percentage points across harnesses — a spread comparable to a full model-generation jump. Anthropic reported that agent performance on SWE-bench "can vary significantly based on this scaffolding, even when using the same underlying AI model." The harness is not plumbing; it is half the product.

## Quick start

No dependencies, no API key needed for the demo:

```bash
git clone https://github.com/shikher20goel/harnessengineering
cd harnessengineering

# Watch the harness work with a scripted mock model (loop, tools,
# a guardrail blocking `sudo rm -rf /`, tracing):
python3 examples/mock_demo.py

# Run the test suite (tests the harness, not the model):
pip install pytest && python3 -m pytest tests/ -q

# Run a real task with a real model:
export ANTHROPIC_API_KEY=sk-ant-...
python3 examples/run_task.py "Write a tested prime sieve in sieve.py"
```

## What's in the harness

```
harness/
├── agent.py       # the ~30-line agent loop everyone converges on, plus wiring
├── model.py       # provider adapter (Anthropic) + MockModel for offline testing
├── tools.py       # tool registry, bash + file tools, output truncation, path confinement
├── guardrails.py  # budgets (turns/calls/time), deny/ask policies, human-in-the-loop hook
├── context.py     # HARNESS.md persistent memory, tool-result aging, compaction
└── trace.py       # JSONL event log — the raw material of harness engineering
```

Each file's docstring explains *which harness-engineering principle it encodes* and where production systems (Claude Code, OpenHands, mini-swe-agent, Aider) do the same thing at scale.

## The docs

| Doc | Contents |
|---|---|
| [01 — What is harness engineering?](docs/01-what-is-harness-engineering.md) | Definitions, origin and timeline of the term, how it relates to prompt & context engineering |
| [02 — How a harness works](docs/02-how-a-harness-works.md) | The canonical agent loop, the six component layers, how real harnesses implement each |
| [03 — How to implement one](docs/03-how-to-implement.md) | A practical, step-by-step build guide mapped to this repo's code, plus the practice loop (the Ratchet Principle) |
| [04 — Resources](docs/04-resources.md) | Annotated bibliography of the primary sources |

## The one-paragraph version

An agent is a model in a `while` loop with tools. The model is rented; everyone has the same one. What you actually own — and what determines whether the agent ships working code or burns tokens in circles — is the harness: which tools it gets and how their errors read, what enters the context window and what gets compacted out, which actions are denied, asked about, or allowed, what budgets stop a runaway loop, and what traces let you see why a run failed. Harness engineering is the discipline of improving that scaffolding *empirically*: every time the agent fails, you change the environment so that failure can't recur — a rule in a memory file, a new tool, a linter, a test gate. Prompting begs; harnesses enforce.

## License

MIT — see [LICENSE](LICENSE).
