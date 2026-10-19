# 2026-10-19 Language Tutor Plan

## Phase A — Word List card grid (morning)

### Features Implemented

- [x] Redesigned the Word List "Browse" tab from stacked expanders into a card grid
- [x] Three cards per row, with rows rendered together so card tops line up
- [x] Card header shows the word, kanji reading, translation, and TTS button
- [x] Metadata rendered as pills (part of speech, formality, proficiency level, tags)
- [x] Definition and first example shown directly on the card
- [x] Secondary details moved into a per-card "More details" expander
- [x] Review stats, review toggle, and delete-with-confirmation kept on each card
- [x] Added unit tests for the metadata pill helper

## Phase B — Full visual overhaul (afternoon)

### Features Implemented

- [x] Added a single design system in `ui/theme.py` (tokens + global CSS + presentational helpers)
- [x] Added `.streamlit/config.toml` with automatic light/dark themes, amber accent,
      warm neutral surfaces, system font stack with CJK fallbacks, and soft radii
- [x] Rebuilt the sidebar: brand mark, language-pair pill, icon navigation with an
      active amber rail, stale-word count, streak and model-status footer
- [x] Chat sessions now appear above the footer, with an active highlight and
      left-aligned rows
- [x] Home: time-based greeting hero, four stat cards, 7-day activity strip,
      quick-action cards, recent-chat cards, optional-model hint
- [x] Lesson: difficulty pills, topic picker card, structured/free-conversation
      stepper, sticky "Words to learn" panel
- [x] Chat: suggestion chips with one-tap save, bubble styling, empty state,
      rename card, inline TTS controls, styled chat input
- [x] Word List: segmented Browse / Add Word / Review switcher, search card,
      tag pills, aligned 3-column card rows, flashcard review redesign
- [x] Test: difficulty pills, question cards with Q badges and progress,
      score-ring result card, colour-coded answer review, history expanders
- [x] Settings: language-pair card, 2×2 model-status grid with badges and
      download commands, red-tinted danger zone with confirmation flow
- [x] Components: word chips, stream shimmer placeholder, speakable-sentence
      blocks, empty states, chips/tags
- [x] Added `LanguageService.get_active_dates()` so the activity strip reflects
      streaks, reviews, quizzes and chats
- [x] Added `ui/labels.py` for shared language names/flags
- [x] Added README screenshot gallery and updated feature/version badges
- [x] Bumped the Streamlit floor to 1.57 (required by `st.pills`,
      `st.segmented_control`, `st.context.theme`, keyed containers)

### Changes Made

#### Theme and configuration

- `.streamlit/config.toml`: light and dark theme blocks, amber primary
  (`#A85E12` light / `#D9913C` dark), warm surfaces, `baseRadius` /
  `buttonRadius`, `showWidgetBorder = false`, `showSidebarBorder = false`,
  `toolbarMode = "minimal"`, system font stack.
- `ui/theme.py`: `Palette` dataclass and `LIGHT` / `DARK` palettes; tokens are
  emitted as CSS custom properties for the active Streamlit theme
  (`st.context.theme.type`); global CSS for shell, typography, sidebar, cards,
  chips, steppers, score rings, chat bubbles, expanders, animations and
  reduced-motion fallbacks; helpers `page_header`, `section_header`, `hero`,
  `empty_state`, `stat_grid`, `activity_strip`, `stepper`, `score_ring`,
  `chip`, `tag`; pure helpers `greeting_for_hour`, `activity_days`.
- `ui/labels.py`: language names, flags and pair label.

#### Pages

- `ui/app.py`: sidebar split into top (brand/nav/LLM guard) and footer
  (streak/models) so page-specific sidebar content slots in between; routes
  unchanged.
- `ui/pages/home.py`, `lesson.py`, `chat.py`, `word_list.py`, `test.py`,
  `settings.py`: restyled with the helpers above, no inline CSS.
- `ui/pages/word_list.py`: Phase A card markup retained, but `_CARD_CSS` and
  `wordcard_`-keyed containers were replaced by the shared `ltcardhover_`
  surface and `.lt-word` / `.lt-example` / `.lt-tag` helpers; rows now render
  three cards at a time so tops align.
- `ui/components/word_chip.py`: suggestion chips are compact keyed cards with a
  one-tap save button and escaped text.
- `ui/components/stream_display.py`: animated shimmer skeleton instead of
  animated dots.
- `ui/components/audio_controls.py`: speakable sentences render inside a
  keyed accent block with an inline play button.

#### Services and tests

- `services/language_service.py`: added `get_active_dates(lang, days=7)`,
  deriving activity from the streak, word reviews, quiz attempts and chat
  sessions.
- `tests/test_theme.py`: greeting boundaries, activity strip assembly, malformed
  dates, window size, language labels.
- `tests/test_language_service.py`: active-date tests for streaks, reviews,
  quizzes/chats and the 7-day window.
- `tests/test_word_list_page.py`: kept the metadata-pill tests and updated the
  expected `#tag` rendering.

### Testing Performed

- `make test` (`uv run pytest`): **126 passed**
- `make lint` (`ruff check` + `ruff format --check`): clean
- Headless Chrome at 1440×900 in both light and dark themes: Home, Lesson,
  Chat (empty and active conversation), Word List (Browse and Review),
  Test (setup and question cards), Settings (model grid and danger zone)
- Streamlit `AppTest` runs for every page plus stateful views: active lesson
  (structured and conversation), quiz results, word review, add-word, chat with
  history. This caught a missing `word_list` argument in the lesson word panel,
  which is fixed.
- Screenshots committed under `docs/screenshots/` and embedded in `README.md`.

### Notes

- The version of this plan committed earlier today described `_CARD_CSS` and
  `var(--secondary-background-color)`. Both were superseded by Phase B:
  Streamlit 1.57 no longer exposes global theme CSS variables, so the design
  system now emits its own `--lt-*` tokens per active theme. The Phase A feature
  list above is kept as history.
- No service, data-store, prompt or model behavior changed apart from the new
  read-only `get_active_dates` helper.
