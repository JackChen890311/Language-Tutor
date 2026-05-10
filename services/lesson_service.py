import json
import uuid

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.chat_service import extract_word_suggestions
from services.prompt_builder import PromptBuilder


class LessonService:
    def __init__(self, store: DataStore, model_manager: ModelManager, prompt_builder: PromptBuilder):
        self._store = store
        self._mm = model_manager
        self._pb = prompt_builder

    def suggest_topics(self, target_lang: str, level: str, n: int = 5) -> list[str]:
        progress = self._store.load_lessons_progress(target_lang)
        completed = progress.get("completed", [])
        completed_note = f"Already covered: {', '.join(completed)}. " if completed else ""
        llm = self._mm.get_llm()
        raw = llm.generate(
            [{"role": "user", "content": (
                f"{completed_note}Suggest {n} lesson topics for a {target_lang} learner "
                f"at level {level}. Return a JSON array of topic name strings only."
            )}],
            enable_thinking=False,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def start_lesson(
        self,
        target_lang: str,
        native_lang: str,
        level: str,
        topic: str,
        difficulty: str = "Normal",
    ) -> dict:
        lesson_id = f"lesson-{uuid.uuid4().hex[:8]}"
        session_id = self._store.create_chat_session(target_lang, f"📝 {topic}", lesson_id=lesson_id)

        system_prompt = self._pb.lesson_system_prompt(
            native_lang=native_lang, target_lang=target_lang, level=level,
            topic=topic, phase="structured", difficulty=difficulty,
        )
        llm = self._mm.get_llm()
        raw_response = llm.generate(
            [{"role": "user", "content": "Please start the lesson."}],
            system_prompt=system_prompt,
            enable_thinking=False,
        )
        clean_response, word_suggestions = extract_word_suggestions(raw_response)
        self._store.save_chat_messages(target_lang, session_id, [
            {"role": "assistant", "content": clean_response}
        ])
        self._store.save_lesson_notes(target_lang, lesson_id, f"# Lesson: {topic}\n\n{clean_response}")

        return {
            "lesson_id": lesson_id,
            "session_id": session_id,
            "response": clean_response,
            "word_suggestions": word_suggestions,
            "phase": "structured",
        }

    def continue_lesson(
        self,
        target_lang: str,
        session_id: str,
        lesson_id: str,
        native_lang: str,
        level: str,
        topic: str,
        phase: str,
        difficulty: str,
        user_text: str,
    ) -> dict:
        messages = self._store.load_chat_messages(target_lang, session_id)
        messages.append({"role": "user", "content": user_text})

        system_prompt = self._pb.lesson_system_prompt(
            native_lang=native_lang, target_lang=target_lang, level=level,
            topic=topic, phase=phase, difficulty=difficulty,
        )
        llm = self._mm.get_llm()
        raw_response = llm.generate(messages, system_prompt=system_prompt, enable_thinking=False)
        clean_response, word_suggestions = extract_word_suggestions(raw_response)

        messages.append({"role": "assistant", "content": clean_response})
        self._store.save_chat_messages(target_lang, session_id, messages)

        existing_notes = self._store.load_lesson_notes(target_lang, lesson_id)
        self._store.save_lesson_notes(
            target_lang, lesson_id,
            existing_notes + f"\n\n**User:** {user_text}\n\n**Tutor:** {clean_response}"
        )

        return {"response": clean_response, "word_suggestions": word_suggestions, "phase": phase}

    def finish_lesson(self, target_lang: str, topic: str) -> None:
        progress = self._store.load_lessons_progress(target_lang)
        if topic not in progress["completed"]:
            progress["completed"].append(topic)
        if topic not in progress.get("topics", []):
            progress.setdefault("topics", []).append(topic)
        self._store.save_lessons_progress(target_lang, progress)
