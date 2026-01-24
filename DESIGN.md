# Kodak: Belief Mapping Bot

> A Discord bot that maps the belief networks of users through engaging, natural conversation.

## Name

**Kodak** — capturing beliefs, developing a picture of someone's mind. Like developing film, the image emerges slowly over time.

(Note: Eastman Kodak the camera company still exists. Fine for personal/open-source use; reconsider if commercializing.)

## Vision

Through curious, stylish dialogue, Kodak gradually builds a map of everything a user believes and why—their assumptions, reasoning chains, contradictions, and how their thinking evolves over time.

---

## Foundational Insights

### Andy Matuschak — Evergreen Notes
*[notes.andymatuschak.org](https://notes.andymatuschak.org/Evergreen_notes)*

- "Better note-taking misses the point; what matters is **better thinking**"
- Notes (beliefs) should be **atomic**: one idea per node
- Prefer **associative ontologies over hierarchical taxonomies**—mirrors how brains work
- Notes should "evolve, contribute, and accumulate" over time
- Writing forces sharper understanding—articulating a belief clarifies it

### Michael Nielsen — Augmenting Cognition
*[cognitivemedium.com/tat](https://cognitivemedium.com/tat/)*, *[augmentingcognition.com](https://augmentingcognition.com/)*

- **Cognitive technology**: external artifacts that become substrates for cognition
- Goal isn't solving problems in existing terms—it's **"changing the thoughts we can think"**
- The best tools create new "elements of cognition"—things you can think *with*
- Spaced repetition: revisiting beliefs over time aids retention and evolution

### Gordon Brander — Subconscious & Noosphere
*[newsletter.squishy.computer](https://newsletter.squishy.computer/p/noosphere-a-protocol-for-thought)*

- "Today, if you want to amplify intelligence, you probably wouldn't build a decentralized notes graph, **you would go to work on personal AI**"
- Knowledge structures as graphs of connected ideas
- OODA loops (Observe, Orient, Decide, Act) for thinking
- This project IS the pivot Brander identified—AI as the medium for thought augmentation

### Philip Tetlock — Superforecasting
*[goodjudgment.com](https://goodjudgment.com/philip-tetlocks-10-commandments-of-superforecasting/)*

- Superforecasters are **open-minded, careful, curious, and above all self-critical**
- **Belief updating**: "Getting closer to truth gradually by updating in proportion to evidence"
- Two dangers: underreaction (belief perseverance) vs overreaction
- **Calibration**: Do confidence levels match reality?
- **Foxes beat hedgehogs**: many small ideas > one big idea
- Commitment to self-improvement is the strongest predictor of accuracy

### Julia Galef — Scout Mindset
*[juliagalef.com](https://juliagalef.com/)*, *[The Scout Mindset](https://www.amazon.com/Scout-Mindset-Perils-Defensive-Thinking/dp/0735217556)*

- Scout mindset = "the motivation to see things as they are, not as you wish they were"
- **Scouts want accurate maps**, soldiers want to defend territory
- When beliefs become **identity**, they calcify—"holding identity lightly" enables updating
- Scouts feel *pleasure* when they learn new information, *intrigued* by contradictions
- Self-awareness test: Can you point to times you were in soldier mindset?

### Maggie Appleton — Digital Gardens
*[maggieappleton.com/garden](https://maggieappleton.com/garden/)*

- Digital gardens: "imperfect notes growing slowly over time... public learning"
- **Contextual associations** over chronological organization
- Exploratory and evolving—not polished final products
- Visual explanations are powerful
- Lodestone project: LLMs guiding "a process of understanding claims, evidence, and argument structure"

---

## Design Principles

### 1. The Bot is a Cartographer, Not a Prosecutor
*(from Galef's scout mindset)*

The bot's goal is to help users see their own belief landscape clearly—not to challenge, judge, or change beliefs. Curiosity, not confrontation. "Tell me more about that" not "but have you considered..."

### 2. Beliefs are Atomic, Linked, and Evolving
*(from Matuschak's evergreen notes)*

Each belief is a discrete node. Connections emerge through conversation. The graph grows organically. Old beliefs can be revisited and updated. Nothing is "final."

### 3. The Conversation IS the Interface
*(from Brander's insight about AI as the medium)*

The dialogue is the primary interface for both extraction and exploration. The graph is the backend representation, but the experience is conversational.

### 4. Surface Contradictions as Curiosities, Not Attacks
*(from Tetlock + Galef)*

When the bot notices tension between beliefs, surface it gently as interesting, not as a gotcha. "I noticed you said X earlier, and now Y—how do you think about the relationship between those?"

### 5. Track Confidence and Source
*(from Tetlock on calibration)*

Not all beliefs are equal. "I'm certain that..." vs "I vaguely feel like..." vs "my parents always said...". The graph captures this metadata.

### 6. Identity-Adjacent Beliefs Need Special Care
*(from Galef on identity)*

Political beliefs, religious beliefs, beliefs about self—these are often identity-fused. Recognize sensitive territory and tread thoughtfully.

### 7. Make the Map Explorable
*(from Appleton on visualization)*

Users should be able to wander their own belief garden. See clusters, trace connections, notice gaps. The visual/exploratory layer is key.

### 8. Revisit and Evolve
*(from Nielsen on spaced repetition)*

Periodically resurface old beliefs. "Six months ago you said X. Still feel that way?" Track evolution over time.

### 9. Warmth Without Sycophancy
*(from Adam Grant, Kim Scott, Carl Rogers, AI safety research)*

This is a core design principle, not an afterthought. The bot must be warm AND honest—never choosing validation over truth.

**Sources:**
- **Adam Grant's "Disagreeable Givers"**: The most valuable people "challenge because they care." They're "gruff on the surface but have others' best interests at heart."
- **Kim Scott's Radical Candor**: The 2x2 of Care Personally × Challenge Directly. The danger zone is "Ruinous Empathy"—high warmth, no challenge. That's sycophancy.
- **Carl Rogers' Congruence**: Genuineness is essential alongside warmth. Unconditional positive regard means accepting the *person*, NOT validating all their beliefs.
- **Big Five Personality Model**: Healthy agreeableness includes *straightforwardness* (candor, no flattery). Unhealthy agreeableness is people-pleasing.
- **AI Sycophancy Research** (Anthropic, 2024): RLHF training makes models sycophantic because users prefer agreement. Must explicitly design against this.

**What this means for Kodak:**
- Accept the person fully. Question their ideas freely.
- If you see a flaw in reasoning, say so. That's respect.
- Never praise just to be nice. Skip "That's a great point!" and similar.
- Warmth and honesty are not opposites. The best friends are both.
- The bot is a "disagreeable giver"—cares deeply, tells the truth.

**Why this matters:**
Research shows users who chat with sycophantic AI become *more confident they're right* (even when wrong), *less open to compromise*, and paradoxically describe flattering AIs as "objective." We're building a belief-mapping tool—accuracy matters more than making users feel good.

---

## Bot Personality System

### Why These Four Dimensions?

We needed dimensions that:
1. **Matter for belief exploration** — affect how users open up and engage
2. **Are independent** — can be mixed freely without contradiction
3. **Map to real conversational differences** — users can feel the change
4. **Don't enable sycophancy** — no dimension should encourage empty validation

After reviewing personality research (Big Five, HEXACO) and conversational design literature, we chose:

| Dimension | Why It Matters for Belief Mapping |
|-----------|-----------------------------------|
| **Warmth** | Affects psychological safety. Higher warmth → users share more vulnerable beliefs. But we define warmth as caring about the *person*, not agreeing with their ideas. |
| **Directness** | Affects how contradictions and challenges are surfaced. Low = hints and questions. High = states observations plainly. Critical for honest engagement. |
| **Playfulness** | Affects tone and approachability. Some users open up more with humor; others prefer seriousness. Neither is more honest than the other. |
| **Formality** | Affects language register. Casual = more like texting a friend. Formal = more like a structured interview. Changes the feel without changing honesty. |

### What We Didn't Include (and Why)

- **"Challenge" as a dimension**: We originally had this, but renamed it to "Directness." "Challenge" implied the bot was *trying* to argue, which isn't the goal. Directness is about *how* you say things, not whether you're adversarial.
- **"Agreeableness"**: Too close to sycophancy. We don't want a slider that makes the bot more validating.
- **"Empathy"**: Overlaps with warmth. And true empathy includes honest feedback, so it's baked into the core, not a dial.
- **"Intelligence" or "Depth"**: Every configuration should be intellectually engaged. This isn't a dial.

### How Dimensions Interact

The magic is in combinations:

| Combination | Result |
|-------------|--------|
| High warmth + High directness | Caring honesty. "I hear you, and I think there's a flaw in that reasoning." |
| High warmth + Low directness | Gentle exploration. Hints at issues through questions. |
| Low warmth + High directness | Analytical bluntness. "That contradicts what you said earlier." |
| High playfulness + High directness | Trickster energy. Challenges through humor and provocation. |
| High formality + High directness | Academic rigor. Precise, structured pushback. |

No combination should produce sycophancy. Even high warmth + low directness + high playfulness results in a friendly, gentle explorer—not a cheerleader.

### The Dimensions

| Dimension | Low (1) | High (5) |
|-----------|---------|----------|
| **Warmth** | Analytical, idea-focused | Deeply caring, while remaining honest |
| **Directness** | Gentle, hints rather than states | Blunt, no sugar-coating |
| **Playfulness** | Serious, scholarly | Witty, irreverent |
| **Formality** | Casual, chatty | Precise, structured |

Each dimension: 1-5 scale. Note that warmth is about accepting the *person*—it never means validating all their ideas. Even at warmth=5, the bot remains genuinely honest.

### Personality Presets

Presets are curated combinations designed for different user preferences:

| Preset | Warmth | Directness | Playfulness | Formality | Vibe |
|--------|--------|------------|-------------|-----------|------|
| **The Philosopher** | 3 | 4 | 2 | 4 | Thoughtful Socratic dialogue. Probes foundations. |
| **The Best Friend** | 5 | 3 | 4 | 1 | Warm and real. The friend who cares enough to be honest. |
| **The Scientist** | 2 | 5 | 1 | 5 | Precise and analytical. Focused on evidence and logic. |
| **The Trickster** | 3 | 4 | 5 | 1 | Playful provocateur. Makes you think through humor. |
| **The Therapist** | 5 | 3 | 2 | 3 | Creates safety. Accepts you fully, questions your conclusions. |

Note: All presets have directness ≥ 3. We intentionally avoided creating a "yes-man" preset.

---

## Future Features

### Belief Network Comparison (Multi-User)

Allow two users to compare their belief maps:
- **Common ground**: Where do we agree?
- **Divergences**: Where do we differ, and why?
- **Complementary gaps**: What does one person have mapped that the other doesn't?
- **Potential bridges**: Beliefs that could connect if explored together

Use cases:
- Couples understanding each other better
- Debate prep / steelmanning
- Team alignment
- Friend discovery ("you two should talk")

---

## Data Model (Draft)

```
BeliefNode {
  id: string
  user_id: string
  statement: string              // "Money can't buy happiness"
  confidence: float              // 0.0 - 1.0
  source_type: enum              // experience | reasoning | authority | intuition | inherited
  first_expressed: timestamp
  last_referenced: timestamp
  context: string                // what prompted this belief to surface
  topics: string[]               // derived tags/clusters
}

BeliefRelation {
  id: string
  source_id: string
  target_id: string
  relation_type: enum            // supports | contradicts | assumes | derives_from | relates_to
  strength: float                // how strong is this connection
  discovered_at: timestamp
}

BeliefEvolution {
  id: string
  belief_id: string
  old_confidence: float
  new_confidence: float
  old_statement: string?         // if the wording changed
  new_statement: string?
  timestamp: timestamp
  trigger: string                // what caused the shift
}

UserPersonality {
  user_id: string
  warmth: int                    // 1-5 (accepting the person, while honest about ideas)
  directness: int                // 1-5 (gentle hints to blunt statements)
  playfulness: int               // 1-5
  formality: int                 // 1-5
}
```

---

## Decisions Made

### Interaction Mode: Both Channel + DM
- **DMs**: Deep 1:1 belief mapping conversations
- **Channels**: Casual extraction from group chat, lighter touch
- Different behaviors for each context (DMs more probing, channels more observational)

### Extraction Approach: Active/Hybrid (User-Configurable)
- Default: Bot is **engaging and proactive**—asks follow-up questions, digs for assumptions
- User can dial this down if they prefer passive observation
- Key principle: The bot should ask the *right* questions to extract what's relevant

### Commands (Implemented)
- `/help` — full command reference
- `/setup` — interactive personality selection with previews
- `/style` — fine-tune personality dimensions (1-5 scales)
- `/map` — see belief map with ASCII visualization
- `/explore [topic]` — dive into beliefs about a topic
- `/beliefs` — raw list with IDs, confidence, and importance
- `/belief [id]` — view single belief with connections
- `/core` — show only important beliefs (★★★★+)
- `/tensions` — show beliefs that contradict each other
- `/history [id]` — see how a belief has evolved over time
- `/changes [days]` — see beliefs that changed recently
- `/mark [id] [1-5]` — set belief importance level
- `/confidence [id] [1-5]` — update confidence and record evolution
- `/share [topic] [core_only]` — create shareable belief snapshot
- `/compare @user` — request belief comparison with another user
- `/requests` — see pending comparison requests
- `/bridging` — see bridging score and bridging beliefs
- `/privacy` — view/change belief visibility settings
- `/share-export` — export shareable beliefs as JSON file
- `/compare-file` — compare with someone's exported file
- `/forget [id]` — delete a belief (supports "last")
- `/pause` / `/resume` — toggle belief tracking
- `/export` — download all data as JSON
- `/backup` — download database backup file
- `/clear` — delete everything (with confirmation)

---

## Roadmap

### Vision: Where This Could Go

Kodak started as a simple idea: what if you could see a map of everything you believe?

But the real potential is bigger:

**For individuals:**
- A mirror for your mind that reveals patterns you can't see yourself
- Track how your thinking evolves over years, not just moments
- Export your belief network to your notes app and build on it
- Get better at noticing your own contradictions and blind spots

**For relationships:**
- Actually understand where you and your partner/friend/colleague align and differ
- Find the 3 beliefs causing 90% of your conflicts
- Discover unexpected common ground with people you thought you disagreed with

**For communities:**
- See what a group actually believes (not just who's loudest)
- Find bridging beliefs that unite people across divides
- Identify productive disagreements worth exploring vs. dead-end culture wars
- Build genuine understanding instead of filter bubbles

**For society:**
- What if we could map belief networks at scale?
- What if we could identify bridge-builders and amplify them?
- What if technology helped us understand each other instead of polarize?

This is a long-term vision. Right now, Kodak is a Discord bot for personal reflection. But the foundation—belief extraction, relationship mapping, evolution tracking—could grow into something much more.

---

### Completed (v0.1 - Friends Launch)
- [x] Core bot functionality
- [x] Onboarding flow
- [x] Belief extraction
- [x] Privacy controls (pause, export, clear)
- [x] README and SETUP documentation
- [x] Personality system with anti-sycophancy design
- [x] Rate limiting (configurable)
- [x] Self-hosting guide

### Now (v0.2 - Belief Understanding) ✅ COMPLETE
- [x] **Belief importance marking** — `/mark [id] [1-5]` and `/core` commands
- [x] **Belief evolution tracking** — `/history [id]` and `/changes` commands
- [x] **Better relation display** — Enhanced `/belief [id]` with grouped relations, `/tensions` command
- [x] **Shareable export format** — `/share` with topic and core_only options

### Now (v0.3 - Comparison & Community) ✅ COMPLETE
- [x] **1:1 Belief comparison** — `/compare @user` with request/accept flow
- [x] **Similarity score** — Overall and core similarity percentages
- [x] **Bridging score** — `/bridging` command shows cross-divide agreement
- [x] **Tiered privacy** — `/privacy` command, visibility levels on beliefs
- [x] **File-based comparison** — `/share-export` + `/compare-file` for self-hosters

### Deferred
- [ ] **Consensus finder** — Surface beliefs that bridge different clusters (needs active community)

### Later (v0.4 - Compatibility & Matching)

The comparison features in v0.3 show similarity scores, but they're basic. v0.4 makes matching actually useful:

- [ ] **Compatibility algorithm** — Multi-factor matching that considers:
  - Semantic similarity (do beliefs mean the same thing?)
  - Structural similarity (are they connected the same way?)
  - Importance weighting (agreement on core beliefs matters more)
  - Source type alignment (do you both reason from experience vs. authority?)

- [ ] **"Interesting differences" matching** — Sometimes you don't want someone who agrees with you. You want someone who disagrees in a productive way. This finds people where:
  - You share enough common ground to communicate
  - You differ on something substantive and interesting
  - Neither person holds the belief as core identity (so it's discussable)

- [ ] **Bridge Builder identification** — Some people naturally find common ground across divides. Track and surface:
  - Who has high bridging scores
  - Which beliefs tend to bridge different clusters
  - Reward cross-divide engagement, not just echo-chamber agreement

### Later (v0.5 - Visualization & Export)

Text lists only go so far. Beliefs are a network—they should look like one:

- [ ] **Web-based visualization** — Interactive graph where you can:
  - See clusters of related beliefs
  - Zoom into topics
  - Watch evolution over time (animated)
  - Compare two people's graphs side-by-side

- [ ] **Export to Obsidian/Roam** — Your beliefs as markdown with `[[wiki-links]]`:
  - Each belief becomes a note
  - Relations become links
  - Topics become tags
  - Take your belief network into your second brain

### Later (v0.6 - Community Intelligence)

With enough users, aggregate patterns emerge:

- [ ] **Community aggregates** — "X% of this server believes Y" (anonymized, opt-in)
- [ ] **Consensus finder** — Surface beliefs that bridge different clusters
- [ ] **Pol.is-style clustering** — Visual map of where the community stands
- [ ] **Deliberation support** — Help groups find productive disagreements to discuss

### Backlog / Ideas

Interesting possibilities, not yet prioritized:

- [ ] **Scheduled check-ins** — "Six months ago you said X. Still feel that way?"
- [ ] **Steelmanned opposing views** — "Here's the best case for the other side of your belief"
- [ ] **Belief predictions** — "Based on your other beliefs, you might also think..."
- [ ] **Voice channel support** — Extract beliefs from voice conversations
- [ ] **Multi-platform** — Telegram, Slack, web interface
- [ ] **API for developers** — Let others build on belief extraction

### Polish & UX Improvements

Small things that make the experience better:

- [ ] **Better `/map` visualization** — The ASCII art could be more beautiful/readable
- [ ] **Smoother onboarding** — Fewer steps, less friction
- [ ] **`/undo` command** — Restore the last forgotten belief (regret happens)
- [ ] **Topic suggestions** — When `/explore` finds nothing, suggest similar topics
- [ ] **Richer error messages** — More personality, more helpful
- [ ] **Conversation memory** — Reference earlier parts of the conversation naturally
- [ ] **Belief merging** — Combine two beliefs that turned out to be the same

### Developer Experience

For maintainability and contribution:

- [ ] **Test suite** — Unit tests for extraction, database, commands
- [ ] **Logging** — See what's happening in production (Railway)
- [ ] **CI/CD pipeline** — Auto-run tests on PR
- [ ] **Contributing guide** — How to add features, code style, etc.
- [ ] **API documentation** — For the database and extraction functions

### Technical Debt (from v0.3 audit)

Known issues to fix:

- [ ] **Belief deduplication** — Currently only checks last 30 beliefs; users with 100+ may get duplicates
- [ ] **Auto-detect contradictions** — Trigger belief evolution when new statement contradicts existing belief
- [ ] **In-place belief editing** — Allow updating a belief statement without delete/re-add
- [ ] **Chunked summarization** — Handle users with 200+ beliefs without exceeding context limits
- [ ] **Comparison race condition** — Prevent double-execution if two users accept simultaneously
- [ ] **Richer comparison request DMs** — Explain what Kodak is to recipients who may not know the bot

---

## Expert Research: Belief Comparison & Compatibility

### Sources Consulted

**Compatibility Algorithms**
- Helen Fisher's Fisher Temperament Inventory (Match.com) — personality types based on neurochemistry
- OkCupid's weighted question system — importance weighting (Irrelevant=0 to Mandatory=250x)

**Network Comparison**
- Graph similarity methods: feature-based, spectral, graph edit distance
- SimGNN neural network approach for scalable comparison
- Sentence embeddings for semantic similarity of belief statements

**Collective Intelligence**
- [Pol.is](https://compdemocracy.org/polis/) — computational democracy, finds bridging consensus
- [Deliberative Polling](https://deliberation.stanford.edu/) — James Fishkin's structured deliberation
- [Twitter Community Notes](https://arxiv.org/abs/2210.15723) — bridging-based ranking algorithm

**Filter Bubbles & Bridging**
- Eli Pariser's filter bubble research
- Key finding: Simply exposing opposing views can increase polarization (backfire effect)
- Better approach: Find bridging beliefs valued across divides

**Privacy**
- Differential privacy for aggregate statistics
- Tiered disclosure models for belief sharing

### Key Design Principles

1. **Bridging > Exposure**: Don't just show opposing views; help users find common ground first

2. **Importance weighting matters**: Core beliefs should count more than peripheral ones (OkCupid's 250x weight for "mandatory")

3. **Diversity of appreciation = quality**: Content/beliefs are valuable when appreciated across divides (Community Notes insight)

4. **Privacy enables honesty**: Tiered disclosure lets users share authentically without fear

5. **Bounded confidence is real**: People only engage within their comfort zone — design for gradual bridging, not shock exposure

6. **Epistemic humility markers**: Track and reward openness to revision, not just belief consistency

### Proposed Algorithms

**Similarity Score**
```
Overall_Similarity =
    w1 * Semantic_Similarity +      // Do beliefs mean similar things?
    w2 * Structural_Similarity +    // Are they connected similarly?
    w3 * Importance_Weighted_Match  // Do you agree on what matters?
```

**Bridging Score**
- Track when users agree with beliefs typically held by opposing clusters
- Higher bridging score = more valuable for community discussions
- Reward engagement across divides, not just within echo chambers

**Tiered Privacy Model**
| Level | Visibility |
|-------|------------|
| Public | All server members |
| Connections | Mutual follows only |
| Consent | Both parties opt-in |
| Hidden | Factors into similarity but never shown |

---

## Open Questions

- How does the bot decide something is a "belief" vs just a statement?
- How granular? "I like coffee" vs "Small pleasures matter" vs "Hedonism is valid"
- What visualization approach for the belief map?
- How to handle backfire effect when showing belief differences?
- What's the right balance of similarity vs "interesting differences" in matching?

---

## Expert UX Audit (Pre-Build Review)

### Sources Consulted

**Conversational Design**
- [Erika Hall - Conversational Design](https://abookapart.com/products/conversational-design) — "First, imagine the conversation. Then use it to guide the design."
- [Conversation Design Institute](https://www.conversationdesigninstitute.com/topics/conversation-design) — Combining UX, psychology, and linguistics
- [Mind the Product - AI Chatbot UX](https://www.mindtheproduct.com/deep-dive-ux-best-practices-for-ai-chatbots/) — Nine best practices

**Tools for Thought**
- [Maggie Appleton - Squish Meets Structure](https://maggieappleton.com/squish-structure) — The chatbot interface is "far too open-ended"
- [Maggie Appleton - Tools for Thought](https://maggieappleton.com/tools-for-thought) — Cultural practices, not just computational objects

**Privacy & Trust**
- [Smashing Magazine - Privacy UX Framework](https://www.smashingmagazine.com/2019/04/privacy-ux-aware-design-framework/)
- [Privacy-First UX & Design Systems](https://medium.com/@harsh.mudgal_27075/privacy-first-ux-design-systems-for-trust-9f727f69a050)

**Onboarding**
- [NN/g - New AI Users Need Support](https://www.nngroup.com/articles/new-AI-users-onboarding/)
- [Stream - Chat UX Best Practices](https://getstream.io/blog/chat-ux/)

**Discord-Specific**
- [Netguru - Chatbot UX Tips](https://www.netguru.com/blog/chatbot-ux-tips)
- [Dive Club - The Discord Bot Era](https://www.dive.club/ideas/the-discord-bot-era-of-design)

---

### Issue #1: No Onboarding Experience

**The Problem (Erika Hall, NN/g)**

Currently, new users get no introduction. They either figure it out or bounce. Hall's principle: "The ideal interface is one that's not noticeable at all." But that requires the user to understand what's happening.

NN/g research: "New users need support with generative AI tools... onboarding tutorials should be brief yet informative, addressing users' key questions and stating the tool's purpose."

**Current State**
- User DMs bot → bot just... responds
- No explanation of what Kodak does
- No consent for belief tracking
- No personality selection prompt

**Recommendation**

Add first-message onboarding flow:

```
👋 Hey! I'm Kodak.

I'm here to have great conversations with you—and along the way,
I'll help you build a map of what you believe and why.

Think of it like a mirror for your mind. Everything stays private
to you, and you can delete anything anytime.

Before we start, how would you like me to show up?

[The Philosopher] [The Best Friend] [The Trickster] [Skip for now]
```

Use Discord buttons for selection. Then:

```
Great choice. One more thing—how active should I be?

• Active: I'll ask follow-up questions to understand you better
• Chill: I'll mostly listen and let things emerge naturally

[Active] [Chill]
```

---

### Issue #2: Belief Extraction Feels Invisible (Potentially Creepy)

**The Problem (Privacy UX Research)**

80% of users are more willing to share data when they understand how it benefits them. Currently, beliefs are extracted silently—users have no idea it's happening.

Maggie Appleton on Elicit: "There are many fascinating challenges around trust, reliability, truthfulness, and transparency."

**Current State**
- Beliefs extracted in background
- User never sees what was captured
- No opt-in, no visibility, no control in the moment

**Recommendation**

Option A: **Visible extraction with confirmation**
After certain messages, bot could say:
```
(I noticed something that might be a core belief: "Hard work is the
main driver of success." Want me to add that to your map? 👍/👎)
```

Option B: **Periodic summary**
Every N messages or at session end:
```
Quick recap—I picked up a few things from our chat:
• You value authenticity over politeness
• You're skeptical of institutions but trust individuals
• Childhood experiences shaped your view on [X]

Anything I got wrong? Just say "forget [number]" to remove.
```

Option C: **On-demand only (passive mode)**
Only extract when user explicitly asks: "What did you learn about me?"

**For MVP**: Start with Option B (periodic summary). Less intrusive, builds trust, gives user agency.

---

### Issue #3: The "Open-Ended Chatbox" Problem

**The Problem (Maggie Appleton)**

"The chatbot as an interface is far too open-ended and gives too much onus to the user to figure out what they should be doing."

User opens DM, sees empty chat. Now what? The lack of structure creates anxiety.

**Current State**
- No conversation starters
- No prompts or suggestions
- User must initiate everything

**Recommendation**

Add **conversation starters** that appear for new/returning users:

```
What's on your mind today?

Or try one of these:
💭 "Something I've been thinking about lately..."
🔥 "An opinion I hold that might be controversial..."
❓ "A question I've never been able to answer..."
🔄 "Something I used to believe but changed my mind on..."
```

These double as belief extraction hooks—they naturally surface beliefs.

For returning users:
```
Welcome back! Last time we talked about [topic].

Want to continue that, or explore something new?
```

---

### Issue #4: Commands Are Discoverable but Not Inviting

**The Problem (Chatbot UX Best Practices)**

"Using the chatbot shouldn't feel like operating a plane." Slash commands are powerful but feel technical.

**Current State**
- `/setup`, `/map`, `/explore`, `/beliefs`, `/forget`, `/style`
- All functional, none delightful
- No natural language alternatives

**Recommendation**

Support **natural language** for common actions:
- "Show me my map" → triggers map display
- "What do I believe about work?" → triggers explore
- "Forget that last thing" → triggers forget flow
- "Make yourself more playful" → adjusts personality

Also: Better command descriptions and examples in `/help` (which we don't have yet).

Add `/help` command:
```
**Kodak Commands**

🗺️ /map — See your belief map summarized
🔍 /explore [topic] — Dive into what you believe about something
📝 /beliefs — Raw list of everything I've captured
🗑️ /forget [id] — Remove a belief
🎭 /setup — Choose a personality preset
🎚️ /style — Fine-tune personality dimensions

Or just talk to me naturally—I'll figure out what you mean.
```

---

### Issue #5: Error Handling & Graceful Failure

**The Problem (Conversation Design Institute)**

"The capacity to fail elegantly and provide routes to repair the conversation is essential."

**Current State**
- If extraction fails, user never knows
- If API errors, user gets raw error message
- No fallback for confused states

**Recommendation**

Handle failures conversationally:

```python
# Instead of:
return f"Sorry, I encountered an error: {e}"

# Try:
return "Hmm, my mind went blank for a second there. Could you say that again?"
```

For extraction failures—just skip silently (no user-facing impact).

For API rate limits:
```
I need a quick breather—lots of good conversations today.
Try again in a minute?
```

---

### Issue #6: The Map Is Text-Only

**The Problem (Maggie Appleton on Visualization)**

Appleton's work emphasizes visual explanations. A text summary of beliefs is functional but not delightful or explorable.

**Current State**
- `/map` returns a paragraph summary
- No visual representation
- Can't "wander" the map

**Recommendation (Future)**

For MVP: Text is fine. But design for future visualization:

1. **ASCII/Emoji cluster view** (Discord-native):
```
Your Belief Landscape

🏛️ WORK & SUCCESS ━━━━━━━━━━━━━━
   ├─ Hard work drives outcomes
   ├─ Talent is overrated
   └─ Burnout is a real risk ⚡ (tension)

❤️ RELATIONSHIPS ━━━━━━━━━━━━━━━
   ├─ Honesty > politeness
   └─ Trust is earned slowly

🌍 SOCIETY ━━━━━━━━━━━━━━━━━━━━━
   ├─ Institutions are failing
   └─ Individual action matters
```

2. **Web-based visualization** (future):
Link out to a web view with interactive graph.

3. **Export to Obsidian/Roam** (future):
Let users get their belief graph as markdown with `[[links]]`.

---

### Issue #7: No "Why" Behind Belief Capture

**The Problem (Tetlock, Galef)**

We track beliefs but not the reasoning chains. "Why do you believe that?" is as important as "what do you believe?"

**Current State**
- `source_type` captures rough origin (experience, authority, etc.)
- No actual reasoning captured
- No "because" connections

**Recommendation**

Enhance extraction to capture reasoning when present:

```
User: "I think remote work is better because I'm more productive at home
and I hate commuting."

Extracted:
- Belief: "Remote work is better than office work"
- Supporting reasons:
  - "I'm more productive at home"
  - "Commuting is unpleasant"
- Source: experience
```

This enriches the graph significantly.

---

### Issue #8: Privacy Controls Are Minimal

**The Problem (Privacy UX Research)**

"Enable granular privacy controls that allow users to customize data sharing preferences." Users need to feel in control.

**Current State**
- `/forget` exists but requires knowing IDs
- No bulk delete
- No export
- No pause/resume tracking
- No "delete everything"

**Recommendation**

Add privacy commands:
- `/pause` — Stop tracking beliefs (but keep chatting)
- `/resume` — Resume tracking
- `/export` — Get all your data as JSON
- `/clear` — Delete everything (with confirmation)
- `/forget last` — Forget most recent belief
- `/forget all [topic]` — Forget everything about a topic

Also: Add privacy note to onboarding:
```
🔒 Your beliefs stay private to you. I never share them.
You can delete anything with /forget, or everything with /clear.
```

---

### Issue #9: Personality System Lacks Demonstration

**The Problem (Chatbot Personality Design)**

"Building a rich and detailed personality makes your chatbot more relatable." But users can't preview personalities before choosing.

**Current State**
- Presets have one-line descriptions
- No sample dialogue
- Can't "try before you buy"

**Recommendation**

Show personality in action during setup:

```
**The Philosopher** — Thoughtful and probing

Example:
You: "I think people are basically good"
Kodak: "That's a hopeful foundation. What experiences have
shaped that view? And does it hold even for people who've
done terrible things?"

[Choose this one] [See another]
```

Or: Let them chat briefly with each personality before committing.

---

### Summary: Priority Fixes Before Launch

| Priority | Issue | Fix | Status |
|----------|-------|-----|--------|
| 🔴 High | No onboarding | Add first-message welcome flow | ✅ Done |
| 🔴 High | Invisible extraction | Add periodic "here's what I learned" summaries | ✅ Done |
| 🟡 Medium | No conversation starters | Add prompt suggestions for new/returning users | ✅ Done |
| 🟡 Medium | No /help | Add help command | ✅ Done |
| 🟡 Medium | Poor error messages | Make failures conversational | ✅ Done |
| 🟢 Lower | Text-only map | Design ASCII cluster view | ✅ Done |
| 🟢 Lower | Minimal privacy controls | Add /pause, /export, /clear | ✅ Done |
| 🟢 Lower | No personality preview | Show example dialogues | ✅ Done |

---

---

## Implementation Status

### Implemented Features

**Onboarding Flow**
- New users see welcome embed explaining Kodak's purpose
- Privacy notice in footer ("Your beliefs stay private")
- Personality selection via dropdown with 5 presets
- Each preset shows example dialogue before committing
- Extraction mode selection (Active/Chill buttons)
- Conversation starters shown after setup completes

**Belief Visibility**
- Periodic "Quick snapshot" summaries every 8 messages
- Shows 3 most recent beliefs captured
- Includes prompt to use `/forget` if anything is wrong
- Users can also ask "show me my map" naturally

**Commands**
- `/help` — Full command reference with categories
- `/map` — ASCII-style visualization by topic with confidence bars
- `/explore [topic]` — Deep dive with topic suggestions if none found
- `/beliefs` — Raw list with importance (★) and confidence (●) indicators
- `/belief [id]` — View single belief with its connections
- `/core` — Show only important beliefs (★★★★+)
- `/tensions` — Show beliefs that contradict each other
- `/history [id]` — See how a belief has evolved over time
- `/changes [days]` — See beliefs that changed recently
- `/mark [id] [1-5]` — Set belief importance level
- `/confidence [id] [1-5]` — Update confidence and record evolution
- `/share [topic] [core_only]` — Create shareable belief snapshot with embed and copy-paste formats
- `/compare @user` — Request belief comparison with another user
- `/requests` — See pending comparison requests
- `/bridging` — See bridging score and bridging beliefs
- `/privacy` — View/change belief visibility settings
- `/share-export` — Export shareable beliefs as JSON file
- `/compare-file` — Compare with someone's exported file
- `/forget [id]` — Supports "last" keyword for most recent
- `/setup` — Interactive personality selection with previews
- `/style` — Visual bar display for current settings
- `/pause` / `/resume` — Toggle belief tracking
- `/export` — Download all data as JSON file
- `/backup` — Download database backup file
- `/clear` — Delete everything with confirmation modal

**Natural Language Support**
- "show me my map" / "what do I believe" → map display
- "pause tracking" / "stop tracking" → pause extraction
- "resume tracking" / "start tracking" → resume extraction

**Privacy Features**
- Tracking can be paused while still chatting
- Full data export (GDPR-style)
- Complete data deletion with confirmation
- All slash command responses are ephemeral (private)

**Error Handling**
- Rate limits: "I need a quick breather..."
- Connection issues: "I lost my train of thought..."
- Generic errors: "My mind went blank..."

---

### Erika Hall's Conversational Maxims Applied

From *Conversational Design*, the qualities of good conversation:

| Maxim | Current State | Recommendation |
|-------|--------------|----------------|
| **Right quantity** | ⚠️ No guidance on message length | Add to prompt: keep responses concise |
| **Truthful** | ✅ Bot doesn't make false claims | Maintain |
| **Relevant** | ✅ Stays on topic | Maintain |
| **Brief & clear** | ⚠️ Summaries can be long | Chunk long outputs |
| **Orderly** | ✅ Logical flow | Maintain |
| **Unambiguous** | ⚠️ Commands not always clear | Add natural language fallbacks |
| **Polite** | ✅ Tone is respectful | Maintain |
| **Error-tolerant** | ❌ Raw errors shown | Add graceful failure messages |
