import streamlit as st
from ui.state import init_services, get

_NAV = [
    ("🏠", "Home"),
    ("📝", "Lesson"),
    ("💬", "Chat"),
    ("📚", "Word List"),
    ("🧪", "Test"),
    ("⚙️", "Settings"),
]

_SIDEBAR_CSS = """
<style>
/* Tighten sidebar padding */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
}
/* Nav buttons: full-width, left-aligned text */
section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left !important;
    justify-content: flex-start;
    border-radius: 10px;
    padding: 0.55rem 0.9rem;
    font-size: 0.97rem;
    font-weight: 500;
    margin-bottom: 2px;
    border: none;
    transition: background 0.15s;
}
/* Inactive buttons: subtle */
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: transparent;
    color: inherit;
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: rgba(128,128,128,0.12);
}
/* Active button: accent fill */
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f8ef7 0%, #7c5cfc 100%);
    color: white;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    opacity: 0.9;
}
</style>
"""


def main() -> None:
    st.set_page_config(page_title="Language Tutor", page_icon="🗣️", layout="wide")
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
    init_services()

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()

    if "page" not in st.session_state:
        st.session_state.page = "Home"

    with st.sidebar:
        st.markdown("### 🗣️ Language Tutor")
        st.markdown(
            f"<div style='font-size:0.85rem;color:grey;margin-bottom:0.75rem'>"
            f"<b>{native_lang}</b> → <b>{target_lang}</b></div>",
            unsafe_allow_html=True,
        )
        st.divider()

        mm = get("mm")
        if not mm.is_model_available("llm"):
            st.error("⚠️ LLM not downloaded")
            st.code(mm.get_download_command("llm"))
            st.stop()

        word_svc = get("word_svc")
        has_stale = word_svc.has_stale_words(target_lang)

        for emoji, name in _NAV:
            badge = " 🔴" if name == "Word List" and has_stale else ""
            label = f"{emoji}  {name}{badge}"
            active = st.session_state.page == name
            if st.button(
                label,
                key=f"nav_{name}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.page = name
                st.rerun()

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


if __name__ == "__main__":
    main()
