# Language Tutor — Design Update, 2026-07-09

_Supplements `docs/superpowers/specs/2026-07-05-language-tutor-design.md`._

---

## Fix: Chat word suggestions never actually appeared; move word suggestions to a right-side panel on Chat and Lesson

**Bug found:** `ui/pages/chat.py` called `render_word_chips(...)` and then `st.rerun()` on the very next line, inside the same `if final_input:` block. The chip render call never survives past that rerun — nothing about it is stored in `st.session_state`, so on the following script run there's nothing left to redraw. In practice, Chat's word suggestions never appear to the user (at best a single-frame flash before the rerun replaces the page). Lesson didn't have this bug: `active_lesson["word_suggestions"]` is stored in session state and re-rendered unconditionally on every run, so it persists — but each new assistant turn *replaces* the list wholesale rather than accumulating it, so a lesson turn's suggestions are lost the moment the next turn arrives.

**Fix — accumulating, deduped suggestion lists:** `ui/components/word_chip.py` gains a pure helper:

```python
def merge_word_suggestions(existing: list[dict], new: list[dict], cap: int = 10) -> list[dict]:
```

Newest suggestions go to the front; if a word already appears in `existing` (matched by the `word` field), its old entry is dropped and the new one takes the front position instead of creating a duplicate. The merged list is truncated to `cap` (10) entries, so older, unsaved suggestions fall off once the cap is exceeded.

- **Chat:** a new `st.session_state["chat_word_suggestions"]` dict, keyed by chat session id, holds each session's accumulated list. After `chat_svc.commit_message(...)`, the result's `word_suggestions` are merged into that session's list via `merge_word_suggestions` instead of being passed straight to `render_word_chips` and discarded. Switching sessions in the sidebar naturally shows that session's own accumulated list; a brand-new session starts with an empty one.
- **Lesson:** `active_lesson["word_suggestions"]` is now built the same way — both `_start_lesson` (initial merge from an empty list) and `_render_active_lesson`'s continue-turn handler merge the turn's new suggestions into the existing list rather than overwriting it.

**Save removes the word from the list:** `render_word_chips`'s signature changes from `render_word_chips(suggestions, lang, native_lang)` to `render_word_chips(suggestions, lang, native_lang, on_save)`, where `on_save(word: str) -> None` is a caller-supplied callback. On clicking "💾 Save", `render_word_chips` still calls `word_svc.add_word(...)` and `st.toast(...)` as before, then calls `on_save(word)` (so the caller can remove that entry from its own state — the session-keyed dict for Chat, `active_lesson["word_suggestions"]` for Lesson) and finally `st.rerun()` so the panel immediately reflects the removal. `word_chip.py` itself stays ignorant of where the list is stored, keeping it a pure rendering component.

**Chip layout:** since chips now always render in a narrow side column rather than the full-width area below the chat, the internal `st.columns(min(len(suggestions), 3))` grid is removed — chips render as a simple vertical stack, one per row.

## Right-side panel layout on Chat and Lesson

Both `ui/pages/chat.py` and `ui/pages/lesson.py` wrap their main-content rendering in `st.columns([3, 1])`:

- **Chat:** the left column (`col1`) gets the session subheader, the message history loop, and the image uploader. The right column (`col2`) gets a `"💡 Word Suggestions"` subheader followed by `render_word_chips(...)` reading from `chat_word_suggestions[active_session]`. `st.chat_input` and the STT input stay outside/after the two-column block (not nested inside `col1`), so the input bar remains pinned full-width at the bottom of the viewport exactly as it behaves today — this is a deliberate scope decision over nesting it in the chat column, which would trade away the always-visible pin for a purely cosmetic containment win.
- **Lesson:** the left column gets the topic/phase header row and the message history loop. The right column gets the same `"💡 Word Suggestions"` subheader plus `render_word_chips(...)` reading from `active_lesson["word_suggestions"]`. `st.chat_input` for the lesson response stays outside the columns for the same pinning reason.

This is a page-level layout change only — Streamlit's existing `st.sidebar` (Chat's session list) is untouched and remains a separate, further-left panel; the new right column lives inside the main content area next to the chat/lesson transcript.

## Testing

`merge_word_suggestions` gets direct unit tests: cap enforcement, dedup-and-reorder-to-front on a repeated word, and empty-input behavior. The existing `AppTest`-based Streamlit harness tests (matching the verification style used for the 2026-07-05 Lesson fixes) are extended to cover: sending a Chat message produces a suggestion chip that is still present after the subsequent rerun (regression test for the bug above), clicking "💾 Save" removes that chip from the panel, and a second Lesson turn's suggestions are added alongside — not in place of — the first turn's.

## Fix: TTS spoke every kanji word twice because of inline furigana readings

**Bug:** `PromptBuilder._furigana_rule` (`services/prompt_builder.py`, added prior to this date's docs) instructs the model to write kanji words immediately followed by their hiragana reading in parentheses — e.g. `食べる(たべる)` — for readability, *inside* the same `<speak>…</speak>` block used for TTS. `extract_speak_text`/`parse_message_segments` (`ui/components/audio_controls.py`) pass that speak-block content through unchanged, and `render_message_with_tts`/`render_tts_button` fed it straight into `tts.synthesize(...)`. Kokoro TTS has no concept of a "silent" parenthetical — it read the kanji form and then the hiragana reading as two consecutive words, so every kanji word in a sentence was audibly spoken twice.

**Fix:** Added `strip_furigana(text: str) -> str` to `ui/components/audio_controls.py`, using `_FURIGANA_RE = re.compile(r"\([ぁ-゚ァ-ー]+\)")` to remove parenthetical spans whose content is entirely hiragana/katakana (the prolonged sound mark `ー` is included in the katakana range). Non-furigana parentheticals — e.g. explanatory asides in Latin script — are left alone since their content isn't pure kana. Both TTS call sites now strip furigana from the text handed to `tts.synthesize(...)`:

- `render_message_with_tts`: `tts.synthesize(strip_furigana(seg["content"]), lang=lang)`
- `render_tts_button`: `tts.synthesize(strip_furigana(extract_speak_text(text)), lang=lang)`

The furigana reading is only stripped from what's spoken — the displayed `st.markdown(seg["content"])` text (and therefore the visible reading aid for the learner) is unaffected. This is a targeted fix at the TTS boundary rather than in `PromptBuilder`, since the furigana annotation is still wanted in the displayed/stored message text; it's specifically redundant, not wrong, when read aloud.
