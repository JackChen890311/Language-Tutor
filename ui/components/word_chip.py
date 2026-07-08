from typing import Callable

import streamlit as st
from ui.state import get

_CHIP_CSS = """
<style>
.word-chip {
    background: rgba(79, 142, 247, 0.1);
    border: 1px solid rgba(79, 142, 247, 0.3);
    border-radius: 10px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.4rem;
}
.word-chip .word { font-size: 1.05rem; font-weight: 600; }
.word-chip .reading { font-size: 0.8rem; color: grey; }
</style>
"""


def merge_word_suggestions(existing: list[dict], new: list[dict], cap: int = 10) -> list[dict]:
    """Newest first, deduped by word, capped at `cap`."""
    merged = list(existing)
    for suggestion in new:
        word = suggestion.get("word", "")
        merged = [s for s in merged if s.get("word") != word]
        merged.insert(0, suggestion)
    return merged[:cap]


def render_word_chips(
    suggestions: list[dict], lang: str, native_lang: str, on_save: Callable[[str], None]
) -> None:
    if not suggestions:
        return
    st.markdown(_CHIP_CSS, unsafe_allow_html=True)
    st.caption("💡 Word suggestions")
    for i, suggestion in enumerate(suggestions):
        word = suggestion.get("word", "")
        reading = suggestion.get("reading", "")
        reading_html = f'<div class="reading">{reading}</div>' if reading else ""
        st.markdown(
            f'<div class="word-chip"><div class="word">{word}</div>{reading_html}</div>',
            unsafe_allow_html=True,
        )
        if st.button("💾 Save", key=f"save_word_{i}_{word}", use_container_width=True):
            word_svc = get("word_svc")
            word_svc.add_word(lang, native_lang, word, reading=reading, source="chat")
            st.toast(f"✅ Saved: {word}")
            on_save(word)
            st.rerun()
