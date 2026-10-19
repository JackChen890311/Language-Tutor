import streamlit as st

from ui import theme
from ui.state import get

_STATE_KEY = "word_suggestions"


def merge_word_suggestions(existing: list[dict], new: list[dict], cap: int = 12) -> list[dict]:
    """Newest first, deduped by word, capped at `cap`."""
    merged = list(existing)
    for suggestion in new:
        word = suggestion.get("word", "")
        merged = [s for s in merged if s.get("word") != word]
        merged.insert(0, suggestion)
    return merged[:cap]


def get_word_suggestions() -> list[dict]:
    """The single word-suggestion list shared across Chat and every Lesson."""
    return st.session_state.setdefault(_STATE_KEY, [])


def add_word_suggestions(new: list[dict], cap: int = 12) -> None:
    st.session_state[_STATE_KEY] = merge_word_suggestions(get_word_suggestions(), new, cap=cap)


def clear_word_suggestions() -> None:
    """Clear the shared word-suggestion list (e.g. when starting a new chat)."""
    st.session_state[_STATE_KEY] = []


def render_word_chips(word_list: list[dict], lang: str, native_lang: str) -> None:
    for suggestion in word_list:
        word = suggestion.get("word", "")
        reading = suggestion.get("reading", "")
        reading_html = (
            f'<div class="lt-wchip-reading">{theme.esc(reading)}</div>' if reading else ""
        )
        with st.container(key=f"wchip_{word}"):
            text_col, save_col = st.columns([5, 1], vertical_alignment="center")
            with text_col:
                st.markdown(
                    f'<div class="lt-wchip-word">{theme.esc(word)}</div>{reading_html}',
                    unsafe_allow_html=True,
                )
            with save_col:
                if st.button(
                    "＋",
                    key=f"save_word_{word}",
                    help=f"Save “{word}” to your word list",
                    type="tertiary",
                ):
                    word_svc = get("word_svc")
                    word_svc.add_word(lang, native_lang, word, reading=reading, source="chat")
                    st.toast(f"✅ Saved: {word}")
