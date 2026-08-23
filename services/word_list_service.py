import json
import uuid
from datetime import date, timedelta

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.prompt_builder import PromptBuilder

STALE_DAYS = 7


class WordListService:
    def __init__(
        self, store: DataStore, model_manager: ModelManager, prompt_builder: PromptBuilder
    ):
        self._store = store
        self._mm = model_manager
        self._pb = prompt_builder

    def add_word(
        self,
        lang: str,
        native_lang: str,
        word: str,
        reading: str = "",
        source: str = "manual",
        tags: list[str] | None = None,
    ) -> dict:
        words = self._store.load_wordlist(lang)
        existing = next((w for w in words if w["word"] == word), None)
        if existing:
            return existing

        enrichment = self._enrich(lang, native_lang, word)
        entry = {
            "id": uuid.uuid4().hex[:8],
            "word": word,
            "reading": reading,
            "source": source,
            "added_date": date.today().isoformat(),
            "tags": tags or [],
            "review_stats": {"last_reviewed": None, "correct": 0, "incorrect": 0},
            **enrichment,
        }
        words.append(entry)
        self._store.save_wordlist(lang, words)
        return entry

    def _enrich(self, lang: str, native_lang: str, word: str) -> dict:
        system_prompt = self._pb.word_enrichment_prompt(target_lang=lang, native_lang=native_lang)
        llm = self._mm.get_llm()
        raw = llm.generate(
            [{"role": "user", "content": f"Word: {word}"}],
            system_prompt=system_prompt,
            enable_thinking=False,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def get_word(self, lang: str, word_id: str) -> dict | None:
        words = self._store.load_wordlist(lang)
        return next((w for w in words if w["id"] == word_id), None)

    def search(self, lang: str, query: str) -> list[dict]:
        words = self._store.load_wordlist(lang)
        q = query.lower()
        return [w for w in words if q in w["word"].lower() or q in w.get("reading", "").lower()]

    def filter_by_tag(self, lang: str, tag: str) -> list[dict]:
        words = self._store.load_wordlist(lang)
        return [w for w in words if tag in w.get("tags", [])]

    def has_stale_words(self, lang: str) -> bool:
        words = self._store.load_wordlist(lang)
        cutoff = (date.today() - timedelta(days=STALE_DAYS)).isoformat()
        for w in words:
            last = w.get("review_stats", {}).get("last_reviewed")
            if last is None or last < cutoff:
                return True
        return False

    def get_stale_words(self, lang: str) -> list[dict]:
        words = self._store.load_wordlist(lang)
        cutoff = (date.today() - timedelta(days=STALE_DAYS)).isoformat()
        return [
            w
            for w in words
            if (last := w.get("review_stats", {}).get("last_reviewed")) is None or last < cutoff
        ]

    def get_all_words(self, lang: str) -> list[dict]:
        return self._store.load_wordlist(lang)

    def update_review_stats(self, lang: str, word_id: str, correct: bool) -> None:
        words = self._store.load_wordlist(lang)
        for w in words:
            if w["id"] == word_id:
                stats = w.setdefault(
                    "review_stats", {"last_reviewed": None, "correct": 0, "incorrect": 0}
                )
                stats["last_reviewed"] = date.today().isoformat()
                if correct:
                    stats["correct"] = stats.get("correct", 0) + 1
                else:
                    stats["incorrect"] = stats.get("incorrect", 0) + 1
                break
        self._store.save_wordlist(lang, words)

    def set_review_status(self, lang: str, word_id: str, reviewed: bool) -> None:
        """Set the review status of a word manually"""
        words = self._store.load_wordlist(lang)
        for w in words:
            if w["id"] == word_id:
                stats = w.setdefault(
                    "review_stats", {"last_reviewed": None, "correct": 0, "incorrect": 0}
                )
                if reviewed:
                    stats["last_reviewed"] = date.today().isoformat()
                else:
                    stats["last_reviewed"] = None
                break
        self._store.save_wordlist(lang, words)

    def clear_all_review_history(self, lang: str) -> None:
        """Clear all review history for all words in the word list"""
        words = self._store.load_wordlist(lang)
        for w in words:
            # Reset only the review stats, keep everything else
            w["review_stats"] = {"last_reviewed": None, "correct": 0, "incorrect": 0}
        self._store.save_wordlist(lang, words)
