# 2026-11-12 Language Tutor Plan

## Features Implemented

- [x] Added per-chat course material: each chat session can hold its own pasted
      chapter, article, vocabulary list or notes
- [x] Made course material optional; a session with no material behaves exactly
      as before
- [x] Injected the material into the chat system prompt as a dedicated
      `## Course material` section, before the tutor rules
- [x] Rebuilt the system prompt from disk on every turn, so saving or clearing
      material takes effect on the next message without restarting anything
- [x] Capped the prompt copy at 20,000 characters and told both the model and
      the user when truncation happened
- [x] Added a right-rail editor with a character count, save, clear and close
      actions
- [x] Added a 📖 toggle in the bottom toolbar, directly beside the 💡
      suggestions toggle; it opens that editor
- [x] Reused the word-suggestion rail layout so the editor appears on the right
      and can share the column with suggestions when both are open
- [x] Shown an active-material caption and highlight on the 📖 toolbar button
      when the current chat has material
- [x] Stored the material as Markdown inside the session folder, so deleting a
      chat also deletes its material
- [x] Added unit coverage for storage isolation, prompt inclusion/omission,
      truncation and per-session prompt assembly

## Changes Made

#### data_store/data_store.py

- `load_chat_material()`, `save_chat_material()` and `clear_chat_material()`
  read and write `data/{lang}/chats/{session_id}/material.md`.
- Blank or whitespace-only saves clear the file, so an empty editor means no
  material.

#### services/prompt_builder.py

- Added `MAX_COURSE_MATERIAL_CHARS = 20_000`.
- `chat_system_prompt()` gained an optional `course_material` argument.
- `_course_material_section()` wraps non-empty material in
  `<course_material>…</course_material>`, instructs the tutor to treat it as the
  primary source, and appends a truncation note when the cap is exceeded.

#### services/chat_service.py

- `send_message()` and `stream_message()` load the current session material and
  pass it to `chat_system_prompt()`. Both the text and vision paths receive it.

#### ui/pages/chat.py

- Added a 📖 toggle to the bottom toolbar, directly beside the 💡 suggestions
  toggle.
- The editor renders in the right rail, matching the word-suggestion column.
  The column opens when either the editor or the suggestions rail is active,
  and both stack when both are open.
- `_render_material_editor()` provides a 260px text area, live character count,
  over-limit warning, `Save material`, `Clear material` and `✕` close actions.
- Saving increments a per-session editor revision so the widget reloads the
  stored value without leaving unsaved widget state behind.
- The action buttons stack vertically to fit the narrow rail.

#### ui/theme.py

- `chat_toolbar` is now a horizontal, right-aligned container so the 📖 and 💡
  pill buttons sit side by side instead of stacking.

#### tests/

- `test_data_store.py`: round-trip, per-session isolation and empty-save clears.
- `test_prompt_builder.py`: material included, empty material omitted, long
  material truncated with counts.
- `test_chat_service.py`: material reaches the system prompt in both streaming
  and non-streaming paths, and is not shared between sessions.

#### README.md

- Added the course-material feature bullet and noted `material.md` in the chat
  data layout.

### Testing Performed

- `make test`: **158 passed**
- `make lint`: clean
- Streamlit `AppTest` smoke run against a temporary data directory:
  - Chat page renders with no exceptions;
  - 📖 opens the editor and loads the saved material;
  - editing and saving updates `material.md`;
  - no runtime exceptions.
- Headless Chrome at 1440×1000: 📖 and 💡 are 15px apart in the bottom
  toolbar, right-aligned above the composer; 📖 is highlighted when material
  exists; the editor card renders in the right rail, and its text area and
  stacked action buttons fit the 213px column.

### Commit

- `feat: add per-chat course material` (`f7334b0`)
- `ui: move course material toggle into composer toolbar` (`543537b`)
- `ui: move course material editor into right rail` (`69e4e41`)
