import gc

from models.base import BaseTTS

_LANG_CODE_MAP = {
    "ja": "j",
    "en": "a",
    "zh": "z",
}

_VOICE_MAP = {
    "j": "jf_alpha",
    "a": "af_heart",
    "z": "zf_xiaobei",
}


class MLXTTSModel(BaseTTS):
    def __init__(self, model_name: str = "prince-canuma/Kokoro-82M"):
        self._model_name = model_name
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from mlx_audio.tts.utils import load

            self._model = load(self._model_name)

    def load(self) -> None:
        self._ensure_loaded()

    def synthesize(self, text: str, lang: str) -> bytes:
        import io
        import wave
        import numpy as np

        self._ensure_loaded()
        lang_code = _LANG_CODE_MAP.get(lang, "a")
        voice = _VOICE_MAP.get(lang_code, "af_heart")
        audio_chunks = []
        sample_rate = 24000
        for result in self._model.generate(text, voice=voice, lang_code=lang_code):
            if result.audio is not None:
                audio_chunks.append(np.array(result.audio))
                sample_rate = result.sample_rate
        if not audio_chunks:
            return b""
        combined = np.concatenate(audio_chunks)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes((combined * 32767).astype(np.int16).tobytes())
        return buf.getvalue()

    def unload(self) -> None:
        self._model = None
        gc.collect()
