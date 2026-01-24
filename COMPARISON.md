# Kodak: Belief Comparison & Compatibility System

> Detailed specification for belief network comparison, compatibility scoring, and community features.

## Vision

People have rich inner worlds of beliefs, values, and assumptions — but rarely get to see them clearly or compare them meaningfully with others. Kodak aims to:

1. **Help individuals understand their own belief networks** — not just what they believe, but how beliefs connect, which ones are core vs. peripheral, and how they evolve
2. **Enable meaningful comparison between people** — finding genuine common ground, understanding real differences, and identifying productive areas for dialogue
3. **Build communities around belief exploration** — where differences are interesting rather than threatening, and where bridging divides is rewarded

This is NOT about:
- Judging whose beliefs are "right"
- Creating filter bubbles of agreement
- Reducing people to compatibility percentages
- Exposing private thoughts without consent

---

## Part 1: Belief Understanding (Foundation)

Before users can meaningfully compare beliefs, they need to understand their own.

### 1.1 Belief Importance Marking

**Why this matters:**
Not all beliefs are equal. "I prefer tea over coffee" and "Human life has inherent value" are both beliefs, but they matter differently. Without importance marking:
- Comparisons are misleading (matching on trivia, missing core values)
- Users can't distinguish their foundations from their opinions
- The belief map is flat when it should have depth

**User Story:**
> As a user, I want to mark how important each belief is to me, so that my belief map reflects what actually matters to me and comparisons focus on what's core.

**UX Flow:**

```
User: /mark 7 5
Kodak: Got it. Marked as core belief (5/5):
       "Hard work is more important than talent"

       Your importance levels:
       ★★★★★ Core (5): Foundational to who you are
       ★★★★☆ High (4): Very important, rarely changes
       ★★★☆☆ Medium (3): Significant but flexible
       ★★☆☆☆ Low (2): Opinions you hold loosely
       ★☆☆☆☆ Peripheral (1): Passing thoughts, trivia
```

Alternative: Mark during extraction
```
Kodak: I noticed a belief: "Success requires sacrifice"
       How important is this to you?
       [★ Peripheral] [★★★ Medium] [★★★★★ Core]
```

**Commands:**
- `/mark [belief_id] [1-5]` — Set importance
- `/core` — Show only beliefs marked 4-5
- `/beliefs` — Now shows importance stars alongside confidence dots

**Data Model Changes:**
```
BeliefNode {
  ...existing fields...
  importance: int              // 1-5, default 3
  importance_set_at: timestamp // When user explicitly set it
  importance_auto: bool        // Was this inferred or explicitly set?
}
```

**Auto-inference (optional):**
Claude could suggest importance based on:
- Language intensity ("I fundamentally believe" → high)
- How often it's referenced
- Whether it supports/underlies other beliefs
- Emotional weight in conversation

User always has final say.

**Edge Cases:**
- User never marks anything → default all to 3, prompt occasionally
- User marks everything as 5 → gentle prompt that not everything can be core
- Belief importance changes → track in evolution history

---

### 1.2 Belief Evolution Tracking

**Why this matters:**
Beliefs aren't static. Tracking how they change reveals:
- Growth and learning patterns
- Triggers that cause belief shifts
- Stability vs. volatility of worldview
- Whether confidence calibrates over time

**User Story:**
> As a user, I want to see how my beliefs have changed over time, so I can understand my own intellectual journey and notice patterns in how I update my views.

**UX Flow:**

```
User: /history 7
Kodak: Evolution of belief #7:
       "Hard work is more important than talent"

       📅 Jan 15 — First expressed
          Confidence: 80% | Source: experience
          Context: Discussing career success

       📅 Jan 22 — Confidence decreased
          Confidence: 80% → 60%
          Trigger: "Read about role of luck in success"

       📅 Jan 28 — Wording refined
          "Hard work matters more than raw talent, but luck plays a role too"
          Confidence: 70%

       Pattern: This belief has moderated over time. You seem
       responsive to new evidence on this topic.
```

**Commands:**
- `/history [belief_id]` — Show evolution of specific belief
- `/changes` — Show all beliefs that changed in last N days
- `/stable` — Show beliefs that haven't changed (your bedrock)
- `/volatile` — Show beliefs that change frequently

**Data Model:**
Already have `BeliefEvolution` table. Need to:
- Actually populate it when beliefs change
- Detect "same belief, different wording" (semantic similarity)
- Track triggers better (what message caused the shift?)

**Detection Logic:**
When new belief extracted, check against existing:
1. High semantic similarity (>0.85) to existing belief?
   - Same belief, possibly evolved
   - Compare confidence, wording
   - Log evolution if changed
2. Contradicts existing belief?
   - Log as potential belief shift
   - Ask user: "You used to say X, now Y. Has your view changed?"

**Patterns to Surface:**
- "Bedrock beliefs" — never change, high importance
- "Evolving edges" — frequently refined, learning areas
- "Confidence calibration" — do you become more/less certain over time?
- "Trigger patterns" — what causes you to update? (evidence, authority, experience)

---

### 1.3 Relation Display Enhancement

**Why this matters:**
Beliefs don't exist in isolation. Understanding connections reveals:
- Which beliefs are foundational (many things depend on them)
- Which beliefs are derived (would fall if foundations change)
- Internal tensions and contradictions
- Clusters of related thinking

**Current state:** We store relations but don't display them well.

**User Story:**
> As a user, I want to see how my beliefs connect to each other, so I can understand my reasoning chains and notice where I might have contradictions.

**UX Flow:**

```
User: /belief 7
Kodak: Belief #7: "Hard work is more important than talent"
       Confidence: [●●●●○] 70% | Importance: ★★★★★
       Source: experience | First expressed: Jan 15

       ┌─ FOUNDATIONS (this belief assumes):
       │  #12 "People have control over their outcomes" [●●●○○]
       │  #18 "Effort is a choice" [●●●●○]
       │
       ├─ SUPPORTS:
       │  #23 "Success is earned, not given" [●●●●○]
       │  #31 "I deserve what I've achieved" [●●●○○]
       │
       ├─ TENSIONS:
       │  ⚡ #28 "Privilege shapes opportunity" [●●●○○]
       │     You hold both, but they create tension.
       │
       └─ RELATED TOPICS: career, success, fairness

       [View foundations] [View full tree] [Resolve tension]
```

**Commands:**
- `/belief [id]` — Enhanced to show connections
- `/tree [id]` — Show full belief tree (what it supports, what supports it)
- `/tensions` — Show all contradictions/tensions in your map
- `/foundations` — Show beliefs that many others depend on

**Visual Representation (ASCII):**
```
User: /tree 7
Kodak: Belief tree for #7:

                    ┌─ #23 Success is earned
       #7 Hard work ┼─ #31 I deserve my achievements
        matters     └─ #45 Laziness is moral failure
            │
            ▼ assumes
       ┌────┴────┐
       #12       #18
    Control    Effort is
    outcomes    choice
```

---

### 1.4 Shareable Export Format

**Why this matters:**
Before building comparison features, let users share manually in Discord. This:
- Tests whether people actually want to share
- Reveals what format is useful
- Builds community engagement without complex features
- Provides data on what comparisons people naturally make

**User Story:**
> As a user, I want to share my belief map (or part of it) in a Discord channel, so I can discuss it with others and see how my beliefs compare to theirs.

**UX Flow:**

```
User: /share topic:career
Kodak: Here's your shareable belief snapshot:

       ┌──────────────────────────────────────┐
       │  🧠 Eric's Beliefs: CAREER           │
       ├──────────────────────────────────────┤
       │  ★★★★★ [●●●●○] Hard work > talent    │
       │  ★★★★☆ [●●●○○] Passion overrated     │
       │  ★★★☆☆ [●●●●○] Remote work is better │
       │  ★★☆☆☆ [●●○○○] Titles don't matter   │
       └──────────────────────────────────────┘

       [Post to #show-your-map] [Copy as text] [Cancel]
```

**Commands:**
- `/share` — Share full map summary
- `/share topic:[topic]` — Share beliefs on specific topic
- `/share belief:[id]` — Share single belief with context
- `/share core` — Share only ★★★★+ importance beliefs

**Format Options:**
1. **Embed** — Discord rich embed, looks nice
2. **Text block** — Copyable plain text for any channel
3. **Anonymous** — Same content, no username attached

**Privacy Controls:**
- Only shares beliefs not marked "hidden"
- User explicitly chooses to share each time
- Can set default share visibility in settings

---

## Part 2: Belief Comparison (Core Feature)

### 2.1 One-on-One Comparison

**Why this matters:**
The core value proposition — see how your beliefs relate to someone else's. Useful for:
- Couples understanding each other
- Friends exploring differences
- Debate prep (understanding the other side)
- Finding unexpected common ground

**User Story:**
> As a user, I want to compare my belief map with a friend's, so I can understand where we align, where we differ, and what we might learn from each other.

**UX Flow:**

```
User: /compare @Alex
Kodak: 📤 Sent comparison request to Alex.
       They'll need to accept to see results.
       (You can only see beliefs they've marked as shareable)
```

```
Alex receives DM:
Kodak: Eric wants to compare belief maps with you.

       This will show:
       • Where you agree
       • Where you differ
       • Your similarity score

       Only beliefs you've marked "shareable" will be visible.

       [Accept] [Decline] [See my privacy settings]
```

```
Both users see (in DM with Kodak):

Kodak: 🔄 Belief Comparison: Eric ↔ Alex

       ═══════════════════════════════════════
       OVERALL SIMILARITY: 67%
       ├─ Core beliefs (★★★★+): 72% aligned
       ├─ All beliefs: 61% aligned
       └─ Bridging potential: High
       ═══════════════════════════════════════

       🤝 STRONG AGREEMENT (you both believe):
       ┌─────────────────────────────────────┐
       │ "Honesty matters more than comfort" │
       │  Eric: [●●●●○] ★★★★★                │
       │  Alex: [●●●●●] ★★★★★                │
       │  → Core shared value                │
       ├─────────────────────────────────────┤
       │ "Remote work is more productive"    │
       │  Eric: [●●●●○] ★★★☆☆                │
       │  Alex: [●●●○○] ★★★★☆                │
       └─────────────────────────────────────┘

       ⚡ INTERESTING DIFFERENCES:
       ┌─────────────────────────────────────┐
       │ On "meritocracy":                   │
       │  Eric: "Hard work determines success│
       │  Alex: "Luck matters more than we   │
       │         admit"                      │
       │  → Different foundations, worth     │
       │    exploring                        │
       └─────────────────────────────────────┘

       🌉 BRIDGING OPPORTUNITIES:
       You disagree on merit vs luck, but both value
       honesty and self-reflection. Start there?

       [Explore differences] [Share to channel] [End comparison]
```

**Commands:**
- `/compare @user` — Request comparison
- `/compare accept` — Accept pending request
- `/compare explore [topic]` — Dive into specific area of comparison

**Algorithm Details:**

```
def calculate_similarity(user_a, user_b):
    # Get shareable beliefs for both users
    beliefs_a = get_shareable_beliefs(user_a)
    beliefs_b = get_shareable_beliefs(user_b)

    # Find semantic matches (same topic/concept)
    matched_pairs = find_semantic_matches(beliefs_a, beliefs_b)

    # For each matched pair, calculate agreement
    agreements = []
    for belief_a, belief_b in matched_pairs:
        # Semantic similarity of the actual statements
        semantic_sim = cosine_similarity(
            embed(belief_a.statement),
            embed(belief_b.statement)
        )

        # Are they saying similar things? (>0.7 = agreement)
        # Are they saying opposite things? (<0.3 = disagreement)

        # Weight by importance (both users' importance matters)
        weight = (belief_a.importance + belief_b.importance) / 2

        agreements.append({
            'pair': (belief_a, belief_b),
            'similarity': semantic_sim,
            'weight': weight,
            'type': classify_agreement(semantic_sim)
        })

    # Calculate weighted similarity score
    total_weight = sum(a['weight'] for a in agreements)
    weighted_sim = sum(
        a['similarity'] * a['weight']
        for a in agreements
    ) / total_weight

    # Calculate core belief similarity (importance >= 4)
    core_agreements = [a for a in agreements if a['weight'] >= 4]
    core_sim = calculate_subset_similarity(core_agreements)

    return {
        'overall': weighted_sim,
        'core': core_sim,
        'agreements': [a for a in agreements if a['type'] == 'agree'],
        'differences': [a for a in agreements if a['type'] == 'disagree'],
        'unique_a': find_unmatched(beliefs_a, matched_pairs),
        'unique_b': find_unmatched(beliefs_b, matched_pairs)
    }
```

**Privacy Considerations:**
- Both users must opt-in
- Only shareable beliefs included
- Can set per-belief visibility
- Results only shown in DMs, not public
- No persistent storage of comparison (computed on-demand)

---

### 2.2 Similarity Score Components

**Why multiple components matter:**
A single percentage is reductive. Breaking it down reveals:
- You might match on conclusions but differ on reasoning
- Core values might align even if opinions differ
- Surface agreement might mask deep differences

**Score Components:**

| Component | What it measures | Why it matters |
|-----------|------------------|----------------|
| **Core Alignment** | Agreement on ★★★★+ beliefs | Foundational compatibility |
| **Surface Alignment** | Agreement on all beliefs | Day-to-day compatibility |
| **Reasoning Match** | Similar belief structures/connections | Think alike vs. agree accidentally |
| **Epistemic Style** | Confidence calibration, update patterns | How you think, not what |
| **Bridging Potential** | Productive difference areas | Learning opportunity |

**Display:**
```
COMPATIBILITY BREAKDOWN:

Core Values:      [████████░░] 82%
  You share fundamental beliefs about honesty, growth, relationships.

Surface Opinions: [██████░░░░] 58%
  You differ on many specific topics, but cores align.

Thinking Style:   [███████░░░] 71%
  Similar confidence patterns. Both update on evidence.

Bridging Score:   [████████░░] 78%
  High potential for productive dialogue on differences.

INTERPRETATION:
Strong foundation with interesting differences.
You're likely to have good debates that go somewhere.
```

---

### 2.3 Bridging Score

**Why this matters:**
Inspired by Twitter Community Notes — the most valuable people aren't those who agree with their tribe, but those who can appreciate ideas across divides.

**What it measures:**
- How often you agree with beliefs typically held by people who disagree with you
- Your ability to find value in opposing perspectives
- Whether you engage productively with difference

**Calculation:**

```
def calculate_bridging_score(user, community_clusters):
    # Identify which "cluster" user primarily belongs to
    # (based on their belief patterns)
    user_cluster = identify_cluster(user)

    # Find beliefs where user agrees with OTHER clusters
    bridging_beliefs = []
    for belief in user.beliefs:
        # What clusters typically hold this belief?
        belief_clusters = get_clusters_holding_belief(belief)

        # If user agrees with belief from "opposing" cluster
        if user_cluster not in belief_clusters:
            bridging_beliefs.append(belief)

    # Score based on frequency and importance of bridging
    score = len(bridging_beliefs) / len(user.beliefs)
    weighted_score = sum(b.importance for b in bridging_beliefs) / sum(b.importance for b in user.beliefs)

    return weighted_score
```

**Display:**
```
YOUR BRIDGING PROFILE:

Bridging Score: [███████░░░] 68%

You often find common ground across different viewpoints.

BRIDGING BELIEFS (you agree with "the other side" on):
• "Economic growth isn't everything"
  (Usually held by: progressives. You lean: libertarian)
• "Personal responsibility matters"
  (Usually held by: conservatives. You lean: progressive)

This makes you valuable for cross-divide conversations.
```

**Community Value:**
High bridging scores could:
- Get "Bridge Builder" role/badge
- Be suggested for moderation roles
- Be matched with people seeking productive disagreement

---

## Part 3: Community Features

### 3.1 Tiered Privacy System

**Why this matters:**
People won't share beliefs honestly if they fear exposure. Privacy must be granular and user-controlled.

**Privacy Levels:**

| Level | Who sees | Use case |
|-------|----------|----------|
| **Public** | Anyone on server | Beliefs you're proud of, want to discuss |
| **Shareable** | Only in comparisons you initiate | Default for most beliefs |
| **Private** | Only you | Sensitive, forming, or personal |
| **Hidden** | Only you, excluded from comparisons | Things you don't want to affect matching |

**UX Flow:**

```
User: /privacy
Kodak: Your belief privacy settings:

       Default for new beliefs: [Shareable ▼]

       PUBLIC (visible to server):     3 beliefs
       SHAREABLE (comparison only):   24 beliefs
       PRIVATE (only you):             8 beliefs
       HIDDEN (excluded):              2 beliefs

       [Set defaults] [Manage individual beliefs]
```

```
User: /privacy set 7 private
Kodak: Belief #7 is now private.
       "Hard work is more important than talent"

       This belief:
       ✗ Won't appear in comparisons
       ✗ Won't be shared when you use /share
       ✓ Still visible to you in /map and /beliefs
```

**Per-Topic Privacy:**
```
User: /privacy topic:politics private
Kodak: All 6 beliefs tagged "politics" are now private.
       New beliefs about politics will default to private.
```

---

### 3.2 Consensus Finder

**Why this matters:**
Inspired by Pol.is — instead of highlighting divisions, surface what brings people together.

**How it works:**
1. Collect beliefs from community members (those marked public/shareable)
2. Find beliefs that appear across different "clusters" of users
3. Surface these as bridging topics for discussion

**UX Flow:**

```
User: /consensus
Kodak: 🌉 BRIDGING BELIEFS IN THIS SERVER

       These beliefs are shared across different viewpoints:

       94% agree: "Honesty in relationships matters most"
         └─ Shared by: career-focused, family-focused,
            independent, traditional

       87% agree: "Learning from failure is valuable"
         └─ Shared by: risk-takers, cautious planners,
            entrepreneurs, employees

       82% agree: "Mental health should be prioritized"
         └─ Shared by: all clusters

       [Discuss in #common-ground] [See all consensus beliefs]
```

**Algorithm:**
```
def find_consensus_beliefs(server_members):
    # Cluster users by belief patterns
    clusters = cluster_users(server_members)

    # Find beliefs held across multiple clusters
    consensus = []
    for belief_pattern in all_belief_patterns:
        clusters_holding = [c for c in clusters if cluster_holds_belief(c, belief_pattern)]

        if len(clusters_holding) >= len(clusters) * 0.7:  # 70%+ of clusters
            consensus.append({
                'belief': belief_pattern,
                'clusters': clusters_holding,
                'agreement_rate': calculate_agreement_rate(belief_pattern, server_members)
            })

    return sorted(consensus, key=lambda x: x['agreement_rate'], reverse=True)
```

---

### 3.3 Community Aggregates (Anonymous Statistics)

**Why this matters:**
Let users see how their beliefs compare to the community without exposing individuals.

**UX Flow:**

```
User: /community topic:career
Kodak: 📊 SERVER BELIEFS: CAREER

       Most common beliefs:
       ├─ 78% believe work-life balance is essential
       ├─ 65% believe passion is overrated
       ├─ 61% believe remote work is more productive
       └─ 45% believe job titles matter

       Your position:
       ├─ ✓ You agree with 78% on work-life balance
       ├─ ✓ You agree with 65% on passion
       ├─ ✓ You agree with 61% on remote work
       └─ ✗ You disagree with 45% on titles

       You align with server majority on 3/4 career beliefs.
```

**Privacy Protection:**
- Minimum 5 users must hold a belief before showing aggregate
- No individual attribution ever
- Percentages rounded to prevent inference
- Users can exclude themselves from aggregates

---

### 3.4 "Interesting Differences" Matching

**Why this matters:**
Echo chambers form when we only connect with similar people. Proactively suggest productive differences.

**How it works:**
Match users who:
1. Share core values (foundation of trust)
2. Differ on specific beliefs (something to explore)
3. Have high bridging scores (can handle disagreement)
4. Have complementary knowledge gaps

**UX Flow:**

```
Kodak DMs user:
       💡 INTERESTING MATCH SUGGESTION

       You and Alex share core values around honesty
       and personal growth, but differ on:

       • Role of luck vs effort in success
       • Whether institutions can be reformed
       • Value of tradition

       Alex has a high bridging score (74%) and you
       both update beliefs based on evidence.

       This could be a productive conversation.

       [Request comparison] [Not interested] [Don't suggest Alex again]
```

**Matching Algorithm:**
```
def find_interesting_match(user):
    candidates = get_all_users_with_consent()

    matches = []
    for candidate in candidates:
        if candidate == user:
            continue

        # Must share core values
        core_sim = calculate_core_similarity(user, candidate)
        if core_sim < 0.6:  # Need 60%+ core alignment
            continue

        # Must have meaningful differences
        surface_sim = calculate_surface_similarity(user, candidate)
        if surface_sim > 0.8:  # Too similar, not interesting
            continue

        # Both should handle disagreement well
        if user.bridging_score < 0.5 or candidate.bridging_score < 0.5:
            continue

        # Calculate "interesting difference" score
        diff_score = core_sim * (1 - surface_sim) * min(user.bridging_score, candidate.bridging_score)

        matches.append({
            'user': candidate,
            'core_sim': core_sim,
            'surface_sim': surface_sim,
            'diff_score': diff_score,
            'difference_areas': find_difference_topics(user, candidate)
        })

    return sorted(matches, key=lambda x: x['diff_score'], reverse=True)[:5]
```

---

## Part 4: Data Model Updates

### New Tables

```sql
-- Track belief importance
ALTER TABLE beliefs ADD COLUMN importance INTEGER DEFAULT 3;
ALTER TABLE beliefs ADD COLUMN importance_set_at TIMESTAMP;
ALTER TABLE beliefs ADD COLUMN importance_auto BOOLEAN DEFAULT TRUE;

-- Privacy settings per belief
ALTER TABLE beliefs ADD COLUMN visibility TEXT DEFAULT 'shareable';
-- Values: 'public', 'shareable', 'private', 'hidden'

-- User privacy preferences
CREATE TABLE user_privacy (
    user_id TEXT PRIMARY KEY,
    default_visibility TEXT DEFAULT 'shareable',
    excluded_from_aggregates BOOLEAN DEFAULT FALSE,
    allow_match_suggestions BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Comparison history (for rate limiting, not storing results)
CREATE TABLE comparison_requests (
    id TEXT PRIMARY KEY,
    requester_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, accepted, declined, expired
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    FOREIGN KEY (requester_id) REFERENCES users(user_id),
    FOREIGN KEY (target_id) REFERENCES users(user_id)
);

-- Community clusters (computed periodically)
CREATE TABLE belief_clusters (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    cluster_label TEXT,  -- e.g., "progressive", "traditional", "pragmatic"
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_clusters (
    user_id TEXT NOT NULL,
    cluster_id TEXT NOT NULL,
    membership_strength REAL,  -- 0-1, how strongly they belong
    PRIMARY KEY (user_id, cluster_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (cluster_id) REFERENCES belief_clusters(id)
);
```

---

## Part 5: Open Questions

### Product Questions
1. **Comparison frequency** — How often can you compare with the same person? (Prevent spam)
2. **Cluster labels** — Should clusters be auto-labeled or just numbered? (Labels could be biased)
3. **Bridging rewards** — What's the right incentive? Badges? Roles? Access to features?
4. **Backfire prevention** — How to show differences without triggering defensive reactions?

### Technical Questions
1. **Embedding model** — Which sentence embedding for semantic similarity? (Speed vs quality)
2. **Clustering algorithm** — K-means? DBSCAN? How many clusters?
3. **Update frequency** — How often to recompute community stats?
4. **Scale** — At what user count do aggregates become meaningful? (Minimum 20?)

### Ethical Questions
1. **Manipulation risk** — Could people game bridging scores?
2. **Filter bubble by design** — Is matching on "core values" just a sophisticated filter bubble?
3. **Privacy of patterns** — Even without individual beliefs, can patterns be identifying?
4. **Consent for clustering** — Should users consent to being clustered?

---

## Part 6: Implementation Priority

### Phase 1: Foundation (v0.2)
```
Week 1-2: Belief Importance
├─ /mark command
├─ Importance display in /beliefs, /map
├─ Update schema
└─ Prompt users to mark importance occasionally

Week 3-4: Better Relations
├─ Enhanced /belief [id] display
├─ /tree visualization
├─ /tensions command
└─ Improve relation extraction in Claude prompts

Week 5-6: Shareable Format
├─ /share command with options
├─ Clean embed format
├─ Copy-as-text option
└─ Privacy checks before sharing
```

### Phase 2: Comparison Core (v0.3)
```
Week 7-9: 1:1 Comparison
├─ /compare request/accept flow
├─ Similarity calculation algorithm
├─ Comparison result display
├─ Privacy controls integration

Week 10-11: Scores & Display
├─ Component breakdown (core, surface, style)
├─ Bridging score calculation
├─ Score explanations
└─ "Explore differences" drill-down

Week 12: Polish
├─ Edge cases
├─ Rate limiting
├─ User testing feedback
└─ Documentation
```

### Phase 3: Community (v0.4)
```
Consensus finder
Community aggregates
Match suggestions
Badges/rewards
```

---

## Appendix: Research Sources

- **Helen Fisher** — Fisher Temperament Inventory, personality-based matching
- **OkCupid** — Importance weighting (0-250x scale), match percentage calculation
- **Pol.is** — Consensus finding, bridging algorithms, computational democracy
- **Twitter Community Notes** — Bridging-based ranking, cross-divide appreciation
- **James Fishkin** — Deliberative polling, structured dialogue
- **Eli Pariser** — Filter bubbles, exposure vs bridging
- **Bounded Confidence Models** — Deffuant-Weisbuch, why gradual bridging works

---

*This document is a living spec. Update as we learn from user testing.*
