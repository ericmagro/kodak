# Values System Audit

> Technical analysis of Kodak's value capture, categorization, and comparison system.
> Conducted January 2026.

---

## Current Architecture

### 1. Extraction (extractor.py)
- Claude analyzes user messages for beliefs
- Each belief tagged with 0-3 Schwartz values
- Tags include: `weight` (1.0 primary, 0.5 secondary), `mapping_confidence` (0.0-1.0)
- Values with mapping_confidence < 0.4 filtered out

### 2. Scoring Formula
```
contribution = belief_confidence × mapping_confidence × weight × temporal_decay
```
- Temporal decay: 90-day half-life (exponential)
- Raw scores summed per value

### 3. Normalization
- User's highest raw score becomes 1.0
- All others scaled proportionally
- **This is relative to the user's own distribution**

### 4. Comparison
- Cosine similarity between two users' normalized vectors
- Identifies shared top values, key differences

---

## Critical Issues

### Issue 1: Normalization Destroys Magnitude (CRITICAL)

**Problem:** Max-value normalization erases how much someone actually cares about values.

Example:
- User A: Achievement=50, Benevolence=25 → Normalized: [1.0, 0.5]
- User B: Achievement=5, Benevolence=100 → Normalized: [0.05, 1.0]

User B mentioned Achievement 5 times — that's real signal! But after normalization, it looks like they don't care about Achievement at all.

**Impact:** Two users with identical rank orderings but completely different value *intensities* appear identical. We're comparing priorities but losing centrality (how values-driven someone is overall).

**Proposed Fix:**
- Switch to sum-normalization (scores sum to 1.0) or z-scores (deviation from own mean)
- Add separate "values intensity" metric: `total_raw_score / belief_count`
- Compare on BOTH priority structure AND intensity

---

### Issue 2: LLM Extraction Has Unknown Reliability (CRITICAL)

**Problem:** No ground truth, no calibration, unknown consistency.

Specific concerns:
- `mapping_confidence` scores are likely overconfident (LLMs don't say "I don't know")
- Same belief might get different tags on different runs (test-retest reliability unknown)
- Distribution probably clustered 0.6-0.9, very few low scores
- Cultural/linguistic bias in interpretation

**Impact:** Every downstream calculation inherits this noise. Errors compound through the pipeline.

**Proposed Fix:**
- Build human-labeled validation dataset (100-200 beliefs with expert-assigned values)
- Measure test-retest reliability (same content, multiple runs)
- Measure inter-prompt reliability (same content, slightly different prompts)
- Enable user corrections ("This belief was tagged wrong")
- Track correction rate as quality signal

---

### Issue 3: Small Sample Profiles Are Noise (CRITICAL)

**Problem:** With 5-10 beliefs, one misclassification flips the dominant value.

Standard error scales with 1/√n. At n=5, you have essentially no precision.

**Impact:** Early users see "profiles" that are mostly noise. Comparisons between low-n profiles are meaningless.

**Proposed Fix:**
- Require minimum ~30 beliefs before showing "stable" profile
- Below threshold: show "emerging themes" with explicit uncertainty
- Block or heavily caveat comparisons below threshold
- Consider blending with priors (population base rates) for cold start

---

### Issue 4: Comparison Validity Is Questionable (HIGH)

**Problem:** What does cosine similarity of two self-relative profiles actually measure?

It measures: "Do these two users have similar *rank orderings* of values, relative to their own baselines, as expressed in their *journaling behavior*, as *interpreted by an LLM*, over their respective *time windows*?"

That's very different from "psychological compatibility" or "shared values."

Additional concerns:
- Profiles with different sample sizes have different reliability
- Cosine similarity treats all value dimensions as equally important
- Complementarity (productive differences) might matter as much as similarity

**Proposed Fix:**
- Weight comparisons by profile confidence
- Require minimum maturity for both profiles
- Consider domain-specific weightings (Hedonism disagreement vs Tradition disagreement)
- Add complementarity analysis, not just similarity
- Track whether high-similarity matches predict positive outcomes (feedback loop)

---

### Issue 5: No Feedback Loop (HIGH)

**Problem:** System generates scores and comparisons but never learns if they're meaningful.

No way to know:
- Are extracted values accurate?
- Do high-similarity matches actually get along?
- Do profiles predict real-world behavior?

**Impact:** Can't improve the system. Can't validate claims. Operating blind.

**Proposed Fix:**
- Enable user corrections on value tags
- Track match outcomes (if social features expand)
- Add behavioral validation where possible
- Build ground truth dataset over time

---

## Medium Priority Issues

### Issue 6: Temporal Decay Is Arbitrary

**Problem:** 90-day half-life has no empirical basis.

Values are supposed to be relatively stable across the lifespan. The decay might be addressing *salience fluctuations* (what's on your mind) rather than actual value change.

**Considerations:**
- Different values might decay at different rates
- Life events might reset relevance (not continuous decay)
- Maybe maintain both "working profile" (recent) and "archival profile" (stable)

---

### Issue 7: Schwartz Framework Gaps

**Problem:** Framework misses values people care about.

Not captured well:
- Authenticity (overlaps Self-Direction but distinct)
- Learning/Growth
- Aesthetic appreciation
- Humor/Playfulness
- Connection/Intimacy (distinct from Benevolence)

**Considerations:**
- Monitor beliefs that don't map to any value
- Consider extending framework with additional values
- Or use Schwartz as base with optional extensions

---

### Issue 8: Cultural Bias

**Problem:** Multiple layers where cultural bias enters.

1. Schwartz framework validated cross-culturally but *importance* of values varies by culture
2. LLM trained primarily on English/Western text
3. Keywords in prompt drawn from Western value expressions
4. Same words mean different things across cultures ("freedom," "family")

**Impact:** System may work better for Western, English-speaking users. Cross-cultural comparisons may be invalid.

**Proposed Fix:**
- Let users self-identify cultural background
- Develop culture-specific norms (compare to cultural baseline, not global)
- Add context to comparisons ("high Conformity in Japan vs US means different things")

---

### Issue 9: Uncertainty Not Communicated

**Problem:** System shows precise scores (0.73, 85% match) that imply false confidence.

Users interpret these as meaningful claims about psychology when they're noisy estimates.

**Proposed Fix:**
- Show confidence intervals or ranges
- Use qualitative labels for low-confidence profiles
- Frame as "emerging picture" not "your values"
- Never show more decimal places than the data supports

---

## Implementation Roadmap

### Phase 1: Foundation (Highest Impact)
- [ ] Fix normalization (sum-based or z-scores)
- [ ] Add confidence/uncertainty display
- [ ] Require minimum beliefs (~30) for comparisons
- [ ] Enable user corrections to value tags

### Phase 2: Validation
- [ ] Build validation dataset (100-200 labeled beliefs)
- [ ] Measure extraction reliability
- [ ] Track correction rate as quality signal

### Phase 3: Refinement
- [ ] Experiment with different decay models
- [ ] Add complementarity analysis to comparisons
- [ ] Consider framework extensions for missing values

### Phase 4: Feedback Loop
- [ ] Track comparison outcomes
- [ ] Behavioral validation where possible
- [ ] Continuous calibration from corrections

---

## Open Questions

1. What's the minimum viable validation dataset size?
2. Should we show raw scores alongside normalized?
3. How do we handle the cold-start problem gracefully?
4. Is Schwartz the right framework, or should we consider alternatives?
5. How do we validate comparisons without creepy tracking?

---

## References

- Schwartz, S. H. (1992). Universals in the content and structure of values
- Schwartz, S. H. (2012). An Overview of the Schwartz Theory of Basic Values
- [Anthropic's work on LLM calibration]
- [Psychometric principles for profile comparison]
