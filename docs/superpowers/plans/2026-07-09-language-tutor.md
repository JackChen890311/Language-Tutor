# Language Tutor Implementation Plan — 2026-07-09 Update

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Status:** All tasks below complete.
>
> Extends `docs/superpowers/plans/2026-07-05-language-tutor.md`. See `docs/superpowers/specs/2026-07-09-language-tutor-design.md` for the design rationale behind these changes.

**Goal:** Fix Chat's word suggestions (currently rendered then immediately wiped by `st.rerun()`, so they never actually appear) and move word-suggestion chips into a right-side panel on both Chat and Lesson, accumulating up to 10 deduped suggestions instead of replacing the list on every turn.

**Architecture:** A pure `merge_word_suggestions(existing, new, cap=10)` helper in `ui/components/word_chip.py` handles dedup/cap/reorder. Chat gains a new session-keyed accumulator in `st.session_state["chat_word_suggestions"]`; Lesson's existing `active_lesson["word_suggestions"]` switches from overwrite to merge. Both pages wrap their main content in `st.columns([3, 1])` — chat/lesson transcript on the left, word-suggestion panel on the right — while `st.chat_input` stays outside the columns so it keeps its full-width pinned-to-bottom behavior.

**Tech Stack:** Streamlit 1.57 (`st.columns`, `st.session_state`), pytest for the pure-function unit tests. No new dependencies.

## Global Constraints

- Suggestion list cap: 10 entries, newest first (spec section "Fix: Chat word suggestions...").
- Dedup by the `word` field — a re-suggested word moves to the front instead of duplicating.
- Saving a word (clicking "💾 Save") removes it from the panel immediately.
- `st.chat_input` (and Chat's `render_stt_input`) must remain outside/after the two-column block on both pages, so it stays pinned full-width at the bottom of the viewport — do not nest it inside a column.
- Right-side panel uses `st.columns([3, 1])` on both pages (main content : suggestions panel).
- Chips render as a vertical stack (one per row) — the old `st.columns(min(len(suggestions), 3))` grid inside `render_word_chips` is removed.
- No new automated UI tests for `ui/pages/chat.py` / `ui/pages/lesson.py` — this repo's `tests/` suite only covers `services/`/`data_store/` and pure UI helpers, never Streamlit pages directly (confirmed in Task 28 of the 2026-07-05 plan). Verify page changes by running the app.

---

## Task 33: Word-suggestion merge helper + `render_word_chips` update

**Files:**
- Modify: `ui/components/word_chip.py`
- Create: `tests/test_word_chip.py`

**Interfaces:**
- Produces: `merge_word_suggestions(existing: list[dict], new: list[dict], cap: int = 10) -> list[dict]`
- Produces: `render_word_chips(suggestions: list[dict], lang: str, native_lang: str, on_save: Callable[[str], None]) -> None` (signature change — `on_save` is new and required; caller supplies a callback that removes the given word from wherever it stores its suggestion list)

- [x] **Step 1: Write the failing tests for `merge_word_suggestions`**

Create `tests/test_word_chip.py`:

```python
from ui.components.word_chip import merge_word_suggestions


def test_merge_empty_existing():
    result = merge_word_suggestions([], [{"word": "食べる", "reading": "たべる"}])
    assert result == [{"word": "食べる", "reading": "たべる"}]


def test_merge_no_new_suggestions():
    existing = [{"word": "食べる", "reading": "たべる"}]
    assert merge_word_suggestions(existing, []) == existing


def test_merge_new_suggestions_go_first():
    existing = [{"word": "食べる", "reading": "たべる"}]
    new = [{"word": "飲む", "reading": "のむ"}]
    result = merge_word_suggestions(existing, new)
    assert result == [{"word": "飲む", "reading": "のむ"}, {"word": "食べる", "reading": "たべる"}]


def test_merge_dedupes_repeated_word_and_moves_to_front():
    existing = [
        {"word": "飲む", "reading": "のむ"},
        {"word": "食べる", "reading": "たべる"},
    ]
    new = [{"word": "食べる", "reading": "たべる (updated)"}]
    result = merge_word_suggestions(existing, new)
    assert result == [
        {"word": "食べる", "reading": "たべる (updated)"},
        {"word": "飲む", "reading": "のむ"},
    ]


def test_merge_caps_at_limit():
    existing = [{"word": f"word{i}"} for i in range(10)]
    new = [{"word": "new_word"}]
    result = merge_word_suggestions(existing, new, cap=10)
    assert len(result) == 10
    assert result[0] == {"word": "new_word"}
    assert result[-1] == {"word": "word8"}
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_word_chip.py -v`
Expected: FAIL with `ImportError: cannot import name 'merge_word_suggestions'`

- [x] **Step 3: Implement `merge_word_suggestions` and update `render_word_chips`**

Rewrite `ui/components/word_chip.py` in full:

```python
from typing import Callable

import streamlit as st
from ui.state import get

_CHIP_CSS = """
<style>
.word-chip {
    background: rgba(79, 142, 247, 0.1);
    border: 1px solid rgba(79, 142, 247, 0.3);
    border-radius: 10px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.4rem;
}
.word-chip .word { font-size: 1.05rem; font-weight: 600; }
.word-chip .reading { font-size: 0.8rem; color: grey; }
</style>
"""


def merge_word_suggestions(existing: list[dict], new: list[dict], cap: int = 10) -> list[dict]:
    """Newest first, deduped by word, capped at `cap`."""
    merged = list(existing)
    for suggestion in new:
        word = suggestion.get("word", "")
        merged = [s for s in merged if s.get("word") != word]
        merged.insert(0, suggestion)
    return merged[:cap]


def render_word_chips(
    suggestions: list[dict], lang: str, native_lang: str, on_save: Callable[[str], None]
) -> None:
    if not suggestions:
        return
    st.markdown(_CHIP_CSS, unsafe_allow_html=True)
    st.caption("💡 Word suggestions")
    for i, suggestion in enumerate(suggestions):
        word = suggestion.get("word", "")
        reading = suggestion.get("reading", "")
        reading_html = f'<div class="reading">{reading}</div>' if reading else ""
        st.markdown(
            f'<div class="word-chip"><div class="word">{word}</div>{reading_html}</div>',
            unsafe_allow_html=True,
        )
        if st.button("💾 Save", key=f"save_word_{i}_{word}", use_container_width=True):
            word_svc = get("word_svc")
            word_svc.add_word(lang, native_lang, word, reading=reading, source="chat")
            st.toast(f"✅ Saved: {word}")
            on_save(word)
            st.rerun()
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_word_chip.py -v`
Expected: PASS (5 tests)

- [x] **Step 5: Commit**

```bash
git add ui/components/word_chip.py tests/test_word_chip.py
git commit -m "feat: add word-suggestion merge/dedup helper, on_save callback on chips"
```

## Task 34: Chat page — persistent, accumulating word suggestions in a right-side panel

**Files:**
- Modify: `ui/pages/chat.py`

**Interfaces:**
- Consumes: `merge_word_suggestions`, `render_word_chips(suggestions, lang, native_lang, on_save)` from Task 33
- Consumes: `chat_svc.commit_message(...) -> dict` (unchanged, already returns `{"response": str, "word_suggestions": list[dict]}` per `services/chat_service.py`)

No new automated tests (see Global Constraints). Verify manually in Step 3.

- [x] **Step 1: Rewrite `ui/pages/chat.py`**

Rewrite `ui/pages/chat.py` in full:

```python
import tempfile
import streamlit as st
from ui.state import get
from ui.components.word_chip import render_word_chips, merge_word_suggestions
from ui.components.audio_controls import render_tts_button, render_message_with_tts, render_stt_input
from ui.components.stream_display import stream_with_thinking


def render() -> None:
    st.title("💬 Chat")

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    store = get("store")
    chat_svc = get("chat_svc")

    with st.sidebar:
        st.subheader("Sessions")
        sessions = store.list_chat_sessions(target_lang)

        if st.button("➕ New Chat"):
            name = f"Chat {len(sessions) + 1}"
            st.session_state.active_session = store.create_chat_session(target_lang, name)
            st.rerun()

        for s in reversed(sessions):
            cols = st.columns([4, 1])
            with cols[0]:
                if st.button(s["name"], key=f"sel_{s['id']}"):
                    st.session_state.active_session = s["id"]
                    st.rerun()
            with cols[1]:
                if st.button("🗑", key=f"del_{s['id']}"):
                    store.delete_chat_session(target_lang, s["id"])
                    if st.session_state.get("active_session") == s["id"]:
                        st.session_state.pop("active_session", None)
                    st.rerun()

    active_session = st.session_state.get("active_session")
    if not active_session:
        st.info("Select or create a chat session from the sidebar.")
        return

    session_info = next((s for s in sessions if s["id"] == active_session), None)

    chat_word_suggestions = st.session_state.setdefault("chat_word_suggestions", {})

    def _on_save(word: str) -> None:
        chat_word_suggestions[active_session] = [
            s for s in chat_word_suggestions.get(active_session, []) if s.get("word") != word
        ]

    col1, col2 = st.columns([3, 1])

    with col1:
        if session_info:
            st.subheader(session_info["name"])

        messages = chat_svc.get_history(target_lang, active_session)
        for msg in messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    render_message_with_tts(msg["content"], lang=target_lang, key=msg["content"][:20])
                else:
                    st.write(msg["content"])

        uploaded_image = st.file_uploader(
            "📷 Attach image (optional)",
            type=["jpg", "jpeg", "png"],
            key=f"img_{active_session}",
            label_visibility="collapsed",
        )
        image_path = None
        if uploaded_image:
            import os

            suffix = os.path.splitext(uploaded_image.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(uploaded_image.getvalue())
                image_path = f.name

    with col2:
        render_word_chips(
            chat_word_suggestions.get(active_session, []),
            lang=target_lang,
            native_lang=native_lang,
            on_save=_on_save,
        )

    stt_text = render_stt_input(key=active_session)
    user_input = st.chat_input("Type a message...")
    final_input = stt_text or user_input

    if final_input:
        with st.chat_message("user"):
            st.write(final_input)

        collector = chat_svc.stream_message(
            lang=target_lang,
            session_id=active_session,
            native_lang=native_lang,
            user_text=final_input,
            image_path=image_path,
        )
        with st.chat_message("assistant"):
            stream_with_thinking(collector)
            render_message_with_tts(collector.full_text, lang=target_lang, key="latest")

        result = chat_svc.commit_message(
            lang=target_lang,
            session_id=active_session,
            native_lang=native_lang,
            user_text=final_input,
            raw_response=collector.full_text,
        )
        chat_word_suggestions[active_session] = merge_word_suggestions(
            chat_word_suggestions.get(active_session, []),
            result.get("word_suggestions", []),
        )

        language_svc.update_streak(target_lang)
        st.rerun()
```

Note what changed from the old version: `render_word_chips(...)` is no longer called right before `st.rerun()` in the `if final_input:` block (that call never survived the rerun — the bug this task fixes). Instead, the new suggestions are merged into `chat_word_suggestions[active_session]` before the rerun, and the right column reads and renders that persisted, accumulated list on every run.

- [x] **Step 2: Run the full test suite to check for regressions**

Run: `uv run pytest -v`
Expected: PASS (all existing tests, plus the 5 new ones from Task 33)

- [x] **Step 3: Manually verify in the running app**

Run: `make run`, open Chat, select or create a session, send a message that should trigger a word suggestion (e.g. ask the tutor to teach you a new word). Confirm:
- A word-suggestion chip appears in the right-hand column after the response streams in, and it is still there after the page's automatic rerun (previously it would never appear at all).
- Sending a second message that introduces another word adds a second chip above the first (newest first), without losing the first.
- Clicking "💾 Save" on a chip removes it from the panel and shows the "✅ Saved" toast.
- The chat input box is still pinned to the bottom of the browser window, spanning the full width below both columns.

- [x] **Step 4: Commit**

```bash
git add ui/pages/chat.py
git commit -m "fix: persist and accumulate Chat word suggestions in a right-side panel"
```

## Task 35: Lesson page — accumulating word suggestions in a right-side panel

**Files:**
- Modify: `ui/pages/lesson.py`

**Interfaces:**
- Consumes: `merge_word_suggestions`, `render_word_chips(suggestions, lang, native_lang, on_save)` from Task 33
- Consumes: `lesson_svc.commit_start_lesson(...)` / `lesson_svc.commit_continue_lesson(...) -> dict` (unchanged, already return `{"response": ..., "word_suggestions": list[dict], "phase": ...}` per `services/lesson_service.py`)

No new automated tests (see Global Constraints). Verify manually in Step 3.

- [x] **Step 1: Rewrite `ui/pages/lesson.py`**

Rewrite `ui/pages/lesson.py` in full:

```python
import streamlit as st
from ui.state import get
from ui.components.word_chip import render_word_chips, merge_word_suggestions
from ui.components.stream_display import stream_with_thinking
from ui.components.audio_controls import render_message_with_tts
from services.prompt_builder import get_difficulty_levels


def render() -> None:
    st.title("📝 Lesson")

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    lesson_svc = get("lesson_svc")

    if "active_lesson" not in st.session_state:
        _render_topic_picker(lesson_svc, target_lang, native_lang)
    else:
        _render_active_lesson(lesson_svc, language_svc, target_lang, native_lang)


def _render_topic_picker(lesson_svc, target_lang, native_lang) -> None:
    st.subheader("Choose a topic")

    framework = get_difficulty_levels(target_lang)
    levels = framework["levels"]
    difficulty = st.select_slider(
        f"Difficulty ({framework['name']})", options=levels, value=levels[len(levels) // 2]
    )

    def _pick_topic(topic: str) -> None:
        st.session_state.lesson_topic_input = topic

    def _submit_topic() -> None:
        topic = st.session_state.get("lesson_topic_input", "").strip()
        if topic:
            st.session_state.pending_topic = topic

    col1, col2 = st.columns([3, 1])
    with col1:
        custom_topic = st.text_input(
            "Or enter a custom topic:",
            placeholder="e.g. ordering coffee",
            key="lesson_topic_input",
            on_change=_submit_topic,
        )
    with col2:
        if st.button("🎲 Suggest Topics"):
            with st.spinner("Getting suggestions..."):
                st.session_state.suggested_topics = lesson_svc.suggest_topics(target_lang)

    suggested = st.session_state.get("suggested_topics", [])
    if suggested:
        st.write("**Suggested topics:**")
        cols = st.columns(min(len(suggested), 5))
        for i, topic in enumerate(suggested):
            with cols[i % 5]:
                st.button(topic, key=f"topic_{i}", on_click=_pick_topic, args=(topic,))

    if custom_topic:
        st.button("▶️ Start Lesson", on_click=_submit_topic)

    pending_topic = st.session_state.pop("pending_topic", None)
    if pending_topic:
        _start_lesson(lesson_svc, target_lang, native_lang, pending_topic, difficulty)


def _start_lesson(lesson_svc, target_lang, native_lang, topic, difficulty) -> None:
    lesson_id, session_id, collector = lesson_svc.stream_start_lesson(
        target_lang, native_lang, topic, difficulty=difficulty
    )
    with st.chat_message("assistant"):
        stream_with_thinking(collector)
    result = lesson_svc.commit_start_lesson(
        target_lang, session_id, lesson_id, topic, collector.full_text
    )
    st.session_state.active_lesson = {
        "lesson_id": lesson_id,
        "session_id": session_id,
        "topic": topic,
        "difficulty": difficulty,
        "phase": result["phase"],
        "messages": [{"role": "assistant", "content": result["response"]}],
        "word_suggestions": merge_word_suggestions([], result.get("word_suggestions", [])),
    }
    st.rerun()


def _render_active_lesson(lesson_svc, language_svc, target_lang, native_lang) -> None:
    lesson = st.session_state.active_lesson
    topic = lesson["topic"]
    phase = lesson["phase"]
    phase_label = "📖 Structured Lesson" if phase == "structured" else "💬 Free Conversation"

    def _on_save(word: str) -> None:
        lesson["word_suggestions"] = [
            s for s in lesson.get("word_suggestions", []) if s.get("word") != word
        ]

    col1, col2 = st.columns([3, 1])

    with col1:
        header_col1, header_col2, header_col3 = st.columns([4, 2, 1])
        with header_col1:
            st.subheader(f"Topic: {topic} — {phase_label}")
        with header_col2:
            if phase == "structured":
                if st.button("➡️ Move to Free Conversation"):
                    lesson["phase"] = "conversation"
                    st.rerun()
        with header_col3:
            if st.button("✅ Finish"):
                lesson_svc.finish_lesson(target_lang, topic)
                language_svc.update_streak(target_lang)
                del st.session_state.active_lesson
                st.session_state.pop("suggested_topics", None)
                st.rerun()

        for msg in lesson["messages"]:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    render_message_with_tts(msg["content"], lang=target_lang, key=msg["content"][:20])
                else:
                    st.write(msg["content"])

    with col2:
        render_word_chips(
            lesson.get("word_suggestions", []),
            lang=target_lang,
            native_lang=native_lang,
            on_save=_on_save,
        )

    user_input = st.chat_input("Your response...")
    if user_input:
        lesson["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        collector = lesson_svc.stream_continue_lesson(
            target_lang=target_lang,
            session_id=lesson["session_id"],
            native_lang=native_lang,
            topic=topic,
            phase=lesson["phase"],
            difficulty=lesson["difficulty"],
            user_text=user_input,
        )
        with st.chat_message("assistant"):
            stream_with_thinking(collector)
            render_message_with_tts(collector.full_text, lang=target_lang, key="lesson_latest")
        result = lesson_svc.commit_continue_lesson(
            target_lang=target_lang,
            session_id=lesson["session_id"],
            lesson_id=lesson["lesson_id"],
            user_text=user_input,
            raw_response=collector.full_text,
            phase=lesson["phase"],
        )

        lesson["messages"].append({"role": "assistant", "content": result["response"]})
        lesson["word_suggestions"] = merge_word_suggestions(
            lesson.get("word_suggestions", []), result.get("word_suggestions", [])
        )
        st.rerun()
```

Note what changed from the old version: the header row's column variables are renamed from `col1`/`col2`/`col3` to `header_col1`/`header_col2`/`header_col3` (nested inside the new outer `col1`) purely to avoid shadowing the outer `col1`/`col2` split — no behavioral difference. `word_suggestions` is now built with `merge_word_suggestions` at both lesson start and on every continue-turn, instead of being overwritten wholesale.

- [x] **Step 2: Run the full test suite to check for regressions**

Run: `uv run pytest -v`
Expected: PASS (all tests)

- [x] **Step 3: Manually verify in the running app**

Run: `make run`, open Lesson, start a lesson on any topic. Confirm:
- Word-suggestion chips appear in the right-hand column as the structured lesson introduces vocabulary.
- Sending a follow-up response that introduces another word adds to the list (newest first) rather than replacing it.
- Clicking "💾 Save" removes that chip from the panel.
- The response input box remains pinned to the bottom of the browser window.
- "➡️ Move to Free Conversation" and "✅ Finish" buttons still work as before.

- [x] **Step 4: Commit**

```bash
git add ui/pages/lesson.py
git commit -m "feat: accumulate Lesson word suggestions in a right-side panel"
```

## Task 36: Final verification, push

**Files:** none (verification only)

- [x] **Step 1: Run the full test suite**

Run: `make test`
Expected: PASS, all tests green

- [x] **Step 2: Run lint**

Run: `make lint`
Expected: no errors; if `ruff format --check` fails on files touched in this plan, run `uv run ruff format ui/components/word_chip.py ui/pages/chat.py ui/pages/lesson.py tests/test_word_chip.py` and re-run `make lint`

Deviation found while running this step: `make lint` also flagged `ui/pages/chat.py`'s carried-over `render_tts_button` import (unused in the original file too, before this plan touched it) as F401, and `ruff format --check` wanted reformatting on `chat.py`/`lesson.py`. Both were fixed (import dropped, `ruff format` run) in an extra commit — see below. A separate pre-existing F401 on the same unused import in `ui/pages/word_list.py`, a file untouched by this plan, was left alone as out of scope.

- [x] **Step 3: Push to origin main**

```bash
git push origin main
```
