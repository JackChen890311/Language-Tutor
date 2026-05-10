import streamlit as st
from ui.state import get

SUPPORTED_LANGUAGES = {
    "zh-TW": "繁體中文 (Traditional Chinese)",
    "en": "English",
    "ja": "日本語 (Japanese)",
    "ko": "한국어 (Korean)",
    "es": "Español (Spanish)",
    "fr": "Français (French)",
    "de": "Deutsch (German)",
}


def render() -> None:
    st.title("⚙️ Settings")

    language_svc = get("language_svc")
    mm = get("mm")
    native_lang, target_lang = language_svc.get_language_pair()

    st.subheader("🌐 Language Pair")
    lang_codes = list(SUPPORTED_LANGUAGES.keys())
    lang_labels = list(SUPPORTED_LANGUAGES.values())

    col1, col2 = st.columns(2)
    with col1:
        native_idx = lang_codes.index(native_lang) if native_lang in lang_codes else 0
        new_native = st.selectbox("Native Language", lang_labels, index=native_idx)
    with col2:
        target_idx = lang_codes.index(target_lang) if target_lang in lang_codes else 2
        new_target = st.selectbox("Learning Language", lang_labels, index=target_idx)

    if st.button("💾 Save Language Settings"):
        new_native_code = lang_codes[lang_labels.index(new_native)]
        new_target_code = lang_codes[lang_labels.index(new_target)]
        language_svc.set_language_pair(native=new_native_code, target=new_target_code)
        st.success("Language settings saved!")
        st.rerun()

    st.divider()
    st.subheader("🤖 Model Status")

    for slot in ("llm", "vlm", "tts", "stt"):
        available = mm.is_model_available(slot)
        model_id = mm.config[slot]["model"]
        icon = "✅" if available else "⬇️"
        st.write(f"**{slot.upper()}** {icon} — `{model_id}`")
        if not available:
            st.code(mm.get_download_command(slot), language="bash")

    st.divider()
    st.subheader("📊 Level Test")
    level_test_svc = get("level_test_svc")
    _, current_target = language_svc.get_language_pair()
    store = get("store")
    level_data = store.load_level(current_target)

    if level_data.get("level"):
        st.info(f"Current level: **{level_data['level']}** (score: {level_data.get('score', '?')}%)")

    if st.button("🎯 Take Level Test"):
        st.session_state._taking_test = True

    if st.session_state.get("_taking_test"):
        _run_level_test(level_test_svc, current_target, language_svc)


def _run_level_test(level_test_svc, target_lang: str, language_svc) -> None:
    if "test_questions" not in st.session_state:
        with st.spinner("Generating test questions..."):
            st.session_state.test_questions = level_test_svc.generate_questions(target_lang)
        st.session_state.test_answers = {}

    questions = st.session_state.test_questions
    st.subheader(f"Level Test ({len(questions)} questions)")

    for i, q in enumerate(questions):
        st.write(f"**Q{i+1}.** {q['question']}")
        answer = st.radio(
            f"q{i}", q["options"], key=f"test_q_{i}", label_visibility="collapsed"
        )
        st.session_state.test_answers[i] = answer[0]  # "A", "B", "C", or "D"

    if st.button("✅ Submit Test"):
        answers = [st.session_state.test_answers.get(i, "A") for i in range(len(questions))]
        result = level_test_svc.evaluate(questions, answers, target_lang)
        st.success(f"Level assessed: **{result['level']}** ({result['score']}%)")
        del st.session_state.test_questions
        del st.session_state.test_answers
        st.session_state._taking_test = False
        language_svc.update_streak(target_lang)
        st.rerun()
