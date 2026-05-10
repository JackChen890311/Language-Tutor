import gc

from models.base import BaseTTS


class MLXTTSModel(BaseTTS):
    def __init__(self, model_name: str = "kokoro"):
        self._model_name = model_name
        self._pipeline = None

    def _ensure_loaded(self) -> None:
        if self._pipeline is None:
            from mlx_audio.tts.models.kokoro import KokoroPipeline
            self._pipeline = KokoroPipeline(
                lang_code="j",
                model=True,
                repo_id="prince-canuma/Kokoro-82M",
            )  # multilingual; model=True auto-loads KokoroModel weights

    def load(self) -> None:
        self._ensure_loaded()

    def synthesize(self, text: str, lang: str) -> bytes:
        import io
        import wave
        import numpy as np
        self._ensure_loaded()
        audio_chunks = []
        for _, _, audio in self._pipeline(text, voice="af_heart"):
            if audio is not None:
                audio_chunks.append(audio)
        if not audio_chunks:
            return b""
        combined = np.concatenate(audio_chunks)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes((combined * 32767).astype(np.int16).tobytes())
        return buf.getvalue()

    def unload(self) -> None:
        self._pipeline = None
        gc.collect()
