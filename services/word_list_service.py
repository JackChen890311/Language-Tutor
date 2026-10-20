import json
import uuid
from datetime import date, timedelta

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.prompt_builder import PromptBuilder

STALE_DAYS = 7


def _review_stats(word: dict) -> dict:
    stats = word.get("review_stats")
    return stats if isinstance(stats, dict) else {}


def is_word_due(word: dict, today: date | None = None) -> bool:
    """A word is due when it has never been reviewed or the review is stale."""
    last = _review_stats(word).get("last_reviewed")
    if not last:
        return True
    cutoff = (today or date.today()) - timedelta(days=STALE_DAYS)
    return last < cutoff.isoformat()


def filter_and_sort_words(
    words: list[dict],
    *,
    query: str = "",
    tag: str = "All",
    level: str = "All",
    review_status: str = "all",
    sort: str = "newest",
    today: date | None = None,
) -> list[dict]:
    """Filter and order words for the Browse view.

    ``review_status`` accepts ``all``, ``due``, ``never`` and ``reviewed``.
    ``sort`` accepts ``newest``, ``oldest``, ``az``, ``za`` and
    ``most_reviewed``. Alphabetical sorting uses the reading when available,
    which gives a sensible order for languages that use kanji.
    """
    tag = tag or "All"
    level = level or "All"
    needle = query.strip().casefold()

    selected: list[tuple[int, dict]] = []
    for index, word in enumerate(words):
        if needle:
            word_text = str(word.get("word", "")).casefold()
            reading_text = str(word.get("reading", "")).casefold()
            if needle not in word_text and needle not in reading_text:
                continue
        if tag != "All" and tag not in word.get("tags", []):
            continue
        if level != "All" and word.get("proficiency_level") != level:
            continue
        last_reviewed = _review_stats(word).get("last_reviewed")
        if review_status == "due" and not is_word_due(word, today):
            continue
        if review_status == "never" and last_reviewed:
            continue
        if review_status == "reviewed" and not last_reviewed:
            continue
        selected.append((index, word))

    def _added_key(item: tuple[int, dict]) -> tuple[str, int]:
        index, word = item
        return (str(word.get("added_date") or ""), index)

    def _alpha_key(item: tuple[int, dict]) -> tuple[str, str]:
        word = item[1]
        reading_or_word = str(word.get("reading") or word.get("word") or "").casefold()
        return (reading_or_word, str(word.get("word") or "").casefold())

    def _reviewed_key(item: tuple[int, dict]) -> tuple[int, str, int]:
        index, word = item
        stats = _review_stats(word)
        count = int(stats.get("correct") or 0) + int(stats.get("incorrect") or 0)
        return (count, str(word.get("added_date") or ""), index)

    if sort == "oldest":
        selected.sort(key=_added_key)
    elif sort == "az":
        selected.sort(key=_alpha_key)
    elif sort == "za":
        selected.sort(key=_alpha_key, reverse=True)
    elif sort == "most_reviewed":
        selected.sort(key=_reviewed_key, reverse=True)
    else:
        selected.sort(key=_added_key, reverse=True)

    return [word for _, word in selected]


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
            "source": source,
            "added_date": date.today().isoformat(),
            "tags": tags or [],
            "review_stats": {"last_reviewed": None, "correct": 0, "incorrect": 0},
            **enrichment,
            "reading": reading or enrichment.get("reading") or "",
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

    def delete_word(self, lang: str, word_id: str) -> bool:
        words = self._store.load_wordlist(lang)
        new_words = [w for w in words if w["id"] != word_id]
        if len(new_words) == len(words):
            return False
        self._store.save_wordlist(lang, new_words)
        return True

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

    def browse(
        self,
        lang: str,
        query: str = "",
        tag: str = "All",
        level: str = "All",
        review_status: str = "all",
        sort: str = "newest",
    ) -> list[dict]:
        return filter_and_sort_words(
            self._store.load_wordlist(lang),
            query=query,
            tag=tag,
            level=level,
            review_status=review_status,
            sort=sort,
        )

    def has_stale_words(self, lang: str) -> bool:
        return any(is_word_due(w) for w in self._store.load_wordlist(lang))

    def get_stale_words(self, lang: str) -> list[dict]:
        return [w for w in self._store.load_wordlist(lang) if is_word_due(w)]

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
