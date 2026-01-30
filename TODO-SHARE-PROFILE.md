# Share Profile Issues

Deployed 2026-01-30. Core functionality works but UX issues found.

## Issues

### 1. ~~`/share-me` alias not responding~~ RESOLVED

**Resolution:** Removed broken aliases. The delegation pattern (calling another command function directly) doesn't work in discord.py - commands that do this fail silently.

**Removed:**
- `/share-me` (was alias for `/share-profile`)
- `/share-values` (was alias for `/share-themes`)
- `/values-history` (was alias for `/themes-history`)

**Working aliases (use inline code duplication instead):**
- `/values` (duplicates `/themes` logic) - works fine

**Lesson:** Don't use `await other_command(interaction)` pattern for aliases. Either duplicate the code or don't have aliases.

### 2. File download UX issues

**Symptom:** User couldn't download the .txt file attachment. Clicking "Download" did nothing. Preview was truncated with "(67 lines left)".

**Workaround:** User expanded window and copy/pasted from the preview.

**Possible solutions:**
- **Option A:** Send as message text instead of file (but Discord has 2000 char limit)
- **Option B:** Send as multiple messages if content is long
- **Option C:** Send as code block (better formatting, still has limits)
- **Option D:** Keep file but also include a "preview" in the message
- **Option E:** Offer both formats - file for full content, message for quick preview

**Recommendation:** Option E - send a short preview in the message body + the full file attachment. Users who can't download can at least see the highlights.

## Next Steps

1. Debug the alias issue - check if other aliases work
2. Decide on UX improvement approach
3. Implement fix
4. Re-deploy and test

## Context

- `/share-profile` generates a human-readable .txt with beliefs + values
- Designed for sharing with friends (no journal entries included)
- First user tried to share with a friend, hit these issues immediately
