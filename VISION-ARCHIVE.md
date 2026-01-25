# Kodak: Expanded Vision

> From personal journaling to decentralized compatibility matching.
> User-owned, open-source, portable—so it can never be taken away.

---

## The Opportunity

Dating apps have been enshittified. What made early OKCupid great—deep questions, thoughtful matching, people presenting as complex humans—has been replaced by swipe-based dopamine slot machines optimized for engagement, not connection.

The same problem exists for finding co-founders, collaborators, and friends. LinkedIn is noisy. Twitter is chaotic. There's no good way to find people who share your values and complement your goals.

**Kodak is already building the foundation:**
- Daily journaling that extracts beliefs naturally
- Value profiling using a validated psychological framework
- Local-first, user-owned data
- Export/import for portability

The question: can this evolve into something bigger?

---

## The Vision

**A decentralized, open-source platform for finding compatible people—romantic partners, co-founders, friends—where users own their data and the system can never be captured or enshittified.**

Core principles:
1. **User-owned data** — Your profile lives on your device, not a corporate server
2. **Portable** — Standard formats that any app can read; switch services anytime
3. **Open source** — The code is public; anyone can run their own instance
4. **Privacy by design** — Share only what you choose, with whom you choose
5. **Optimized for connection** — Not engagement, not ads, not data harvesting

---

## What Made OKCupid Great (And What Got Lost)

**What worked:**
- Hundreds of thousands of user-submitted questions about values and beliefs
- Asymmetric matching: how you answer + how you want them to answer + importance weighting
- Questions surfaced *dealbreakers* and *values alignment*, not just preferences
- Profiles read like personal essays—people were *interesting*
- The experience required effort, which filtered for seriousness

**What got lost:**
- Match Group acquisition → incentives inverted (working app loses users)
- Photos-first, swipe-based interfaces reduced people to aesthetic judgments
- Questions became optional; complexity was hidden
- Optimization shifted from connection to engagement

---

## Architecture Options

### Option A: Fully Peer-to-Peer
Each user stores their own data, discovery via gossip protocols/DHT.
- **Pro:** Maximum decentralization
- **Con:** Discovery is terrible, requires nodes online, O(n²) matching

### Option B: Federated (Mastodon-style)
Users pick an instance, instances federate.
- **Pro:** Reasonable discovery within instances
- **Con:** Instance operators become power centers, fragmentation

### Option C: Smart Contract + Off-chain Data
Commitments on-chain, data in IPFS, verifiable matching.
- **Pro:** Credible neutrality
- **Con:** Expensive, slow, still needs discovery layer

### Option D: Hybrid with User-Chosen Relays ← **Recommended**
Users own data locally. Optionally publish encrypted profiles to relays (open-source servers anyone can run). Relays do matching, but users can switch anytime because data is portable.

**Key insight from Moxie:** What matters is *Can users exit?* If you can export data and move to a competitor, you've achieved most of what decentralization promises without the complexity.

---

## Discovery Without a Central Database

**The problem:** How do you find compatible people without everyone's data in one place?

**Solution: Progressive disclosure**

1. **Public layer:** Publish a "blurred" profile—just the 10 Schwartz value scores, no detailed beliefs
2. **Discovery:** Relays can match on blurred profiles (rough compatibility)
3. **Reveal:** Once matched, users can choose to share more detailed beliefs
4. **Verification:** Detailed matching happens between consenting parties only

**Advanced:** Private Set Intersection (PSI) cryptography could enable "what do we have in common?" queries without revealing what's *not* in common.

---

## What Actually Predicts Compatibility

### Romantic Relationships
**Does predict:**
- Attachment style compatibility
- Life goal alignment (kids, career, location)
- Conflict resolution style similarity
- Shared values on key dimensions (religion, politics, intellectual curiosity)
- Timing (both people ready)

**Doesn't predict:**
- Matching on personality traits
- Shared hobbies
- Physical "type" preferences

### Co-founder Relationships
- Prior relationship (worked together before) is #1 predictor
- Complementary skills + aligned values on risk and ethics
- Similar work style expectations

### Friendships
- Similar values on benevolence and universalism
- Shared interests matter more than deep value alignment

**Implication:** Weight Schwartz dimensions differently based on relationship type being sought.

---

## MVP Roadmap

### Phase 1: Comparison Tool (No Network Effects Needed)
- Generate standardized "Compatibility Profile" from existing journaling
- Share profile directly with specific people (file transfer, not platform)
- Side-by-side comparison with explanations of alignment/divergence
- Frame as "questions to explore together," not scores

**Use cases that don't need a network:**
- New couples understanding each other
- Potential co-founders vetting compatibility
- Friends who've grown apart
- People in conflict seeking common ground

### Phase 2: Opt-in Discovery
- Optional publishing of blurred profile (Schwartz vector only) to relay
- Browse/search others who've published
- Request to reveal more (mutual consent required)
- Single relay to start—federation later

### Phase 3: Protocol Layer
- Standardize profile format for interoperability
- Allow multiple relays
- Add reputation/verification options
- Consider DAO governance for protocol changes

---

## Abuse Prevention

**Threats:**
- Catfishing / fake profiles
- Harassment via matching
- Data harvesting
- Romance scams
- Gaming for validation without genuine intent

**Mitigations:**
- **Mutual matching** before any contact
- **Friction is protective** — effort filters for seriousness
- **Social proof verification** — link to established identities (optional)
- **Sybil resistance** — proof-of-personhood or social graph verification
- **Fewer, higher-quality matches** — don't maximize options

**Counterintuitive insight:** The "worse" UX of a decentralized system (slower, more friction, fewer immediate options) might actually produce better connection outcomes than optimized engagement.

---

## Key Risks

| Risk | Mitigation |
|------|------------|
| Nobody uses it (cold start) | Phase 1 doesn't need network effects |
| Capture by dominant client/relay | Open-source relay code, trivial to run your own |
| Privacy breach | Minimize stored data, encrypt at rest, progressive disclosure |
| Governance capture | Explicit constitution, DAO structure, limits on what can change |
| Works too well (manipulation risk) | Limit what's exposed for matching, careful with political beliefs |
| False confidence in scores | Frame as "explore together" not verdicts |
| Optimizes for wrong thing | Constitutional limits ("We will never..."), sustainable non-engagement-based funding |

---

## What This Is NOT

- Not trying to "disrupt" dating apps with better swiping
- Not a blockchain project that happens to have dating
- Not a social network that harvests data
- Not optimizing for engagement or time-on-app
- Not trying to replace human judgment with algorithms

---

## Open Questions

1. **Bootstrapping:** How do you get critical mass without network effects? Specific communities?
2. **Verification:** How much identity verification is needed without becoming invasive?
3. **Sustainability:** How does this get funded without incentive corruption?
4. **Scope:** Romantic + professional + friendship, or start with one?
5. **Protocol timing:** When is it right to extract a protocol from the app?

---

## Inspirations & References

- **OKCupid (2004-2012)** — Questions-based matching, profile essays
- **Keybase** — Portable identity with social proofs
- **Signal** — Privacy-preserving, practical "decentralization"
- **Nostr** — Simple relay-based protocol for social
- **Schwartz Value Survey** — Validated psychological framework
- **The Gottman Institute** — Research on relationship compatibility
- **Esther Perel** — Connection requires vulnerability, not just matching

---

## The Bet

Most platform plays fail because they require network effects before providing value.

Kodak's bet: **build something valuable for individuals first** (journaling, self-understanding), **then for pairs** (comparison, exploring compatibility), **then for networks** (discovery, matching).

Each phase is useful on its own. You don't need 10,000 users for Phase 1 to matter.

The long game: if Kodak becomes the way thoughtful people understand their own values, the matching network can grow from that foundation.
