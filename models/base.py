from abc import ABC, abstractmethod
from typing import Iterator


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages: list[dict], system_prompt: str = "") -> str: ...

    @abstractmethod
    def stream(self, messages: list[dict], system_prompt: str = "") -> Iterator[str]: ...

    @abstractmethod
    def unload(self) -> None: ...


class BaseVLM(ABC):
    @abstractmethod
    def generate(self, messages: list[dict], image_path: str, system_prompt: str = "") -> str: ...

    @abstractmethod
    def unload(self) -> None: ...


class BaseTTS(ABC):
    @abstractmethod
    def synthesize(self, text: str, lang: str = "en-us") -> bytes: ...

    @abstractmethod
    def unload(self) -> None: ...


class BaseSTT(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> str: ...

    @abstractmethod
    def unload(self) -> None: ...
