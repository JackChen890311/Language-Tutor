import json
from unittest.mock import MagicMock
from services.level_test_service import LevelTestService
from services.prompt_builder import PromptBuilder


def _make_svc(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return LevelTestService(tmp_store, mm, pb)


def _mock_questions():
    return json.dumps(
        [
            {
                "question": "What does 食べる mean?",
                "options": ["A) to eat", "B) to drink", "C) to sleep", "D) to walk"],
                "correct": "A",
                "explanation": "食べる means to eat.",
            },
            {
                "question": "Which particle marks the subject?",
                "options": ["A) を", "B) に", "C) が", "D) で"],
                "correct": "C",
                "explanation": "が marks the subject.",
            },
        ]
    )


def test_generate_questions(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.generate_questions("ja")
    assert len(questions) == 2
    assert questions[0]["question"] == "What does 食べる mean?"


def test_evaluate_perfect_score(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.generate_questions("ja")
    answers = ["A", "C"]
    result = svc.evaluate(questions, answers, "ja")
    assert result["score"] == 100
    assert result["level"] in ("N5", "N4", "N3", "N2", "N1")


def test_evaluate_zero_score(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.generate_questions("ja")
    answers = ["B", "A"]
    result = svc.evaluate(questions, answers, "ja")
    assert result["score"] == 0
    assert result["level"] == "N5"


def test_evaluate_saves_result(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.generate_questions("ja")
    svc.evaluate(questions, ["A", "C"], "ja")
    saved = tmp_store.load_level("ja")
    assert saved["level"] is not None
    assert saved["score"] == 100
