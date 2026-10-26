import gc

from models.base import BaseSTT


class WhisperModel(BaseSTT):
    # Whisper expects bare ISO-639-1 codes, so regional variants collapse.
    _LANG_MAP = {"zh-TW": "zh", "zh-HK": "zh", "zh-CN": "zh"}

    # A fallback language must beat the target language by this much average
    # log-probability per token before we trust it. Forcing the wrong language
    # yields visibly lower confidence, but keeping a margin means a clip that
    # is plausibly Japanese stays Japanese.
    _FALLBACK_MARGIN = 0.15

    def __init__(self, model_name: str = "mlx-community/whisper-large-v3-turbo"):
        self._model_name = model_name
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            import mlx_whisper

            self._model = mlx_whisper

    def load(self) -> None:
        self._ensure_loaded()

    def _decode(self, audio_path: str, lang: str | None) -> dict:
        kwargs = {"path_or_hf_repo": self._model_name, "task": "transcribe"}
        if lang:
            # Pin the language instead of relying on Whisper's auto-detect:
            # turbo mislabels short Japanese clips as English and then
            # transcribes them as English text.
            kwargs["language"] = self._LANG_MAP.get(lang, lang)
        return self._model.transcribe(audio_path, **kwargs)

    @staticmethod
    def _confidence(result: dict) -> float:
        logprobs = [
            seg["avg_logprob"]
            for seg in result.get("segments") or []
            if seg.get("avg_logprob") is not None
        ]
        return sum(logprobs) / len(logprobs) if logprobs else float("-inf")

    def transcribe(
        self, audio: str | bytes, lang: str | None = None, fallback_lang: str | None = None
    ) -> str:
        import os
        import tempfile

        self._ensure_loaded()
        tmp_path = None
        try:
            if isinstance(audio, bytes):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    f.write(audio)
                    tmp_path = f.name
                audio_path = tmp_path
            else:
                audio_path = audio

            primary = self._decode(audio_path, lang)
            primary_text = primary.get("text", "").strip()

            # No language (or a redundant fallback) means one pass only.
            if (
                not lang
                or not fallback_lang
                or self._LANG_MAP.get(lang, lang)
                == self._LANG_MAP.get(fallback_lang, fallback_lang)
            ):
                return primary_text

            secondary = self._decode(audio_path, fallback_lang)
            secondary_text = secondary.get("text", "").strip()
            if not secondary_text:
                return primary_text
            if not primary_text:
                return secondary_text
            if self._confidence(secondary) > self._confidence(primary) + self._FALLBACK_MARGIN:
                return secondary_text
            return primary_text
        finally:
            if tmp_path:
                os.unlink(tmp_path)

    def unload(self) -> None:
        self._model = None
        gc.collect()
