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

### Remaining Work
See ROADMAP.md Phase 0 for outstanding items.
