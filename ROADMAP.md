# Kodak Roadmap

Ideas for future development, roughly prioritized.

---

## Summaries & Reflection

### Weekly/Monthly Summaries
Automatic digests of your journaling activity:
- Topics you reflected on most
- Beliefs that emerged or evolved
- Value shifts detected
- Patterns noticed ("You mentioned work stress 6 times this month")

Could be sent automatically or triggered with `/summary week` or `/summary month`.

### Year-End Summary
A comprehensive annual reflection:
- **Accomplishments & milestones** mentioned throughout the year
- **Major belief changes** — what you thought in January vs December
- **Value evolution** — how your priorities shifted
- **Themes** — what dominated your reflections (career, relationships, health, etc.)
- **Patterns** — recurring concerns, breakthroughs, cycles
- **Growth moments** — times you updated a belief or resolved a tension
- **Stats** — sessions completed, beliefs extracted, most active months

Delivered around late December or on-demand with `/summary year`.

---

## Pattern Recognition

### Longer-Term Pattern Surfacing
Proactive prompts that reference the past:
- "Six months ago you said X. Still feel that way?"
- "You've mentioned feeling stuck at work three times this month"
- "Last year around this time you were dealing with Y"

Requires: tracking seasonal patterns, belief timestamps, theme detection.

### Tension Resolution
When contradictory beliefs are detected, offer guided exploration:
- Surface the tension explicitly
- Ask which feels more true
- Explore the nuance (maybe both are true in different contexts)
- Optionally update or retire one belief

### Value Drift Alerts
Notify when values shift significantly:
- "Your Security score dropped 20% this month"
- "Achievement has become your top value (was #4 last month)"
- Could be opt-in to avoid being annoying

---

## Visualization & Export

### Web Visualization
Interactive graph of beliefs and values:
- Nodes = beliefs, edges = relationships (supports, contradicts, relates)
- Color-coded by value or topic
- Click to explore
- Filter by time period, confidence, importance

Could be a simple static site generated from `/export` data, or a hosted dashboard.

### Obsidian Export
Export belief network to markdown:
- One file per belief with YAML frontmatter
- Wikilinks between related beliefs
- Value tags
- Ready to drop into an Obsidian vault

### Mobile-Friendly Export
PDF or image summaries for sharing:
- Value profile as a shareable graphic
- "My 2026 in reflection" year-end card
- Comparison results as an image

---

## Social & Community

### Group Insights
Aggregate value profiles across users (opt-in):
- "What does this Discord server actually value?"
- Anonymous aggregation — no individual data exposed
- Could surface: shared values, value diversity, outliers

### Enhanced Comparison
Beyond the current file-based comparison:
- Direct user-to-user comparison (with consent)
- Comparison history — track alignment over time
- "Find someone who..." — match based on value similarity or interesting differences

---

## Customization

### Prompt Customization
Let users influence the opener prompts:
- Add custom prompts to the rotation
- Weight certain prompt types (more work-focused, more relationship-focused)
- "Never ask me about X"

### Session Preferences
More granular control:
- Preferred session length (not just quick/standard/deep)
- Topics to focus on or avoid
- Extraction sensitivity (more/fewer beliefs per session)

---

## Technical Improvements

### Smarter Scheduling
- Multiple check-in times per day (morning + evening)
- Day-of-week preferences (skip weekends, or weekends only)
- Vacation mode with return date

### Better Catch-Up
When you miss several days:
- Option to do a "week in review" session
- Batch catch-up: "Anything notable from the last few days?"

### Conversation Memory
Reference past sessions more intelligently:
- "Last time we talked about your job interview. How did that go?"
- Requires: session summarization, topic threading

---

## Ideas Parking Lot

Lower priority or needs more thought:

- **Voice input** — Speak instead of type (Discord voice? External?)
- **Mood tracking** — Infer or ask about mood, correlate with beliefs
- **Goal tracking** — Set goals, check in on progress
- **Shared journals** — Couples or close friends journaling together
- **API access** — Let users build on top of their data
- **Integrations** — Calendar (what happened today), Spotify (what you listened to), etc.

---

## Contributing

Ideas welcome. Open an issue or PR.
