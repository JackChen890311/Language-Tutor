# 2026-10-20 Language Tutor Spec

## Summary

Fixes the missing in-app theme switcher and makes theme changes instant. Later
the same day, Word List Browse gained sorting and extra filters.

Delta vs the 2026-10-19 spec: the main menu is available again, the custom CSS
emits both palettes instead of one, and shadow tokens are split into colours and
offsets. The theme change made no service, data, prompt or model changes; the
Word List addition below adds a read-only service helper only.

## Problem

Two issues combined:

1. `ui/theme.py` hid `#MainMenu` along with Streamlit's deploy button and status
   widget, and `client.toolbarMode = "minimal"` hid the toolbar entirely. Users
   had no way to reach System / Light / Dark from inside the app.
2. Even once the menu is reachable, Streamlit applies a client-side theme switch
   without rerunning the script. Tokens were generated from
   `st.context.theme.type` at render time, so the custom markup kept the previous
   palette until some other interaction triggered a rerun (the native widgets
   changed immediately, producing a half-themed screen).

## Design

### Menu

- `toolbarMode = "viewer"` keeps the main menu while omitting developer actions.
- CSS hides only `stAppDeployButton`, `stStatusWidget` and `footer`.
- `#MainMenu button` uses the muted text colour, a soft accent hover and the
  shared button radius.

### Theme-reactive tokens

`_token_css()` emits each token as:

```css
--lt-bg: light-dark(#FBFAF8, #141310);
```

`light-dark()` resolves against the used `color-scheme`, which Streamlit sets on
`.stApp` (`light` or `dark`) for both automatic and manually selected themes.
Because the value is resolved by the browser, switching from the ⋮ menu updates
custom markup immediately, with no rerun and no server round trip.

Tokens cover backgrounds, surfaces, borders, text, muted text, accent variants,
on-accent/on-danger, success/danger variants and the ring track.

### Shadows

`light-dark()` only accepts `<color>`, so the former full-shadow tokens were
split:

| Token | Light | Dark |
|---|---|---|
| `--lt-shadow-color` | `rgba(31, 27, 22, 0.06)` | `rgba(0, 0, 0, 0.40)` |
| `--lt-shadow-hover-color` | `rgba(31, 27, 22, 0.14)` | `rgba(0, 0, 0, 0.55)` |

Rules use `0 1px 2px var(--lt-shadow-color)` and
`0 12px 28px var(--lt-shadow-hover-color)`. The hover offset is now shared by
both themes (previously 28px light / 32px dark) in exchange for a single
theme-aware colour.

### Removed API

`palette()` and `is_dark()` are gone. Pages and components must not branch on the
active theme; all theme decisions live in CSS. `st.context.theme.type` is still
available if a future feature needs it, but it is not used for styling.

## Behaviour

- System / Light / Dark are available from the ⋮ menu.
- Selecting a mode immediately restyles native widgets (Streamlit) and custom
  markup (our tokens).
- The menu icon inherits the muted colour and gains an accent hover.
- Theme choice persists in the browser (`localStorage`), independent of the OS
  setting.

## Testing

- `make test`: 133 passed.
- `make lint`: clean.
- Manual headless-Chrome checks:
  - menu contains System / Light / Dark;
  - light → dark and dark → light update `.stApp` background, hero background,
    card surfaces and text colours without a rerun;
  - `.stApp` `color-scheme` matches the selected mode.
- New unit tests assert that every token has a `light-dark()` pair and that
  shadow tokens are colours, not full shadow declarations.

## Compatibility

`light-dark()` needs `color-scheme` support: Chrome 123+, Safari 17.5+, Firefox
120+. The app already targets a current macOS browser and Streamlit 1.57.

## Word List sorting and filtering

### Problem

Word List → Browse only supported free-text search and tag pills. Users could
not reorder the list, isolate words due for review, or narrow it to one
proficiency level, which became awkward as the saved list grew.

### Design

Filtering and ordering are service concerns, not page logic.
`filter_and_sort_words()` is a pure helper; `WordListService.browse()` loads the
list and applies it. It accepts stable keys rather than UI labels:

| Control | Keys |
|---|---|
| Review status | `all`, `due`, `never`, `reviewed` |
| Sort | `newest`, `oldest`, `az`, `za`, `most_reviewed` |
| Tag | `"All"` or a tag string |
| Level | `"All"` or a proficiency value |
| Query | matched against word and reading |

- **Due** means never reviewed or last reviewed more than the existing
  `STALE_DAYS` (7) ago. `is_word_due()` is now the single definition used by the
  Browse filter, `has_stale_words()` and `get_stale_words()`, so the review
  queue and sidebar badge stay consistent.
- **Newest/oldest** order by `added_date`, with insertion order as the tie-break
  so same-day additions are still deterministic.
- **A → Z / Z → A** sort by `reading` when present, falling back to `word`. This
  gives useful ordering for kanji words instead of Unicode code-point order.
- **Most reviewed** orders by `correct + incorrect` attempts, newest-added first
  on ties.

In the Browse filter card:

1. Search and Sort by share one row.
2. Review status renders as pills; when the list contains more than one
   proficiency level, Level pills render beside it.
3. Tags remain their own pills row and only appear when tags exist.

The section caption shows `N of M words` while any filter is active. The
no-matches state names search, tag, level and review filters as possible causes.

### Behaviour

- Changing any control reruns the page and updates the card grid immediately.
- Search, tag, level and review filters combine (logical AND).
- The selected sort applies after filtering.
- Defaults are Search empty, Sort by Newest first, Review status All, Level All,
  Tags All.
- Filter state persists in session state under `wordlist_*` keys across section
  switches.

### Testing

- `make test`: 151 passed.
- `make lint`: clean.
- Streamlit `AppTest` smoke run verified control rendering, newest/A–Z ordering,
  the Due filter, combined review-status + level filters, tag filtering, and
  Most reviewed ordering. No runtime exceptions.
