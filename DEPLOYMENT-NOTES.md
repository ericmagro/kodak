# Deployment Notes

## Jan 25, 2025 - Initial Railway Deployment

### Issues Found & Fixed
This was the first real deployment. Code had never been run end-to-end.

**Critical bugs fixed (21 total):**
- Import errors: Wrong function names in 8+ files
- Constructor mismatches: OnboardingFlow, JournalScheduler
- Type errors: ValueProfile treated as dict
- Missing timezone in onboarding (UX bug - users got UTC times)

**Root cause:** Code written but never executed locally before deployment.

**Prevention:**
- Add `python -m py_compile` to pre-deploy checks
- Document local testing workflow

See commits b7c5483 through e4867da for complete fix history.

## Jan 25, 2025 - First User Onboarding (Evening)

### Critical Database Schema Bug
**Symptom:** Onboarding appeared to complete successfully with confirmation message, but data wasn't persisting. Users forced to re-onboard on every interaction. Scheduled messages never sent.

**Root cause:** Missing `last_prompt_date` column in database schema
- Code referenced `last_prompt_date` in `update_user()` function (db.py:110)
- Column didn't exist in schema.sql or via migration
- SQLite error was silently swallowed by Discord button callback handlers
- No error appeared in logs until explicit try/catch added to onboarding flow

**Debugging process:**
1. Railway volume showed 0 bytes usage → database writes failing
2. Added `KODAK_LOG_LEVEL=DEBUG` environment variable
3. Added error handling to onboarding completion callbacks
4. Error revealed: `"no such column: last_prompt_date"`

**Fixes applied (commits ab6fd82, 7940c82, fbff1b1):**
- Added error logging to `OnboardingFlow._on_wait()` and `_on_start_now()`
- Added `last_prompt_date` column to schema.sql
- Added migration in `db.py` to update existing databases
- Added `last_opener` to `ALLOWED_USER_COLUMNS` (was causing warnings)

**Key lesson:** Discord interaction callbacks silently swallow exceptions. Always wrap critical operations in try/catch with explicit logging.

**Verification:**
- Database now persists between sessions
- Railway volume shows usage (database file exists)
- Scheduled messages delivered at correct timezone-aware times
- Logs show: `"User {id} completed onboarding: {personality}, {time} {timezone}"`

### Remaining Work
See ROADMAP.md Phase 0 for outstanding items.
