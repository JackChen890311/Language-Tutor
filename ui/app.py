import streamlit as st

from ui import theme
from ui.labels import language_pair_label
from ui.state import get, init_services

_NAV = [
    ("🏠", "Home"),
    ("📝", "Lesson"),
    ("💬", "Chat"),
    ("📚", "Word List"),
    ("🧪", "Test"),
    ("⚙️", "Settings"),
]


def _render_sidebar_top(native_lang: str, target_lang: str) -> None:
    mm = get("mm")
    if not mm.is_model_available("llm"):
        st.error("⚠️ LLM not downloaded")
        st.code(mm.get_download_command("llm"))
        st.stop()

    stale_count = len(get("word_svc").get_stale_words(target_lang))

    st.html(
        '<div class="lt-brand"><div class="lt-brand-mark">🗣️</div>'
        '<div><div class="lt-brand-name">Language Tutor</div>'
        '<div class="lt-brand-sub">On-device · private</div></div></div>'
        f'<div class="lt-langpair">{language_pair_label(native_lang, target_lang)}</div>'
    )

    with st.container(key="nav"):
        for emoji, name in _NAV:
            label = f"{emoji}   {name}"
            if name == "Word List" and stale_count:
                label += f"   · {stale_count}"
            active = st.session_state.page == name
            if st.button(
                label,
                key=f"nav_{name}",
                use_container_width=True,
                type="primary" if active else "tertiary",
            ):
                st.session_state.page = name
                st.rerun()


def _render_sidebar_footer(target_lang: str) -> None:
    mm = get("mm")
    streak = get("language_svc").get_stats(target_lang)["streak"]
    slots = [("LLM", "llm"), ("Vision", "vlm"), ("Speech", "tts"), ("Voice", "stt")]
    dots = "".join(
        f'<span class="lt-dot{" is-on" if mm.is_model_available(slot) else ""}"></span>'
        for _, slot in slots
    )
    st.html(
        '<div class="lt-sidefoot">'
        f'<div class="lt-sidefoot-row"><span>🔥 Streak</span><b>{streak} days</b></div>'
        f'<div class="lt-sidefoot-row"><span>Models</span>'
        f'<span class="lt-dots">{dots}</span></div>'
        "</div>"
    )


def main() -> None:
    st.set_page_config(
        page_title="Language Tutor",
        page_icon="🗣️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    theme.inject()
    init_services()

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()

    if "page" not in st.session_state:
        st.session_state.page = "Home"

    with st.sidebar:
        _render_sidebar_top(native_lang, target_lang)

    page = st.session_state.page

    if page == "Home":
        from ui.pages import home

        home.render()
    elif page == "Lesson":
        from ui.pages import lesson

        lesson.render()
    elif page == "Chat":
        from ui.pages import chat

        chat.render()
    elif page == "Word List":
        from ui.pages import word_list

        word_list.render()
    elif page == "Test":
        from ui.pages import test

        test.render()
    elif page == "Settings":
        from ui.pages import settings

        settings.render()

    with st.sidebar:
        _render_sidebar_footer(target_lang)


if __name__ == "__main__":
    main()
