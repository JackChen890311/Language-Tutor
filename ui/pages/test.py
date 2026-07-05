import streamlit as st
from ui.state import get


def render() -> None:
    st.title("🧪 Test")
    st.caption("Practice with a random quiz — no proficiency level involved.")

    language_svc = get("language_svc")
    quiz_svc = get("quiz_svc")
    _, target_lang = language_svc.get_language_pair()

    if st.button("🎲 Generate Test"):
        st.session_state.test_questions = quiz_svc.generate_questions(target_lang)
        st.session_state.test_answers = {}
        st.session_state.pop("test_result", None)
        st.rerun()

    if "test_questions" not in st.session_state:
        st.info("Click **Generate Test** to get a fresh set of random questions.")
        return

    questions = st.session_state.test_questions
    result = st.session_state.get("test_result")

    if result:
        st.success(f"Score: **{result['correct']}/{result['total']}** ({result['score']}%)")
        for i, q in enumerate(questions):
            given = st.session_state.test_answers.get(i)
            correct = q["correct"]
            icon = "✅" if given == correct else "❌"
            st.write(f"{icon} **Q{i + 1}.** {q['question']}")
            st.caption(f"Correct answer: {correct} — {q.get('explanation', '')}")
        if st.button("🔄 Try Another Test"):
            for key in ("test_questions", "test_answers", "test_result"):
                st.session_state.pop(key, None)
            st.rerun()
        return

    st.subheader(f"Test ({len(questions)} questions)")
    for i, q in enumerate(questions):
        st.write(f"**Q{i + 1}.** {q['question']}")
        answer = st.radio(f"q{i}", q["options"], key=f"test_q_{i}", label_visibility="collapsed")
        st.session_state.test_answers[i] = answer[0]

    if st.button("✅ Submit Test"):
        answers = [st.session_state.test_answers.get(i, "A") for i in range(len(questions))]
        st.session_state.test_result = quiz_svc.evaluate(questions, answers)
        language_svc.update_streak(target_lang)
        st.rerun()
