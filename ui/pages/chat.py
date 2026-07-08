import tempfile
import streamlit as st
from ui.state import get
from ui.components.word_chip import render_word_chips, merge_word_suggestions
from ui.components.audio_controls import render_message_with_tts, render_stt_input
from ui.components.stream_display import stream_with_thinking


def render() -> None:
    st.title("💬 Chat")

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    store = get("store")
    chat_svc = get("chat_svc")

    with st.sidebar:
        st.subheader("Sessions")
        sessions = store.list_chat_sessions(target_lang)

        if st.button("➕ New Chat"):
            name = f"Chat {len(sessions) + 1}"
            st.session_state.active_session = store.create_chat_session(target_lang, name)
            st.rerun()

        for s in reversed(sessions):
            cols = st.columns([4, 1])
            with cols[0]:
                if st.button(s["name"], key=f"sel_{s['id']}"):
                    st.session_state.active_session = s["id"]
                    st.rerun()
            with cols[1]:
                if st.button("🗑", key=f"del_{s['id']}"):
                    store.delete_chat_session(target_lang, s["id"])
                    if st.session_state.get("active_session") == s["id"]:
                        st.session_state.pop("active_session", None)
                    st.rerun()

    active_session = st.session_state.get("active_session")
    if not active_session:
        st.info("Select or create a chat session from the sidebar.")
        return

    session_info = next((s for s in sessions if s["id"] == active_session), None)

    chat_word_suggestions = st.session_state.setdefault("chat_word_suggestions", {})

    def _on_save(word: str) -> None:
        chat_word_suggestions[active_session] = [
            s for s in chat_word_suggestions.get(active_session, []) if s.get("word") != word
        ]

    col1, col2 = st.columns([3, 1])

    with col1:
        if session_info:
            st.subheader(session_info["name"])

        messages = chat_svc.get_history(target_lang, active_session)
        for msg in messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    render_message_with_tts(
                        msg["content"], lang=target_lang, key=msg["content"][:20]
                    )
                else:
                    st.write(msg["content"])

        uploaded_image = st.file_uploader(
            "📷 Attach image (optional)",
            type=["jpg", "jpeg", "png"],
            key=f"img_{active_session}",
            label_visibility="collapsed",
        )
        image_path = None
        if uploaded_image:
            import os

            suffix = os.path.splitext(uploaded_image.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(uploaded_image.getvalue())
                image_path = f.name

    with col2:
        render_word_chips(
            chat_word_suggestions.get(active_session, []),
            lang=target_lang,
            native_lang=native_lang,
            on_save=_on_save,
        )

    stt_text = render_stt_input(key=active_session)
    user_input = st.chat_input("Type a message...")
    final_input = stt_text or user_input

    if final_input:
        with st.chat_message("user"):
            st.write(final_input)

        collector = chat_svc.stream_message(
            lang=target_lang,
            session_id=active_session,
            native_lang=native_lang,
            user_text=final_input,
            image_path=image_path,
        )
        with st.chat_message("assistant"):
            stream_with_thinking(collector)
            render_message_with_tts(collector.full_text, lang=target_lang, key="latest")

        result = chat_svc.commit_message(
            lang=target_lang,
            session_id=active_session,
            native_lang=native_lang,
            user_text=final_input,
            raw_response=collector.full_text,
        )
        chat_word_suggestions[active_session] = merge_word_suggestions(
            chat_word_suggestions.get(active_session, []),
            result.get("word_suggestions", []),
        )

        language_svc.update_streak(target_lang)
        st.rerun()
