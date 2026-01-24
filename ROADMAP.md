# Kodak Roadmap

A living document of where Kodak is going.

**See also:**
- [VISION.md](VISION.md) — The bigger picture: decentralized compatibility matching
- [VALUES-SYSTEM-AUDIT.md](VALUES-SYSTEM-AUDIT.md) — Technical audit of the values system

---

## Recently Completed

- [x] Weekly summaries (`/summary week`)
- [x] Past summaries viewing (`/summaries`)
- [x] Value snapshots for tracking change over time
- [x] File-based value comparison (`/share-values`, `/compare-file`)

---

## Near-Term: Values System Fixes

These address critical issues identified in the [values system audit](VALUES-SYSTEM-AUDIT.md).

### Fix Normalization (Critical)
Current max-value normalization loses magnitude information, making comparisons less meaningful.

- [ ] Switch to sum-normalization or z-scores
- [ ] Add "values intensity" metric (how values-driven overall)
- [ ] Compare on both priority structure AND intensity

### Add Uncertainty Display (Critical)
System shows false precision. Users need to understand confidence levels.

- [ ] Show confidence bounds on profiles
- [ ] Frame early profiles as "emerging themes"
- [ ] Require minimum beliefs (~30) for comparisons
- [ ] Visual indication of profile maturity

### Enable User Corrections (High)
Let users fix misclassified values—improves accuracy and builds training data.

- [ ] "This belief was tagged wrong" feedback
- [ ] Track correction rate as quality signal
- [ ] Use corrections to improve extraction over time

### Extraction Validation (High)
We don't know how reliable the LLM extraction is.

- [ ] Build validation dataset (100-200 human-labeled beliefs)
- [ ] Measure test-retest reliability
- [ ] Measure inter-prompt reliability

---

## Near-Term: Features

### Monthly Summaries
Extend weekly summaries to monthly cadence.

- [ ] Longer-term pattern detection
- [ ] Value change narratives across weeks
- [ ] Comparison to previous months

### Year-End Summary
Comprehensive annual reflection:
- Accomplishments & milestones mentioned
- Major belief changes (January vs December)
- Value evolution across the year
- Themes, patterns, growth moments
- Stats (sessions, beliefs, most active months)

### Longer-Term Pattern Surfacing
Proactive prompts that reference the past:
- "Six months ago you said X. Still feel that way?"
- "You've mentioned feeling stuck at work three times this month"
- "Last year around this time you were dealing with Y"

### Tension Resolution
When contradictory beliefs are detected:
- Surface the tension explicitly
- Guided exploration of which feels more true
- Option to update or retire one belief

---

## Medium-Term: Comparison & Compatibility

### Improved Comparison
- [ ] Weight dimensions differently for different relationship types
- [ ] Add complementarity analysis (productive differences)
- [ ] Show "questions to explore together" based on differences
- [ ] Comparison history — track alignment over time

### Portable Compatibility Profiles
Standardized format for sharing value profiles outside Kodak.

- [ ] Generate shareable "Compatibility Profile" document
- [ ] Side-by-side comparison with detailed explanations
- [ ] Frame as conversation starters, not scores

### Relationship Type Matching
Different weighting for:
- Romantic relationships (attachment, life goals, conflict style)
- Co-founder relationships (complementary skills, aligned ethics)
- Friendships (shared interests, benevolence alignment)

---

## Long-Term: Decentralized Matching

See [VISION.md](VISION.md) for full details.

### Phase 1: Comparison Tool
No network effects needed—useful for pairs.
- Compare with known relationships (partner, potential co-founder, friend)
- Export shareable profiles
- Frame as "questions to explore together"

### Phase 2: Opt-in Discovery
- Publish blurred profile (Schwartz values only) to optional relay
- Browse/search others who've opted in
- Mutual consent required to reveal details
- Single relay to start

### Phase 3: Protocol Layer
- Standardize profile format for interoperability
- Multiple relays (federated)
- Reputation/verification options
- Consider DAO governance

---

## Visualization & Export

### Web Visualization
Interactive graph of beliefs and values:
- Nodes = beliefs, edges = relationships
- Color-coded by value or topic
- Filter by time period, confidence, importance

### Obsidian Export
Export belief network to markdown:
- One file per belief with YAML frontmatter
- Wikilinks between related beliefs
- Ready for Obsidian vault

---

## Ideas Parking Lot

Lower priority or needs more thought:

- **Voice input** — Speak instead of type
- **Mood tracking** — Correlate mood with beliefs
- **Goal tracking** — Set goals, check in on progress
- **Shared journals** — Couples or friends journaling together
- **API access** — Let users build on top of their data
- **Group insights** — "What does this Discord server value?"
- **Integrations** — Calendar, Spotify, etc.

---

## Contributing

Ideas welcome. Open an issue or PR.
