import tempfile
import streamlit as st
from ui.state import get
from ui.components.word_chip import render_word_chips, add_word_suggestions, get_word_suggestions
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

    # Toggle button for word suggestions at top of chat
    show_suggestions = st.session_state.get("show_word_suggestions", False)
    if st.button("💡 Word Suggestions" + (" ✅" if show_suggestions else " 🔄"), key="toggle_suggestions"):
        st.session_state.show_word_suggestions = not show_suggestions
        st.rerun()

    # Show word suggestions in 3-column layout at top (when toggled)
    if show_suggestions:
        st.markdown("---")
        # Get all word suggestions to distribute evenly across columns
        word_suggestions = get_word_suggestions()

        if word_suggestions:
            col1, col2, col3 = st.columns([1, 1, 1])

            # Calculate split points for even distribution
            total_words = len(word_suggestions)
            col1_count = (total_words + 2) // 3  # Round up to handle odd numbers
            col2_count = (total_words + 1) // 3

            # Split words into three groups
            col1_words = word_suggestions[:col1_count]
            col2_words = word_suggestions[col1_count:col1_count + col2_count]
            col3_words = word_suggestions[col1_count + col2_count:]

            with col1:
                st.markdown("### Column 1")
                # Use a temporary approach to display just these words
                for suggestion in col1_words:
                    word = suggestion.get("word", "")
                    reading = suggestion.get("reading", "")
                    if reading:
                        st.write(f"{word} ({reading})")
                    else:
                        st.write(word)

            with col2:
                st.markdown("### Column 2")
                for suggestion in col2_words:
                    word = suggestion.get("word", "")
                    reading = suggestion.get("reading", "")
                    if reading:
                        st.write(f"{word} ({reading})")
                    else:
                        st.write(word)

            with col3:
                st.markdown("### Column 3")
                for suggestion in col3_words:
                    word = suggestion.get("word", "")
                    reading = suggestion.get("reading", "")
                    if reading:
                        st.write(f"{word} ({reading})")
                    else:
                        st.write(word)
        else:
            # If no words, show empty columns
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.markdown("### Column 1")
                st.write("No suggestions available")
            with col2:
                st.markdown("### Column 2")
                st.write("No suggestions available")
            with col3:
                st.markdown("### Column 3")
                st.write("No suggestions available")

    # Main chat area below (single column for actual chatting)
    st.markdown("---")

    col1 = st.container()
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
        add_word_suggestions(result.get("word_suggestions", []))

        language_svc.update_streak(target_lang)
        st.rerun()
