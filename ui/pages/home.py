import streamlit as st
from ui.state import get


def render() -> None:
    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()

    st.title("🏠 Home")
    language_svc.update_streak(target_lang)
    stats = language_svc.get_stats(target_lang)

    st.subheader(f"Learning **{target_lang}** · {stats['level'] or 'Level not set'}")

    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    with col1:
        st.metric("🔥 Streak", f"{stats['streak']} days")
    with col2:
        st.metric("📚 Words Saved", stats["words_saved"])
    with col3:
        st.metric("📖 Lessons", stats["lessons_completed"])
    with col4:
        st.metric("✅ Reviewed This Week", stats["words_reviewed_this_week"])
    with col5:
        st.metric("📅 Last Active", stats["last_active"] or "Today")
    with col6:
        mm = get("mm")
        vlm_ok = "✅" if mm.is_model_available("vlm") else "⬇️"
        tts_ok = "✅" if mm.is_model_available("tts") else "⬇️"
        stt_ok = "✅" if mm.is_model_available("stt") else "⬇️"
        st.metric("Models", f"VLM {vlm_ok} TTS {tts_ok} STT {stt_ok}")

    st.divider()

    store = get("store")
    sessions = store.list_chat_sessions(target_lang)
    if sessions:
        st.subheader("💬 Recent Chats")
        for session in reversed(sessions[-3:]):
            st.write(f"• {session['name']} — {session['created_at'][:10]}")
