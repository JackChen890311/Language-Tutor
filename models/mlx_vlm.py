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

    def load(self) -> None:
        self._ensure_loaded()

    def generate(self, messages: list[dict], image: str | bytes, system_prompt: str = "") -> str:
        import os
        import tempfile
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template

        self._ensure_loaded()
        user_text = messages[-1]["content"] if messages else ""
        tmp_path = None
        try:
            if isinstance(image, bytes):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                    f.write(image)
                    tmp_path = f.name
                image_path = tmp_path
            else:
                image_path = image
            if system_prompt:
                user_text = f"{system_prompt}\n\n{user_text}"
            prompt = apply_chat_template(self._processor, self._config, user_text, num_images=1)
            return generate(
                self._model, self._processor, image_path, prompt, max_tokens=1024, verbose=False
            )
        finally:
            if tmp_path:
                os.unlink(tmp_path)

    def stream(
        self, messages: list[dict], image: str | bytes, system_prompt: str = ""
    ) -> Iterator[str]:
        result = self.generate(messages, image, system_prompt)
        yield result

    def unload(self) -> None:
        self._model = None
        self._processor = None
        self._config = None
        gc.collect()
