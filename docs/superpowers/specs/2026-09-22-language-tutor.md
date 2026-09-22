# 2026-09-22 Language Tutor Spec

## Summary

Starting a new chat ("➕ New Chat") now clears the shared word-suggestion
list, so suggestions left over from another chat (or lesson) no longer
carry over into the fresh session.

Delta vs 2026-09-19 spec (which only covered session auto-rename): no
changes to chat streaming, TTS/STT, title generation, or manual rename
behavior.

## Changes

### ui/components/word_chip.py

**New:** `clear_word_suggestions() -> None`
- Sets `st.session_state["word_suggestions"] = []`.
- Single place to reset the global list owned by `get_word_suggestions()` /
  `add_word_suggestions()`.

### ui/pages/chat.py

**Behavior changes:**
- "➕ New Chat" handler calls `clear_word_suggestions()` after creating the
  new session and popping `renaming_session`, before `st.rerun()`.
- Session switching (`sel_`) and lesson flows are intentionally untouched —
  only an explicit new chat resets the list, preserving the continuous
  learning-aid behavior elsewhere.

## Rationale

User request (2026-09-22): when starting a new chat, clear existing word
suggestions which may be from another chat. Root cause is the single global
`st.session_state["word_suggestions"]` list (introduced as a deliberate
continuous-aid decision — see 2026-07-09 spec) surviving across sessions.
The fix resets it exactly at new-chat creation, which is the point where
stale cross-chat suggestions are unambiguously unwanted.

## Correction note

No correction to a prior dated doc — this behavior (clear-on-new-chat) is a
new product decision that narrows the earlier "one continuous list"
intent, not a fix for an inaccuracy in an earlier spec.
