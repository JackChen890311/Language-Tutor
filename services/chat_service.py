import json
import re

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.memory_service import MemoryService
from services.prompt_builder import PromptBuilder

_WORD_SUGGESTION_RE = re.compile(r"<!--WORD_SUGGESTION:(.*?)-->", re.DOTALL)


def extract_word_suggestions(text: str) -> tuple[str, list[dict]]:
    suggestions = []
    for match in _WORD_SUGGESTION_RE.finditer(text):
        try:
            suggestions.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            pass
    clean = _WORD_SUGGESTION_RE.sub("", text).strip()
    return clean, suggestions


class ChatService:
    def __init__(
        self,
        store: DataStore,
        model_manager: ModelManager,
        prompt_builder: PromptBuilder,
        memory_service: MemoryService,
    ):
        self._store = store
        self._mm = model_manager
        self._pb = prompt_builder
        self._memory = memory_service

    def send_message(
        self,
        lang: str,
        session_id: str,
        native_lang: str,
        level: str,
        user_text: str,
        image_path: str | None = None,
    ) -> dict:
        messages = self._store.load_chat_messages(lang, session_id)
        messages.append({"role": "user", "content": user_text})

        context = self._memory.assemble_context(lang, session_id)
        context.append({"role": "user", "content": user_text})

        system_prompt = self._pb.chat_system_prompt(
            native_lang=native_lang, target_lang=lang, level=level
        )

        if image_path:
            vlm = self._mm.get_vlm()
            raw_response = vlm.generate(context, image=image_path, system_prompt=system_prompt)
        else:
            llm = self._mm.get_llm()
            raw_response = llm.generate(context, system_prompt=system_prompt)

        clean_response, word_suggestions = extract_word_suggestions(raw_response)
        messages.append({"role": "assistant", "content": clean_response})
        self._store.save_chat_messages(lang, session_id, messages)
        self._memory.maybe_summarize(lang, session_id, native_lang)

        return {"response": clean_response, "word_suggestions": word_suggestions}

    def get_history(self, lang: str, session_id: str) -> list[dict]:
        return self._store.load_chat_messages(lang, session_id)
