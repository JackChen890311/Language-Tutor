# 2026-10-19 Language Tutor Spec

## Summary

The app now has a single warm, soft-modern visual language. An amber accent
replaces the old blue-purple gradient, every page composes shared components
from `ui/theme.py` instead of shipping its own `<style>` block, and both light
and dark themes are first-class. The Word List keeps the card grid introduced
earlier in the day, restyled to use the shared system.

Delta vs the 2026-09-22 spec (word-suggestion clearing): presentation-layer
rewrite across `ui/`, plus a new read-only activity helper in
`LanguageService`. No prompt, model, storage-schema or chat/lesson/quiz
behavior changes.

---

## Design system

### Theme configuration

`.streamlit/config.toml` defines `[theme.light]` and `[theme.dark]`, so the app
follows the operating system and can also be switched from Streamlit's menu.

| Token | Light | Dark |
|---|---|---|
| Primary | `#A85E12` | `#D9913C` |
| Background | `#FBFAF8` | `#141310` |
| Secondary background / sidebar | `#F3F0EA` | `#181613` |
| Text | `#1F1B16` | `#F2EDE6` |
| Border | `#E4DED4` | `#2E2B25` |
| Link | `#9A5514` | `#E8A44C` |

Shared config: system font stack (`-apple-system`, SF Pro, Segoe UI, Hiragino
Sans, Noto Sans JP, PingFang TC), `baseFontSize = 16`, `baseRadius = 0.9rem`,
`buttonRadius = 0.65rem`, `showWidgetBorder = false`,
`showSidebarBorder = false`, `linkUnderline = false`, `toolbarMode = "minimal"`.
No fonts are downloaded; the app stays local-first.

### CSS tokens

`ui/theme.py` owns every visual decision. It selects `LIGHT` or `DARK` from
`st.context.theme.type` and emits `--lt-*` custom properties on `.stApp`
(`--lt-accent`, `--lt-surface`, `--lt-border`, `--lt-muted`, `--lt-danger`, …)
plus the global stylesheet exactly once per run.

This replaces the earlier approach of styling from Streamlit theme variables:
Streamlit 1.57 themes through Emotion and no longer exposes
`--primary-color` / `--secondary-background-color` to app CSS.

### Helper vocabulary

- `page_header(icon, title, subtitle)` — page title block with an amber icon tile
- `section_header(title, caption, icon)` — section label and optional meta
- `hero(...)` / `empty_state(...)` / `stat_grid(...)` / `activity_strip(...)`
- `stepper(steps, active)` — compact numbered phase rail
- `score_ring(percent, correct, total)` — conic-gradient result ring
- `chip(...)` / `tag(...)` — safe inline markup fragments
- `card` surfaces via keyed containers (`ltcard_*`, `ltcardhover_*`)
- Pure helpers: `greeting_for_hour`, `activity_days`, `esc`

Pages never interpolate unescaped user/model text into custom HTML without
`theme.esc`.

---

## Shell and navigation

- Sidebar: brand mark, "On-device · private" subtitle, language-pair pill,
  icon navigation, stale-word count on Word List, and a footer with streak and
  four model-status dots.
- Navigation keeps the existing `st.session_state.page` routing. Active items
  use an amber tint, amber text and a 3px inset rail; inactive items are
  borderless and tint on hover.
- The sidebar is composed in three calls so page-specific content (chat
  sessions) can slot between navigation and the footer.
- Main content is capped at 1180px and centred; the header/toolbar chrome is
  hidden except Streamlit's minimal menu.
- Buttons share radius, weight and hover lift. Primary buttons use the accent
  with a contrasting label (white in light, near-black ink in dark).

---

## Pages

### Home

- Greeting derived from the local hour, target-language title, streak sentence,
  and three chips (words, lessons, reviewed this week).
- Four stat cards: streak, words saved, lessons completed, reviewed in 7 days.
- 7-day activity strip; active days combine the streak, word reviews, quiz
  attempts and chat-session creation dates via `LanguageService.get_active_dates`.
- Three quick-action cards (Lesson, Chat, Word List) and up to four recent
  chats, each with an Open button that restores the session.
- Optional-model hint when fewer than four model slots are installed.

### Lesson

- Topic picker: proficiency framework label, difficulty pills (previous
  selection is kept per language), custom-topic input, suggestion button and
  Start lesson.
- Suggested topics render as three hover-lift cards with a one-click start.
- Active lesson: topic card with phase caption, Free conversation / Finish
  actions, and a two-step rail (Structured lesson → Free conversation).
- Messages use chat bubbles; the right column holds a sticky "Words to learn"
  chip panel backed by the shared suggestion list.
- Finishing records the lesson and streak, then clears the active lesson.

### Chat

- Session list in the sidebar: New chat, active highlight, per-row delete,
  rendered above the streak/model footer.
- Header row with session title, rename button and a Suggestions toggle showing
  the current count.
- Rename opens a card with Save/Cancel.
- Suggestion panel renders four chips per row; each chip saves immediately.
- Conversation bubbles: assistant on surface, user in an accent tint; assistant
  messages expose per-sentence pronunciation buttons.
- Empty session shows a centred prompt; image upload and voice input are kept
  below the transcript, with the chat input pinned at the bottom.

### Word List

- Segmented control switches Browse / Add Word / Review.
- Browse: search card plus tag pills (when tags exist), then a three-column card
  grid rendered row by row so card tops align. Cards show word/reading,
  translation, metadata and `#tags`, definition, first example, a details
  expander, review stats and Mark reviewed / delete actions.
- Add Word: manual entry with optional reading and tags, then AI enrichment.
- Review: due-word queue with a progress bar and a mode picker (Flashcard,
  Fill-in-the-blank, Sentence construction). Flashcard mode centres the word,
  reveals translation/definition, and records Got it / Missed. Empty queue and
  completion states are explicit.

### Test

- Difficulty pills and a content-width Generate test button; generation streams
  behind the shimmer without revealing answers.
- Question cards with Q badges, radio options and an answered-count progress
  bar.
- Result card with a score ring and Try another test.
- Review uses green/red tinted blocks for correct/incorrect answers with both
  explanations.
- Past attempts list in expanders.

### Settings

- Language pair card with native/target selects and Save.
- Model status grid: badge (Ready/Missing), purpose, model id and the exact
  download command when missing.
- Danger zone card tinted with the danger colour; Clear all history opens an
  explicit confirmation before deleting the language's data.

---

## Components

- `word_chip`: compact keyed chip cards, escaped word/reading, one-tap save.
  Shared merge/clear behavior unchanged.
- `stream_display`: shimmer skeleton while waiting; token streaming with a
  cursor; silent drain for hidden answers.
- `audio_controls`: speakable sentences become accent blocks with an inline
  play button; parsing/escaping behavior unchanged.

---

## Services

`LanguageService.get_active_dates(lang, days=7)` returns sorted ISO dates within
the window that have any activity:

- the consecutive days encoded by the stored streak ending at `last_active`;
- word `review_stats.last_reviewed` dates;
- quiz `tested_at` dates;
- chat session `created_at` dates.

Malformed dates are ignored and the result is clipped to the window.

---

## Testing

- `tests/test_theme.py` — greeting boundaries, activity strip length/today flag,
  duplicate and malformed dates, custom window, language labels.
- `tests/test_language_service.py` — active dates from streaks, reviews,
  quizzes/chats and the window cutoff.
- `tests/test_word_list_page.py` — metadata pills skipped when empty/dash and
  tags rendered as `#tag`.
- Streamlit `AppTest` smoke runs for all six pages and for active lesson,
  quiz-result, review and add-word states.

Result: 126 tests passing; Ruff check and format clean.

## Rationale

User request (2026-10-19): make the UI substantially prettier through a full
design-system pass, using a warm amber accent and working in both light and
dark mode, while keeping everything local. Centralising CSS removes four
scattered style blocks, makes colours theme-aware, and lets every page share the
same cards, headers and empty states.

## Correction note

The earlier same-day Word List spec described `_CARD_CSS`,
`wordcard_`-prefixed containers and `var(--secondary-background-color)`
surfaces. Phase B supersedes that: the cards now use the shared `ltcardhover_`
surface and `--lt-*` tokens emitted by `ui/theme.py`, because Streamlit 1.57 no
longer provides global theme CSS variables. The visual intent of the morning
card grid is unchanged.
