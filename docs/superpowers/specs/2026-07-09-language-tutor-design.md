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

## Fix: recognize miscapitalized `<speaK>` tags

**Bug:** `_SPEAK_BLOCK_RE` in `ui/components/audio_controls.py` already tolerated stray characters inside the angle brackets (e.g. `<s speak>`, fixed 2026-07-05) but was still case-sensitive, so a miscapitalized tag like `<speaK>` — observed in a real model response — didn't match at all and leaked into the displayed message as raw text, the same failure class as the prior malformed-tag bugs.

**Fix:** added `re.IGNORECASE` to `_SPEAK_BLOCK_RE`'s compiled flags (alongside the existing `re.DOTALL`). No change to the pattern itself.

## Investigation: word suggestions "disappearing" when moving from Lesson to Chat

**Reported symptom:** word-suggestion chips would show up while inside a Lesson, then appear to vanish after switching to the Chat page.

**Investigated and ruled out:** direct calls to the real, locally-configured LLM (bypassing all UI code) confirmed `extract_word_suggestions` and the marker-emission prompt instruction both work correctly when the model complies, and that compliance is inherently probabilistic (the same exact prompt produced markers in 4 of 5 real generations tried during this investigation) — this is expected LLM behavior, not a defect, and applies equally regardless of which page triggered generation.

**Actual root cause:** the per-page design introduced earlier in this file — Chat's `chat_word_suggestions` dict keyed by chat session id, and Lesson's `active_lesson["word_suggestions"]` — meant Chat and every Lesson each had their own independently-scoped suggestion list. Moving from a Lesson (which had accumulated suggestions) to Chat (a different, unrelated session key with its own empty or different list) correctly showed a *different* list — which looked, from the user's perspective, like the suggestions had disappeared.

**Fix — one global suggestion list:** `ui/components/word_chip.py` now owns the suggestion list itself, keyed under a single `st.session_state["word_suggestions"]` list shared across Chat and every Lesson, via two new functions:

```python
def get_word_suggestions() -> list[dict]:
    return st.session_state.setdefault("word_suggestions", [])

def add_word_suggestions(new: list[dict], cap: int = 10) -> None:
    st.session_state["word_suggestions"] = merge_word_suggestions(get_word_suggestions(), new, cap=cap)
```

`render_word_chips` no longer takes a `suggestions` list or an `on_save` callback — its signature shrinks to `render_word_chips(lang: str, native_lang: str) -> None`; it reads `get_word_suggestions()` and removes a saved word directly from the shared state itself, since there's now only one place the list can live. `ui/pages/chat.py` drops its `chat_word_suggestions` dict and per-session `_on_save` closure entirely; `ui/pages/lesson.py` drops `word_suggestions` from the `active_lesson` dict and its `_on_save` closure. Both pages now just call `add_word_suggestions(result.get("word_suggestions", []))` after each turn and `render_word_chips(lang=target_lang, native_lang=native_lang)` to display — no state threading required. This is a deliberate product decision (confirmed with the user) that word suggestions are one continuous learning aid across the whole app session, not scoped per conversation.
