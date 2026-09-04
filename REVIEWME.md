# Review Session Prep

Read this before the review session at the end of the week. It is here to help
you prepare — it is not a script to read out, and nobody is going to mark you
on it.

## What the session is

A 30-minute informal chat with Lizzie and one or two other engineers. Roughly
15 minutes of you talking through what you built, and the rest is
conversation.

It is deliberately low-key. People will interrupt with questions, you will go
off on tangents, and that is fine — that is what makes it a conversation
rather than a presentation.

The three things we want to get out of it:

| # | Goal                                                                  |
| - | --------------------------------------------------------------------- |
| 1 | You show off what you built — the model and the dashboard             |
| 2 | You practise explaining technical things to someone new to them       |
| 3 | We talk about what you would do with more time                        |

Goal 2 is the one worth taking seriously. Explaining your work clearly is a
real engineering skill, and it is genuinely harder than writing the code.

## Why explaining it clearly actually matters here

This is not a soft skill we tacked on the end. From the project brief:

> At Gigaton, we spend a lot of time talking to our customers to ensure that
> they understand our models. If customers do not understand what our models
> are doing and why, we are out of business.

A model nobody trusts does not get used, and a model that does not get used
saves zero carbon. So being able to explain a model to someone who did not
build it is part of the job, not a bonus.

You have already done this once — you built the dashboard for exactly that
audience. This session is the same exercise, out loud.

## Rough shape for your 15 minutes

A loose suggestion, not a running order. Adapt it, or ignore it.

| Minutes | Roughly                                                        |
| ------- | -------------------------------------------------------------- |
| 2       | What problem you were solving, and why it matters              |
| 4       | The model — what goes in, what comes out, how you know if it works |
| 5       | Demo the dashboard, live                                       |
| 4       | What you would do next, and what you found hard                |

If you overrun, cut the demo short rather than the "what I'd do next" part.
That last section usually makes for the best discussion.

## Preparing goal 1: showing your work

### Have it running before people arrive

Open the dashboard and have the terminal ready **before** the session starts.
Watching someone wait for a build is a boring way to spend two of your fifteen
minutes.

Have your commands ready to paste. If something is broken on the day, say so
and talk through it anyway — a screenshot and an honest "this bit is still
failing" is completely fine. Nobody expects a finished product after one week.

### Lead with the problem, not the code

Start with what you were trying to do and why anyone would care. Then show the
thing. Then, if people want it, open the code.

The tempting order is the reverse — start at the code, because that is what
you spent the week looking at. Resist it. People cannot follow the code until
they know what it is for.

### Pick your three things

You cannot show everything in fifteen minutes. Before the session, decide the
three things you actually want people to see, and let the rest go.

Prompts to help you choose:

- What is the bit you are most pleased with?
- What was hardest, and what did you learn from it?
- What surprised you — in the data, or in a tool?
- What did you change your mind about halfway through?

The thing you struggled with is usually more interesting to talk about than the
thing that worked first time.

## Preparing goal 2: explaining it clearly

### Assume less knowledge than feels natural

After a week inside a problem, everything about it feels obvious. It is not.
The people listening have not read your code, and some of them will not know
the cement or the ML side.

The reliable trick: for each thing you plan to explain, ask **"what would I
have needed to know to understand this last Monday?"** Then say that first.

### Practise these out loud

Actually say these to a wall, or a friend, or the dog. Reading them silently
gives you a false sense of how ready you are — the words come out in a much
worse order than you expect the first time.

Keep each answer to about a minute, and use no jargon you have not explained:

1. What does your model predict, and why is that a useful thing to predict?
2. Where does your data come from, and what did you have to do to it before
   it was usable?
3. How do you know whether your model is any good? What number tells you that,
   and what counts as a good value?
4. How does the thing that does the actual learning work — in plain English?
5. Why did you choose the charts you chose for the dashboard?
6. What is the build tool for? What does it do that running Python directly
   does not?
7. Pick one thing that went wrong. What was it, how did you work it out, and
   what do you know now that you did not before?

If you get stuck on any of these, that is exactly what the session is for —
bring the question rather than avoiding it.

### Jargon to watch for

You have picked up a lot of vocabulary this week without necessarily noticing.
Each of these needs a plain-English version ready:

- The metric your model predicts, and its units
- The names of your input features
- Training data vs. test data, and why they have to be different
- Whatever error or score numbers you quote
- The names of the libraries and tools, and what each one is *for*

A good test: could you explain it to someone in your class who has never
written Python? If not, simplify it once more.

### Analogies help, but say where they break

An analogy is the fastest way to get someone to a rough understanding. It is
also the fastest way to leave them with a subtly wrong one.

So use one, then say where it stops being true. "It is a bit like drawing a
line of best fit through a scatter plot — except with several inputs at once,
so you cannot actually draw it." That second half is what stops the analogy
misleading people.

### "I don't know" is a good answer

You will get asked something you have not thought about. The strong answer is
"I don't know — my guess would be X, but I'd have to check." That reads as
confidence, not weakness. Guessing and hoping does not.

Nobody in the room expects you to know everything after a week. They will be
more impressed by you knowing where the edge of your knowledge is.

## Preparing goal 3: what you'd do with more time

The best bit of the session, usually. It shows you can see past what you built
to what it *should* be — which is most of what senior engineering judgement
actually is.

Come with three or four ideas. For each one, be ready to say **why** it would
help, not just what it is. "Add more features" is thin; "the model does badly
during startups, and I think that is because it cannot see X" is a real
engineering thought.

Places to look for ideas:

| Area          | Questions to ask yourself                                        |
| ------------- | ---------------------------------------------------------------- |
| The data      | What would you clean or check that you did not get to? What did you have to ignore? |
| The model     | What would you try next, and what would you expect it to fix?    |
| Testing       | What could break without you noticing? What would you test first? |
| The dashboard | What would someone using it daily still be missing?              |
| Deployment    | What would it take to run this on a schedule, unattended?        |
| If you redid it | What would you do differently from day one, knowing what you know now? |

Also worth thinking about: what would you want to know before trusting this
model on a real plant? That question has no tidy answer, which is what makes
it a good one to discuss.

## Questions you'll probably get

Not a test — you do not need polished answers to all of these. Skim them, spot
the ones that make you pause, and think about those.

**On the model**

- Why did you pick this approach rather than something else?
- What happens if you feed it data unlike anything it trained on?
- Which input matters most, and does that match what you would expect?
- Is it good enough to be useful? How would you decide?

**On the data**

- How much data did you have, and was it enough?
- Did you find anything odd or wrong in it?
- What did you do about missing values, and what else could you have done?

**On the tools**

- What did the build tool give you over just running Python?
- Why write tests for this? What would you have caught without them?
- What was the most confusing tool to learn, and what unstuck you?

**On the dashboard**

- Who is it for, and what do they need from it in ten seconds?
- Why that chart rather than a different one?
- What did you deliberately leave out, and why?

**Bigger picture**

- What surprised you most this week?
- What would you tell someone starting this project on Monday?
- Which part would you want to spend another month on?

## A checklist for the day

- [ ] Dashboard running before the session starts
- [ ] Commands ready to paste, not typed from memory
- [ ] Three things you definitely want to show, chosen in advance
- [ ] The seven questions above said out loud at least once
- [ ] Three or four "with more time" ideas, each with a reason
- [ ] Any questions of your own — about the code, the company, the job

That last one matters. Bring at least one question you actually want answered.
This is your session as much as ours, and a 30-minute slot with a few engineers
is a good chance to ask whatever you have been wondering about all week.

## Last thing

You built a working model and a dashboard in a week, in a language and a
toolchain that were new to you, on an industrial process most adults could not
explain. That is a lot.

The session is not an exam. It is a few people who are interested in what you
did, and want to hear you talk about it.
