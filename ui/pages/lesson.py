import streamlit as st
from ui.state import get
from ui.components.word_chip import render_word_chips
from ui.components.audio_controls import render_tts_button


def render() -> None:
    st.title("📝 Lesson")

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    lesson_svc = get("lesson_svc")
    store = get("store")
    level_data = store.load_level(target_lang)
    level = level_data.get("level", "N4")

    if "active_lesson" not in st.session_state:
        _render_topic_picker(lesson_svc, target_lang, native_lang, level)
    else:
        _render_active_lesson(lesson_svc, language_svc, target_lang, native_lang, level)


def _render_topic_picker(lesson_svc, target_lang, native_lang, level) -> None:
    st.subheader("Choose a topic")

    difficulty = st.select_slider(
        "Difficulty", options=["Easy", "Normal", "Hard"], value="Normal"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        custom_topic = st.text_input("Or enter a custom topic:", placeholder="e.g. ordering coffee")
    with col2:
        if st.button("🎲 Suggest Topics"):
            with st.spinner("Getting suggestions..."):
                st.session_state.suggested_topics = lesson_svc.suggest_topics(target_lang, level)

    suggested = st.session_state.get("suggested_topics", [])
    if suggested:
        st.write("**Suggested topics:**")
        cols = st.columns(min(len(suggested), 5))
        for i, topic in enumerate(suggested):
            with cols[i % 5]:
                if st.button(topic, key=f"topic_{i}"):
                    _start_lesson(lesson_svc, target_lang, native_lang, level, topic, difficulty)

    if custom_topic and st.button("▶️ Start Lesson"):
        _start_lesson(lesson_svc, target_lang, native_lang, level, custom_topic, difficulty)


def _start_lesson(lesson_svc, target_lang, native_lang, level, topic, difficulty) -> None:
    lesson_id, session_id, collector = lesson_svc.stream_start_lesson(
        target_lang, native_lang, level, topic, difficulty=difficulty
    )
    with st.chat_message("assistant"):
        st.write_stream(collector)
    result = lesson_svc.commit_start_lesson(target_lang, session_id, lesson_id, topic, collector.full_text)
    st.session_state.active_lesson = {
        "lesson_id": lesson_id,
        "session_id": session_id,
        "topic": topic,
        "difficulty": difficulty,
        "phase": result["phase"],
        "messages": [{"role": "assistant", "content": result["response"]}],
        "word_suggestions": result.get("word_suggestions", []),
    }
    st.rerun()


def _render_active_lesson(lesson_svc, language_svc, target_lang, native_lang, level) -> None:
    lesson = st.session_state.active_lesson
    topic = lesson["topic"]
    phase = lesson["phase"]
    phase_label = "📖 Structured Lesson" if phase == "structured" else "💬 Free Conversation"

    col1, col2, col3 = st.columns([4, 2, 1])
    with col1:
        st.subheader(f"Topic: {topic} — {phase_label}")
    with col2:
        if phase == "structured":
            if st.button("➡️ Move to Free Conversation"):
                lesson["phase"] = "conversation"
                st.rerun()
    with col3:
        if st.button("✅ Finish"):
            lesson_svc.finish_lesson(target_lang, topic)
            language_svc.update_streak(target_lang)
            del st.session_state.active_lesson
            st.session_state.pop("suggested_topics", None)
            st.rerun()

    for msg in lesson["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                render_tts_button(msg["content"], lang=target_lang, key=msg["content"][:20])

    render_word_chips(lesson.get("word_suggestions", []), lang=target_lang, native_lang=native_lang)

    user_input = st.chat_input("Your response...")
    if user_input:
        lesson["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        collector = lesson_svc.stream_continue_lesson(
            target_lang=target_lang,
            session_id=lesson["session_id"],
            native_lang=native_lang,
            level=level,
            topic=topic,
            phase=lesson["phase"],
            difficulty=lesson["difficulty"],
            user_text=user_input,
        )
        with st.chat_message("assistant"):
            st.write_stream(collector)
            render_tts_button(collector.full_text, lang=target_lang, key="lesson_latest")
        result = lesson_svc.commit_continue_lesson(
            target_lang=target_lang,
            session_id=lesson["session_id"],
            lesson_id=lesson["lesson_id"],
            user_text=user_input,
            raw_response=collector.full_text,
            phase=lesson["phase"],
        )

        lesson["messages"].append({"role": "assistant", "content": result["response"]})
        lesson["word_suggestions"] = result.get("word_suggestions", [])
        st.rerun()
