import streamlit as st
from ui.state import get


def render_word_chip(suggestion: dict, lang: str, native_lang: str, idx: int = 0) -> None:
    word = suggestion.get("word", "")
    reading = suggestion.get("reading", "")
    label = f"💾 Save: {word}" + (f" ({reading})" if reading else "")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📌 New word suggestion: **{word}** {reading}")
    with col2:
        if st.button(label, key=f"save_word_{idx}_{word}"):
            word_svc = get("word_svc")
            word_svc.add_word(lang, native_lang, word, reading=reading, source="chat")
            st.toast(f"✅ Saved: {word}")
