# Kodak v2.0 Implementation Plan

> Tracking document for the v2.0 rewrite from belief mapping bot to reflective journaling companion.

**Design doc:** [DESIGN-v2.md](DESIGN-v2.md)

---

## Approach

**New files, then replace:** Rather than heavily modifying existing v1 files, we create new v2 files alongside them. This lets v1 remain functional while we build and test v2. Once v2 is working, we remove v1 code.

**File naming convention:** New files use `_v2` suffix during development (e.g., `bot_v2.py`). After Sprint 6, we rename them to replace the originals.

---

## Sprint 1: Schema & Core Infrastructure

**Goal:** Database ready, scheduler working, basic session tracking

**Status:** Not started

| Task | File | Description | Status |
|------|------|-------------|--------|
| 1.1 | `schema-v2.sql` | New schema with scheduling, sessions, values tables | ⬜ |
| 1.2 | `src/db_v2.py` | Database functions for v2 (sessions, scheduling, values) | ⬜ |
| 1.3 | `src/scheduler.py` | Background task for daily prompts + catch-up logic | ⬜ |
| 1.4 | `src/values.py` | Schwartz constants, value derivation functions | ⬜ |
| 1.5 | `src/bot_v2.py` | Core bot with scheduler integration (minimal commands) | ⬜ |

**Definition of done:**
- [ ] Bot starts without errors
- [ ] Scheduler runs as background task
- [ ] Can send a test prompt at a configured time
- [ ] Database tables created correctly

---

## Sprint 2: Onboarding & Sessions

**Goal:** User can complete onboarding, receive prompts, have a journaling session

**Status:** Not started

| Task | File | Description | Status |
|------|------|-------------|--------|
| 2.1 | `src/onboarding.py` | New onboarding flow (personality → schedule) | ⬜ |
| 2.2 | `src/prompts.py` | Opener pools, probe templates, closure templates | ⬜ |
| 2.3 | `src/session.py` | Session state management (opener → probe → close) | ⬜ |
| 2.4 | `src/personality_v2.py` | Adapted personality system for journaling | ⬜ |
| 2.5 | `src/bot_v2.py` | Wire up onboarding, session handling | ⬜ |

**Definition of done:**
- [ ] New user can complete onboarding (personality + time selection)
- [ ] User receives prompt at scheduled time
- [ ] Full session works: opener → probes → closure
- [ ] Session adapts to response depth
- [ ] First session has special handling (lighter probing)

---

## Sprint 3: Extraction & Values

**Goal:** Beliefs extracted from sessions, values derived and stored

**Status:** Not started

| Task | File | Description | Status |
|------|------|-------------|--------|
| 3.1 | `src/extractor_v2.py` | Extended extraction: beliefs + value tagging | ⬜ |
| 3.2 | `src/values.py` | Value profile aggregation, normalization, temporal decay | ⬜ |
| 3.3 | `src/db_v2.py` | Store belief-value mappings, snapshots | ⬜ |
| 3.4 | `src/bot_v2.py` | `/values`, `/values-history` commands | ⬜ |
| 3.5 | `src/session.py` | Show extracted beliefs at session close | ⬜ |

**Definition of done:**
- [ ] Beliefs extracted from journal sessions
- [ ] Each belief tagged with 0-3 Schwartz values + mapping confidence
- [ ] Value profile aggregates correctly (with temporal decay)
- [ ] `/values` shows narrative profile
- [ ] `/values-history` shows change over time
- [ ] Session close shows extracted beliefs

---

## Sprint 4: Commands & Polish

**Goal:** All commands working, edge cases handled

**Status:** Not started

| Task | File | Description | Status |
|------|------|-------------|--------|
| 4.1 | `src/bot_v2.py` | Migrate `/map`, `/beliefs`, `/explore`, `/belief`, `/forget`, `/undo` | ⬜ |
| 4.2 | `src/bot_v2.py` | Migrate `/history`, `/tensions`, `/changes`, `/mark`, `/confidence` | ⬜ |
| 4.3 | `src/bot_v2.py` | New: `/schedule`, `/timezone`, `/depth`, `/journal`, `/skip` | ⬜ |
| 4.4 | `src/bot_v2.py` | Migrate `/setup`, `/style`, `/pause`, `/resume` | ⬜ |
| 4.5 | `src/bot_v2.py` | Migrate `/export`, `/backup`, `/clear` | ⬜ |
| 4.6 | `src/bot_v2.py` | Updated `/help` for v2 | ⬜ |
| 4.7 | `src/scheduler.py` | Edge cases: re-engagement, missed prompts, mid-day schedule change | ⬜ |

**Definition of done:**
- [ ] All retained commands work
- [ ] All new commands work
- [ ] Re-engagement flow works (user absent 2+ weeks)
- [ ] Missed prompt catch-up works
- [ ] `/help` reflects v2 commands

---

## Sprint 5: Comparison

**Goal:** File-based value comparison working

**Status:** Not started

| Task | File | Description | Status |
|------|------|-------------|--------|
| 5.1 | `src/bot_v2.py` | `/share-values` with privacy selection UI | ⬜ |
| 5.2 | `src/values.py` | Export format (JSON schema) | ⬜ |
| 5.3 | `src/bot_v2.py` | `/compare-file` — load, compare, display | ⬜ |
| 5.4 | `src/values.py` | Comparison algorithm (similarity, differences) | ⬜ |

**Definition of done:**
- [ ] User can export values with privacy selection
- [ ] Export file is valid JSON with documented schema
- [ ] Recipient can load file and see comparison
- [ ] Comparison shows: overall alignment, shared priorities, differences

---

## Sprint 6: Cleanup & Documentation

**Goal:** Remove v1 code, update all docs, ready for release

**Status:** Not started

| Task | File | Description | Status |
|------|------|-------------|--------|
| 6.1 | Various | Remove v1 files (`bot.py`, `db.py`, etc.) | ⬜ |
| 6.2 | Various | Rename v2 files (remove `_v2` suffix) | ⬜ |
| 6.3 | `schema.sql` | Replace with v2 schema | ⬜ |
| 6.4 | `README.md` | Update for v2 (description, commands, setup) | ⬜ |
| 6.5 | `SETUP.md` | Update for any new setup steps | ⬜ |
| 6.6 | `SETUP.md` | Add auto-start documentation (macOS, Linux, Windows) | ⬜ |
| 6.7 | `DESIGN.md` | Archive v1 design or merge relevant parts | ⬜ |

**Definition of done:**
- [ ] No v1 code remains
- [ ] All documentation reflects v2
- [ ] Auto-start instructions for all platforms
- [ ] Clean git history (no leftover v2 suffixes)

---

## File Overview

### New Files (v2)

| File | Purpose |
|------|---------|
| `schema-v2.sql` | Database schema for v2 |
| `src/bot_v2.py` | Main bot with v2 logic |
| `src/db_v2.py` | Database functions for v2 |
| `src/scheduler.py` | Daily prompt scheduler |
| `src/values.py` | Schwartz values framework |
| `src/session.py` | Session state management |
| `src/prompts.py` | Opener pools, probes, closures |
| `src/onboarding.py` | Onboarding flow |
| `src/personality_v2.py` | Adapted personality system |
| `src/extractor_v2.py` | Belief + value extraction |

### Retained from v1 (may need minor updates)

| File | Notes |
|------|-------|
| `src/personality.py` | Base for `personality_v2.py` |
| `src/extractor.py` | Base for `extractor_v2.py` |

### Removed in Sprint 6

| File | Reason |
|------|--------|
| `src/bot.py` | Replaced by `bot_v2.py` |
| `src/db.py` | Replaced by `db_v2.py` |
| `schema.sql` | Replaced by `schema-v2.sql` |

---

## Progress Log

*Update this section after each sprint/session*

| Date | Sprint | Notes |
|------|--------|-------|
| 2026-01-24 | Planning | Created DESIGN-v2.md and this implementation plan |

---

## Testing Checklist

### Manual Testing (each sprint)

- [ ] Bot starts without errors
- [ ] Commands respond correctly
- [ ] Database operations work
- [ ] No regressions from previous sprint

### End-to-End Testing (before Sprint 6)

- [ ] New user: onboarding → first session → beliefs extracted
- [ ] Returning user: scheduled prompt → session → values updated
- [ ] Long absence: re-engagement flow works
- [ ] Comparison: export → share → compare works
- [ ] All commands work as documented

---

## Notes

- **Local-first focus:** Design assumes users run locally. Railway/cloud is supported but not primary.
- **Keep v1 running:** Until Sprint 6, v1 should still work for existing testers.
- **Database migration:** Not needed — fresh start for v2 (per user decision).
