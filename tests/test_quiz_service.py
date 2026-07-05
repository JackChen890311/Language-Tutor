import json
from unittest.mock import MagicMock
from services.quiz_service import QuizService
from services.prompt_builder import PromptBuilder


def _make_svc(mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return QuizService(mm, pb)


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


def test_generate_questions(mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(mock_llm)
    questions = svc.generate_questions("ja")
    assert len(questions) == 2
    assert questions[0]["question"] == "What does 食べる mean?"


def test_evaluate_perfect_score(mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(mock_llm)
    questions = svc.generate_questions("ja")
    result = svc.evaluate(questions, ["A", "C"])
    assert result["score"] == 100
    assert result["correct"] == 2
    assert result["total"] == 2
    assert "level" not in result


def test_evaluate_zero_score(mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(mock_llm)
    questions = svc.generate_questions("ja")
    result = svc.evaluate(questions, ["B", "A"])
    assert result["score"] == 0
    assert result["correct"] == 0
