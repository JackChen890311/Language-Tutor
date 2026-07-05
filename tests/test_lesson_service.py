import json
from unittest.mock import MagicMock
from services.lesson_service import LessonService
from services.prompt_builder import PromptBuilder


def _make_svc(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return LessonService(tmp_store, mm, pb)


def test_suggest_topics(tmp_store, mock_llm):
    mock_llm.generate.return_value = json.dumps(["Food", "Travel", "Shopping", "Weather", "Family"])
    svc = _make_svc(tmp_store, mock_llm)
    topics = svc.suggest_topics("ja")
    assert len(topics) == 5
    assert "Food" in topics


def test_start_lesson_creates_session(tmp_store, mock_llm):
    mock_llm.generate.return_value = "Let's start with vocabulary for food..."
    svc = _make_svc(tmp_store, mock_llm)
    result = svc.start_lesson("ja", "zh-TW", "Food", difficulty="Normal")
    assert "lesson_id" in result
    assert "session_id" in result
    assert "response" in result


def test_continue_lesson_structured(tmp_store, mock_llm):
    mock_llm.generate.return_value = "Good! Now let's do exercises."
    svc = _make_svc(tmp_store, mock_llm)
    lesson_id = "lesson-001"
    session_id = tmp_store.create_chat_session("ja", "Food Lesson", lesson_id=lesson_id)
    tmp_store.save_chat_messages(
        "ja", session_id, [{"role": "assistant", "content": "Let's start."}]
    )
    result = svc.continue_lesson(
        "ja",
        session_id,
        lesson_id,
        "zh-TW",
        "Food",
        phase="structured",
        difficulty="Normal",
        user_text="I understand.",
    )
    assert "response" in result
    assert "phase" in result


def test_finish_lesson_saves_progress(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    svc.finish_lesson("ja", "Food")
    progress = tmp_store.load_lessons_progress("ja")
    assert "Food" in progress["completed"]
