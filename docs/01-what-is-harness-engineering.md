# 01 — What Is Harness Engineering?

## First, what's an agent?

An AI model (like Claude or GPT) only does one thing: text in, text out. It can't run commands or open files by itself.

An **agent** is what you get when you put the model in a loop and give it tools. The model says "run this command," your code runs it, and the output goes back to the model. Repeat until the task is done.

## So what's the harness?

The **harness** is everything in that setup *except* the model:

- the loop itself
- the tools (run a command, read a file, edit a file...)
- the safety rules (what the agent may and may not do)
- the memory management (what the agent gets to see as conversations grow)
- the logs (so you can see what happened)

**Harness engineering** is the practice of building that scaffolding and improving it over time — especially this habit: *every time the agent makes a mistake, change its environment so the same mistake can't happen again.*

Here's how the people who shaped the idea describe it, in plain terms:

- **Databricks**: the harness is "the software infrastructure that wraps around a large language model (LLM) and enables it to act on tasks, not just respond to prompts." The model is the brain; the harness is the body.
- **Vivek Trivedy (LangChain)**: "Agent = Model + Harness. … The model contains the intelligence and the harness makes that intelligence useful."
- **Birgitta Böckeler (on martinfowler.com)**: the harness is "everything in an AI agent except the model itself."
- **Mitchell Hashimoto** (creator of Terraform): when the agent messes up, don't just hope — engineer the environment so it can't happen again, using rules files and purpose-built tools.
- **OpenAI**: build the systems and limits that let agents work on their own. "Humans steer. Agents execute."
- **Louis-François Bouchard**: "The model is the engine… the harness is the rest of the car. Steering, brakes, lane boundaries, maintenance schedule, warning lights."

## Where the term came from

"Harness" is old engineering vocabulary — test harnesses have existed for decades. The AI meaning took shape over about four months:

| When | What happened |
|---|---|
| Nov 2025 | Anthropic's engineering blog writes about "harnesses" for agents that run a long time. The phrase "agent harness" is already floating around the community. |
| Feb 5, 2026 | Mitchell Hashimoto writes about his AI journey and names "Engineer the Harness" as a stage every developer eventually reaches. Most people credit him with making it a named practice. |
| Feb 11, 2026 | OpenAI publishes a post literally titled "Harness engineering," about a small team shipping ~1 million lines of code in 5 months. |
| Mar 2026 | LangChain publishes "The Anatomy of an Agent Harness." |
| Mar–Jun 2026 | Everyone joins in: HumanLayer, Bouchard, Firecrawl, martinfowler.com, Addy Osmani, Databricks. The term becomes normal vocabulary. |

(Small footnote: sources disagree on who exactly coined the phrase — some say Hashimoto, some say Trivedy. The dates favor Hashimoto. Either way, as Firecrawl notes, the term just gave a name to things developers were already doing.)

## Isn't this just "prompt engineering" with a new name?

No. The three terms cover different layers:

- **Prompt engineering** = wording one request well. *"How do I phrase this ask?"*
- **Context engineering** = managing what information the model sees over a whole task — what to include, what to summarize, what to drop. *"What's on the model's desk?"*
- **Harness engineering** = designing the whole system: which tools exist, what's blocked, what budgets apply, how failures are handled, how work gets verified. *"What world does the agent live in?"*

Sources argue about which one "contains" the others, but the practical takeaway is Bouchard's: harness engineering "is not a trendy rename for prompting. It is what shows up when you stop demoing intelligence and start trying to ship it."

## Why the harness matters as much as the model

The evidence, briefly:

- **Terminal-Bench** (a public benchmark): the same model scores from ~58% to ~76% depending only on the harness. An ~18-point swing — like a whole model-generation upgrade.
- **Anthropic** (2024): agent scores on SWE-bench "can vary significantly based on this scaffolding, even when using the same underlying AI model." Their deliberately *simple* harness beat fancier ones.
- **Aider** (an open-source coding agent): splitting one task across two model roles — one plans, one edits — raised a model's score from 61% to 71%. Same models, different wiring.
- **The humbling counterpoint**: mini-swe-agent, only ~100 lines of Python with just a shell tool, gets within a few points of huge commercial agents. Lesson: the *valuable* part of a harness is usually its limits and checks, not its bells and whistles.

> "A decent model with a great harness beats a great model with a bad harness." — Addy Osmani

Next: [02 — How a harness works](02-how-a-harness-works.md).
