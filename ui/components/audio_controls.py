import base64
import re
import tempfile
import streamlit as st
from ui.state import get

# Tolerates malformed tags the model occasionally emits (e.g. "<s speak>"
# instead of "<speak>") by only requiring "speak" as a whole word inside
# the angle brackets, rather than an exact "<speak>"/"</speak>" match.
_SPEAK_BLOCK_RE = re.compile(r"<[^>]*\bspeak\b[^>]*>(.*?)</[^>]*\bspeak\b[^>]*>", re.DOTALL)


def extract_speak_text(text: str) -> str:
    chunks = [m.group(1) for m in _SPEAK_BLOCK_RE.finditer(text)]
    stripped = [c.strip() for c in chunks if c.strip()]
    return " ".join(stripped) if stripped else text


def parse_message_segments(text: str) -> list[dict]:
    segments = []
    pos = 0
    for m in _SPEAK_BLOCK_RE.finditer(text):
        if m.start() > pos:
            segments.append({"type": "text", "content": text[pos : m.start()]})
        content = m.group(1).strip()
        if content:
            segments.append({"type": "speak", "content": content})
        pos = m.end()
    if pos < len(text):
        segments.append({"type": "text", "content": text[pos:]})
    return segments


def autoplay_audio_html(audio_bytes: bytes) -> str:
    encoded = base64.b64encode(audio_bytes).decode()
    return (
        f'<audio autoplay style="display:none">'
        f'<source src="data:audio/wav;base64,{encoded}" type="audio/wav">'
        f"</audio>"
    )


def render_message_with_tts(text: str, lang: str, key: str) -> None:
    mm = get("mm")
    tts_available = mm.is_model_available("tts")
    segments = parse_message_segments(text)

    for i, seg in enumerate(segments):
        if seg["type"] == "text":
            st.markdown(seg["content"])
        else:
            col_text, col_btn = st.columns([10, 1])
            with col_text:
                st.markdown(f"**{seg['content']}**")
            with col_btn:
                if tts_available and st.button("🔊", key=f"tts_{key}_{i}", help="Play audio"):
                    with st.spinner(""):
                        tts = mm.get_tts()
                        audio_bytes = tts.synthesize(seg["content"], lang=lang)
                    st.html(autoplay_audio_html(audio_bytes))


def render_tts_button(text: str, lang: str, key: str) -> None:
    mm = get("mm")
    if not mm.is_model_available("tts"):
        return
    if st.button("🔊", key=f"tts_{key}", help="Play audio"):
        with st.spinner("Generating audio..."):
            tts = mm.get_tts()
            audio_bytes = tts.synthesize(extract_speak_text(text), lang=lang)
        st.html(autoplay_audio_html(audio_bytes))


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
