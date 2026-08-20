# Harness Engineering: The Discipline That Decides Whether Your AI Agent Actually Works

*The model is rented. The harness is yours. Here's how to build one — and how to practice the craft everyone from OpenAI to Anthropic is now writing about.*

---

There's a number that should change how you think about AI agents.

On Terminal-Bench 2.0 — a benchmark where agents complete real tasks in a terminal — the *same frontier model* scores anywhere from the high 50s to the mid 70s depending on one variable: the harness wrapped around it. That's roughly an 18-point spread. For context, that's about the size of the gap you'd expect between two model *generations*. Anthropic said the quiet part out loud back in 2024, in their SWE-bench write-up: agent performance "can vary significantly based on this scaffolding, even when using the same underlying AI model."

Everyone is calling the same model APIs. The intelligence is a commodity you rent by the token. What you actually own — and what increasingly determines whether your agent ships working code or burns $40 of tokens going in circles — is everything *around* the model.

That "everything around" now has a name: the **agent harness**. And the practice of deliberately designing and improving it is **harness engineering**.

## What is a harness?

The cleanest formula comes from Vivek Trivedy at LangChain:

> **Agent = Model + Harness.** "If you're not the model, you're the harness."

Concretely, the harness is: the loop that drives the model, the tools it can call, the environment those tools execute in, the rules that constrain what it's allowed to do, the machinery that decides what enters its context window, and the feedback loops that tell it — and you — whether the work succeeded.

Louis-François Bouchard's analogy is the one that sticks: *the model is the engine; the harness is the rest of the car.* Steering, brakes, lane boundaries, warning lights. Nobody ships an engine to customers.

The term itself crystallized fast. Anthropic's engineering blog was writing about "effective harnesses" in late 2025. In February 2026, Mitchell Hashimoto (of HashiCorp/Ghostty fame) published his AI adoption journey and named "Engineer the Harness" as a distinct stage of maturity — the point where, instead of hoping the agent does better next time, you change the environment so the failure can't recur. Days later, OpenAI published "Harness engineering: leveraging Codex in an agent-first world," describing how a handful of engineers shipped roughly a million lines of code in five months by obsessing over scaffolding rather than prompts. Their slogan: *"Humans steer. Agents execute."* By spring, LangChain, Thoughtworks (on martinfowler.com), Addy Osmani, HumanLayer, Firecrawl, and Databricks had all published their own takes. A buzzword was born — but unusually for AI buzzwords, this one names something real, old, and load-bearing. It's the direct descendant of test harnesses, middleware, and platform engineering.

Is it just "prompt engineering" rebranded? No — and the distinction matters. Prompt engineering optimizes the wording of a request. Context engineering curates what information the model sees. Harness engineering designs the *system*: which tools exist and how their errors read, when context gets loaded and compacted, which actions are denied outright, what budgets stop a runaway loop. As Bouchard puts it: "It is not a trendy rename for prompting. It is what shows up when you stop demoing intelligence and start trying to ship it."

## The 30 lines at the center of everything

Here's a secret hiding in plain sight: strip the branding off Claude Code, the OpenAI Agents SDK, Hugging Face's smolagents, mini-swe-agent, and OpenHands, and you find the *same loop*:

```python
messages = [system_prompt, user_task]
while True:
    response = model.complete(system, messages, tools)
    if not response.tool_calls:      # model produced a final answer
        break
    results = execute(response.tool_calls)
    messages += [response, results]  # feed observations back
```

Call the model. If it wants tools, run them, append the results, go again. Stop when it answers without calling tools — or when a budget runs out.

That's it. That's the "agent." Anthropic frames it conceptually as *gather context → take action → verify work → repeat*, but the code is a while loop you could write in an afternoon.

Which raises the obvious question: if the loop is 30 lines and the model is an API call, where do the other 18 benchmark points live?

They live in five unglamorous layers. To make them concrete, I built a minimal harness — about 500 lines of dependency-free Python, every layer implemented and unit-tested — and put it on GitHub with the full research notes: **[github.com/shikher20goel/harnessengineering](https://github.com/shikher20goel/harnessengineering)**. Code below is from that repo.

## Layer 1: Tools — interface design for a non-human user

Tools are the agent's only way to touch the world, and designing them is UX design where the user is a model. Anthropic's team calls this the *agent-computer interface* (ACI), and their SWE-bench post contains my favorite example of the genre: they noticed the model kept making relative-path mistakes, so they changed the file tools to *require absolute paths*. One constraint, an entire error class deleted, and a then-state-of-the-art benchmark result built partly on such fixes.

Three rules do most of the work:

**Errors are prompts.** Every tool result goes straight into the model's context, so an error message is an instruction for the next step. Compare a raw `ValueError` to this, from the edit tool in my repo:

```python
def edit_file(path: str, old: str, new: str) -> str:
    text = p.read_text()
    n = text.count(old)
    if n == 0:
        return f"ERROR: old string not found in {path}. Read the file first."
    if n > 1:
        return f"ERROR: old string appears {n} times in {path}; make it unique."
```

The second version tells the agent exactly how to recover. Agents given readable, actionable errors self-correct; agents given stack traces flail.

**Truncate ruthlessly.** One `cat` of a build log can be two megabytes. If that lands in the context window verbatim, it evicts the task itself. Every serious harness caps tool output — mine keeps the head and tail and drops the middle, because the middle of huge outputs is rarely load-bearing.

**Never let a tool kill the loop.** Exceptions become error results the model can react to. The loop must survive anything a tool does.

How many tools? Fewer than you think. Mini-swe-agent — from the SWE-bench team — scores within a few points of elaborate harnesses using *only bash*, no tool-calling API at all. Mario Zechner's pi ships exactly four: read, write, edit, bash. Every tool schema you add is context the model pays for on every single request, and Anthropic explicitly warns against "bloated tool sets" with "ambiguous decision points."

## Layer 2: Context — the scarcest resource in the system

The context window feels big until your agent is 40 turns into a task. And it degrades before it fills: Anthropic's context-engineering post documents *context rot* — retrieval accuracy declines as token count grows. Treat context as "a finite resource with diminishing marginal returns."

Production harnesses converge on the same toolkit:

**A persistent memory file.** Claude Code has CLAUDE.md; the open AGENTS.md format is used by 60,000+ repositories and is now stewarded under the Linux Foundation. It's a rules file injected into every request, surviving any compression of history. My harness calls it HARNESS.md and folds it into the system prompt each turn. Keep it brutally short — Addy Osmani's guidance is under ~60 lines, because "every line is competing for attention."

**Tool-result aging.** A file read from twenty turns ago is stale anyway. Old tool results get collapsed to a stub — `[result elided by harness — re-run the tool if needed]` — and the agent re-reads if it cares. Cheap, safe, effective.

**Compaction.** When the window nears its budget, fold the oldest turns into a summary while preserving the original task verbatim. Claude Code does this automatically; OpenHands' summarizing condenser cut API costs up to 2× *with no measured performance loss*. One implementation subtlety that will bite you on real APIs: never split a tool call from its result — a `tool_result` whose `tool_use` was compacted away is a hard API error.

**Just-in-time retrieval.** Don't pre-load the world; give the agent lightweight identifiers — file paths, queries — and let it fetch what it needs. OpenAI's phrasing is the memorable one: "Give Codex a map, not a 1,000-page instruction manual."

**Sub-agents as context firewalls.** For big exploratory subtasks, spawn a fresh-context agent and let only a distilled summary — typically 1,000–2,000 tokens, per Anthropic — return to the parent. The parent gets the conclusion without the 50,000 tokens of searching that produced it.

## Layer 3: Guardrails — the part that says no

An autonomous agent is a process that spends your money and mutates your filesystem in a loop. Anthropic's dry phrasing: autonomy means "higher costs, and the potential for compounding errors." The harness answers with three escalating mechanisms.

**Budgets.** Max turns, max tool calls, wall-clock limits. Non-negotiable, and checked *before* each turn, not after:

```python
looping = ModelResponse(tool_calls=[ToolCall("t", "bash", {"command": "true"})])
script = [looping] * 50
r = make_harness(tmp_path, script, max_turns=5).run("loop forever")
assert r.stopped_by == "guardrail"     # passes
```

**Policy.** Allow/deny/ask rules over tool calls. Deny the classic regrets categorically — `rm -rf`, `sudo`, `curl | sh`, force-push. Route the gray zone (`pip install`, `git push`) to a human callback. Claude Code implements this as parameterized permission rules like `Bash(npm *)`; OpenHands risk-rates every action and pauses for confirmation policy. The ordering is doctrine: deny beats ask beats allow.

**Sandboxing.** Real isolation is at the OS level, and it needs *both* halves: filesystem boundaries (the agent can only touch its workspace) and network boundaries (it can only reach approved hosts). Anthropic's sandboxing post makes the threat model concrete — a prompt-injected agent shouldn't be able to read your SSH keys *or* phone home — and reports a lovely side effect: strong boundaries let them cut permission prompts by 84%, because you no longer need to ask about every action inside a wall you trust. And heed Hugging Face's bluntness about smolagents' local executor: it "is not a security boundary." In-process sandboxes are conveniences. Containers are boundaries.

## Layer 4: Feedback — guides and sensors

Birgitta Böckeler's essay on martinfowler.com gives this layer the cleanest theory, borrowed from control engineering. A harness needs **guides** — feedforward signals like conventions, architecture docs, type systems — and **sensors** — feedback like linters, tests, and review checks. Her warning about using either alone:

> "Separately, you get either an agent that keeps repeating the same mistakes… or an agent that encodes rules but never finds out whether they worked."

Anthropic ranks verification methods: rules-based checks (tests, linters) beat visual feedback (screenshots) beat LLM-as-judge. OpenAI's variant is *enforcement over prescription* — don't write a doc asking agents to respect layer boundaries; write a linter that fails the build when they don't. Docs request. CI enforces.

And one rule from Anthropic's long-running-agents work deserves to be engraved somewhere, because agents under pressure will reward-hack: **"It is unacceptable to remove or edit tests."**

## Layer 5: Observability — the flight recorder

Every model response, tool call, policy block, and compaction goes to a JSONL trace. This isn't nice-to-have logging; it's the raw material of the entire discipline, because you cannot fix what you cannot see. When a 30-turn run fails, the trace is where you find the *first* wrong step — usually somewhere around turn 7, long before the visible failure.

## The actual discipline: the ratchet

Everything above is scaffolding you build once. Harness engineering proper is what you do *after* — and it's an empirical loop, not an architecture.

Hashimoto's founding move: every time the agent does a Bad Thing, make an earnest effort to ensure it can never do that specific bad thing again. Osmani sharpened it into what he calls a traceability test:

> "Every line in a good AGENTS.md should be traceable back to a specific thing that went wrong."

I think of the fixes as a four-level ratchet, ordered by strength:

1. **A rule** in the memory file ("run pytest before declaring done"). Cheapest — and weakest, because it's advisory and competes for attention.
2. **A tool** that makes the right behavior easy: a `run_tests` tool that already knows the flags, a screenshot script. The agent no longer has to figure it out.
3. **A sensor** that catches the failure mechanically: a test, a linter, a CI gate, a review agent. Now the failure is *detected* instead of hoped against.
4. **A constraint** that makes the failure impossible: a deny rule, a sandbox wall, a required-absolute-path schema. The failure class is deleted.

Prefer the highest level you can afford. Rules drift. Constraints don't.

The working rhythm is unglamorous: run a real task, read the trace, find the first wrong step, ask *what in the environment allowed this*, fix at the highest proportionate ratchet level, re-run. Start from an empty memory file and let failures grow it — Osmani again: "The right harness for your codebase is shaped by your failure history. You can't download it."

One more practice separates the professionals from the tinkerers: keep a fixed suite of evaluation tasks and re-run it after every harness change. A harness "improvement" that drops your pass rate is a regression, no matter how clever it feels. This is why the harness in my repo is built around a `MockModel` — a scripted stand-in that makes the entire harness deterministic to test. Eleven tests cover loop termination, guardrail blocks, path-escape refusal, result aging, compaction, and memory injection, and they run in 50 milliseconds with no API key. You test the harness *separately* from the model, exactly like any other piece of systems software. Because that's what it is.

## The counterargument worth taking seriously

Won't better models make all this obsolete? It's not a strawman — mini-swe-agent's whole thesis is that ~100 lines of Python and a bash prompt get within a few points of elaborate harnesses on SWE-bench, and the gap keeps shrinking as models improve. The *feature* layers of harnesses — planning modes, elaborate tool suites, clever retrieval — probably do have a shelf life.

But look at which layers were doing the work in every case study above. The constraint and verification layers — budgets, policies, sandboxes, tests, traces — don't get less necessary as models get more capable and more autonomous. They get more necessary, for exactly the reason we build guardrails for talented humans: capability without constraint scales damage as fast as it scales output. Harrison Chase's line captures the trajectory: "Better models expand what harnesses need to do, not replace the need for them."

The engine keeps getting better, faster, cheaper. Someone still has to build the rest of the car.

---

*All the code in this article — the full ~500-line harness, tests, offline demo, and four research docs with complete citations — is at [github.com/shikher20goel/harnessengineering](https://github.com/shikher20goel/harnessengineering) (MIT).*

**Primary sources:** [OpenAI — Harness engineering](https://openai.com/index/harness-engineering/) · [Mitchell Hashimoto — My AI Adoption Journey](https://mitchellh.com/writing/my-ai-adoption-journey) · [LangChain — The Anatomy of an Agent Harness](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness) · [Böckeler — Harness Engineering for Coding Agent Users](https://martinfowler.com/articles/harness-engineering.html) · [Addy Osmani — Agent Harness Engineering](https://addyosmani.com/blog/agent-harness-engineering/) · [Anthropic — Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [Anthropic — Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) · [Anthropic — Claude Code sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing) · [Terminal-Bench](https://www.tbench.ai/) · [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)
