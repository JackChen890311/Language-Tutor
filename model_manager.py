import json
from pathlib import Path

from models.base import BaseLLM, BaseVLM, BaseTTS, BaseSTT


class ModelManager:
    def __init__(self, config_path: str = "config/models.json"):
        with open(config_path, encoding="utf-8") as f:
            self.config: dict = json.load(f)
        self._llm: BaseLLM | None = None
        self._vlm: BaseVLM | None = None
        self._tts: BaseTTS | None = None
        self._stt: BaseSTT | None = None

    def is_model_available(self, slot: str) -> bool:
        import os

        model_id: str = self.config[slot]["model"]
        hf_cache = os.environ.get("HF_HUB_CACHE") or os.path.join(
            os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface")), "hub"
        )
        cache_dir = Path(hf_cache)
        dir_name = "models--" + model_id.replace("/", "--")
        return (cache_dir / dir_name).exists()

    def get_download_command(self, slot: str) -> str:
        model_id: str = self.config[slot]["model"]
        return f"huggingface-cli download {model_id}"

    def get_llm(self) -> BaseLLM:
        if self._llm is None:
            from models.mlx_llm import MLXLLMModel

            self._llm = MLXLLMModel(self.config["llm"]["model"])
        return self._llm

    def get_vlm(self) -> BaseVLM:
        if self._vlm is None:
            from models.mlx_vlm import MLXVLMModel

            self._vlm = MLXVLMModel(self.config["vlm"]["model"])
        return self._vlm

    def get_tts(self) -> BaseTTS:
        if self._tts is None:
            from models.mlx_tts import MLXTTSModel

            self._tts = MLXTTSModel(self.config["tts"]["model"])
        return self._tts

    def get_stt(self) -> BaseSTT:
        if self._stt is None:
            from models.mlx_stt import WhisperModel

            self._stt = WhisperModel(self.config["stt"]["model"])
        return self._stt

    def unload(self, slot: str) -> None:
        if slot not in ("llm", "vlm", "tts", "stt"):
            raise ValueError(f"Unknown model slot: {slot!r}. Must be one of: llm, vlm, tts, stt")
        model = getattr(self, f"_{slot}")
        if model is not None:
            model.unload()
            setattr(self, f"_{slot}", None)
