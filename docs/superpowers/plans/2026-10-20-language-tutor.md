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
