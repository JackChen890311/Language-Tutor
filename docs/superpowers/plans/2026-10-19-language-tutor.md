# 2026-10-19 Language Tutor Plan

## Features Implemented

- [x] Redesigned the Word List "Browse" tab from stacked expanders into a card grid
- [x] Three cards per row, with rows rendered together so card tops line up
- [x] Card header shows the word, kanji reading, translation, and TTS button
- [x] Metadata rendered as pills (part of speech, formality, proficiency level, tags)
- [x] Definition and first example shown directly on the card
- [x] Secondary details (synonyms, collocations, related words, conjugations,
      language-specific info, grammar notes, extra examples) moved into a
      per-card "More details" expander
- [x] Review stats, review toggle, and delete-with-confirmation kept on each card
- [x] Added unit tests for the metadata pill helper

## Changes Made

### ui/pages/word_list.py

- Added `_CARD_CSS` describing the card shell (surface background, border,
  radius, shadow, hover lift) and card typography/pills. Card containers use
  `st.container(key=f"wordcard_{id}")` so CSS can target
  `div[class*="st-key-wordcard_"]`.
- `_render_browse` now renders words in rows of three `st.columns`, preserving
  the existing search and tag filtering.
- Extracted `_render_word_card`, `_pills_html`, `_render_details`, and
  `_render_card_actions` from the old inline expander body.
- Added `_esc` so word/translation/definition text is HTML-escaped before being
  interpolated into custom markup.
- Added a result count caption and a "no words match your filters" empty state.
- All existing behavior is preserved: TTS playback, mark reviewed/unreviewed,
  delete confirmation flow, and reading shown for kanji words.

### tests/test_word_list_page.py

- `test_pills_include_metadata_and_tags`
- `test_pills_skip_missing_or_dash_values`

## Testing Performed

- `make test` (`uv run pytest`): 111 passed (109 existing + 2 new)
- Ruff check + format on the changed files: clean
- Visually verified with headless Chrome at 1600px wide: three cards per row,
  no horizontal overflow, dark- and light-theme backgrounds both readable
- Note: repo-wide `make lint` currently flags the pre-existing, untracked
  `ui/theme.py` for formatting; that file is unrelated to this change and was
  left untouched.
