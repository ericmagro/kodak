# Kodak: Design Document

> A Discord bot that helps you understand yourself through daily journaling.

---

## Vision

Kodak is a journaling companion that makes reflection effortless.

Each day at a time you choose, it checks in with a thoughtful prompt. Through conversation, it draws out what's on your mind. Over time, it surfaces patterns in what you believe and value.

**The insight:** Most people don't journal because of the blank page problem. But everyone can answer a question. Kodak asks the questions.

---

## Why This Matters

### The Problem with Self-Knowledge

People think they know what they value. But ask them to list their values and you get generic answers: "family, honesty, success." These are socially acceptable placeholders, not genuine insight.

Real values emerge through behavior, through what you actually spend time thinking about, through how you react when things go wrong. Journaling captures this—but only if you actually do it.

### Why Journaling Fails

1. **Blank page problem** — "What should I write about?"
2. **No feedback loop** — You write, nothing happens
3. **No pattern recognition** — Individual entries feel disconnected
4. **No comparison** — You can't see how you relate to others

### How Kodak Solves This

1. **Daily prompts** — The bot initiates, you just respond
2. **Conversational depth** — Follow-up questions draw out more than writing alone
3. **Automatic extraction** — Beliefs and values surfaced as byproducts
4. **Value framework** — Schwartz's 10 values enable meaningful comparison

---

## Core Concepts

### Beliefs

A belief is a statement about how you see the world:
- "Hard work matters more than talent"
- "Most people are fundamentally good"
- "I work better under pressure"

Kodak extracts these from your reflections. You don't have to do anything special—just talk naturally.

### Values

Values are derived from beliefs using Schwartz's 10 Basic Human Values—a research-backed framework used in cross-cultural psychology:

| Value | What it means |
|-------|---------------|
| **Self-Direction** | Independence, creativity, freedom |
| **Stimulation** | Excitement, novelty, challenge |
| **Hedonism** | Pleasure, enjoying life |
| **Achievement** | Success, competence, ambition |
| **Power** | Authority, wealth, social status |
| **Security** | Safety, stability, order |
| **Conformity** | Obedience, self-discipline |
| **Tradition** | Respect for customs, humility |
| **Benevolence** | Helping those close to you |
| **Universalism** | Tolerance, social justice for all |

Each belief you express is tagged with 0-3 values. Over time, this builds a profile of what you actually prioritize.

### Value Comparison

Because values are standardized, you can compare them meaningfully:
- **Alignment %** — How similar are two people's value priorities?
- **Shared priorities** — Where do you both score high?
- **Differences** — Where do your priorities diverge?

This isn't about finding people who agree with you. It's about understanding where you connect and where you differ.

---

## The Daily Loop

```
┌─────────────────────────────────────────────────────────┐
│                    DAILY SESSION                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   [Scheduled time]                                      │
│         │                                               │
│         ▼                                               │
│   ┌─────────────┐                                       │
│   │   Opener    │  "What's been on your mind today?"    │
│   └──────┬──────┘                                       │
│          │                                              │
│          ▼                                              │
│   ┌─────────────┐                                       │
│   │   Anchor    │  Focus on one concrete thing          │
│   └──────┬──────┘                                       │
│          │                                              │
│          ▼                                              │
│   ┌─────────────┐                                       │
│   │   Probe     │  "What made that frustrating?"        │
│   └──────┬──────┘  (adapts to response depth)           │
│          │                                              │
│          ▼                                              │
│   ┌─────────────┐                                       │
│   │   Close     │  Summarize, surface beliefs           │
│   └─────────────┘                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Adaptive Depth

Sessions adapt to your energy:
- **Quick day:** Brief responses → 2-3 exchanges → done
- **Lots to process:** Long responses → deeper probing → more extraction

You control the depth with `/depth quick|standard|deep`.

---

## Design Principles

### 1. The Bot Prompts, The User Reflects
The bot initiates. You just respond. No blank page.

### 2. Conversation Draws Out More Than Writing Alone
"What made that frustrating?" surfaces things a blank page wouldn't.

### 3. Beliefs and Values Are Byproducts
You come for "easy journaling." You stay for "wow, I can see what I actually value."

### 4. Warmth Without Sycophancy
The bot accepts you fully while questioning your ideas freely. No empty validation. Honest reflection requires honest responses.

### 5. Surface Patterns as Curiosities
"I noticed you've mentioned your sister three times this week"—observation, not judgment.

### 6. Privacy First
All data stays on your machine (or your Railway instance). Nothing is shared unless you explicitly export it.

---

## Personality System

Users choose how Kodak shows up:

| Preset | Style |
|--------|-------|
| **The Philosopher** | Asks "why" a lot, probes assumptions |
| **The Best Friend** | Warm, supportive, honest |
| **The Scientist** | Precise, analytical, evidence-focused |
| **The Trickster** | Playful, irreverent, challenges you |
| **The Therapist** | Gentle, never pushes, creates safety |

This affects tone and probing style, not the underlying extraction.

---

## Technical Architecture

### Stack
- **Discord.py** — Bot framework
- **Anthropic Claude** — Conversation and extraction
- **SQLite** — Local database
- **pytz** — Timezone-aware scheduling

### Key Components

| File | Purpose |
|------|---------|
| `bot.py` | Main bot, commands, session handling |
| `scheduler.py` | Daily prompts, timezone-aware |
| `session.py` | Session state, adaptive depth |
| `extractor.py` | Belief + value extraction |
| `values.py` | Schwartz framework, comparison |
| `db.py` | Database operations |

### Deployment Options
- **Local** — Run on your computer (free)
- **Railway** — Cloud hosting (~$5/month, always on)

---

## Commands Reference

### Scheduling
- `/schedule [time]` — Set daily check-in time
- `/journal` — Start a session now
- `/skip` — Skip today's check-in
- `/pause` / `/resume` — Pause/resume check-ins
- `/timezone [tz]` — Set timezone

### Beliefs
- `/map` — Beliefs organized by topic
- `/beliefs` — Full list with IDs
- `/belief [id]` — View one in detail
- `/explore [topic]` — Dive into a topic
- `/core` — Most important beliefs

### Values
- `/values` — Your value profile
- `/values-history` — How values shifted over time
- `/share-values` — Export for comparison
- `/compare-file` — Compare with someone's export

### Data
- `/export` — Download all your data
- `/clear` — Delete everything

---

## Foundational Influences

### Andy Matuschak — Evergreen Notes
"Writing forces sharper understanding—articulating a belief clarifies it."

Journaling is articulation. The bot's questions force clarity.

### Michael Nielsen — Augmenting Cognition
Spaced repetition aids retention and evolution.

Daily journaling IS spaced repetition for self-knowledge.

### Philip Tetlock — Superforecasting
"Getting closer to truth gradually through belief updating."

Kodak tracks how your beliefs evolve over time.

### Julia Galef — Scout Mindset
Scouts want accurate maps of reality.

Kodak builds an accurate map of your own mind.

### Gordon Brander — Personal AI
"If you want to amplify intelligence, go to work on personal AI."

The bot is a thinking partner, not just a note-taker.

---

## What's Next

Potential future directions:
- **Web visualization** — Interactive belief/value graphs
- **Obsidian export** — Take your data into your notes app
- **Longer-term patterns** — "Six months ago you said X. Still feel that way?"
- **Group insights** — What does a community actually value?

---

## Philosophy

Kodak is designed to be a genuine companion, not a sycophant.

Most AI assistants are yes-men. They validate everything you say. This feels good but doesn't help you grow.

Kodak will engage honestly, notice contradictions, and sometimes disagree. That's not rudeness—it's respect. You deserve a thinking partner who takes your ideas seriously enough to challenge them.

The goal isn't to make you feel good about what you believe. It's to help you understand what you actually believe, and whether those beliefs serve you.
