import gc

from models.base import BaseSTT


class WhisperModel(BaseSTT):
    def __init__(self, model_name: str = "whisper-large-v3"):
        self._model_name = model_name
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            import mlx_whisper
            self._model = mlx_whisper

    def load(self) -> None:
        self._ensure_loaded()

    def transcribe(self, audio: str | bytes) -> str:
        import tempfile
        self._ensure_loaded()
        if isinstance(audio, bytes):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio)
                audio_path = f.name
        else:
            audio_path = audio
        result = self._model.transcribe(
            audio_path, path_or_hf_repo=f"mlx-community/{self._model_name}"
        )
        return result.get("text", "").strip()

    def unload(self) -> None:
        self._model = None
        gc.collect()
