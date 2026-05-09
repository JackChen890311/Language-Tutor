import gc
from typing import Iterator

from models.base import BaseVLM


class MLXVLMModel(BaseVLM):
    def __init__(self, model_path: str):
        self._model_path = model_path
        self._model = None
        self._processor = None
        self._config = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from mlx_vlm import load
            from mlx_vlm.utils import load_config
            self._model, self._processor = load(self._model_path)
            self._config = load_config(self._model_path)

    def _resolve_image(self, image: str | bytes) -> str:
        """If bytes, write to a temp file and return path."""
        if isinstance(image, str):
            return image
        import tempfile
        import os
        suffix = ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(image)
            return f.name

    def load(self) -> None:
        self._ensure_loaded()

    def generate(self, messages: list[dict], image: str | bytes, system_prompt: str = "") -> str:
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template
        self._ensure_loaded()
        user_text = messages[-1]["content"] if messages else ""
        image_path = self._resolve_image(image)
        prompt = apply_chat_template(
            self._processor, self._config, user_text, num_images=1
        )
        return generate(
            self._model, self._processor, image_path, prompt, max_tokens=1024, verbose=False
        )

    def stream(self, messages: list[dict], image: str | bytes, system_prompt: str = "") -> Iterator[str]:
        # mlx_vlm does not expose a streaming API yet; fall back to full generate
        result = self.generate(messages, image, system_prompt)
        yield result

    def unload(self) -> None:
        self._model = None
        self._processor = None
        self._config = None
        gc.collect()
