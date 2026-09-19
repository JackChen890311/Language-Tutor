# 2026-09-19 Language Tutor Spec

## Summary

Chat sessions no longer use sequential "Chat N" names. After the user's first
message, the session is auto-renamed once via LLM to an intent-based title
(e.g. 歌詞翻譯請求, 學習天氣用法) written in `native_lang`. Users can still
manually rename any session afterwards.

Delta vs 2026-08-23 spec (which only covered word-suggestion toggle layout):
no changes to word suggestions, chat streaming, or TTS/STT behavior.

## Changes

### services/prompt_builder.py

**New:** `session_title_prompt(native_lang)`
- Instructs LLM to output ONLY a 4-12 character intent title in `native_lang`,
  hard-capped at 20 characters, no quotes/punctuation/explanation.
- Reuses `_chinese_rule` so zh-TW titles stay in Traditional Chinese / 台灣用語.

### services/chat_service.py

**New:** `generate_session_title(native_lang, user_text) -> str`
- Calls `llm.generate` with the title prompt (`enable_thinking=False`).
- `_clean_title` strips whitespace/quotes/brackets, collapses spaces, caps at
  20 chars, defaults to "新對話".
- Any LLM exception returns fallback = first 15 chars of `user_text`
  (or "新對話" if empty); empty LLM output also falls back. So offline/model
  failure never breaks chat.

### data_store/data_store.py

**New:** `rename_chat_session(lang, session_id, new_name) -> bool`
- Returns False on empty name or unknown session id; otherwise strips and
  truncates to 30 chars, persists to `sessions.json`, returns True.

### ui/pages/chat.py

**Behavior changes:**
- "➕ New Chat" creates sessions named "新對話" (was `Chat {N+1}`).
- On message send, records `is_first_message = len(history_before) == 0`;
  only then (once per session) calls `generate_session_title` + renames.
  Later messages never auto-rename, so manual names are preserved.
- Title header gains ✏️ button → inline `text_input` (max 30 chars) with
  儲存/取消; empty save shows warning and keeps old name.
- Auto-rename is wrapped in try/except so title failure never blocks reply.

## Rationale

User request (2026-09-19): name rooms by intent ("歌詞翻譯請求",
"學習天氣用法") instead of chat1/chat2. Clarified choices applied:
LLM-generated titles (not rule truncation), title language = `native_lang`,
auto-rename exactly once after the first message, manual rename always allowed.

## Correction note

2026-08-23 spec describes the word-suggestion area as a "3-column layout"
while `ui/pages/chat.py` actually renders 4 columns
(`col1..col4` with `(total+3)//4` splits). Left as-is; fix in a later delta
if the 3-column intent is confirmed.
