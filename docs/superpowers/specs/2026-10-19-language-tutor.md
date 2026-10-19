# 2026-10-19 Language Tutor Spec

## Summary

The Word List "Browse" tab is now a card grid instead of a vertical stack of
expanders. Each saved word is a self-contained card that surfaces the most
useful information at a glance and tucks the long tail into an expander.

Delta vs 2026-09-22 spec (which only covered clearing word suggestions on new
chat): this is a presentation-only change to `ui/pages/word_list.py`; no
service, data-store, prompt, chat, or lesson behavior changes.

## Changes

### Card layout

- Words are laid out three per row. Each row is rendered with its own
  `st.columns(3)` call so cards on the same row start at the same vertical
  position; card heights follow their content.
- Cards are keyed containers (`wordcard_<word id>`), styled through the
  `st-key-` class Streamlit adds. The card shell uses
  `var(--secondary-background-color)` for its surface, a subtle border, 16px
  radius, soft shadow, and a 2px hover lift with an accent-tinted border.
- Long words wrap (`overflow-wrap: anywhere`) rather than widening the grid.

### Card content

- Header row: word in large bold text, reading in muted small text (kanji words
  only, unchanged rule), translation underneath, and the existing 🔊 TTS button
  in a narrow right column.
- Pills: part of speech, formality, and proficiency level; tags render as
  accent-coloured `#tag` pills. Empty and `"-"` values are skipped.
- Body: definition and the first example sentence.
- `More details` expander: synonyms, collocations, related words, conjugations,
  language-specific info, grammar notes, and any additional examples.
- Footer: review stats caption (✅/❌ counts and last-reviewed date), the
  mark-reviewed/unreviewed button, and the delete button with the existing
  inline confirmation flow.

### Filtering

- Search and tag filter are unchanged. A `"N words"` caption is shown below the
  filters, and an info message is shown when filters match nothing.

### Safety

- Dynamic text inserted into card markup is HTML-escaped (`html.escape`) to
  avoid broken markup or injection from model-generated word data.

## Rationale

User request (2026-10-19): optimize the Word List layout and make it look
card-like and pretty. Cards make better use of the wide layout, expose the word
and translation without an extra click, and keep secondary information one
click away.

## Correction note

No correction to a prior dated doc. `_format_word_display` is retained for
callers that need the combined `word(reading)` form, but the card header renders
the word and reading as separate styled elements.
