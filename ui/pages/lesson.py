import streamlit as st

from services.prompt_builder import get_difficulty_levels
from ui import theme
from ui.components.audio_controls import render_message_with_tts
from ui.components.stream_display import stream_with_thinking
from ui.components.word_chip import (
    add_word_suggestions,
    get_word_suggestions,
    render_word_chips,
)
from ui.state import get


def render() -> None:
    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    lesson_svc = get("lesson_svc")

    theme.page_header(
        "📝",
        "Lesson",
        "Vocabulary, grammar and guided conversation on a topic you choose.",
    )

    if "active_lesson" not in st.session_state:
        _render_topic_picker(lesson_svc, target_lang, native_lang)
    else:
        _render_active_lesson(lesson_svc, language_svc, target_lang, native_lang)


def _render_topic_picker(lesson_svc, target_lang: str, native_lang: str) -> None:
    framework = get_difficulty_levels(target_lang)
    levels = framework["levels"]
    midpoint = levels[len(levels) // 2]

    with st.container(key="ltcard_topic_picker"):
        theme.section_header(f"Difficulty · {framework['name']}", icon="🎚️")
        difficulty = st.pills(
            "Difficulty",
            levels,
            default=midpoint,
            key=f"lesson_difficulty_{target_lang}",
            label_visibility="collapsed",
        )
        if difficulty is None:
            difficulty = midpoint

        st.write("")
        theme.section_header("Choose a topic", icon="🧭")
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            custom_topic = st.text_input(
                "Custom topic",
                placeholder="e.g. ordering coffee",
                key="lesson_topic_input",
            )
        with col2:
            if st.button("🎲 Suggest topics", use_container_width=True):
                with st.spinner("Getting suggestions…"):
                    st.session_state.suggested_topics = lesson_svc.suggest_topics(target_lang)

        if st.button(
            "▶️  Start lesson",
            type="primary",
            disabled=not (custom_topic or "").strip(),
        ):
            st.session_state.pending_topic = custom_topic.strip()

    suggested = st.session_state.get("suggested_topics", [])
    if suggested:
        theme.section_header("Suggested topics", icon="✨")
        columns = st.columns(min(len(suggested), 3))
        for i, topic in enumerate(suggested):
            with columns[i % 3]:
                with st.container(key=f"ltcardhover_topic_{i}"):
                    st.markdown(f"**{topic}**")
                    if st.button(
                        "Start this topic",
                        key=f"topic_{i}",
                        use_container_width=True,
                        type="primary",
                    ):
                        st.session_state.pending_topic = topic

    pending_topic = st.session_state.pop("pending_topic", None)
    if pending_topic:
        _start_lesson(lesson_svc, target_lang, native_lang, pending_topic, difficulty)


def _start_lesson(lesson_svc, target_lang, native_lang, topic: str, difficulty: str) -> None:
    lesson_id, session_id, collector = lesson_svc.stream_start_lesson(
        target_lang, native_lang, topic, difficulty=difficulty
    )
    with st.chat_message("assistant"):
        stream_with_thinking(collector)
    result = lesson_svc.commit_start_lesson(
        target_lang, session_id, lesson_id, topic, collector.full_text
    )
    add_word_suggestions(result.get("word_suggestions", []))
    st.session_state.active_lesson = {
        "lesson_id": lesson_id,
        "session_id": session_id,
        "topic": topic,
        "difficulty": difficulty,
        "phase": result["phase"],
        "messages": [{"role": "assistant", "content": result["response"]}],
    }
    st.rerun()


def _render_active_lesson(lesson_svc, language_svc, target_lang: str, native_lang: str) -> None:
    lesson = st.session_state.active_lesson
    topic = lesson["topic"]
    phase = lesson["phase"]
    is_structured = phase == "structured"

    with st.container(key="ltcard_lesson_head"):
        title_col, action_col = st.columns([3, 1], vertical_alignment="center")
        with title_col:
            st.markdown(f"### {topic}")
            st.caption("Structured lesson" if is_structured else "Free conversation · speak freely")
        with action_col:
            if is_structured:
                if st.button("➡️  Free conversation", use_container_width=True):
                    lesson["phase"] = "conversation"
                    st.rerun()
            if st.button("✅  Finish", use_container_width=True, type="primary"):
                lesson_svc.finish_lesson(target_lang, topic)
                language_svc.update_streak(target_lang)
                del st.session_state.active_lesson
                st.session_state.pop("suggested_topics", None)
                st.rerun()
        st.write("")
        theme.stepper(["Structured lesson", "Free conversation"], 0 if is_structured else 1)

    main_col, side_col = st.columns([3, 1], gap="large")

    with main_col:
        for i, msg in enumerate(lesson["messages"]):
            avatar = "🗣️" if msg["role"] == "assistant" else None
            with st.chat_message(msg["role"], avatar=avatar):
                if msg["role"] == "assistant":
                    render_message_with_tts(msg["content"], lang=target_lang, key=f"hist{i}")
                else:
                    st.write(msg["content"])

    with side_col:
        with st.container(key="lesson_words"):
            theme.section_header("Words to learn", icon="💡")
            suggestions = get_word_suggestions()
            if suggestions:
                render_word_chips(suggestions, lang=target_lang, native_lang=native_lang)
            else:
                st.caption("Words from this lesson will collect here as you go.")

    user_input = st.chat_input("Your response…")
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
        add_word_suggestions(result.get("word_suggestions", []))
        st.rerun()
