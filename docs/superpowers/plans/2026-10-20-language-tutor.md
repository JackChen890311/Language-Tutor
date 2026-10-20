# 2026-10-20 Language Tutor Plan

## Features Implemented

- [x] Restored Streamlit's main menu so the theme can be switched from the app
      (System / Light / Dark)
- [x] Styled the ⋮ button to match the amber design system instead of leaving
      Streamlit's default chrome
- [x] Made every custom colour token theme-reactive via CSS `light-dark()`, so a
      theme switch applies instantly without waiting for a rerun
- [x] Split shadow tokens into theme-aware colours plus explicit offsets
      (offsets cannot be passed through `light-dark()`)
- [x] Added regression tests for token pairing and shadow definitions
- [x] Documented the in-app theme switch in the README feature list

## Changes Made

### .streamlit/config.toml

- `client.toolbarMode` changed from `"minimal"` to `"viewer"`.
  `"minimal"` hides the whole toolbar, including the main menu and therefore the
  theme picker. `"viewer"` keeps the menu while still hiding developer actions,
  and the deploy button remains hidden by CSS.

### ui/theme.py

- Removed `#MainMenu` from the CSS hide rule; kept hiding the deploy button,
  status widget and footer.
- Added hover/colour styling for `#MainMenu button` and made
  `[data-testid="stMainMenu"]` visible.
- `_token_css()` now emits `light-dark(light, dark)` for all 19 tokens using the
  existing `LIGHT` and `DARK` palettes.
- Removed `palette()` / `is_dark()` — pages never branch on the active theme.
- `LIGHT.shadow` / `DARK.shadow` (and the hover variants) are now colours, not
  complete shadow values; all 11 `box-shadow` rules use
  `0 1px 2px var(--lt-shadow-color)` and
  `0 12px 28px var(--lt-shadow-hover-color)`.

### tests/test_theme.py

- Added `test_tokens_switch_with_color_scheme_without_rerun` (every token has a
  light/dark pair, spot-checks the base, text and accent values).
- Added `test_shadow_tokens_are_colours_not_full_shadows`.

### README.md

- Noted that light/dark can be switched instantly from the ⋮ menu.

## Testing Performed

- `make test`: **133 passed**
- `make lint`: clean
- Headless Chrome at 1440×900:
  - confirmed the ⋮ menu lists System / Light / Dark
  - switched light → dark and dark → light with the menu open; the app
    background, hero, cards and text all changed immediately with no rerun
  - verified `color-scheme` flips on `.stApp` and the menu follows the theme

## Notes

- This corrects the 2026-10-19 spec's assumption that `st.context.theme.type`
  alone is enough to keep custom markup in sync. It is evaluated at render time,
  but choosing a theme in the client menu does not trigger a rerun, so tokens
  baked from `st.context` stayed on the previous palette until the next
  interaction. Emitting both palettes with `light-dark()` removes that gap.
- `light-dark()` requires a modern browser (`color-scheme` support: Chrome 123+,
  Safari 17.5+, Firefox 120+), which matches the app's macOS + Streamlit 1.57
  baseline. `stApp` receives an explicit `color-scheme` from Streamlit in both
  modes.

## Phase C — Word List sorting and filtering (evening)

### Features Implemented

- [x] Added a sort control to Word List → Browse: Newest first, Oldest first,
      A → Z, Z → A, and Most reviewed
- [x] Added a review-status filter: All, Due, Never reviewed, Reviewed
- [x] Added a proficiency-level filter when the list contains more than one level
- [x] Kept search and tag pills, and combined every control in the filter card
- [x] Moved filtering/sorting into `WordListService.browse()` via a pure
      `filter_and_sort_words()` helper
- [x] Reused one `is_word_due()` definition for the review filter and the
      existing stale-word badge/queue
- [x] Added service and page tests for the new behaviour
- [x] Verified the controls headlessly with Streamlit `AppTest`

### Changes Made

#### services/word_list_service.py

- Added `filter_and_sort_words(words, *, query, tag, level, review_status,
  sort, today)`, a pure helper accepting `review_status` keys `all` / `due` /
  `never` / `reviewed` and `sort` keys `newest` / `oldest` / `az` / `za` /
  `most_reviewed`.
- Added `is_word_due(word, today)`, the single definition of "due": never
  reviewed or last reviewed more than `STALE_DAYS` ago.
- Added `WordListService.browse(lang, ...)` as the UI-facing entry point.
- `has_stale_words()` and `get_stale_words()` now use `is_word_due()`, so the
  Browse "Due" filter and the sidebar review count cannot disagree.
- Newest-first ordering uses `added_date` plus insertion order, so words saved on
  the same day appear most-recent first. Alphabetical modes sort by `reading`
  when present and fall back to `word`.

#### ui/pages/word_list.py

- Browse filter card now has a Search + Sort by row, a Review status row (with a
  Level row beside it when more than one level exists), and the existing Tags
  pills.
- UI labels map to stable service keys through `_SORT_OPTIONS` and
  `_REVIEW_OPTIONS`.
- The section caption shows `N of M words` when filters narrow the list, and
  the no-matches empty state mentions all filter types.

#### tests

- `tests/test_word_list_service.py`: due-date boundary and never-reviewed
  handling, query/tag/level combinations, review-status filters,
  newest/oldest, alphabetical-by-reading, most-reviewed ordering, and a
  `browse()` integration test.
- `tests/test_word_list_page.py`: option maps stay aligned with the service key
  sets.

### Testing Performed

- `make test`: **151 passed**
- `make lint`: clean
- Streamlit `AppTest` smoke run with three words:
  - default order is newest → oldest
  - A → Z sorts by reading
  - Due excludes a word reviewed the day before
  - review status + level combine, tag filtering works, and Most reviewed
    orders by total attempts

### Commit

- `feat: add sorting and filtering to word list` (`f291ba8`)
