import inspect


def test_base_classes_are_abstract():
    from models.base import BaseLLM, BaseVLM, BaseTTS, BaseSTT

    assert inspect.isabstract(BaseLLM)
    assert inspect.isabstract(BaseVLM)
    assert inspect.isabstract(BaseTTS)
    assert inspect.isabstract(BaseSTT)


def test_mock_llm_conforms_to_interface(mock_llm):
    result = mock_llm.generate([{"role": "user", "content": "hi"}])
    assert isinstance(result, str)
