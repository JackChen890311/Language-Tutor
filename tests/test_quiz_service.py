import json
from unittest.mock import MagicMock
from services.quiz_service import QuizService
from services.prompt_builder import PromptBuilder


def _make_svc(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return QuizService(tmp_store, mm, pb)


def _mock_questions():
    return json.dumps(
        [
            {
                "question": "What does 食べる mean?",
                "options": ["A) to eat", "B) to drink", "C) to sleep", "D) to walk"],
                "correct": "A",
                "explanation_target": "食べるは食べることを意味します。",
                "explanation_native": "食べる的意思是吃。",
            },
            {
                "question": "Which particle marks the subject?",
                "options": ["A) を", "B) に", "C) が", "D) で"],
                "correct": "C",
                "explanation_target": "がは主語を示します。",
                "explanation_native": "が用來標示主語。",
            },
        ]
    )


def test_stream_questions_then_parse(tmp_store, mock_llm):
    mock_llm.stream.return_value = iter([_mock_questions()])
    svc = _make_svc(tmp_store, mock_llm)
    collector = svc.stream_questions("zh-TW", "ja", "N3")
    list(collector)  # consume the stream, filling collector.full_text
    questions = svc.parse_questions(collector.full_text)
    assert len(questions) == 2
    assert questions[0]["question"] == "What does 食べる mean?"


def test_parse_questions_strips_code_fence(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    fenced = f"```json\n{_mock_questions()}\n```"
    questions = svc.parse_questions(fenced)
    assert len(questions) == 2


def test_evaluate_perfect_score(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.parse_questions(_mock_questions())
    result = svc.evaluate(questions, ["A", "C"], "ja")
    assert result["score"] == 100
    assert result["correct"] == 2
    assert result["total"] == 2
    assert result["questions"][0]["is_correct"] is True
    assert result["questions"][0]["explanation_native"] == "食べる的意思是吃。"


def test_evaluate_zero_score(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.parse_questions(_mock_questions())
    result = svc.evaluate(questions, ["B", "A"], "ja")
    assert result["score"] == 0
    assert result["questions"][0]["is_correct"] is False


def test_evaluate_persists_to_history(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.parse_questions(_mock_questions())
    result = svc.evaluate(questions, ["A", "C"], "ja")
    history = tmp_store.load_quiz_history("ja")
    assert len(history) == 1
    assert history[0]["id"] == result["id"]
    assert history[0]["score"] == 100
