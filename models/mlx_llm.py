import gc
import re
from typing import Iterator

from models.base import BaseLLM

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    return _THINK_RE.sub("", text).strip()


class MLXLLMModel(BaseLLM):
    def __init__(self, model_path: str):
        self._model_path = model_path
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from mlx_lm import load
            self._model, self._tokenizer = load(self._model_path)

    def _build_prompt(self, messages: list[dict], system_prompt: str, enable_thinking: bool = True) -> str:
        self._ensure_loaded()
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)
        try:
            return self._tokenizer.apply_chat_template(
                all_messages, tokenize=False, add_generation_prompt=True,
                enable_thinking=enable_thinking,
            )
        except TypeError:
            # Tokenizer doesn't support enable_thinking (non-Qwen3 model)
            return self._tokenizer.apply_chat_template(
                all_messages, tokenize=False, add_generation_prompt=True,
            )

    def load(self) -> None:
        self._ensure_loaded()

    def generate(self, messages: list[dict], system_prompt: str = "", enable_thinking: bool = True) -> str:
        from mlx_lm import generate
        self._ensure_loaded()
        prompt = self._build_prompt(messages, system_prompt, enable_thinking=enable_thinking)
        raw = generate(self._model, self._tokenizer, prompt=prompt, max_tokens=8192, verbose=False)
        return _strip_thinking(raw)

    def stream(self, messages: list[dict], system_prompt: str = "", enable_thinking: bool = True) -> Iterator[str]:
        from mlx_lm import stream_generate
        self._ensure_loaded()
        prompt = self._build_prompt(messages, system_prompt, enable_thinking=enable_thinking)
        buffer = []
        in_think = False
        for token in stream_generate(self._model, self._tokenizer, prompt=prompt, max_tokens=8192):
            text = token.text
            buffer.append(text)
            joined = "".join(buffer)
            if "<think>" in joined:
                in_think = True
            if in_think:
                if "</think>" in joined:
                    in_think = False
                    after = joined.split("</think>", 1)[1]
                    buffer = [after]
                    if after:
                        yield after
                continue
            yield text
            buffer = []

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        gc.collect()
