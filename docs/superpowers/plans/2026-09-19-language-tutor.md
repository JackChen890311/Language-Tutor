# 2026-09-19 Language Tutor Plan

## Features Implemented

- [x] Auto-rename chat session from user intent after first message (LLM-generated)
- [x] Session title prompt in native_lang (4-12 chars, max 20)
- [x] ChatService.generate_session_title with truncation + fallback
- [x] DataStore.rename_chat_session (strip, 30-char cap, bool result)
- [x] Manual rename UI (✏️ + text_input + save/cancel)
- [x] New sessions default to "新對話" instead of "Chat N"

## Changes Made

### services/prompt_builder.py
- Added `session_title_prompt(native_lang)` — title-only, native_lang, 20-char cap

### services/chat_service.py
- Added `generate_session_title(native_lang, user_text)` + `_clean_title` helper
- LLM failure / empty output falls back to first 15 chars of user text

### data_store/data_store.py
- Added `rename_chat_session(lang, session_id, new_name) -> bool`

### ui/pages/chat.py
- New Chat creates "新對話" placeholder
- After first user message only (`len(history_before) == 0`), generate + rename
- Title row with ✏️ button, text_input (max 30), 儲存/取消

## Testing Performed

- Verified prompt contains native_lang and 20-char rule
- Verified LLM title cleaned (e.g. "歌詞翻譯請求"), truncation to 20 chars
- Verified exception fallback and empty-output fallback
- Verified rename success / empty-name reject / unknown-id reject / 30-char cap
- Ran `make test` (uv run pytest): 103 passed
- Ran `make lint` (ruff check + format): clean
