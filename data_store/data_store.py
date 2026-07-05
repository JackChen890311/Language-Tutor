import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path


class DataStore:
    def __init__(self, data_dir: str = "data"):
        self.root = Path(data_dir)
        self.root.mkdir(exist_ok=True)

    # --- Settings ---

    def load_settings(self) -> dict:
        path = self.root / "settings.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def save_settings(self, settings: dict) -> None:
        path = self.root / "settings.json"
        path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Progress ---

    def _progress_dir(self, lang: str) -> Path:
        d = self.root / lang / "progress"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def load_streak(self, lang: str) -> dict:
        path = self._progress_dir(lang) / "streak.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def save_streak(self, lang: str, data: dict) -> None:
        path = self._progress_dir(lang) / "streak.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_lessons_progress(self, lang: str) -> dict:
        path = self._progress_dir(lang) / "lessons.json"
        if not path.exists():
            return {"completed": [], "topics": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def save_lessons_progress(self, lang: str, data: dict) -> None:
        path = self._progress_dir(lang) / "lessons.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Chat ---

    def _sessions_index_path(self, lang: str) -> Path:
        d = self.root / lang / "chats"
        d.mkdir(parents=True, exist_ok=True)
        return d / "sessions.json"

    def list_chat_sessions(self, lang: str) -> list[dict]:
        path = self._sessions_index_path(lang)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def create_chat_session(self, lang: str, name: str, lesson_id: str | None = None) -> str:
        session_id = uuid.uuid4().hex[:8]
        sessions = self.list_chat_sessions(lang)
        sessions.append(
            {
                "id": session_id,
                "name": name,
                "created_at": datetime.now().isoformat(),
                "lesson_id": lesson_id,
            }
        )
        path = self._sessions_index_path(lang)
        path.write_text(json.dumps(sessions, ensure_ascii=False, indent=2), encoding="utf-8")
        return session_id

    def delete_chat_session(self, lang: str, session_id: str) -> None:
        d = self.root / lang / "chats" / session_id
        if d.exists():
            shutil.rmtree(d)
        sessions = [s for s in self.list_chat_sessions(lang) if s["id"] != session_id]
        path = self._sessions_index_path(lang)
        path.write_text(json.dumps(sessions, ensure_ascii=False, indent=2), encoding="utf-8")

    def _chat_session_dir(self, lang: str, session_id: str) -> Path:
        d = self.root / lang / "chats" / session_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def load_chat_messages(self, lang: str, session_id: str) -> list[dict]:
        path = self._chat_session_dir(lang, session_id) / "messages.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def save_chat_messages(self, lang: str, session_id: str, messages: list[dict]) -> None:
        path = self._chat_session_dir(lang, session_id) / "messages.json"
        path.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_chat_summary(self, lang: str, session_id: str) -> str:
        path = self._chat_session_dir(lang, session_id) / "summary.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def append_chat_summary(self, lang: str, session_id: str, summary: str) -> None:
        path = self._chat_session_dir(lang, session_id) / "summary.md"
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        separator = "\n\n---\n\n" if existing else ""
        path.write_text(existing + separator + summary, encoding="utf-8")

    # --- Words ---

    def _words_dir(self, lang: str) -> Path:
        d = self.root / lang / "words"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def load_wordlist(self, lang: str) -> list[dict]:
        path = self._words_dir(lang) / "wordlist.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def save_wordlist(self, lang: str, words: list[dict]) -> None:
        path = self._words_dir(lang) / "wordlist.json"
        path.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Data management ---

    def clear_language_history(self, lang: str) -> None:
        lang_dir = self.root / lang
        if lang_dir.exists():
            shutil.rmtree(lang_dir)

    # --- Lessons ---

    def _lessons_dir(self, lang: str) -> Path:
        d = self.root / lang / "lessons"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_lesson_notes(self, lang: str, lesson_id: str, notes: str) -> None:
        path = self._lessons_dir(lang) / f"{lesson_id}.md"
        path.write_text(notes, encoding="utf-8")

    def load_lesson_notes(self, lang: str, lesson_id: str) -> str:
        path = self._lessons_dir(lang) / f"{lesson_id}.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")
