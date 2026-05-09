import inspect
from unittest.mock import MagicMock
from models.base import BaseLLM, BaseVLM, BaseTTS, BaseSTT


def test_base_classes_are_abstract():
    assert inspect.isabstract(BaseLLM)
    assert inspect.isabstract(BaseVLM)
    assert inspect.isabstract(BaseTTS)
    assert inspect.isabstract(BaseSTT)


def test_mock_llm_conforms_to_interface(mock_llm):
    result = mock_llm.generate([{"role": "user", "content": "hi"}])
    assert isinstance(result, str)
