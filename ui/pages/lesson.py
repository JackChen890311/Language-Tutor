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
                    render_message_with_tts(
                        msg["content"], lang=target_lang, key=msg["content"][:20]
                    )
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
