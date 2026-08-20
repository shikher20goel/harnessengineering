# Harness Engineering, Explained Simply: Why Your AI Agent Fails (and How to Fix It)

*The AI model is only half the story. The other half is everything you build around it. Here's the whole idea in plain English, with working code.*

---

## Start with a surprising fact

Take one AI model. Wrap it in two different pieces of software. Give both the same coding tasks.

One setup scores 58%. The other scores 76%.

Same model. Same tasks. An 18-point difference — about the same jump you'd get from waiting for a whole new generation of AI models. (This is from Terminal-Bench, a public benchmark that tests AI agents on real terminal tasks.)

So what changed? Not the AI. The thing *around* the AI changed.

That thing has a name now: the **harness**. And learning to build and improve it is called **harness engineering**. In 2026, everyone from OpenAI to Anthropic has been writing about it. This article explains what it is, how it works, and how to build one yourself — without the buzzwords.

## What is an AI agent, really?

Let's clear up the word "agent" first, because it sounds fancier than it is.

An AI model like Claude or GPT does one thing: you send it text, it sends text back. That's it. It can't run code, open files, or browse your project. It just talks.

An **agent** is what you get when you put that model inside a loop and give it tools:

1. You give the model a task: "Fix the failing test in my project."
2. The model replies: "I want to run the command `pytest`."
3. Your code actually runs `pytest` and sends the output back to the model.
4. The model looks at the output and asks for the next step: "Now open `utils.py`."
5. This repeats until the model says: "Done, here's what I did."

In code, the whole loop looks like this:

```python
messages = [the_task]
while True:
    response = model.ask(messages, tools)
    if not response.wants_a_tool:   # model says it's finished
        break
    result = run_the_tool(response)
    messages.append(result)         # show the model what happened
```

Here's the fun part: this loop is basically identical inside Claude Code, OpenAI's agent SDK, and every other major agent product. About 30 lines of code. No magic.

## So where does the real work go?

If the loop is 30 lines and the model is just an API call, why do some agents work great while others go in circles and waste your money?

The answer is everything *around* the loop:

- Which tools does the agent get, and what happens when a tool fails?
- What does the agent get to "see" when the conversation gets really long?
- What is the agent *not allowed* to do?
- How do you find out why a run went wrong?

All of that together is the **harness**. A good one-line picture comes from AI educator Louis-François Bouchard: *the model is the engine, and the harness is the rest of the car* — the steering, the brakes, the seatbelts, the dashboard warning lights. Nobody drives an engine to work.

And the LangChain team boiled it into a formula:

> **Agent = Model + Harness.** "If you're not the model, you're the harness."

One more thing worth knowing: you rent the model. Everyone calls the same APIs, so the model is the same for you and your competitors. The harness is the part you actually own — and as the benchmark above shows, it can matter as much as the model itself.

## A quick history (so you know this isn't just hype)

The idea is old — test setups, build pipelines, and safety rails have always existed. The *name* is new:

- **Late 2025** — Anthropic's engineering blog starts writing about "harnesses" for long-running agents.
- **Feb 2026** — Mitchell Hashimoto (creator of Terraform and the Ghostty terminal) writes about his AI journey and names a key habit: every time the agent makes a mistake, don't just hope it does better next time — *change its environment so that mistake can't happen again.*
- **A week later** — OpenAI publishes a post literally titled "Harness engineering," describing how a small team shipped about a million lines of code in five months. Their motto: **"Humans steer. Agents execute."**
- **Spring 2026** — LangChain, martinfowler.com, Addy Osmani, Databricks, and others all publish their own guides. The term sticks.

## The five parts of a harness

I built a small working harness to go with this article — about 500 lines of plain Python, no libraries needed, fully tested. It's free on GitHub: **[github.com/shikher20goel/harnessengineering](https://github.com/shikher20goel/harnessengineering)**. The code below comes from it.

A harness has five parts. Let's walk through them like a normal engineer would.

### Part 1: Tools — the agent's hands

Tools are the only way the agent can touch the world: run a command, read a file, edit a file. Designing them well is the highest-value work in the whole harness. Three simple rules:

**Rule 1: Error messages are instructions.** Whatever a tool returns goes straight back to the model, and the model acts on it. So a good error message literally teaches the agent what to do next. Compare:

```
ValueError: substring not found
```

versus what the edit tool in my repo returns:

```
ERROR: old string not found in app.py. Read the file first.
```

The first one confuses the agent. The second one tells it exactly how to recover. Agents with helpful errors fix themselves. Agents with raw stack traces flail.

Real-world proof: Anthropic's team noticed their agent kept messing up relative file paths (`../src/app.py`). Instead of asking it nicely to be careful, they changed the file tools to *only accept full paths*. That entire category of mistake disappeared overnight — and helped them set a record on a major coding benchmark.

**Rule 2: Cut long outputs.** One `cat` of a build log can be two megabytes. If you paste all of that into the conversation, it pushes the actual task out of the model's memory. Every serious harness caps tool output. Mine keeps the beginning and the end and drops the middle — the middle of a huge log is rarely the important part.

**Rule 3: A tool crash must never crash the loop.** Catch every error and hand it back to the model as text it can react to.

And how many tools do you need? Fewer than you'd guess. One famous mini agent from the SWE-bench team scores nearly as well as huge commercial agents using *only* a shell command tool — nothing else. Every extra tool you add is extra text the model must read on every single turn. Start with four: read, write, edit, run a command.

### Part 2: Memory — deciding what the agent gets to see

A model can only "see" a limited amount of text at once — its **context window**. Think of it as the agent's desk. Long tasks pile paper onto that desk fast, and here's the catch: models actually get *worse* at finding things as the pile grows, even before the desk is full. Anthropic calls this "context rot."

So the harness cleans the desk. Three habits cover most of it:

**A notes file.** A small text file of project rules that gets shown to the agent at the start of every single turn. Claude Code calls it `CLAUDE.md`; the open standard is called `AGENTS.md` (used by over 60,000 projects); my repo calls it `HARNESS.md`. Things like "always run tests before saying you're done" or "never use tabs" live here. Keep it short — under 60 lines — because every line competes for the agent's attention.

**Throw away stale results.** A file the agent read 20 turns ago is old news; it can always read it again. So the harness replaces old tool outputs with a one-line note: *"result removed — re-run the tool if you need it."*

**Summarize old history.** When the conversation gets close to the limit, fold the oldest turns into a short summary and keep going. Claude Code does this automatically. One open-source project (OpenHands) found this cut their API bill in half with no drop in quality.

### Part 3: Guardrails — the part that says "no"

An agent is a program that spends your money and changes your files in a loop. You want brakes. Three kinds, from softest to hardest:

**Budgets.** A maximum number of turns, tool calls, and minutes. A confused agent should cost you a bounded amount, then stop. From my repo's tests:

```python
# an agent that tries to loop forever...
r = harness_with(max_turns=5).run("loop forever")
assert r.stopped_by == "guardrail"   # ...gets stopped. Test passes.
```

**Block/ask lists.** Some commands are just banned: `rm -rf`, `sudo`, piping a download straight into a shell. Others sit in a gray zone (`pip install`, `git push`) — for those, the harness pauses and asks a human "allow this? y/n". The order matters: block beats ask, ask beats allow.

**Real walls.** For a truly autonomous agent, run it inside a container or sandbox where it *physically can't* touch files outside its folder or call the internet freely. A nice bonus Anthropic found: once real walls exist, you can stop nagging the user with "allow this?" popups — theirs dropped by 84%.

### Part 4: Checking the work — trust but verify

An agent that can't check its own work will confidently hand you broken code. So the harness gives it two things:

- **Guidance up front** — the notes file, project conventions, existing types and docs. This steers the agent before it acts.
- **Checks after the fact** — tests, linters, builds. This catches it when it drifts.

You need both. As Birgitta Böckeler puts it on martinfowler.com: with only one of them, "you get either an agent that keeps repeating the same mistakes… or an agent that encodes rules but never finds out whether they worked."

A rule of thumb from Anthropic: automatic checks (tests, linters) are the most trustworthy, screenshots are next, and asking another AI to judge the work is the weakest. And write this one down, because agents under pressure will cheat: **"It is unacceptable to remove or edit tests."** Yes, agents really do try to delete failing tests to "finish" a task.

### Part 5: The flight recorder

Log everything the agent does — every model reply, every tool call, every blocked command — into one file, one event per line. When a 30-turn run fails, the visible failure is at turn 30, but the *actual* mistake usually happened around turn 7. The log is how you find it.

This isn't optional logging. It's the raw material for the entire practice, because of what comes next.

## The actual skill: fix the environment, not the prompt

Everything above is stuff you build once, in a weekend. Harness engineering as a *practice* is what you do afterward, forever. It's one simple habit, applied ruthlessly:

**Every time the agent messes up, change its world so that exact mistake can't happen again.**

Not "add 'please be careful' to the prompt." Change the environment. There's a ladder of fixes, from weakest to strongest:

1. **Add a rule** to the notes file. *"Run pytest before declaring done."* Cheap, but it's only advice — the agent can ignore it.
2. **Add a tool** that makes the right thing easy. If the agent keeps fumbling test commands, give it a `run_tests` tool that already knows the right flags.
3. **Add a check** that catches the mistake automatically. A test, a linter, a CI step. Now the mistake gets *caught* instead of hoped against.
4. **Add a wall** that makes the mistake impossible. A banned command, a sandbox, a tool that only accepts full paths. Now the mistake is *deleted*.

Always climb as high on the ladder as you reasonably can. Rules get ignored. Walls don't.

Addy Osmani has a great test for whether you're doing this right:

> "Every line in a good AGENTS.md should be traceable back to a specific thing that went wrong."

In other words: don't copy someone else's giant rules file. Start empty. Run real tasks. Read the log. Find the first wrong step. Fix it at the highest level you can. Repeat. Your harness ends up shaped by *your* project's actual failure history — which is exactly why it works, and why (as Osmani says) "you can't download it."

One more professional habit: keep a small fixed set of test tasks and re-run them after every harness change. If your "improvement" makes the pass rate drop, it wasn't an improvement.

This is also why the harness in my repo is built to be testable *without* any AI at all. It includes a fake model that just replays a script, so all 11 tests — loop stops correctly, dangerous commands get blocked, old results get cleaned up, notes file gets injected — run in 50 milliseconds with no API key. The harness is normal software. Test it like normal software.

## "Won't better models make this pointless?"

Fair question. Partly, yes: the *fancy* parts of harnesses (elaborate planning modes, huge tool collections) keep getting less necessary as models improve. Tiny bash-only agents already come close to the big ones on some benchmarks.

But notice which parts were doing the heavy lifting in everything above: budgets, blocked commands, sandboxes, tests, logs. Those don't become less necessary as agents get more capable and more autonomous — they become *more* necessary, for the same reason talented humans still need code review and production still needs guardrails. Capability without limits scales damage just as fast as it scales output.

Harrison Chase (LangChain's founder) said it well: "Better models expand what harnesses need to do, not replace the need for them."

The engine keeps getting better and cheaper. Someone still has to build the rest of the car. That someone is you.

## Try it yourself

Everything from this article — the 500-line harness, the tests, a demo you can run with zero setup and zero API keys, and four deeper research docs with all sources — is free here:

**[github.com/shikher20goel/harnessengineering](https://github.com/shikher20goel/harnessengineering)** (MIT license)

```bash
git clone https://github.com/shikher20goel/harnessengineering
cd harnessengineering
python3 examples/mock_demo.py   # watch the loop, tools, and a guardrail in action
```

---

**Sources & further reading:** [OpenAI — Harness engineering](https://openai.com/index/harness-engineering/) · [Mitchell Hashimoto — My AI Adoption Journey](https://mitchellh.com/writing/my-ai-adoption-journey) · [LangChain — The Anatomy of an Agent Harness](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness) · [Böckeler — Harness Engineering for Coding Agent Users](https://martinfowler.com/articles/harness-engineering.html) · [Addy Osmani — Agent Harness Engineering](https://addyosmani.com/blog/agent-harness-engineering/) · [Anthropic — Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [Anthropic — Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) · [Terminal-Bench](https://www.tbench.ai/) · [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)
