import json
import uuid
from datetime import datetime

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.chat_service import StreamCollector
from services.prompt_builder import PromptBuilder


class QuizService:
    def __init__(
        self, store: DataStore, model_manager: ModelManager, prompt_builder: PromptBuilder
    ):
        self._store = store
        self._mm = model_manager
        self._pb = prompt_builder

    def stream_questions(
        self, native_lang: str, target_lang: str, n_questions: int = 8
    ) -> StreamCollector:
        system_prompt = self._pb.test_system_prompt(native_lang, target_lang, n_questions)
        llm = self._mm.get_llm()
        return StreamCollector(
            llm.stream(
                [{"role": "user", "content": "Generate the test questions now."}],
                system_prompt=system_prompt,
                enable_thinking=False,
            )
        )

    def parse_questions(self, raw: str) -> list[dict]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON for test: {e}") from e

    def evaluate(self, questions: list[dict], answers: list[str], target_lang: str) -> dict:
        breakdown = []
        correct_count = 0
        for q, given in zip(questions, answers):
            is_correct = q["correct"] == given
            correct_count += int(is_correct)
            breakdown.append(
                {
                    "question": q["question"],
                    "options": q["options"],
                    "correct": q["correct"],
                    "given": given,
                    "is_correct": is_correct,
                    "explanation_target": q.get("explanation_target", ""),
                    "explanation_native": q.get("explanation_native", ""),
                }
            )
        score = round(correct_count / len(questions) * 100) if questions else 0
        result = {
            "id": uuid.uuid4().hex[:8],
            "tested_at": datetime.now().isoformat(),
            "score": score,
            "correct": correct_count,
            "total": len(questions),
            "questions": breakdown,
        }
        self._store.append_quiz_result(target_lang, result)
        return result
