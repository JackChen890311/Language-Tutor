# 2026-09-22 Language Tutor Plan

## Features Implemented

- [x] Clear shared word suggestions when starting a new chat
- [x] New `clear_word_suggestions()` helper in word_chip component
- [x] Unit tests for clear behavior (non-empty + already-empty)

## Changes Made

### ui/components/word_chip.py
- Added `clear_word_suggestions()` — resets `st.session_state["word_suggestions"]` to `[]`

### ui/pages/chat.py
- "➕ New Chat" handler now calls `clear_word_suggestions()` before `st.rerun()`
- Updated import to include `clear_word_suggestions`

### tests/test_word_chip.py
- Added `test_clear_word_suggestions_empties_shared_list`
- Added `test_clear_word_suggestions_when_already_empty`

## Testing Performed

- Ran `make test` (uv run pytest): 105 passed (103 existing + 2 new)
- Ran `make lint` (ruff check + format): clean
