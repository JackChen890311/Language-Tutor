import os
import tempfile

import streamlit as st

from ui import theme
from ui.components.audio_controls import render_message_with_tts, transcribe_audio
from ui.components.stream_display import stream_with_thinking
from ui.components.word_chip import (
    add_word_suggestions,
    clear_word_suggestions,
    get_word_suggestions,
    rail_is_open,
    render_word_rail,
    reset_word_rail_preference,
    set_rail_open,
)
from ui.state import get


def _save_uploaded_image(uploaded) -> str:
    """Copy an uploaded image to a temp file so the model layer can open it."""
    suffix = os.path.splitext(uploaded.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(uploaded.getvalue())
        return f.name


def _render_sessions(store, target_lang: str, active_session: str | None) -> None:
    st.markdown("##### 💬 Sessions")
    if st.button("➕  New chat", key="new_chat", use_container_width=True, type="secondary"):
        name = "新對話"
        st.session_state.active_session = store.create_chat_session(target_lang, name)
        st.session_state.pop("renaming_session", None)
        clear_word_suggestions()
        reset_word_rail_preference()
        st.rerun()

    with st.container(key="chat_sessions"):
        for s in reversed(store.list_chat_sessions(target_lang)):
            cols = st.columns([6, 1], vertical_alignment="center")
            with cols[0]:
                is_active = s["id"] == active_session
                if st.button(
                    s["name"],
                    key=f"sel_{s['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "tertiary",
                ):
                    st.session_state.active_session = s["id"]
                    st.rerun()
            with cols[1]:
                if st.button("🗑", key=f"del_{s['id']}", type="tertiary", help="Delete chat"):
                    store.delete_chat_session(target_lang, s["id"])
                    if active_session == s["id"]:
                        st.session_state.pop("active_session", None)
                    st.rerun()


def render() -> None:
    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    store = get("store")
    chat_svc = get("chat_svc")
    stt_available = get("mm").is_model_available("stt")

    theme.page_header(
        "💬",
        "Chat",
        "Free conversation with corrections, suggestions and pronunciation.",
    )

    active_session = st.session_state.get("active_session")
    with st.sidebar:
        _render_sessions(store, target_lang, active_session)

    if not active_session:
        theme.empty_state(
            "💬",
            "Pick a conversation",
            "Choose a session in the sidebar, or start a new chat to begin talking.",
        )
        return

    session_info = next(
        (s for s in store.list_chat_sessions(target_lang) if s["id"] == active_session), None
    )

    show_rail = rail_is_open()
    title_col, rename_col = st.columns([6, 1], vertical_alignment="center")
    with title_col:
        st.markdown(f"### {session_info['name'] if session_info else 'Chat'}")
    with rename_col:
        if st.button("✏️", key=f"rename_{active_session}", help="Rename chat", type="tertiary"):
            st.session_state.renaming_session = active_session
            st.rerun()

    if st.session_state.get("renaming_session") == active_session:
        with st.container(key="ltcard_rename"):
            new_name = st.text_input(
                "Chat name",
                value=session_info["name"] if session_info else "",
                key=f"rename_input_{active_session}",
                max_chars=30,
            )
            save_col, cancel_col = st.columns(2)
            with save_col:
                if st.button("Save", key=f"rename_save_{active_session}", type="primary"):
                    if store.rename_chat_session(target_lang, active_session, new_name):
                        st.session_state.pop("renaming_session", None)
                        st.rerun()
                    else:
                        st.warning("Name cannot be empty.")
            with cancel_col:
                if st.button("Cancel", key=f"rename_cancel_{active_session}"):
                    st.session_state.pop("renaming_session", None)
                    st.rerun()

    if show_rail:
        chat_col, rail_col = st.columns([3, 1], gap="large")
    else:
        chat_col, rail_col = st.container(), None

    with chat_col:
        theme.section_header("Conversation", icon="🗨️")

        messages = chat_svc.get_history(target_lang, active_session)
        if not messages:
            theme.empty_state(
                "🌱",
                "Say hello",
                "Try a simple greeting, ask about the weather, or describe your day.",
            )

        for i, msg in enumerate(messages):
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    render_message_with_tts(msg["content"], lang=target_lang, key=f"hist{i}")
                else:
                    st.write(msg["content"])

    if rail_col is not None:
        with rail_col:
            with st.container(key="word_rail"):
                render_word_rail(
                    target_lang,
                    native_lang,
                    title="Suggestions",
                    empty_text="Words worth learning will appear here as you chat.",
                    closable=True,
                )

    suggestions = get_word_suggestions()
    with st.bottom:
        with st.container(key="chat_toolbar"):
            help_text = f"{'Hide' if show_rail else 'Show'} word suggestions"
            if suggestions:
                help_text += f" ({len(suggestions)})"
            if st.button(
                f"💡 Suggestions · {len(suggestions)}" if suggestions else "💡 Suggestions",
                key="toggle_suggestions",
                help=help_text,
                type="primary" if show_rail else "tertiary",
            ):
                set_rail_open(not show_rail)
                st.rerun()

    submission = st.chat_input(
        "Type a message…",
        accept_file=True,
        file_type=["jpg", "jpeg", "png"],
        accept_audio=stt_available,
        audio_sample_rate=16000,
        key=f"composer_{active_session}",
    )
    if not submission:
        return

    final_input = submission.text.strip()
    audio = getattr(submission, "audio", None)
    if audio is not None:
        transcript = transcribe_audio(audio, lang=target_lang, fallback_lang=native_lang)
        if transcript:
            final_input = transcript

    image_path = _save_uploaded_image(submission.files[0]) if submission.files else None
    final_input = final_input or ("📷" if image_path else "")
    if not final_input:
        return

    try:
        history_before = chat_svc.get_history(target_lang, active_session)
        is_first_message = len(history_before) == 0
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

        if is_first_message:
            try:
                auto_title = chat_svc.generate_session_title(native_lang, final_input)
                store.rename_chat_session(target_lang, active_session, auto_title)
            except Exception:
                pass

        language_svc.update_streak(target_lang)
        st.rerun()
    finally:
        if image_path:
            os.unlink(image_path)
