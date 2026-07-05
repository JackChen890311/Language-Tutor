import streamlit as st
from ui.state import get
from ui.components.stream_display import stream_with_thinking


def render() -> None:
    st.title("🧪 Test")
    st.caption("Practice with a random quiz — no proficiency level involved.")

    language_svc = get("language_svc")
    quiz_svc = get("quiz_svc")
    store = get("store")
    native_lang, target_lang = language_svc.get_language_pair()

    if st.button("🎲 Generate Test"):
        collector = quiz_svc.stream_questions(native_lang, target_lang)
        stream_with_thinking(collector)
        st.session_state.test_questions = quiz_svc.parse_questions(collector.full_text)
        st.session_state.test_answers = {}
        st.session_state.pop("test_result", None)
        st.rerun()

    questions = st.session_state.get("test_questions")
    result = st.session_state.get("test_result")

    if questions and not result:
        st.subheader(f"Test ({len(questions)} questions)")
        for i, q in enumerate(questions):
            st.write(f"**Q{i + 1}.** {q['question']}")
            answer = st.radio(
                f"q{i}", q["options"], key=f"test_q_{i}", label_visibility="collapsed"
            )
            st.session_state.test_answers[i] = answer[0]

        if st.button("✅ Submit Test"):
            answers = [st.session_state.test_answers.get(i, "A") for i in range(len(questions))]
            st.session_state.test_result = quiz_svc.evaluate(questions, answers, target_lang)
            language_svc.update_streak(target_lang)
            st.rerun()
        return

    if result:
        st.success(f"Score: **{result['correct']}/{result['total']}** ({result['score']}%)")
        _render_review(result["questions"])
        if st.button("🔄 Try Another Test"):
            for key in ("test_questions", "test_answers", "test_result"):
                st.session_state.pop(key, None)
            st.rerun()

    _render_history(store, target_lang)


def _render_review(questions: list[dict]) -> None:
    for i, q in enumerate(questions):
        icon = "✅" if q["is_correct"] else "❌"
        st.write(f"{icon} **Q{i + 1}.** {q['question']}")
        st.caption(f"Correct answer: {q['correct']}")
        st.caption(f"🎯 {q.get('explanation_target', '')}")
        st.caption(f"🏠 {q.get('explanation_native', '')}")


def _render_history(store, target_lang: str) -> None:
    history = store.load_quiz_history(target_lang)
    st.divider()
    st.subheader("📜 Past Attempts")
    if not history:
        st.info("No attempts yet — click **Generate Test** above to start.")
        return
    for attempt in reversed(history):
        label = (
            f"{attempt['tested_at'][:16].replace('T', ' ')} — "
            f"{attempt['score']}% ({attempt['correct']}/{attempt['total']})"
        )
        with st.expander(label):
            _render_review(attempt["questions"])
