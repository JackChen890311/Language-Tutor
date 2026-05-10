import pytest
from unittest.mock import MagicMock
from models.base import BaseLLM, BaseVLM, BaseTTS, BaseSTT


@pytest.fixture
def tmp_store(tmp_path):
    from data_store.data_store import DataStore  # imported lazily; DataStore added in Task 3

    return DataStore(str(tmp_path))


@pytest.fixture
def mock_llm():
    mock = MagicMock(spec=BaseLLM)
    mock.generate.return_value = "mock response"
    mock.stream.return_value = iter(["mock", " ", "response"])
    return mock


@pytest.fixture
def mock_vlm():
    mock = MagicMock(spec=BaseVLM)
    mock.generate.return_value = "mock vlm response"
    return mock


@pytest.fixture
def mock_tts():
    mock = MagicMock(spec=BaseTTS)
    mock.synthesize.return_value = b"mock audio bytes"
    return mock


@pytest.fixture
def mock_stt():
    mock = MagicMock(spec=BaseSTT)
    mock.transcribe.return_value = "mock transcription"
    return mock
