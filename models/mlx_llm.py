import gc
from typing import Iterator

from models.base import BaseLLM


class MLXLLMModel(BaseLLM):
    def __init__(self, model_path: str):
        self._model_path = model_path
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from mlx_lm import load
            self._model, self._tokenizer = load(self._model_path)

    def _build_prompt(self, messages: list[dict], system_prompt: str) -> str:
        self._ensure_loaded()
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)
        return self._tokenizer.apply_chat_template(
            all_messages, tokenize=False, add_generation_prompt=True
        )

    def load(self) -> None:
        self._ensure_loaded()

    def generate(self, messages: list[dict], system_prompt: str = "") -> str:
        from mlx_lm import generate
        self._ensure_loaded()
        prompt = self._build_prompt(messages, system_prompt)
        return generate(self._model, self._tokenizer, prompt=prompt, max_tokens=2048, verbose=False)

    def stream(self, messages: list[dict], system_prompt: str = "") -> Iterator[str]:
        from mlx_lm import stream_generate
        self._ensure_loaded()
        prompt = self._build_prompt(messages, system_prompt)
        for token in stream_generate(self._model, self._tokenizer, prompt=prompt, max_tokens=2048):
            yield token

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        gc.collect()
