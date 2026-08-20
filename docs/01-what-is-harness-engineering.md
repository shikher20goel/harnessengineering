# 01 — What Is Harness Engineering?

## The definition

An **agent harness** is everything in an AI agent except the model itself: the loop that drives it, the tools it can call, the environment it runs in, the rules that constrain it, the context-management machinery that decides what it sees, and the feedback loops that tell it (and you) whether it worked.

**Harness engineering** is the discipline of designing and — crucially — *continuously improving* that scaffolding. Definitions from the primary sources converge:

- **Databricks**: "the software infrastructure that wraps around a large language model (LLM) and enables it to act on tasks, not just respond to prompts." The model is the brain; the harness is the body.
- **Vivek Trivedy (LangChain)**: the harness is all code, configuration, and execution logic beyond the model. "Agent = Model + Harness. … The model contains the intelligence and the harness makes that intelligence useful."
- **Birgitta Böckeler (Thoughtworks, on martinfowler.com)**: the harness is "everything in an AI agent except the model itself"; harness engineering is what users of coding agents do to raise confidence in outputs and reduce supervision.
- **Mitchell Hashimoto**: the practice that "anytime you find an agent makes a mistake, you take the time to engineer" the environment so it can't recur — via rules files (AGENTS.md) and purpose-built tools.
- **OpenAI (Ryan Lopopolo)**: building the systems, constraints, and feedback loops that let agents execute autonomously. "Humans steer. Agents execute."
- **Louis-François Bouchard**: "the work around an AI agent that makes its behavior inspectable, testable, and constrained." His analogy: "The model is the engine… the harness is the rest of the car. Steering, brakes, lane boundaries, maintenance schedule, warning lights."

## Origin and timeline of the term

The word "harness" is old engineering vocabulary — test harnesses, eval harnesses (`lm-evaluation-harness`), scaffolds, middleware. The AI-agent usage crystallized over roughly four months:

| When | What |
|---|---|
| Nov 2025 | Anthropic's engineering blog uses "harness" prominently: *Effective harnesses for long-running agents*. "Agent harness" already circulating in the community; the "Agent = Model + Harness" shorthand spreads via LangChain material. |
| Feb 5, 2026 | Mitchell Hashimoto's *My AI Adoption Journey* names "Engineer the Harness" as a distinct stage of AI adoption — widely credited with formalizing the practice. |
| Feb 11, 2026 | OpenAI publishes *Harness engineering: leveraging Codex in an agent-first world* — the first frontier-lab post using the exact phrase, with the much-cited claim of ~1M lines of code shipped by a small team in 5 months. |
| Mar 10, 2026 | LangChain publishes Trivedy's *The Anatomy of an Agent Harness*. |
| Mar–Jun 2026 | The ecosystem piles on: HumanLayer, Bouchard, Firecrawl, Böckeler on martinfowler.com, Addy Osmani, Databricks. The term becomes standard vocabulary. |

Attribution note: some sources (Osmani, HumanLayer) credit Trivedy with coining the phrase; others (Firecrawl, Bouchard, Stuart Miller) credit Hashimoto. Publication dates favor Hashimoto for the named discipline, with "agent harness" as a community term predating both. As Firecrawl puts it, the term "named existing informal practices developers had already built."

## How it relates to prompt engineering and context engineering

The three disciplines nest, though sources disagree about which contains which:

- **Prompt engineering** optimizes the wording of individual model inputs.
- **Context engineering** (a term popularized by Dex Horthy's 12-factor agents and Anthropic's engineering blog) curates *what information* occupies the context window across a task — retrieval, compaction, memory.
- **Harness engineering** designs the *system* around the model: which tools exist, when context gets loaded, which actions are allowed, how failures are handled, what gets verified.

Databricks calls prompt and context engineering subsets of harness engineering; HumanLayer inverts the nesting ("harness engineering is a subset of context engineering"); Böckeler splits the difference ("a specific form of context engineering"). Trivedy's synthesis is the most useful: "Harnesses today are largely delivery mechanisms for good context engineering." What everyone agrees on is Bouchard's point: "It is not a trendy rename for prompting. It is what shows up when you stop demoing intelligence and start trying to ship it."

## Why the harness matters as much as the model

The empirical case, from the sources:

- Anthropic (SWE-bench post, Oct 2024): "the performance of an agent on SWE-bench can vary significantly based on this scaffolding, even when using the same underlying AI model." Their deliberately minimal scaffold beat more elaborate prior SOTA.
- Terminal-Bench 2.0 exists precisely because harness choice moves a fixed model's score by 10–20+ points — a spread comparable to a model-generation jump.
- Aider's architect/editor split (a pure harness change — same models, different wiring) raised o1-mini from 61.1% to 71.4% on its benchmark.
- Databricks reports a benchmark where the harness, not the model upgrade, drove the gain.
- Counterpoint that keeps the field honest: **mini-swe-agent** scores within a few points of elaborate harnesses on SWE-bench Verified using ~100 lines of Python and *only bash* — evidence that harness complexity has diminishing returns as models improve, and that the valuable part of a harness is often its constraints and feedback, not its features.

> "A decent model with a great harness beats a great model with a bad harness." — Addy Osmani

Continue to [02 — How a harness works](02-how-a-harness-works.md).
