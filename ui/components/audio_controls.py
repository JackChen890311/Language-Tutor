import tempfile
import streamlit as st
from ui.state import get


def render_tts_button(text: str, lang: str, key: str) -> None:
    mm = get("mm")
    if not mm.is_model_available("tts"):
        return
    if st.button("🔊", key=f"tts_{key}", help="Play audio"):
        with st.spinner("Generating audio..."):
            tts = mm.get_tts()
            audio_bytes = tts.synthesize(text, lang=lang)
        st.audio(audio_bytes, format="audio/wav")


def render_stt_input(key: str) -> str | None:
    mm = get("mm")
    if not mm.is_model_available("stt"):
        return None
    audio = st.audio_input("🎤 Speak", key=f"stt_{key}")
    if audio:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio.getvalue())
            tmp_path = f.name
        with st.spinner("Transcribing..."):
            stt = mm.get_stt()
            return stt.transcribe(tmp_path)
    return None
