# Kodak: Design Document

> A Discord bot that notices what you keep coming back to.

---

## Vision

Kodak is a journaling companion that makes reflection effortless.

Each day at a time you choose, it checks in with a thoughtful prompt. Through conversation, it draws out what's on your mind. Over time, it surfaces patterns—themes you keep returning to, shifts in focus, contradictions worth exploring.

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
3. **Pattern recognition** — Themes and beliefs noticed as byproducts
4. **Progress celebration** — Milestone messages encourage continued engagement
5. **Proactive insights** — Weekly summary prompts after productive periods
6. **Comparison** — Share themes with others, explore where you align and differ

---

## Core Concepts

### Beliefs

A belief is a statement about how you see the world:
- "Hard work matters more than talent"
- "Most people are fundamentally good"
- "I work better under pressure"

Kodak extracts these from your reflections. You don't have to do anything special—just talk naturally.

### Themes

Themes are what you keep coming back to in conversation. Kodak pays attention to recurring patterns:

- **Achievement** — Success, competence, ambition
- **Security** — Safety, stability, order
- **Self-Direction** — Independence, creativity, freedom
- **Connection** — Helping others, loyalty, relationships
- **Stimulation** — Excitement, novelty, challenge
- And others...

This isn't a personality test—it's pattern recognition. The themes Kodak notices are based on what you actually talk about, not how you answer a questionnaire.

Kodak shows you the source material: when it identifies a theme, it includes quotes from your conversations that drove that assessment. It also surfaces uncertainty—how many conversations inform each pattern, and when more data is needed for confidence.

### Theme Comparison

When you share your themes with someone else, Kodak helps you explore:
- **What you both talk about** — Shared themes
- **Where you differ** — Different focuses
- **Questions to explore** — Starting points for conversation

This isn't about compatibility scores. It's about understanding where you connect and where you might see things differently.

---

## Getting Started

New users are guided through an interactive setup that demonstrates exactly what to expect. Kodak shows sample conversations from different scenarios—work stress, relationships, personal goals—so users understand the journaling style before committing to daily check-ins.

Users choose their preferred conversational personality and check-in time, then can start their first session immediately or wait for the scheduled prompt.

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

### 3. Patterns Are Byproducts
You come for "easy journaling." You stay for "wow, I never realized I keep coming back to that."

### 4. Warmth Without Sycophancy
The bot accepts you fully while questioning your ideas freely. No empty validation. Honest reflection requires honest responses.

### 5. Surface Patterns as Curiosities
"I noticed you've mentioned your sister three times this week"—observation, not judgment.

### 6. Privacy by Default
All data is stored locally (or on your Railway instance). Conversations are sent to Anthropic's Claude API for processing—see their [privacy policy](https://www.anthropic.com/privacy). Nothing is shared with other users unless you explicitly export it.

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
| `values.py` | Theme categorization, comparison |
| `db.py` | Database operations |

### Deployment Options
- **Local** — Run on your computer (free)
- **Railway** — Cloud hosting (~$5/month, always on)

---

## Commands Reference

### Scheduling & Preferences
- `/schedule [time]` — Set daily check-in time
- `/journal` — Start a session now
- `/skip` — Skip today's check-in
- `/pause` / `/resume` — Pause/resume check-ins
- `/timezone [tz]` — Set timezone
- `/setup` — Choose personality preset
- `/style` — Fine-tune personality dimensions
- `/depth` — Set session depth preference

### Beliefs
- `/map` — Beliefs organized by topic
- `/beliefs` — Full list with IDs
- `/belief [id]` — View one in detail
- `/explore [topic]` — Dive into a topic
- `/core` — Most important beliefs
- `/history [id]` — See how a belief evolved
- `/changes` — Recent belief changes
- `/confidence [id] [1-5]` — Update belief confidence
- `/mark [id] [1-5]` — Mark belief importance
- `/forget [id]` — Delete a belief
- `/undo` — Restore last forgotten belief
- `/tensions` — Find contradicting beliefs

### Themes
- `/themes` (or `/values`) — Patterns Kodak has noticed
- `/themes-history` (or `/values-history`) — How themes shifted over time
- `/share-themes` (or `/share-values`) — Export for comparison
- `/compare-file` — Compare with someone's export

### Summaries
- `/summary week` — Weekly digest of your journaling
- `/summaries` — View past summaries

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
- **Monthly/yearly summaries** — Expanding on weekly digests
- **Web visualization** — Interactive belief/value graphs
- **Obsidian export** — Take your data into your notes app
- **Longer-term patterns** — "Six months ago you said X. Still feel that way?"
- **Group insights** — What does a community actually value?

See [ROADMAP.md](ROADMAP.md) for the full list.

---

## Philosophy

Kodak is designed to be a genuine companion, not a sycophant.

Most AI assistants are yes-men. They validate everything you say. This feels good but doesn't help you grow.

Kodak will engage honestly, notice contradictions, and sometimes disagree. That's not rudeness—it's respect. You deserve a thinking partner who takes your ideas seriously enough to challenge them.

The goal isn't to make you feel good about what you believe. It's to help you understand what you actually believe, and whether those beliefs serve you.
