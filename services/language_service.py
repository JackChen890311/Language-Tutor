from datetime import date, timedelta
from data_store.data_store import DataStore


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

    def update_streak(self, lang: str) -> None:
        streak_data = self._store.load_streak(lang)
        today = date.today().isoformat()
        last_active = streak_data.get("last_active")
        streak = streak_data.get("streak", 0)

        if last_active == today:
            return
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        streak = (streak + 1) if last_active == yesterday else 1
        streak_data["streak"] = streak
        streak_data["last_active"] = today
        self._store.save_streak(lang, streak_data)

    def get_stats(self, lang: str) -> dict:
        streak_data = self._store.load_streak(lang)
        words = self._store.load_wordlist(lang)
        lessons = self._store.load_lessons_progress(lang)
        return {
            "streak": streak_data.get("streak", 0),
            "last_active": streak_data.get("last_active", ""),
            "words_saved": len(words),
            "words_reviewed_this_week": sum(
                1
                for w in words
                if w.get("review_stats", {}).get("last_reviewed") is not None
                and w["review_stats"]["last_reviewed"]
                >= (date.today() - timedelta(days=7)).isoformat()
            ),
            "lessons_completed": len(lessons.get("completed", [])),
        }

    def get_active_dates(self, lang: str, days: int = 7) -> list[str]:
        """ISO dates within the last ``days`` days with any learning activity.

        Activity is derived from the streak (which records consecutive days but
        not each day individually), word reviews, finished quizzes and chat
        sessions.
        """
        today = date.today()
        cutoff = today - timedelta(days=days - 1)
        found: set[str] = set()

        streak = self._store.load_streak(lang)
        last_active = streak.get("last_active")
        streak_len = streak.get("streak", 0)
        if last_active and streak_len:
            try:
                cursor = date.fromisoformat(str(last_active)[:10])
            except ValueError:
                cursor = None
            for _ in range(min(streak_len, days)):
                if cursor is None or cursor < cutoff:
                    break
                found.add(cursor.isoformat())
                cursor -= timedelta(days=1)

        for word in self._store.load_wordlist(lang):
            last_reviewed = (word.get("review_stats") or {}).get("last_reviewed")
            if last_reviewed:
                found.add(str(last_reviewed)[:10])

        for attempt in self._store.load_quiz_history(lang):
            if attempt.get("tested_at"):
                found.add(str(attempt["tested_at"])[:10])

        for session in self._store.list_chat_sessions(lang):
            if session.get("created_at"):
                found.add(str(session["created_at"])[:10])

        return sorted(d for d in found if cutoff.isoformat() <= d <= today.isoformat())
