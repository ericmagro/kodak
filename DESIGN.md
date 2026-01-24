# Kodak v2.0: Reflective Journaling Companion

> A Discord bot that helps you reflect on your day and, over time, reveals the values and beliefs that shape how you see the world.

## The Pivot

Kodak v1 was a "belief mapping bot" — you chatted with it, and it extracted your beliefs. The problem: **why would anyone consistently talk to it?**

v2 reframes around **reflective journaling**:
- The bot prompts you daily at a time you choose
- You reflect on your day through conversation
- Beliefs and values are extracted as a byproduct
- Over time, you see patterns in what you value and believe

The core insight remains: through conversation, build a map of someone's mind. But now there's a reason to show up every day.

---

## Vision

Kodak is a journaling companion that makes reflection effortless.

**For the user:**
- Daily prompts eliminate the blank-page problem
- Conversation draws out more than you'd write alone
- You see your beliefs and values emerge over time
- You notice how your thinking evolves

**What makes it different from other journaling apps:**
- Conversational, not form-based
- Adapts to your personality preference
- Extracts structured insights (beliefs, values) from unstructured reflection
- Enables comparison with others based on values, not surface-level statements

---

## Foundational Insights

*These remain from v1 — they're even more relevant for journaling.*

### Andy Matuschak — Evergreen Notes
- "Writing forces sharper understanding—articulating a belief clarifies it"
- This is exactly what journaling does. The bot's probing questions force articulation.

### Michael Nielsen — Augmenting Cognition
- Spaced repetition: revisiting beliefs over time aids retention and evolution
- Daily journaling IS spaced repetition for self-knowledge.

### Philip Tetlock — Superforecasting
- Belief updating: "Getting closer to truth gradually"
- Journaling tracks this evolution. "Six months ago you said X. Still feel that way?"

### Julia Galef — Scout Mindset
- Scouts want accurate maps of reality
- Journaling builds an accurate map of your own mind — values, beliefs, contradictions.

### Gordon Brander — AI as the Medium
- "If you want to amplify intelligence, you would go to work on personal AI"
- The bot is a thinking partner, not just a note-taker.

---

## Design Principles

### 1. The Bot Prompts, The User Reflects
The bot initiates. The user just responds. This inverts the cold-start problem.

### 2. Conversation Draws Out More Than Writing Alone
A follow-up question ("What made that frustrating?") surfaces things a blank page wouldn't.

### 3. Beliefs and Values Are Byproducts, Not The Pitch
Users come for "easy journaling." They stay for "wow, I can see what I actually value."

### 4. Adapt to Response Depth
Some days: "Fine, nothing special." Some days: paragraphs. The bot adapts.

### 5. Warmth Without Sycophancy
*(Carried from v1 — still critical)*

The bot accepts the person fully while questioning their ideas freely. No empty validation. Honest reflection requires honest responses.

### 6. Surface Patterns as Curiosities
"I noticed you've mentioned your sister three times this week" — not judgment, just observation.

### 7. Values Enable Meaningful Comparison
Raw belief text is too variable. Derived values (Schwartz framework) enable real comparison.

### 8. Local-First, Privacy-First
Data stays on user's machine. Scheduling works locally. No cloud dependency required.

---

## Core Loop

```
┌─────────────────────────────────────────────────────────┐
│                    DAILY CYCLE                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   [Scheduled time]                                      │
│         │                                               │
│         ▼                                               │
│   Bot sends prompt ──► User responds                    │
│         │                     │                         │
│         │                     ▼                         │
│         │              Bot probes deeper                │
│         │                     │                         │
│         │                     ▼                         │
│         │              [Conversation continues]         │
│         │                     │                         │
│         ▼                     ▼                         │
│   Session ends ◄────── User disengages or              │
│         │              natural close                    │
│         │                                               │
│         ▼                                               │
│   Extract beliefs + derive values                       │
│         │                                               │
│         ▼                                               │
│   Update user's value profile                           │
│         │                                               │
│         ▼                                               │
│   [Next day]                                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Session Flow

Each journaling session follows a flexible structure:

### 1. OPENER (Low commitment)
Get them talking with something easy. **Rotate openers** — don't use the same one every day. Build a pool of 5-10 per personality.

### 2. ANCHOR (One concrete thing)
Focus on a specific moment, event, or feeling.

### 3. PROBE (Go deeper)
Follow-up questions that draw out meaning.

### 4. CONNECT (If engaged)
Link to patterns, past entries, or emerging themes.

**Pattern surfacing frequency:** Max once per week. "You've mentioned your sister three times recently" is useful. Daily pattern-noting feels like surveillance.

### 5. CLOSE (Explicit closure)
The bot must **clearly signal** the session is ending. Users need this boundary.

**Closure elements:**
- Brief reflection on what emerged: "Sounds like today was about [theme]"
- Gratitude: "Thanks for sharing"
- Forward hook (optional): "See you tomorrow" or "Anything you want to pick up next time?"

**Example closes by personality:**
| Personality | Closure style |
|-------------|---------------|
| Philosopher | "Interesting threads today. Let them sit." |
| Best Friend | "Thanks for catching up. Talk tomorrow?" |
| Scientist | "Good data point. We'll see what patterns emerge." |
| Trickster | "Alright, go touch grass. See you tomorrow." |
| Therapist | "Take care of yourself tonight. I'm here when you need me." |

### Extraction Visibility

**Decision:** Show extracted beliefs at session close (lightweight visibility).

During the session, extraction happens silently — no interruptions. At close, include a brief note:

> "Thanks for tonight. I noticed something worth remembering:
> *'Feeling stuck at work makes me question if I'm on the right path'*
>
> See you tomorrow."

This serves three purposes:
1. User sees the system is working (builds trust)
2. User can correct misunderstandings ("that's not what I meant")
3. Reinforces the value proposition (beliefs emerge from conversation)

If no clear beliefs were extracted, skip this part — just close normally. Don't force it.

### Adaptive Depth

**Don't rely on manual depth settings.** Infer from the conversation:

- **Short responses** (< 20 words) → fewer probes, move to close
- **Long responses** (> 100 words) → more connection, follow their energy
- **One-word answers** → one gentle follow-up, then close without pressure
- **User explicitly goes deep** → stay with them, extend session

**Occasionally ask:** "Want to go deeper on this, or leave it there?" — gives user control without requiring upfront settings.

**The depth setting (quick/standard/deep) is a ceiling, not a target.** Quick mode means never more than 3 exchanges. Standard means up to 6. Deep means follow them as long as they're engaged.

### First Session Special Handling

The first journal session after onboarding is different:
- **Lighter probing** — User is still figuring out the dynamic
- **Explicit framing if needed** — "Just tell me whatever comes to mind, there's no right way to do this"
- **Shorter session** — Don't overwhelm; 3-4 exchanges max
- **End with reassurance** — "That's a great start. See you tomorrow."

After the first session, normal adaptive depth applies.

---

## Personality System (Adapted for Journaling)

The four dimensions from v1 remain, but behaviors are journaling-specific.

### Dimensions

| Dimension | Low (1) | High (5) |
|-----------|---------|----------|
| **Warmth** | Idea-focused, analytical | Deeply caring, emotionally attuned |
| **Directness** | Gentle, lets you lead | Names what it sees plainly |
| **Playfulness** | Serious, reflective | Witty, light touch |
| **Formality** | Casual, conversational | Structured, precise |

### Presets (Journaling Behaviors)

| Preset | W | D | P | F | Journaling Style |
|--------|---|---|---|---|------------------|
| **The Philosopher** | 3 | 4 | 2 | 4 | Asks "why" and "what does that mean to you?" Probes assumptions. Treats your day as material for deeper inquiry. |
| **The Best Friend** | 5 | 3 | 4 | 1 | Warm and real. "Ugh, that sounds annoying." Validates first, then gets curious. Makes reflection feel like venting to someone who gets it. |
| **The Scientist** | 2 | 5 | 1 | 5 | Precise questions. "What exactly did they say?" "What happened next?" Helps you see events clearly before interpreting them. |
| **The Trickster** | 3 | 4 | 5 | 1 | Uses humor to surface things. "Sounds like your boss is speedrunning bad management." Lightness that still lands. |
| **The Therapist** | 5 | 3 | 2 | 3 | Reflects back without judgment. "It sounds like that really affected you." Creates safety for vulnerable reflection. |

### Prompt Depth Setting

In addition to personality, users can set prompt depth:
- **Quick** — 2-3 exchanges, light check-in
- **Standard** — 4-6 exchanges, moderate exploration (default)
- **Deep** — 8+ exchanges, thorough reflection

The bot adapts based on this setting AND response length.

---

## Values Framework: Schwartz's Basic Human Values

We derive values from beliefs using Schwartz's empirically-validated framework.

### The 10 Values (Grouped by Higher-Order Dimension)

**Self-Transcendence** (concern for others' welfare)
- **Universalism** — tolerance, social justice, equality, protecting nature
- **Benevolence** — helpfulness, honesty, loyalty to those close to you

**Conservation** (preserving stability)
- **Tradition** — respect for customs, humility, devotion
- **Conformity** — obedience, self-discipline, politeness
- **Security** — safety, stability, social order

**Self-Enhancement** (personal success)
- **Achievement** — success, competence, ambition
- **Power** — authority, wealth, social recognition

**Openness to Change** (independence and novelty)
- **Self-Direction** — creativity, freedom, independence
- **Stimulation** — excitement, novelty, challenge
- **Hedonism** — pleasure, enjoying life

*Note: In Schwartz's circular model, Hedonism sits between Self-Enhancement and Openness to Change — it's a bridge value. For simplicity we group it under Openness, but implementation should recognize its dual nature.*

### How Values Are Derived

1. **Extract beliefs** from journal entries (as before)
2. **Tag each belief** with relevant values (1-3 values per belief)
3. **Assess mapping confidence** — how clearly does this belief map to a value?
4. **Weight by belief confidence × mapping confidence** — uncertain beliefs or ambiguous mappings contribute less
5. **Apply temporal decay** — recent beliefs contribute more than old ones (people change)
6. **Aggregate over time** — build a value profile from all beliefs
7. **Normalize** — scores from 0.0 to 1.0 for each value

**Normalization method:** Normalize relative to the user's own profile — strongest value = 1.0, scale others proportionally. This makes profiles comparable even if one user has expressed more beliefs than another.

```
For each value v:
  raw_score[v] = sum of weighted contributions
  normalized_score[v] = raw_score[v] / max(raw_score across all values)
```

**Mapping confidence:** Not every belief clearly indicates a value. "I work hard to succeed" → high mapping confidence for Achievement. "I had a weird day" → no clear value mapping, don't force it.

**Temporal decay:** A belief from 6 months ago shouldn't weigh the same as one from yesterday. Apply exponential decay (half-life of ~3 months):
```
weight = base_weight × (0.5 ^ (days_ago / 90))
```

Example:
```
Belief: "I work hard because I want to be recognized as excellent"
Belief confidence: 0.8
Mapping confidence: 0.9 (clear Achievement signal)
Days ago: 30
Temporal weight: 0.5 ^ (30/90) = 0.79

Values: Achievement (primary, weight=1.0), Power (secondary, weight=0.5)

Contribution to profile:
  Achievement: 0.8 × 0.9 × 0.79 × 1.0 = 0.57
  Power: 0.8 × 0.9 × 0.79 × 0.5 = 0.28
```

### Value Profile Display

Users see their values narratively, not numerically:

> **What you seem to value most:**
>
> You often come back to themes of **independence and self-direction** —
> making your own choices, not being constrained by others' expectations.
>
> **Achievement** matters to you, but it's personal achievement —
> being good at what you do, not status for its own sake.
>
> You show less emphasis on **tradition and conformity** —
> you question inherited rules rather than accepting them.

### Value Change Over Time

Static profiles are less interesting than evolution. Track and surface change:

> **How your values are shifting:**
>
> Your emphasis on **security** has increased over the past month.
> Recent entries mention stability and planning more than before.
>
> **Stimulation** has decreased slightly — fewer mentions of
> novelty-seeking compared to 3 months ago.

**Implementation:** Store periodic snapshots of value profiles (weekly). Compare current profile to 1 month ago, 3 months ago. Surface significant changes (> 0.15 shift in any value).

---

## Comparison Model

### The Problem with v1 Comparison

v1 compared raw belief statements:
- "Hard work leads to success" vs "Effort determines outcomes"
- Semantically similar? Yes. But the comparison is fragile.

Cam's feedback nailed it: semantic similarity ≠ conceptual alignment.

### v2 Solution: Compare Value Profiles

Instead of matching belief text, compare derived values:

```
User A's Value Profile:
  Achievement: 0.7
  Self-Direction: 0.8
  Benevolence: 0.4
  Security: 0.2
  ...

User B's Value Profile:
  Achievement: 0.6
  Self-Direction: 0.7
  Benevolence: 0.5
  Security: 0.3
  ...

Similarity: High (both prioritize Achievement + Self-Direction)
```

### File-Based Comparison (Local-First)

Since users run their own instances, comparison works via file export:

```
1. User A: /share-values
   → Selects which values/beliefs to include (privacy control)
   → Downloads JSON file

2. User A sends file to User B
   (Discord DM, email, whatever — outside the bot)

3. User B: /compare-file [attaches file]
   → Sees comparison of their values vs User A's shared values
```

**No @user mentions, no request flows, no server coordination.** Simple and privacy-preserving.

### What Comparison Shows

1. **Overall value alignment** — How similar are your value profiles?
2. **Shared priorities** — Which values you both emphasize
3. **Interesting differences** — Where you diverge (potential for learning)
4. **Complementary gaps** — Values one has that the other doesn't emphasize

### Intended Use Cases

- **Understanding a friend better** — "I didn't realize we both value self-direction so much"
- **Couples/partners** — See where you align and where you might clash
- **Curiosity** — "How similar am I to this person I admire?"

This is NOT a matching/dating feature. It's a reflection tool for existing relationships.

### Privacy for Comparison

- User explicitly chooses what to export (opt-in per value, per belief)
- Export UI makes it easy to exclude sensitive values/beliefs
- Only exported data is shared — raw journal entries never leave the device
- Recipient only sees what was shared, displayed alongside their own profile

---

## Scheduling System

### User Experience

1. During onboarding, user picks a time: "When should I check in? (e.g., 8pm)"
2. Bot sends a prompt at that time daily
3. User can change time anytime with `/schedule`
4. User can skip days or pause entirely

### Technical Implementation (Local-First)

```python
# Background task runs while bot is active
async def scheduler_loop():
    while True:
        await asyncio.sleep(60)  # Check every minute

        current_time = get_local_time()
        users_due = get_users_due_for_prompt(current_time)

        for user in users_due:
            await send_journal_prompt(user)
            mark_prompt_sent(user)
```

### Local Running: Friction & Mitigations

**The reality:** Local-first means the bot must be running to send prompts. This creates friction.

| Scenario | Problem | Mitigation |
|----------|---------|------------|
| User restarts computer | Bot stops, misses prompts | Document auto-start setup |
| User closes terminal | Bot stops | Run as background service |
| User forgets to start | No prompt that day | Catch-up prompt on next start |
| User travels (timezone) | Wrong prompt time | `/timezone` command |

**Auto-start setup (document for users):**
- **macOS:** launchd plist file
- **Linux:** systemd service unit
- **Windows:** Task Scheduler entry

**Catch-up logic on startup:**
```python
async def check_missed_prompts():
    for user in get_all_users_with_scheduling():
        if missed_todays_prompt(user):
            hours_since = hours_since_scheduled_time(user)
            if hours_since < 4:
                await send_catch_up_prompt(user)
            elif hours_since < 12 and not too_late_at_night():
                await send_gentle_catch_up(user)
            # else: skip, wait for tomorrow
```

**For Railway/cloud users:** No friction — always running.

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Bot wasn't running at scheduled time | On startup, check for missed prompts. If within 4 hours, send catch-up. If within 12 hours and not too late, gentle catch-up. Otherwise skip to tomorrow. |
| User doesn't respond | Don't nag. After 3 ignored prompts, ask once: "Should I check in less often?" Then adapt based on response. |
| User wants to journal off-schedule | Always welcome. Just DM the bot anytime. |
| Timezone handling | Store user's preferred time + timezone. `/timezone` command to update. For local hosting, default to system timezone. |
| User changes schedule mid-day to past time | Wait until tomorrow. Don't trigger immediately (confusing). |
| User returns after long absence (2+ weeks) | Warm re-engagement: "Hey, it's been a while. No pressure — want to catch up, or just pick up fresh?" Don't guilt-trip about missed sessions. |

---

## Data Model

### New Tables

```sql
-- User scheduling preferences (extends users table)
ALTER TABLE users ADD COLUMN prompt_time TEXT;           -- "20:00"
ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'local';
ALTER TABLE users ADD COLUMN prompt_depth TEXT DEFAULT 'standard';  -- quick/standard/deep
ALTER TABLE users ADD COLUMN last_prompt_sent TEXT;
ALTER TABLE users ADD COLUMN prompts_ignored INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN prompt_frequency TEXT DEFAULT 'daily';  -- daily/every_other/weekly

-- Journal sessions
CREATE TABLE journal_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    prompt_type TEXT,          -- 'scheduled', 'user_initiated', 'catch_up'
    message_count INTEGER DEFAULT 0,
    beliefs_extracted INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Value scores (derived from beliefs)
CREATE TABLE user_values (
    user_id TEXT NOT NULL,
    value_name TEXT NOT NULL,  -- 'achievement', 'benevolence', etc.
    score REAL DEFAULT 0.0,    -- 0.0 to 1.0
    belief_count INTEGER DEFAULT 0,
    last_updated TEXT,
    PRIMARY KEY (user_id, value_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Belief-to-value mapping
CREATE TABLE belief_values (
    belief_id TEXT NOT NULL,
    value_name TEXT NOT NULL,
    weight REAL DEFAULT 1.0,           -- primary=1.0, secondary=0.5
    mapping_confidence REAL DEFAULT 1.0, -- how clearly this belief maps to this value
    PRIMARY KEY (belief_id, value_name),
    FOREIGN KEY (belief_id) REFERENCES beliefs(id)
);

-- Value profile snapshots (for tracking change over time)
CREATE TABLE value_snapshots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,       -- date of snapshot
    values_json TEXT NOT NULL,         -- JSON of {value_name: score}
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
-- Create weekly snapshots to track value evolution
-- Future consideration: retention policy (keep weekly for 3 months,
-- then monthly, then quarterly) to prevent unbounded growth
```

### Existing Tables (Retained)

- `users` — extended with scheduling fields
- `beliefs` — unchanged
- `belief_topics` — unchanged
- `belief_relations` — unchanged
- `belief_evolution` — unchanged
- `conversations` — unchanged

### Removed/Deferred

- `comparison_requests` — rethink for value-based comparison
- `comparison_results` — rethink for value-based comparison
- `bridging_beliefs` — defer until v2.1

---

## Commands

### Retained (as-is or minor tweaks)

| Command | Notes |
|---------|-------|
| `/help` | Update for v2 commands |
| `/map` | Shows beliefs grouped by topic |
| `/explore [topic]` | Dive into beliefs about a topic |
| `/beliefs` | Raw list with confidence/importance |
| `/belief [id]` | View single belief with connections |
| `/history [id]` | Belief evolution over time |
| `/forget [id]` | Delete a belief |
| `/undo` | Restore last forgotten |
| `/pause` / `/resume` | Pause/resume extraction |
| `/export` | Download all data |
| `/clear` | Delete everything |
| `/setup` | Personality selection |
| `/style` | Fine-tune dimensions |

### New Commands

| Command | Description |
|---------|-------------|
| `/schedule [time]` | Set your daily prompt time (e.g., `/schedule 8pm`) |
| `/timezone [tz]` | Set your timezone (for travelers or misconfigured systems) |
| `/depth [level]` | Set max prompt depth: quick, standard, deep |
| `/values` | See your derived value profile (narrative display) |
| `/values-history` | See how your values have shifted over time |
| `/share-values` | Export value profile as shareable JSON (with privacy selection) |
| `/compare-file` | Compare your values with someone's exported file |
| `/journal` | Start an off-schedule journal session |
| `/skip` | Skip today's prompt |

### Removed/Deferred

| Command | Reason |
|---------|--------|
| `/compare @user` | Removed — use file-based comparison instead (local-first) |
| `/bridging` | Defer — rethink for values in future version |
| `/share` | Replaced by `/share-values` |
| `/share-export` | Replaced by `/share-values` |
| `/requests` | Removed — no request flow needed for file-based comparison |
| `/core` | Keep — still useful for viewing important beliefs |
| `/tensions` | Keep — still useful |
| `/changes` | Keep — still useful |
| `/mark` | Keep — importance still matters |
| `/confidence` | Keep — confidence still matters |
| `/backup` | Keep — still useful |
| `/privacy` | Keep simplified — per-belief toggle for "include in value profile" |

---

## Onboarding Flow

Simplified for v2:

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Hey! I'm Kodak.                                          │
│                                                            │
│  I'm a journaling companion. Each day at a time you       │
│  choose, I'll check in and help you reflect.              │
│                                                            │
│  Over time, I'll help you see patterns in what you        │
│  believe and value.                                        │
│                                                            │
│  Everything stays private on your device.                  │
│                                                            │
│  First — how would you like me to show up?                │
│                                                            │
│  [The Philosopher] [The Best Friend] [The Therapist]      │
│  [The Scientist] [The Trickster]                          │
│                                                            │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  [Shows personality preview with example exchange]         │
│                                                            │
│  [Choose this one] [See another]                          │
│                                                            │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  When should I check in?                                   │
│                                                            │
│  Most people like evening — time to reflect on the day.   │
│                                                            │
│  [7pm] [8pm] [9pm] [10pm] [Other time...]                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  You're all set!                                          │
│                                                            │
│  I'll message you at [time] each day.                     │
│                                                            │
│  Or just message me anytime you want to reflect.          │
│                                                            │
│  Ready for your first session?                            │
│                                                            │
│  [Let's go] [I'll wait for the first prompt]              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Prompt Design Guidelines

### System Prompt Structure

Keep it tight. Under 300 words total.

```
[Base instructions — ~150 words]
- You are Kodak, a reflective journaling companion
- Your role is to help the user reflect on their day
- Session flow: opener → anchor → probe → connect → close
- Adapt to response depth (short = fewer probes)
- Never validate just to be nice
- Surface patterns as curiosities, not judgments

[Personality flavor — ~50 words]
- [Personality-specific instructions based on preset]

[Session state — ~20 words]
- Current stage: [opener/anchor/probe/connect/close]
- Response depth setting: [quick/standard/deep]

[Recent context — last 2-3 exchanges only]
```

### Opener Pools by Personality

Each personality has a pool of 7-10 openers. Rotate randomly — don't repeat consecutively.

**The Philosopher:**
- "What occupied your mind today?"
- "What's something from today that deserves more thought?"
- "Any moments today that made you pause?"
- "What assumptions did today challenge?"
- "What's sitting with you from today?"
- "Anything today that surprised you about yourself?"
- "What would you want to remember from today?"

**The Best Friend:**
- "Hey! How was today?"
- "What's the vibe tonight?"
- "Anything good happen today?"
- "How you doing?"
- "What's on your mind?"
- "Tell me about your day."
- "Any highlights? Or lowlights?"
- "What's the headline from today?"

**The Scientist:**
- "What happened today that's worth examining?"
- "What data did today generate?"
- "Any observations from today?"
- "What would you want to document from today?"
- "What patterns did you notice today?"
- "Anything today that warrants analysis?"
- "What's the most notable event from today?"

**The Trickster:**
- "Survive another day in the simulation?"
- "What chaos did today bring?"
- "Any good stories from today?"
- "What's the most absurd thing that happened today?"
- "Did the universe mess with you today?"
- "Any plot twists today?"
- "What would today's episode be titled?"
- "How'd the NPCs treat you today?"

**The Therapist:**
- "How are you feeling this evening?"
- "How was today for you?"
- "What's present for you right now?"
- "How are you arriving tonight?"
- "What are you carrying from today?"
- "How's your heart tonight?"
- "What does today feel like?"

### Probe Examples by Personality

Probes are more contextual than openers — these are templates/styles, not a rotation pool.

**The Philosopher:**
- "What does that reveal about what matters to you?"
- "What's the assumption underneath that?"
- "Why do you think that bothered you?"
- "What would it mean if the opposite were true?"
- "What's the deeper question here?"

**The Best Friend:**
- "Ugh, that sounds frustrating. What was the worst part?"
- "Wait, tell me more about that."
- "How'd that make you feel?"
- "That's a lot. What's the piece that sticks with you most?"
- "What did you want to happen instead?"

**The Scientist:**
- "What specifically triggered that reaction?"
- "What happened right before that?"
- "Can you walk me through the sequence?"
- "What evidence led you to that conclusion?"
- "What's the specific thing that's bothering you?"

**The Trickster:**
- "Classic. What's the pettiest thought you had about it?"
- "On a scale from 'mildly annoyed' to 'plotting revenge,' where are we?"
- "What would chaos goblin you do about this?"
- "What's the version of this story you'd tell at a bar?"
- "Is this a 'vent and forget' or a 'this actually matters' situation?"

**The Therapist:**
- "It sounds like that really landed. How are you sitting with it?"
- "What's that bringing up for you?"
- "Where do you feel that in your body?"
- "What would you want someone to understand about this?"
- "What do you need right now?"

---

## What Survives from v1

| Component | Status |
|-----------|--------|
| Name "Kodak" | ✅ Kept |
| Foundational insights | ✅ Kept (more relevant now) |
| Design principles (most) | ✅ Kept, some adapted |
| Anti-sycophancy stance | ✅ Kept (critical) |
| Personality dimensions | ✅ Kept, behaviors adapted |
| Personality presets | ✅ Kept, behaviors adapted |
| Belief extraction | ✅ Kept |
| Belief storage model | ✅ Kept |
| Topics and relations | ✅ Kept |
| Evolution tracking | ✅ Kept |
| Privacy controls | ✅ Kept |
| Export functionality | ✅ Kept |
| Most commands | ✅ Kept |

## What Changes

| Component | Change |
|-----------|--------|
| Core loop | Reactive → Scheduled prompts |
| Primary framing | "Belief mapping" → "Reflective journaling" |
| Onboarding | Personality+mode → Personality+schedule |
| Comparison | Raw beliefs → Value profiles |
| Extraction | Beliefs only → Beliefs + derived values |
| Channel mode | Removed (DM-only) |
| Comparison flows | Simplified (no request/accept) |

## What's New

| Component | Description |
|-----------|-------------|
| Scheduling system | Daily prompts at user-chosen time |
| Session model | Structured journal sessions |
| Values framework | Schwartz's 10 Basic Human Values |
| Value derivation | Beliefs → tagged values → profile |
| Value comparison | Compare profiles, not raw text |
| Prompt depth setting | Quick / Standard / Deep |

---

## Implementation Roadmap

### Phase 1: Core Rewrite
- [ ] New onboarding flow (personality → schedule time)
- [ ] Scheduling system (background task + catch-up logic)
- [ ] Session model (start/end/track)
- [ ] Adapted prompt design (personality-specific journaling openers + probes)
- [ ] Opener pools (7-10 per personality, with rotation)
- [ ] Probe templates by personality
- [ ] Clear session closure behavior (with extraction visibility)
- [ ] First session special handling (lighter, reassuring)
- [ ] Re-engagement flow for returning users (2+ weeks absent)
- [ ] Adaptive depth inference from response length
- [ ] Remove channel mode (DM-only)
- [ ] Document auto-start setup for local users

### Phase 2: Values
- [ ] Add Schwartz value constants (10 values + higher-order dimensions)
- [ ] Extend extraction to tag beliefs with values + mapping confidence
- [ ] Temporal decay weighting (3-month half-life)
- [ ] Value normalization (relative to user's own max)
- [ ] Build value profile aggregation
- [ ] Weekly value snapshots for change tracking
- [ ] `/values` command with narrative display
- [ ] `/values-history` command showing change over time

### Phase 3: Comparison (File-Based)
- [ ] `/share-values` with privacy selection UI
- [ ] Export format (JSON with selected values/beliefs)
- [ ] `/compare-file` to load and compare
- [ ] Comparison display (shared values, differences, narrative)

### Phase 4: Polish
- [ ] Adaptive prompting (ask about frequency after ignored prompts)
- [ ] Pattern surfacing (max once per week)
- [ ] Weekly reflection summaries (optional)
- [ ] `/timezone` command
- [ ] Per-belief "exclude from values" toggle

---

## Open Questions

1. **How many values per belief?** Start with 1-3, see if that's too noisy.

2. **How to handle value conflicts?** Same person can value both Security and Stimulation in different contexts. Consider domain-tagging beliefs (work vs. relationships vs. personal)?

3. **Mapping confidence threshold?** Should we skip tagging beliefs that don't clearly map to values (confidence < 0.5)? Or tag everything but weight low-confidence mappings less? *Leaning toward: tag everything, weight by confidence.*

4. **Weekly summaries?** "Here's what I noticed this week" — test with users. Make it optional/skippable if annoying.

5. **Opener fatigue?** With 7-10 openers per personality, how long before they feel repetitive? May need to expand pools over time or add seasonal/contextual variation.

## Resolved Questions

- **Extraction visibility:** Show at session close, not during. ✅
- **What if someone only wants journaling?** Extraction always on, values only surface if asked. ✅
- **Auto-start priority:** Document it but accept local users need some setup. ✅
- **First session handling:** Lighter, with explicit reassurance. ✅
- **Re-engagement after absence:** Warm, no guilt-trip. ✅

---

## References

### Values Research
- Schwartz, S.H. (1992). Universals in the content and structure of values
- Schwartz, S.H. (2012). An Overview of the Schwartz Theory of Basic Values
- World Values Survey methodology

### Journaling Research
- Pennebaker, J.W. — Expressive writing and health outcomes
- Reflection and metacognition literature

### Conversational Design
- Erika Hall — *Conversational Design*
- Conversation Design Institute

### From v1 (Still Relevant)
- Andy Matuschak — Evergreen Notes
- Michael Nielsen — Augmenting Cognition
- Julia Galef — Scout Mindset
- Philip Tetlock — Superforecasting
- Gordon Brander — Noosphere
