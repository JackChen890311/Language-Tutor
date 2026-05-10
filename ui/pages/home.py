import streamlit as st
from ui.state import get

_LANG_NAMES = {
    "zh-TW": "Traditional Chinese", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "en": "English", "es": "Spanish", "fr": "French", "de": "German",
}


def render() -> None:
    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    target_name = _LANG_NAMES.get(target_lang, target_lang)

    st.title("🏠 Home")
    language_svc.update_streak(target_lang)
    stats = language_svc.get_stats(target_lang)

    st.subheader(f"Learning **{target_name}** · {stats['level'] or 'Level not set'}")

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
        slots = [("📷", "vlm"), ("🔊", "tts"), ("🎤", "stt")]
        ready = sum(mm.is_model_available(s) for _, s in slots)
        st.metric("Optional Models", f"{ready} / {len(slots)} ready")
        badges = " · ".join(
            f"{'✅' if mm.is_model_available(s) else '⬇️'} {e}"
            for e, s in slots
        )
        st.caption(badges)

    st.divider()

    store = get("store")
    sessions = store.list_chat_sessions(target_lang)
    if sessions:
        st.subheader("💬 Recent Chats")
        for session in reversed(sessions[-3:]):
            st.write(f"• {session['name']} — {session['created_at'][:10]}")
