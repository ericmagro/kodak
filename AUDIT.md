# Kodak Pre-Launch Audit

**Date:** January 2026
**Auditors:** Code quality, security, and UX expert panel (synthesized)

---

## Executive Summary

Kodak is **ready for friends launch** with minor improvements recommended. No critical security issues found. The codebase is clean, well-organized, and follows good async patterns. UX is thoughtful with proper onboarding and privacy controls.

**Verdict: Ship it.** Address high-priority items in next iteration.

---

## Code Quality Audit

### Strengths

| Area | Assessment |
|------|------------|
| **Code organization** | ✅ Clean separation: bot.py, db.py, extractor.py, personality.py |
| **Async patterns** | ✅ Proper use of asyncio, parallel extraction with `asyncio.create_task()` |
| **Error handling** | ✅ Graceful API error messages, JSON parse failures handled |
| **Type hints** | ✅ Present on function signatures |
| **Documentation** | ✅ Docstrings on all public functions |

### Issues Found

| Priority | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| 🟡 Medium | **No connection pooling** | db.py | Each DB operation opens/closes connection. Fine for friends launch, but add aiosqlitepool for scale. See [aiosqlitepool](https://github.com/slaily/aiosqlitepool) |
| 🟡 Medium | **Anthropic client is sync** | extractor.py:8 | Using sync `anthropic.Anthropic()` in async context. Works but not optimal. Switch to `anthropic.AsyncAnthropic()` |
| 🟢 Low | **Missing try/except in on_message** | bot.py:182 | Unhandled exceptions could crash message loop. Wrap main logic in try/except. |
| 🟢 Low | **No logging** | All files | Using `print()` for output. Add proper logging for production debugging. |
| 🟢 Low | **DB path is relative** | db.py:9 | Path works but consider making configurable via env var for deployment flexibility. |

---

## Security Audit

### Prompt Injection Risk Assessment

*Source: [OWASP LLM Security](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)*

| Risk | Assessment | Notes |
|------|------------|-------|
| **Direct injection** | 🟢 Low | User messages go to Claude, but Kodak has no privileged actions (no file access, no code execution, no external API calls). Worst case: user gets weird responses. |
| **Indirect injection** | 🟢 N/A | No RAG, no external document fetching |
| **Data exfiltration** | 🟢 Low | System prompt contains other beliefs but these belong to same user. No cross-user data leakage possible. |
| **Privilege escalation** | 🟢 N/A | Bot has no elevated privileges to escalate to |

**Verdict:** Low risk. The bot's limited capabilities mean prompt injection has minimal impact.

### Data Security

| Area | Assessment |
|------|------------|
| **Secrets management** | ✅ Env vars, .env in .gitignore |
| **User data isolation** | ✅ All queries filter by user_id |
| **SQL injection** | ✅ Parameterized queries throughout |
| **Data deletion** | ✅ `/clear` does full cascade delete |
| **Export** | ✅ User can export all their data |

### Discord Security

| Area | Assessment |
|------|------------|
| **Token protection** | ✅ In env var, not in code |
| **Permission scope** | ✅ Minimal permissions requested |
| **Command privacy** | ✅ All slash commands are ephemeral |

---

## UX Audit

*Sources: [UXMatters Trust in AI](https://www.uxmatters.com/mt/archives/2025/11/the-design-psychology-of-trust-in-ai-crafting-experiences-users-believe-in.php), [Mind the Product AI Chatbots](https://www.mindtheproduct.com/deep-dive-ux-best-practices-for-ai-chatbots/)*

### Strengths

| Principle | Implementation |
|-----------|---------------|
| **Transparency** | ✅ Periodic belief summaries show what's captured |
| **User control** | ✅ Pause, export, clear, forget commands |
| **Graceful failure** | ✅ Human-friendly error messages |
| **Personality/voice** | ✅ Configurable presets with previews |
| **Onboarding** | ✅ Clear intro, consent implicit in flow |
| **Feedback mechanism** | ✅ Can tell bot beliefs are wrong, use /forget |

### Issues Found

| Priority | Issue | Recommendation |
|----------|-------|----------------|
| 🟡 Medium | **No thumbs up/down on beliefs** | Add reaction-based feedback on belief summaries |
| 🟡 Medium | **No "undo" for forget** | Consider soft-delete with 24hr recovery window (already have soft delete, just need restore command) |
| 🟢 Low | **Ephemeral messages vanish** | Already documented in /help footer. Could add note to onboarding. |
| 🟢 Low | **No confirmation after onboarding personality pick** | User picks personality, then mode, then done. Could show final "You picked X with Y mode" summary. |

---

## Performance Audit

### Current State

| Metric | Assessment |
|--------|------------|
| **API calls per message** | 2-3 (response + extraction + optional relations) |
| **Parallel processing** | ✅ Extraction runs parallel to response |
| **DB queries per message** | ~5-8 (could be reduced with caching) |
| **Message latency** | Dependent on Claude API (~1-3 seconds typical) |

### Scaling Concerns (Not Relevant for Friends Launch)

| Concern | When It Matters | Mitigation |
|---------|-----------------|------------|
| **SQLite write contention** | 50+ concurrent users | Switch to PostgreSQL or add connection pooling |
| **Discord rate limits** | 50 req/sec, 10k invalid/10min | discord.py handles automatically |
| **Anthropic rate limits** | Depends on tier | Add per-user message rate limiting |

---

## Recommendations by Priority

### Before Friends Launch (Do Now)

None required. Ship it.

### After Friends Launch (Next Week)

| Item | Effort | Impact |
|------|--------|--------|
| Switch to AsyncAnthropic | Low | Medium - cleaner async |
| Add basic logging | Low | Medium - debugging |
| Add try/except wrapper in on_message | Low | Medium - stability |

### Before Public Launch (Later)

| Item | Effort | Impact |
|------|--------|--------|
| Connection pooling | Medium | High - performance |
| User rate limiting | Medium | High - cost control |
| Thumbs up/down on summaries | Medium | High - UX feedback |
| PostgreSQL migration | High | High - scale |

---

## Checklist Before Sending Invite

- [x] Bot is online and responding
- [x] DMs work with bot
- [x] Onboarding flow completes successfully
- [x] /map, /beliefs commands work
- [x] /export downloads JSON file
- [x] /clear deletes data
- [x] Welcome message posted in #welcome
- [x] #welcome is read-only
- [x] README is complete and accurate
- [x] .gitignore protects .env
- [x] Repo is public at github.com/ericmagro/kodak

---

## Sources

- [Discord Rate Limits](https://support-dev.discord.com/hc/en-us/articles/6223003921559-My-Bot-is-Being-Rate-Limited)
- [aiosqlite Best Practices](https://aiosqlite.omnilib.dev/)
- [OWASP LLM Prompt Injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [AWS Prompt Injection Best Practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/llm-prompt-engineering-best-practices/best-practices.html)
- [UXMatters - Trust in AI](https://www.uxmatters.com/mt/archives/2025/11/the-design-psychology-of-trust-in-ai-crafting-experiences-users-believe-in.php)
- [Mind the Product - AI Chatbot UX](https://www.mindtheproduct.com/deep-dive-ux-best-practices-for-ai-chatbots/)
- [Designing Trustworthy AI Assistants](https://orangeloops.com/2025/07/9-ux-patterns-to-build-trustworthy-ai-assistants/)
