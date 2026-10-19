from datetime import date, datetime

import streamlit as st

from ui import theme
from ui.labels import language_name
from ui.state import get


def _count(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _go(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def render() -> None:
    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    target_name = language_name(target_lang)

    language_svc.update_streak(target_lang)
    stats = language_svc.get_stats(target_lang)
    store = get("store")
    mm = get("mm")

    theme.page_header("🏠", "Home", f"Your {target_name} practice at a glance.")

    streak = stats["streak"]
    greeting = theme.greeting_for_hour(datetime.now().hour)
    streak_line = (
        f"{_count(streak, 'day', 'days')} in a row — keep the habit alive"
        if streak > 1
        else "A fresh start today. One small step is enough."
    )
    theme.hero(
        title_html=(
            f'Keep your <span class="lt-hl">{theme.esc(target_name)}</span> momentum going'
        ),
        greeting=f"{greeting} 👋",
        subtitle=streak_line,
        chips=[
            theme.chip(f"📚 {_count(stats['words_saved'], 'word', 'words')}"),
            theme.chip(f"📖 {_count(stats['lessons_completed'], 'lesson', 'lessons')}"),
            theme.chip(f"✅ {stats['words_reviewed_this_week']} reviewed this week"),
        ],
    )

    theme.section_header("Your progress", icon="📈")
    theme.stat_grid(
        [
            ("🔥", str(streak), "Day streak", "Consecutive active days"),
            ("📚", str(stats["words_saved"]), "Words saved", "In your word list"),
            ("📖", str(stats["lessons_completed"]), "Lessons", "Completed so far"),
            ("✅", str(stats["words_reviewed_this_week"]), "Reviewed", "In the last 7 days"),
        ]
    )

    days = theme.activity_days(language_svc.get_active_dates(target_lang), date.today().isoformat())
    if days:
        theme.section_header("This week", icon="🗓️")
        theme.activity_strip(days)

    theme.section_header("Jump back in", icon="⚡")
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        with st.container(key="ltcardhover_quick_lesson"):
            st.markdown("**📝 Start a lesson**")
            st.caption("Vocabulary, grammar and conversation.")
            if st.button("Open Lesson", key="home_lesson", use_container_width=True):
                _go("Lesson")
    with col2:
        with st.container(key="ltcardhover_quick_chat"):
            st.markdown("**💬 Free chat**")
            st.caption("Talk about anything you like.")
            if st.button("Open Chat", key="home_chat", use_container_width=True):
                _go("Chat")
    with col3:
        with st.container(key="ltcardhover_quick_review"):
            st.markdown("**🔁 Review words**")
            st.caption("Flashcards and quick drills.")
            if st.button("Open Word List", key="home_review", use_container_width=True):
                _go("Word List")

    sessions = store.list_chat_sessions(target_lang)
    theme.section_header(
        "Recent chats", caption=f"{len(sessions)} total" if sessions else None, icon="💬"
    )
    if not sessions:
        theme.empty_state(
            "💬",
            "No chats yet",
            "Start a conversation and your sessions will show up here.",
        )
    else:
        for session in reversed(sessions[-4:]):
            with st.container(key=f"ltcard_chat_{session['id']}"):
                info_col, open_col = st.columns([5, 1], vertical_alignment="center")
                with info_col:
                    st.markdown(f"**{session['name']}**")
                    st.caption(f"Last opened {str(session.get('created_at', ''))[:10]}")
                with open_col:
                    if st.button(
                        "Open",
                        key=f"home_open_{session['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.active_session = session["id"]
                        _go("Chat")

    ready = sum(mm.is_model_available(slot) for slot in ("llm", "vlm", "tts", "stt"))
    if ready < 4:
        theme.section_header("Optional models", icon="🧩")
        theme.empty_state(
            "🧩",
            f"{ready} of 4 models ready",
            "Vision, text-to-speech and voice input are optional. "
            "Add them in Settings whenever you want them.",
        )
