import streamlit as st

from ui import theme
from ui.components.audio_controls import autoplay_audio_html
from ui.state import get

_STATE_KEY = "word_suggestions"
_TOGGLE_KEY = "show_word_suggestions"
_TOAST_KEY = "word_suggestion_toast"


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


def rail_is_open() -> bool:
    """Whether the suggestion rail should render.

    Until the user makes an explicit choice the rail follows the suggestion
    list: it opens as soon as the first word arrives.
    """
    if _TOGGLE_KEY not in st.session_state:
        return bool(get_word_suggestions())
    return bool(st.session_state[_TOGGLE_KEY])


def set_rail_open(open_: bool) -> None:
    """Remember an explicit open/closed choice for the suggestion rail."""
    st.session_state[_TOGGLE_KEY] = bool(open_)


def reset_word_rail_preference() -> None:
    """Forget the explicit choice so the rail goes back to auto-open behaviour."""
    st.session_state.pop(_TOGGLE_KEY, None)


def render_word_rail(
    lang: str,
    native_lang: str,
    *,
    title: str = "Suggestions",
    empty_text: str = "Words worth learning will appear here as you chat.",
    closable: bool = False,
) -> None:
    """Render the single-column, card-style word suggestion rail."""
    suggestions = get_word_suggestions()

    flash = st.session_state.pop(_TOAST_KEY, None)
    if flash:
        st.toast(flash)

    heading = f"{title} · {len(suggestions)}" if suggestions else title
    if closable:
        title_col, close_col = st.columns([6, 1], vertical_alignment="center")
        with title_col:
            theme.section_header(heading, icon="💡")
        with close_col:
            if st.button(
                "✕",
                key="close_word_rail",
                help="Hide word suggestions",
                type="tertiary",
            ):
                set_rail_open(False)
                st.rerun()
    else:
        theme.section_header(heading, icon="💡")

    if not suggestions:
        st.caption(empty_text)
        return

    saved_words = {w.get("word") for w in get("word_svc").get_all_words(lang)}
    mm = get("mm")
    tts_available = mm.is_model_available("tts")
    for suggestion in suggestions:
        _render_suggestion_card(suggestion, lang, native_lang, saved_words, mm, tts_available)


def _render_suggestion_card(
    suggestion: dict,
    lang: str,
    native_lang: str,
    saved_words: set[str],
    mm,
    tts_available: bool,
) -> None:
    word = suggestion.get("word", "")
    reading = suggestion.get("reading", "")
    reading_html = f'<div class="lt-wchip-reading">{theme.esc(reading)}</div>' if reading else ""
    is_saved = word in saved_words

    with st.container(key=f"wchip_{word}"):
        st.markdown(
            f'<div class="lt-wchip-word">{theme.esc(word)}</div>{reading_html}',
            unsafe_allow_html=True,
        )

        if tts_available:
            audio_col, save_col = st.columns(2)
        else:
            audio_col, save_col = None, st.container()

        if audio_col is not None:
            with audio_col:
                if st.button(
                    "🔊",
                    key=f"tts_word_{word}",
                    help=f"Hear “{word}”",
                    type="tertiary",
                    use_container_width=True,
                ):
                    with st.spinner(""):
                        audio_bytes = mm.get_tts().synthesize(word, lang=lang)
                    st.html(autoplay_audio_html(audio_bytes))

        with save_col:
            if is_saved:
                st.button(
                    "✓",
                    key=f"saved_word_{word}",
                    help="Already in your word list",
                    type="tertiary",
                    disabled=True,
                    use_container_width=True,
                )
            elif st.button(
                "＋",
                key=f"save_word_{word}",
                help=f"Save “{word}” to your word list",
                type="tertiary",
                use_container_width=True,
            ):
                word_svc = get("word_svc")
                word_svc.add_word(lang, native_lang, word, reading=reading, source="chat")
                st.session_state[_TOAST_KEY] = f"✅ Saved: {word}"
                st.rerun()
