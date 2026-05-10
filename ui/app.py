import streamlit as st
from ui.state import init_services, get


def main() -> None:
    st.set_page_config(page_title="Language Tutor 🗣️", page_icon="🗣️", layout="wide")
    init_services()

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()

    with st.sidebar:
        st.title("🗣️ Language Tutor")
        st.caption(f"**{native_lang}** → **{target_lang}**")
        st.divider()

        mm = get("mm")
        if not mm.is_model_available("llm"):
            st.error("⚠️ LLM not downloaded")
            st.code(mm.get_download_command("llm"))
            st.stop()

        word_svc = get("word_svc")
        has_stale = word_svc.has_stale_words(target_lang)
        word_list_label = "📚 Word List 🔴" if has_stale else "📚 Word List"

        page = st.radio(
            "nav",
            ["🏠 Home", "📝 Lesson", "💬 Chat", word_list_label, "⚙️ Settings"],
            label_visibility="collapsed",
        )

    if page == "🏠 Home":
        from ui.pages import home
        home.render()
    elif page == "📝 Lesson":
        from ui.pages import lesson
        lesson.render()
    elif page == "💬 Chat":
        from ui.pages import chat
        chat.render()
    elif word_list_label in page or page == "📚 Word List":
        from ui.pages import word_list
        word_list.render()
    elif page == "⚙️ Settings":
        from ui.pages import settings
        settings.render()


if __name__ == "__main__":
    main()
