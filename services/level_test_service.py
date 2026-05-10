import json
from datetime import datetime

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.language_service import PROFICIENCY_FRAMEWORKS, _CEFR
from services.prompt_builder import PromptBuilder


class LevelTestService:
    def __init__(self, store: DataStore, model_manager: ModelManager, prompt_builder: PromptBuilder):
        self._store = store
        self._mm = model_manager
        self._pb = prompt_builder

    def generate_questions(self, target_lang: str, n_questions: int = 8) -> list[dict]:
        system_prompt = self._pb.level_test_system_prompt(target_lang, n_questions)
        llm = self._mm.get_llm()
        raw = llm.generate(
            [{"role": "user", "content": "Generate the test questions now."}],
            system_prompt=system_prompt,
            enable_thinking=False,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON for level test: {e}") from e

    def evaluate(self, questions: list[dict], answers: list[str], target_lang: str) -> dict:
        correct = sum(1 for q, a in zip(questions, answers) if q["correct"] == a)
        score = round(correct / len(questions) * 100) if questions else 0
        level = self._score_to_level(score, target_lang)
        result = {
            "level": level,
            "score": score,
            "correct": correct,
            "total": len(questions),
            "tested_at": datetime.now().isoformat(),
        }
        self._store.save_level(target_lang, result)
        return result

    def _score_to_level(self, score: int, target_lang: str) -> str:
        framework = PROFICIENCY_FRAMEWORKS.get(target_lang, _CEFR)
        levels = framework["levels"]
        idx = min(int(score / 100 * len(levels)), len(levels) - 1)
        return levels[idx]
