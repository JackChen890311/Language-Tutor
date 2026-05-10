from unittest.mock import MagicMock
from services.memory_service import MemoryService
from services.prompt_builder import PromptBuilder


def _make_messages(n: int) -> list[dict]:
    return [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"} for i in range(n)
    ]


def test_assemble_context_under_threshold(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    messages = _make_messages(10)
    tmp_store.save_chat_messages("ja", sid, messages)
    context = svc.assemble_context("ja", sid)
    assert len(context) == 10


def test_assemble_context_includes_summary(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    tmp_store.append_chat_summary("ja", sid, "Previous summary.")
    messages = _make_messages(5)
    tmp_store.save_chat_messages("ja", sid, messages)
    context = svc.assemble_context("ja", sid)
    assert context[0]["role"] == "system"
    assert "Previous summary." in context[0]["content"]


def test_maybe_summarize_no_trigger(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    messages = _make_messages(20)
    tmp_store.save_chat_messages("ja", sid, messages)
    svc.maybe_summarize("ja", sid, "zh-TW")
    mock_llm.generate.assert_not_called()


def test_maybe_summarize_triggers_at_35(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    mock_llm.generate.return_value = "Summary of conversation."
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    messages = _make_messages(35)
    tmp_store.save_chat_messages("ja", sid, messages)
    svc.maybe_summarize("ja", sid, "zh-TW")
    mock_llm.generate.assert_called_once()
    remaining = tmp_store.load_chat_messages("ja", sid)
    assert len(remaining) == 15
    summary = tmp_store.load_chat_summary("ja", sid)
    assert "Summary of conversation." in summary


def test_maybe_summarize_no_trigger_at_34(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    messages = _make_messages(34)
    tmp_store.save_chat_messages("ja", sid, messages)
    svc.maybe_summarize("ja", sid, "zh-TW")
    mock_llm.generate.assert_not_called()


def test_maybe_summarize_second_cycle_appends(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    mock_llm.generate.return_value = "Second summary."
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    # Seed an existing summary (from a prior cycle)
    tmp_store.append_chat_summary("ja", sid, "First summary.")
    # Start the second cycle with a fresh 35-message window
    messages = _make_messages(35)
    tmp_store.save_chat_messages("ja", sid, messages)
    svc.maybe_summarize("ja", sid, "zh-TW")
    summary = tmp_store.load_chat_summary("ja", sid)
    assert "First summary." in summary
    assert "Second summary." in summary
    remaining = tmp_store.load_chat_messages("ja", sid)
    assert len(remaining) == 15
