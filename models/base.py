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
    def generate(self, messages: list[dict], image: str | bytes, system_prompt: str = "") -> str: ...

    @abstractmethod
    def stream(self, messages: list[dict], image: str | bytes, system_prompt: str = "") -> Iterator[str]: ...

    @abstractmethod
    def unload(self) -> None: ...


class BaseTTS(ABC):
    @abstractmethod
    def synthesize(self, text: str, lang: str) -> bytes: ...

    @abstractmethod
    def unload(self) -> None: ...


class BaseSTT(ABC):
    @abstractmethod
    def transcribe(self, audio: str | bytes) -> str: ...

    @abstractmethod
    def unload(self) -> None: ...
