import streamlit as st

from ui import theme
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
    language_svc = get("language_svc")
    mm = get("mm")
    native_lang, target_lang = language_svc.get_language_pair()

    theme.page_header("⚙️", "Settings", "Languages, models and saved history.")

    with st.container(key="ltcard_languages"):
        theme.section_header("Language pair", icon="🌐")
        lang_codes = list(SUPPORTED_LANGUAGES.keys())
        lang_labels = list(SUPPORTED_LANGUAGES.values())

        col1, col2 = st.columns(2)
        with col1:
            native_idx = lang_codes.index(native_lang) if native_lang in lang_codes else 0
            new_native = st.selectbox("I speak", lang_labels, index=native_idx)
        with col2:
            target_idx = lang_codes.index(target_lang) if target_lang in lang_codes else 2
            new_target = st.selectbox("I'm learning", lang_labels, index=target_idx)

        if st.button("💾  Save language settings", type="primary"):
            new_native_code = lang_codes[lang_labels.index(new_native)]
            new_target_code = lang_codes[lang_labels.index(new_target)]
            language_svc.set_language_pair(native=new_native_code, target=new_target_code)
            st.success("Language settings saved.")
            st.rerun()

    theme.section_header("Model status", caption="All on-device", icon="🤖")
    slots = [
        ("llm", "LLM", "Conversation and lessons", "🧠"),
        ("vlm", "Vision", "Image chat", "📷"),
        ("tts", "Speech", "Pronunciation playback", "🔊"),
        ("stt", "Voice", "Spoken input", "🎤"),
    ]
    grid = st.columns(2)
    for i, (slot, label, purpose, icon) in enumerate(slots):
        available = mm.is_model_available(slot)
        model_id = mm.config[slot]["model"]
        with grid[i % 2]:
            with st.container(key=f"ltcard_model_{slot}"):
                head_col, badge_col = st.columns([4, 1], vertical_alignment="center")
                with head_col:
                    st.markdown(f"**{icon} {label}**")
                with badge_col:
                    if available:
                        st.badge("Ready", color="green")
                    else:
                        st.badge("Missing", color="orange")
                st.caption(purpose)
                st.code(model_id, language=None)
                if not available:
                    st.code(mm.get_download_command(slot), language="bash")

    theme.section_header("Danger zone", icon="⚠️")
    with st.container(key="ltcard_danger"):
        store = get("store")
        st.caption(
            f"Permanently delete all chats, saved words, lessons and progress for "
            f"**{target_lang}**. This cannot be undone."
        )

        if not st.session_state.get("_confirm_clear"):
            if st.button("🗑️  Clear all history", type="secondary"):
                st.session_state._confirm_clear = True
                st.rerun()
        else:
            st.warning(
                "This will delete **all** chat history, saved words, lesson notes and "
                "progress for this language. This cannot be undone."
            )
            col_yes, col_no = st.columns([1, 2])
            with col_yes:
                if st.button("Yes, delete everything", type="primary"):
                    store.clear_language_history(target_lang)
                    for key in [
                        "_confirm_clear",
                        "active_lesson",
                        "suggested_topics",
                        "test_questions",
                        "test_answers",
                        "test_result",
                    ]:
                        st.session_state.pop(key, None)
                    st.success("All history cleared.")
                    st.rerun()
            with col_no:
                if st.button("Cancel"):
                    st.session_state._confirm_clear = False
                    st.rerun()
