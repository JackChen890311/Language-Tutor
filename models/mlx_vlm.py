import gc
import warnings
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

            # Some multimodal processors (e.g. Gemma4Processor) bundle an audio feature
            # extractor that eagerly builds its mel filterbank at construction time, even
            # though we never send audio through this VLM. With that extractor's num_mel_filters
            # baked into the model repo's own processor_config.json, the filterbank has
            # legitimately empty rows and transformers warns about it — noise, not our bug.
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", message="At least one mel filter has all zero values"
                )
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
            result = generate(
                self._model,
                self._processor,
                prompt=prompt,
                image=image_path,
                max_tokens=1024,
                verbose=False,
            )
            return result.text
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
