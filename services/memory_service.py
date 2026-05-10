from data_store.data_store import DataStore
from model_manager import ModelManager
from services.prompt_builder import PromptBuilder

FULL_WINDOW = 15
SUMMARIZE_TRIGGER = 35
SUMMARIZE_COUNT = 20


class MemoryService:
    def __init__(self, store: DataStore, model_manager: ModelManager, prompt_builder: PromptBuilder):
        self._store = store
        self._mm = model_manager
        self._pb = prompt_builder

    def assemble_context(self, lang: str, session_id: str) -> list[dict]:
        messages = self._store.load_chat_messages(lang, session_id)
        summary = self._store.load_chat_summary(lang, session_id)
        if not summary:
            return messages
        summary_msg = {"role": "system", "content": f"[Conversation summary so far]\n{summary}"}
        return [summary_msg] + messages

    def maybe_summarize(self, lang: str, session_id: str, native_lang: str) -> None:
        messages = self._store.load_chat_messages(lang, session_id)
        if len(messages) < SUMMARIZE_TRIGGER:
            return
        to_summarize = messages[:SUMMARIZE_COUNT]
        keep = messages[SUMMARIZE_COUNT:]
        conversation_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in to_summarize
        )
        system_prompt = self._pb.summarization_prompt(native_lang)
        llm = self._mm.get_llm()
        summary = llm.generate(
            [{"role": "user", "content": conversation_text}],
            system_prompt=system_prompt,
        )
        self._store.append_chat_summary(lang, session_id, summary)
        self._store.save_chat_messages(lang, session_id, keep)
