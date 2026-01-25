# Kodak Roadmap

A living document of where Kodak is going.

**See also:**
- [VALUES-SYSTEM-AUDIT.md](VALUES-SYSTEM-AUDIT.md) — Technical notes on theme extraction

---

## Current Priority: Stability & Testing 🔧

Phases 1-4 complete, but deployment revealed critical runtime errors. Focusing on stability before launch.

---

## Phase 0: Critical Stability Fixes (Complete)

**Status:** All critical bugs fixed. Bot is production-ready with first user onboarded successfully.

### Completed (Jan 2025)
- [x] **Import errors** — Fixed 15+ missing/misnamed function imports across codebase
  - `get_session` → `get_active_session`
  - `SchedulerManager` → `JournalScheduler` with correct constructor params
  - Extractor, values, and db module import mismatches
- [x] **Function signature mismatches** — Fixed parameter order/types
  - OnboardingFlow constructor
  - export_themes_for_sharing parameters
  - parse_exported_themes type handling
- [x] **Type errors** — Fixed ValueProfile dict/object access patterns
- [x] **Invalid parameters** — Removed non-existent `include_topics` parameter
- [x] **JSON encoding bugs** — Fixed double-encoding in theme exports
- [x] **Database schema bug** — Missing `last_prompt_date` column (Jan 25 evening)
  - Added column to schema.sql and migration
  - Added error handling to onboarding callbacks
  - Fixed `last_opener` allowed column issue
  - **Result:** Onboarding persistence works, scheduled messages delivered successfully

### Remaining Work
- [ ] **Exception handler double-response errors** — Fix interaction.response called twice in error paths
  - Affects: All command files when exceptions occur after successful response
  - Priority: Low (rare edge case, doesn't affect normal usage)
  - Solution: Check `interaction.response.is_done()` before sending error messages
- [ ] **Add basic import validation** — Prevent import errors from reaching production
  - Add `python -m py_compile src/**/*.py` to CI/CD or pre-commit hook
  - Consider basic smoke tests that import all modules
- [ ] **Local testing workflow** — Document how to run bot locally before deploying
  - Setup instructions with .env template
  - Database initialization steps
  - How to test Discord interactions locally

---

## Recently Completed

- [x] **Code refactoring** — Split 2,057-line bot.py into organized modules (90% reduction!)
- [x] **Production readiness** — Health check endpoint and structured JSON logging
- [x] Milestone messages (5, 15, 20, 50 sessions) — Celebratory encouragement
- [x] Weekly summary prompting — Proactive nudge after 5+ sessions
- [x] Documentation updates — All commands properly documented
- [x] Weekly summaries (`/summary week`)
- [x] Past summaries viewing (`/summaries`)
- [x] Theme snapshots for tracking change over time
- [x] File-based theme comparison (`/share-themes`, `/compare-file`)
- [x] Repositioning: "themes" not "psychological profile"
- [x] Same-session insights at session close
- [x] **Phase 4: Engagement Features** — Sample sessions in onboarding, source beliefs with themes, softer theme language, extraction honesty

---

## Phase 1: Critical Fixes ✓

Infrastructure and reliability.

- [x] **Shared Anthropic client** — Consolidated into `client.py` with `create_message()` helper
- [x] **LLM timeout** — 30-second default timeout on all LLM calls
- [x] **Error handling** — `APITimeoutError` and `APIError` caught with user-facing messages
- [x] **In-memory state persistence** — `last_opener` persisted to DB with migration support

---

## Phase 2: UX Quick Wins ✓

Make the experience feel polished and motivating.

- [x] **Tier help command** — Essential commands by default, "See all commands" button expands
- [x] **Progress indicator on `/themes`** — Shows belief count and distance to emerging (15) / stable (50) thresholds
- [x] **Better empty state for `/themes`** — Shows progress toward meaningful themes with specific counts
- [x] **Milestone messages** — At key session counts, show encouragement:
  - **5 sessions:** "Getting to know you" phase complete. Tease what's coming.
  - **15-20 sessions:** "Themes are emerging." First real payoff moment.
  - **~50 sessions:** "Your themes are stable." Invite comparison/sharing.
- [x] **Prompt for weekly summary** — After 5+ sessions in a week, nudge: "Want to see your weekly summary?"

---

## Phase 3: Code Cleanup ✓

Split bot.py and improve structure.

- [x] **Split bot.py** into:
  - `bot.py` — Main bot, event handlers, startup (209 lines, down from 2,057!)
  - `commands/` — Slash commands grouped by feature (journal, themes, beliefs, summary, data, help, settings)
  - `handlers/` — Message processing and session lifecycle
  - `views/` — Discord UI components (ready for future use)
- [x] **Health check endpoint** — HTTP server on port 8080 for Railway/monitoring
- [x] **Structured JSON logging** — Production-ready JSON logs with context

---

## Phase 4: Engagement Features ✓

Make the first experience compelling and build trust in themes.

- [x] **Sample session in onboarding** — Show a sample conversation during setup so users know what to expect
- [x] **Show source beliefs with themes** — When `/themes` shows a theme, include 1-2 actual quotes that drove it. "Based on things like: [quote]"
- [x] **Softer theme language** — "Achievement has come up" not "You value achievement." Observational, not definitional.
- [x] **Extraction honesty** — Always surface uncertainty: "Based on what you've shared so far" and show sample size

---

## Phase 5: Reliability & Observability

Improvements for production monitoring and debugging.

### Error Handling & Recovery
- [ ] **Session state persistence** — Save active sessions to DB so Railway restarts don't lose context
  - Store session messages and stage in database
  - Restore on bot restart
- [ ] **Graceful degradation** — Better fallbacks when LLM calls fail
  - Cache last successful prompt for retry
  - Simple acknowledgment responses when extraction fails
- [ ] **Better error messages** — User-friendly errors with actionable next steps
  - "Try again" vs "contact support" guidance
  - Log correlation IDs for debugging

### Monitoring & Debugging
- [ ] **Command usage metrics** — Track which features are actually used
  - Log command invocations (without PII)
  - Session completion rates
  - Onboarding drop-off points
- [ ] **Error rate monitoring** — Alert on unusual error patterns
  - Integration with Railway logs
  - Slack/email alerts for critical errors
- [ ] **Database backups** — Automated backup strategy
  - Volume snapshots on Railway
  - Export to S3/backup location

---

## Phase 6: Post-Launch Features (After User Feedback)

Only build these after real users tell us what's missing.

### Self-Improving Corrections
Each instance learns from its own user. When a theme is tagged wrong, the user corrects it and the bot adjusts future extraction.

- [ ] "Does this seem right?" prompt on theme tags
- [ ] Store corrections locally
- [ ] Feed corrections into extraction context for future sessions

### Longer-Term Pattern Surfacing
Kodak proactively brings up things from the past during sessions.

- "Six months ago you said you wanted to leave your job. How's that feeling now?"
- "You've mentioned feeling overwhelmed at work three times this month."

### Monthly Summaries
Extend `/summary week` to `/summary month`.

### One-Sided Sharing
Reframe `/share-themes` as "here's what I've learned about myself" for sharing with anyone, not just other Kodak users.

### Richer Comparison
Better questions based on actual differences, comparison history over time.

---

## Deferred

- Tension resolution (guided exploration of contradictions)
- Web visualization (interactive belief graph)
- Obsidian export (markdown for notes apps)
- Metrics/observability

---

## Ideas Parking Lot

- Voice input
- Mood tracking
- Goal tracking
- Shared journals (couples/friends)
- API access
- Group insights
- Integrations (calendar, Spotify, etc.)

---

## Contributing

Ideas welcome. Open an issue or PR.
