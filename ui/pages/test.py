import streamlit as st

from services.prompt_builder import get_difficulty_levels
from ui import theme
from ui.components.stream_display import stream_silently
from ui.state import get


def render() -> None:
    language_svc = get("language_svc")
    quiz_svc = get("quiz_svc")
    store = get("store")
    native_lang, target_lang = language_svc.get_language_pair()

    theme.page_header(
        "🧪",
        "Test",
        "A quick quiz at your level, mapped to a recognised proficiency scale.",
    )

    framework = get_difficulty_levels(target_lang)
    levels = framework["levels"]
    midpoint = levels[len(levels) // 2]

    with st.container(key="ltcard_test_setup"):
        theme.section_header(f"Difficulty · {framework['name']}", icon="🎚️")
        difficulty = st.pills(
            "Difficulty",
            levels,
            default=midpoint,
            key=f"test_difficulty_{target_lang}",
            label_visibility="collapsed",
        )
        if difficulty is None:
            difficulty = midpoint
        st.write("")
        if st.button("🎲  Generate test", type="primary"):
            collector = quiz_svc.stream_questions(native_lang, target_lang, difficulty)
            stream_silently(collector)
            st.session_state.test_questions = quiz_svc.parse_questions(collector.full_text)
            st.session_state.test_answers = {}
            st.session_state.pop("test_result", None)
            st.rerun()

    questions = st.session_state.get("test_questions")
    result = st.session_state.get("test_result")

    if questions and not result:
        _render_questions(questions, quiz_svc, language_svc, target_lang)

    if result:
        _render_result(result)

    _render_history(store, target_lang)


def _render_questions(questions: list[dict], quiz_svc, language_svc, target_lang: str) -> None:
    answered = len(st.session_state.get("test_answers", {}))
    theme.section_header(
        f"{len(questions)} questions",
        caption=f"{answered} answered",
        icon="📋",
    )
    st.progress(answered / len(questions) if questions else 0)

    for i, q in enumerate(questions):
        with st.container(key=f"ltcard_q_{i}"):
            st.html(f'<div class="lt-quiz-head"><span class="lt-quiz-num">Q{i + 1}</span></div>')
            st.markdown(f"**{q['question']}**")
            answer = st.radio(
                f"q{i}",
                q["options"],
                key=f"test_q_{i}",
                label_visibility="collapsed",
                index=None,
            )
            if answer:
                st.session_state.test_answers[i] = answer[0]

    if st.button("✅  Submit test", type="primary", use_container_width=True):
        answers = [st.session_state.test_answers.get(i, "A") for i in range(len(questions))]
        st.session_state.test_result = quiz_svc.evaluate(questions, answers, target_lang)
        language_svc.update_streak(target_lang)
        st.rerun()


def _render_result(result: dict) -> None:
    theme.section_header("Result", icon="🏁")
    with st.container(key="ltcard_result"):
        theme.score_ring(result["score"], result["correct"], result["total"])
        st.write("")
        if st.button("🔄  Try another test", use_container_width=True):
            for key in ("test_questions", "test_answers", "test_result"):
                st.session_state.pop(key, None)
            st.rerun()

    theme.section_header("Review", icon="🔍")
    _render_review(result["questions"])


def _render_review(questions: list[dict]) -> None:
    for i, q in enumerate(questions):
        correct = q["is_correct"]
        wrapper = "lt-ok" if correct else "lt-no"
        title_cls = "lt-ok-title" if correct else "lt-no-title"
        icon = "✅" if correct else "❌"
        given = q.get("given", "")
        answer_line = (
            f"Your answer: <b>{theme.esc(given)}</b>"
            if correct
            else f"Your answer: <b>{theme.esc(given)}</b> · Correct: "
            f"<b>{theme.esc(q['correct'])}</b>"
        )
        theme_html = (
            f'<div class="{wrapper}"><div class="{title_cls}">{icon} Question {i + 1}</div>'
            f'<div style="margin:.3rem 0">{theme.esc(q["question"])}</div>'
            f'<div class="lt-muted">{answer_line}</div>'
            f'<div style="margin-top:.4rem">{theme.esc(q.get("explanation_target", ""))}</div>'
            f'<div class="lt-muted">{theme.esc(q.get("explanation_native", ""))}</div></div>'
        )
        st.html(theme_html)


def _render_history(store, target_lang: str) -> None:
    history = store.load_quiz_history(target_lang)
    theme.section_header("Past attempts", caption=f"{len(history)} total", icon="📜")
    if not history:
        theme.empty_state(
            "📜",
            "No attempts yet",
            "Generate a test above and your scores will be recorded here.",
        )
        return
    for attempt in reversed(history):
        label = (
            f"{attempt['tested_at'][:16].replace('T', ' ')} — "
            f"{attempt['score']}% ({attempt['correct']}/{attempt['total']})"
        )
        with st.expander(label):
            _render_review(attempt["questions"])
