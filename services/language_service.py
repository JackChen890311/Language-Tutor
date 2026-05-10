from datetime import date, timedelta
from data_store.data_store import DataStore

PROFICIENCY_FRAMEWORKS: dict[str, dict] = {
    "ja": {
        "name": "JLPT",
        "levels": ["N5", "N4", "N3", "N2", "N1"],
    },
    "zh": {
        "name": "HSK",
        "levels": ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6"],
    },
    "zh-TW": {
        "name": "HSK",
        "levels": ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6"],
    },
    "ko": {
        "name": "TOPIK",
        "levels": ["TOPIK1", "TOPIK2", "TOPIK3", "TOPIK4", "TOPIK5", "TOPIK6"],
    },
}
_CEFR = {"name": "CEFR", "levels": ["A1", "A2", "B1", "B2", "C1", "C2"]}


class LanguageService:
    def __init__(self, store: DataStore):
        self._store = store

    def set_language_pair(self, native: str, target: str) -> None:
        settings = self._store.load_settings()
        settings["native_lang"] = native
        settings["target_lang"] = target
        self._store.save_settings(settings)

    def get_language_pair(self) -> tuple[str, str]:
        settings = self._store.load_settings()
        return settings.get("native_lang", "en"), settings.get("target_lang", "ja")

    def get_proficiency_framework(self, target_lang: str) -> dict:
        return PROFICIENCY_FRAMEWORKS.get(target_lang, _CEFR)

    def update_streak(self, lang: str) -> None:
        level_data = self._store.load_level(lang)
        today = date.today().isoformat()
        last_active = level_data.get("last_active")
        streak = level_data.get("streak", 0)

        if last_active == today:
            return
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        streak = (streak + 1) if last_active == yesterday else 1
        level_data["streak"] = streak
        level_data["last_active"] = today
        self._store.save_level(lang, level_data)

    def get_stats(self, lang: str) -> dict:
        level_data = self._store.load_level(lang)
        words = self._store.load_wordlist(lang)
        lessons = self._store.load_lessons_progress(lang)
        return {
            "level": level_data.get("level", ""),
            "streak": level_data.get("streak", 0),
            "last_active": level_data.get("last_active", ""),
            "words_saved": len(words),
            "words_reviewed_this_week": sum(
                1 for w in words
                if w.get("review_stats", {}).get("last_reviewed") is not None
                and w["review_stats"]["last_reviewed"] >= (date.today() - timedelta(days=7)).isoformat()
            ),
            "lessons_completed": len(lessons.get("completed", [])),
        }
