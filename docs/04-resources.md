# 04 — Resources

Annotated bibliography of the sources behind this repo, in rough reading order.

## The term and the discipline

- **[My AI Adoption Journey](https://mitchellh.com/writing/my-ai-adoption-journey)** — Mitchell Hashimoto, Feb 2026. Names "Engineer the Harness" as a stage of AI adoption; the origin of the fix-the-environment-on-every-mistake framing.
- **[Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)** — Ryan Lopopolo, OpenAI, Feb 2026. The frontier-lab manifesto: docs-as-source-of-truth, mechanical enforcement, application legibility, per-worktree environments. Source of "Humans steer. Agents execute." and the ~1M-LoC claim.
- **[The Anatomy of an Agent Harness](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness)** — Vivek Trivedy, LangChain, Mar 2026. "Agent = Model + Harness"; harness vs framework distinction; harnesses as "delivery mechanisms for good context engineering."
- **[Harness Engineering for Coding Agent Users](https://martinfowler.com/articles/harness-engineering.html)** — Birgitta Böckeler, martinfowler.com, Apr 2026. The most rigorous treatment: guides (feedforward) vs sensors (feedback), steering loops, computational vs inferential checks, "harnessability" of codebases.
- **[Agent Harness Engineering](https://addyosmani.com/blog/agent-harness-engineering/)** — Addy Osmani, Apr 2026. The practitioner synthesis: six component categories, the Ratchet Principle, AGENTS.md minimalism.
- **[Skill Issue: Harness Engineering for Coding Agents](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents)** — HumanLayer, Mar 2026. "The model is probably fine. It's just a skill issue." Sub-agents as context firewalls.
- **[Harness Engineering: The Missing Layer Behind AI Agents](https://www.louisbouchard.ai/harness-engineering/)** — Louis-François Bouchard, Mar 2026. The car analogy; inspectable/testable/constrained framing.
- **[What Is an Agent Harness?](https://www.firecrawl.dev/blog/what-is-an-agent-harness)** — Ninad Pathak, Firecrawl, Apr 2026. Four-subsystem decomposition; treat every failure as a permanent environmental problem.
- **[AI Agent Harness](https://www.databricks.com/blog/ai-harness)** — Databricks, Jun 2026. Eight-component enterprise view; failure modes (context rot, tool overload, agent sprawl).
- **[What is Harness Engineering? Why the AI Industry's Newest Buzzword is an Old Idea](https://haverin.substack.com/p/what-is-harness-engineering-ai-hype)** — Stuart Miller, May 2026. The skeptical genealogy: test harnesses, middleware, platform engineering, Toyota.

## Anthropic engineering series (harness-relevant)

- **[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)** — Dec 2024. Workflows vs agents; the five workflow patterns; agent-computer interface (ACI) doctrine; start simple.
- **[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)** — Sep 2025. Context rot; attention budgets; compaction, note-taking, sub-agents, just-in-time retrieval.
- **[Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)** — 2025. Gather context → take action → verify work → repeat; "give Claude a computer"; verification hierarchy.
- **[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)** — Nov 2025. Initializer/executor split; feature-list JSON; progress files; "compaction isn't sufficient."
- **[Claude Code sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)** — bubblewrap/Seatbelt; filesystem + network boundaries; −84% permission prompts.
- **[Raising the bar on SWE-bench Verified](https://www.anthropic.com/news/swe-bench-sonnet)** — Oct 2024. The scaffolding-moves-scores statement, and a minimal harness beating elaborate ones.

## Harnesses worth reading (code)

- **[mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)** — ~100 lines, bash-only, linear history; the minimalist existence proof.
- **[smolagents](https://github.com/huggingface/smolagents)** — ReAct in <1k lines; CodeAgent/code-as-action (per [CodeAct, arXiv:2402.01030](https://arxiv.org/abs/2402.01030)).
- **[OpenHands Software Agent SDK](https://arxiv.org/abs/2511.03690)** — the maximalist pole: event-sourced state, condensers, security analyzers.
- **[Aider](https://aider.chat/docs/repomap.html)** — repo maps, per-model [edit formats](https://aider.chat/docs/more/edit-formats.html), [architect/editor mode](https://aider.chat/2024/09/26/architect.html).
- **[OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)** — handoffs, guardrail tripwires, sessions.
- **[Google ADK](https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/)** — deterministic workflow agents as first-class constructs.
- **[Claude Agent SDK — agent loop docs](https://code.claude.com/docs/en/agent-sdk/agent-loop)** — the canonical loop, documented.
- **[AGENTS.md](https://agents.md/)** — the open memory-file format (60k+ repos, Linux Foundation stewardship).

## Benchmarks

- **[Terminal-Bench](https://www.tbench.ai/)** — same model, different harness, 10–20 pt spreads; the Terminus reference harness (a bare tmux pane) exists to decouple model from harness.
- **[SWE-bench Verified](https://www.swebench.com/)** — where most harness-vs-harness evidence comes from.
