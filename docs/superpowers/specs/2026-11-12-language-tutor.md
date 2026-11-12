# 2026-11-12 Language Tutor Spec

## Summary

Delta vs the 2026-10-26 spec. A chat can now carry its own pasted course
material. The material is injected into the system prompt on every turn, so the
tutor reads it before replying and uses it for the rest of the conversation.
Editing or clearing the material changes the next reply immediately; no restart
or session reset is needed. The composer toolbar also gains a Back to top
button.

---

## Problem

Learners often work from a specific chapter, article or vocabulary list. The
existing prompt only knows the native/target language pair and generic rules, so
the tutor had no way to follow the user's actual course. The material also needs
to be editable at any time, and every chat should be able to have different
material — or none at all.

## Design

### Storage

- Each chat session owns one optional Markdown file:
  `data/{lang}/chats/{session_id}/material.md`.
- `DataStore.load_chat_material()` returns `""` when the file is missing.
- `save_chat_material()` trims and writes the text; a blank value delegates to
  `clear_chat_material()`, which deletes the file.
- Because the file lives inside the session folder, deleting a chat removes its
  material with the rest of the session.

### Prompt assembly

`PromptBuilder.chat_system_prompt()` accepts an optional `course_material`.
Non-empty material is inserted after the language pair and before `Rules:`:

```text
## Course material
The learner pasted the following course material for this conversation.
Read it before replying and treat it as the primary source ...

<course_material>
...
</course_material>
```

The instructions tell the tutor to:

- use the material's vocabulary, grammar, examples and progression;
- reuse its words and structures in practice sentences;
- avoid contradicting it or inventing inconsistent content;
- help with outside questions but make clear they are outside the material;
- not recite the material unless asked.

Empty or whitespace-only material produces no section at all.

### Length limit

The prompt copy is capped at `MAX_COURSE_MATERIAL_CHARS = 20_000`. The stored
file keeps the full text. When the cap is exceeded:

- the model receives only the first 20,000 characters;
- the prompt includes `[Material truncated: showing the first 20,000 of N
  characters.]`;
- the editor shows a warning with the same numbers.

This keeps long textbook chapters from silently pushing recent conversation out
of the model's context window.

### Refresh semantics

`ChatService.send_message()` and `ChatService.stream_message()` call
`load_chat_material()` every time they build a system prompt. There is no cached
material and no material history in the message list. Saving or clearing the
editor therefore affects the very next turn, including mid-conversation.

### Chat UI

- A 📖 button sits in the bottom toolbar, directly beside the 💡 suggestions
  toggle and right-aligned above the composer.
- It opens a card above the transcript with a collapsed-label text area, a live
  character count, and `Save material` / `Clear material` actions.
- The button is highlighted when material exists, and the title area shows
  `📖 Course material · N characters`, adding `(first 20,000 used)` when
  truncated.
- The editor is per-session. Switching chats closes the previous editor view;
  drafts are keyed by session so another chat's material is never shown.
- The material can be empty, which is the default for every new or existing
  chat.
- The toolbar uses a horizontal container with `width: auto` button wrappers, so
  the book, bulb and up-arrow pills stay side by side instead of stretching to
  full width.

### Back to top

- A ⬆️ button renders after the 💡 toggle in the same toolbar.
- Clicking it sets a one-shot session flag and reruns. On the next render,
  `ui/components/scroll_top.py` pops the flag and injects a script through
  `st.html(..., unsafe_allow_javascript=True)`.
- The script calls `scrollTo({ top: 0 })` on
  `section[data-testid="stAppScrollToBottomContainer"]` (the app's main scroll
  pane) and on the window. It runs on the next animation frame and again after
  150ms and 500ms, because Streamlit may restore its chat scroll position after
  the rerun.
- The button performs no model or data work; it only affects the browser scroll
  position.

## Behaviour

- New chats start with no material and behave as before.
- Pasting material and saving changes the next tutor reply only for that chat.
- Clearing material immediately removes the section from future system prompts.
- Material follows the session through renames and is deleted with the session.
- Long material is usable but explicitly truncated in both the UI and prompt.
- ⬆️ returns the main pane to the top in long conversations.

## Scope

The material is applied to the Chat page and any chat session opened there.
Structured Lesson generation prompts are unchanged; a lesson-created session can
still receive material if it is opened as a chat.

## Testing

- `make test`: **160 passed**
- `make lint`: clean
- Streamlit `AppTest` smoke run:
  - one 📖 button and no exceptions on the Chat page;
  - opening the editor loads the saved material;
  - editing and saving writes the new value to `material.md`.
- Headless Chrome at 1440×1000, with a 40-message conversation:
  - 📖, 💡 and ⬆️ render side by side in the bottom toolbar;
  - clicking ⬆️ moved the main scroll container from `scrollTop=2945` to `0`;
  - the top of the conversation was visible afterwards.
- Unit coverage:
  - material round-trip and empty-save clearing;
  - per-session isolation;
  - prompt inclusion, omission and truncation;
  - streaming and non-streaming chat paths both receive the session material;
  - the scroll flag is set, the script is injected once, and the flag is cleared.

## Rationale

User request (2026-11-12): paste course material, have the tutor read it first in
the system prompt, use it in the following conversation, and allow the material
to change at any time with the prompt refreshing accordingly. Per-chat scope was
chosen so different conversations can follow different chapters without a
separate material library. A 20,000-character prompt cap balances fidelity
against the model's context budget. The 📖 toggle was moved from the title row
into the composer toolbar on the same day so it sits beside 💡 and the pair reads
as one compact action group. A right-rail experiment was reverted at the user's
request, returning the editor above the transcript. The ⬆️ button was added to
the same toolbar because long conversations leave the pinned composer far from
the start of the chat.
