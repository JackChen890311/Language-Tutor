from unittest.mock import MagicMock
from services.chat_service import ChatService, extract_word_suggestions
from services.memory_service import MemoryService
from services.prompt_builder import PromptBuilder


def _make_services(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    memory_svc = MemoryService(tmp_store, mm, pb)
    return ChatService(tmp_store, mm, pb, memory_svc), pb


def test_extract_word_suggestions_found():
    text = 'Hello <!--WORD_SUGGESTION:{"word": "食べる", "reading": "たべる"}--> world'
    clean, suggestions = extract_word_suggestions(text)
    assert len(suggestions) == 1
    assert suggestions[0]["word"] == "食べる"
    assert "<!--" not in clean


def test_extract_word_suggestions_none():
    clean, suggestions = extract_word_suggestions("No suggestions here")
    assert suggestions == []
    assert clean == "No suggestions here"


def test_send_message_returns_response(tmp_store, mock_llm):
    mock_llm.generate.return_value = "いいですね。"
    svc, _ = _make_services(tmp_store, mock_llm)
    sid = tmp_store.create_chat_session("ja", "Test")
    result = svc.send_message("ja", sid, "zh-TW", "N4", "Hello", image_path=None)
    assert result["response"] == "いいですね。"
    assert result["word_suggestions"] == []


def test_send_message_saves_messages(tmp_store, mock_llm):
    mock_llm.generate.return_value = "こんにちは。"
    svc, _ = _make_services(tmp_store, mock_llm)
    sid = tmp_store.create_chat_session("ja", "Test")
    svc.send_message("ja", sid, "zh-TW", "N4", "Hi", image_path=None)
    messages = tmp_store.load_chat_messages("ja", sid)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_send_message_extracts_word_suggestions(tmp_store, mock_llm):
    mock_llm.generate.return_value = (
        'Try 食べる <!--WORD_SUGGESTION:{"word": "食べる", "reading": "たべる"}-->'
    )
    svc, _ = _make_services(tmp_store, mock_llm)
    sid = tmp_store.create_chat_session("ja", "Test")
    result = svc.send_message("ja", sid, "zh-TW", "N4", "What does eat mean?", image_path=None)
    assert len(result["word_suggestions"]) == 1
    assert "<!--" not in result["response"]


def test_send_message_with_image_uses_vlm(tmp_store, mock_llm, mock_vlm):
    mock_vlm.generate.return_value = "画像に猫がいます。"
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    mm.get_vlm.return_value = mock_vlm
    memory_svc = MemoryService(tmp_store, mm, pb)
    svc = ChatService(tmp_store, mm, pb, memory_svc)
    sid = tmp_store.create_chat_session("ja", "Test")
    result = svc.send_message("ja", sid, "zh-TW", "N4", "What is this?", image_path="/tmp/fake.jpg")
    assert result["response"] == "画像に猫がいます。"
    mm.get_vlm.assert_called_once()
    mm.get_llm.assert_not_called()
