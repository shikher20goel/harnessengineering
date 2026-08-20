# 04 — Sources

Everything this repo is based on, with a one-line plain-English summary of each. Roughly in the order worth reading.

## The idea and the practice

- **[My AI Adoption Journey](https://mitchellh.com/writing/my-ai-adoption-journey)** — Mitchell Hashimoto, Feb 2026. Where "engineer the harness" became a named habit: fix the environment on every mistake.
- **[Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)** — OpenAI, Feb 2026. How a small team shipped ~1M lines of code in 5 months. Source of "Humans steer. Agents execute."
- **[The Anatomy of an Agent Harness](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness)** — LangChain, Mar 2026. Source of "Agent = Model + Harness."
- **[Harness Engineering for Coding Agent Users](https://martinfowler.com/articles/harness-engineering.html)** — Birgitta Böckeler, Apr 2026. The most careful treatment: guidance-before vs checks-after, and why you need both.
- **[Agent Harness Engineering](https://addyosmani.com/blog/agent-harness-engineering/)** — Addy Osmani, Apr 2026. The practical playbook. Source of "every line should be traceable to something that went wrong."
- **[Skill Issue: Harness Engineering for Coding Agents](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents)** — HumanLayer, Mar 2026. "The model is probably fine. It's just a skill issue."
- **[Harness Engineering: The Missing Layer Behind AI Agents](https://www.louisbouchard.ai/harness-engineering/)** — Louis-François Bouchard, Mar 2026. The engine-vs-rest-of-the-car analogy.
- **[What Is an Agent Harness?](https://www.firecrawl.dev/blog/what-is-an-agent-harness)** — Firecrawl, Apr 2026. A clean four-part breakdown of harness subsystems.
- **[AI Agent Harness](https://www.databricks.com/blog/ai-harness)** — Databricks, Jun 2026. The enterprise view; good list of common failure modes.
- **[Why the AI Industry's Newest Buzzword is an Old Idea](https://haverin.substack.com/p/what-is-harness-engineering-ai-hype)** — Stuart Miller, May 2026. The healthy skeptic: this is test harnesses and platform engineering, renamed.

## Anthropic's engineering series

- **[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)** — Dec 2024. Start simple; treat tool design like interface design.
- **[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)** — Sep 2025. Why models get worse as their memory fills, and what to do about it.
- **[Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)** — 2025. The loop in words: gather context → act → check → repeat.
- **[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)** — Nov 2025. How to structure agents that work for days: task lists, progress files, git.
- **[Claude Code sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)** — Real walls (files + network), and how they cut permission popups by 84%.
- **[Raising the bar on SWE-bench Verified](https://www.anthropic.com/news/swe-bench-sonnet)** — Oct 2024. Proof that scaffolding moves benchmark scores; a simple harness beat fancy ones.

## Harnesses worth reading (actual code)

- **[mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)** — a full coding agent in ~100 lines with only a shell tool. Read this first.
- **[smolagents](https://github.com/huggingface/smolagents)** — Hugging Face's small agent library; its CodeAgent writes Python instead of tool calls.
- **[OpenHands Agent SDK](https://arxiv.org/abs/2511.03690)** — the big-harness end of the spectrum: event logs, summarizers, risk analysis.
- **[Aider](https://aider.chat/docs/repomap.html)** — clever context tricks: the repo map, per-model [edit formats](https://aider.chat/docs/more/edit-formats.html), and the [two-model architect/editor split](https://aider.chat/2024/09/26/architect.html).
- **[OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)** — agent handoffs and guardrails as a library.
- **[Google ADK](https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/)** — fixed workflows (sequential/parallel/loop) as first-class building blocks.
- **[Claude Agent SDK — the agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)** — the canonical loop, officially documented.
- **[AGENTS.md](https://agents.md/)** — the open notes-file standard (60k+ projects).

## Benchmarks

- **[Terminal-Bench](https://www.tbench.ai/)** — same model, different harness, ~18-point score swings. The clearest evidence the harness matters.
- **[SWE-bench Verified](https://www.swebench.com/)** — the standard coding-agent benchmark most of the numbers above come from.
