import json
import re
from typing import Iterator

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.memory_service import MemoryService
from services.prompt_builder import PromptBuilder

_WORD_SUGGESTION_RE = re.compile(r"<!--WORD_SUGGE\w*:(.*?)-->", re.DOTALL)


class StreamCollector:
    """Wraps a token generator: yields display-safe tokens (WORD_SUGGESTION markers
    filtered out) while accumulating the full raw text in .full_text."""

    def __init__(self, token_gen: Iterator[str]):
        self._gen = token_gen
        self.full_text = ""

    def __iter__(self) -> Iterator[str]:
        buf = ""
        for token in self._gen:
            self.full_text += token
            buf += token
            while True:
                marker_start = buf.find("<!--")
                if marker_start == -1:
                    if buf:
                        yield buf
                        buf = ""
                    break
                if marker_start > 0:
                    yield buf[:marker_start]
                    buf = buf[marker_start:]
                end = buf.find("-->")
                if end == -1:
                    break  # incomplete marker — wait for more tokens
                chunk = buf[: end + 3]
                buf = buf[end + 3 :]
                if not _WORD_SUGGESTION_RE.search(chunk):
                    yield chunk
        if buf:
            m = buf.find("<!--")
            if m > 0:
                yield buf[:m]
            elif m == -1:
                yield buf


_SENTENCE_CHARS = set("。、！？.!?,；;")


def _is_valid_word(word: str) -> bool:
    if not word or len(word) > 25:
        return False
    return not any(c in _SENTENCE_CHARS for c in word)


def extract_word_suggestions(text: str) -> tuple[str, list[dict]]:
    suggestions = []
    seen: set[str] = set()
    for match in _WORD_SUGGESTION_RE.finditer(text):
        try:
            entry = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        word = entry.get("word", "").strip()
        if not _is_valid_word(word) or word in seen:
            continue
        seen.add(word)
        entry["word"] = word
        suggestions.append(entry)
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
        user_text: str,
        image_path: str | None = None,
    ) -> dict:
        messages = self._store.load_chat_messages(lang, session_id)
        messages.append({"role": "user", "content": user_text})

        context = self._memory.assemble_context(lang, session_id)
        context.append({"role": "user", "content": user_text})
        # messages: raw storage list (no summary); context: LLM input (may include summary prefix)

        system_prompt = self._pb.chat_system_prompt(native_lang=native_lang, target_lang=lang)

        if image_path:
            vlm = self._mm.get_vlm()
            raw_response = vlm.generate(context, image=image_path, system_prompt=system_prompt)
        else:
            llm = self._mm.get_llm()
            raw_response = llm.generate(context, system_prompt=system_prompt, enable_thinking=False)

        clean_response, word_suggestions = extract_word_suggestions(raw_response)
        messages.append({"role": "assistant", "content": clean_response})
        self._store.save_chat_messages(lang, session_id, messages)
        self._memory.maybe_summarize(lang, session_id, native_lang)

        return {"response": clean_response, "word_suggestions": word_suggestions}

    def stream_message(
        self,
        lang: str,
        session_id: str,
        native_lang: str,
        user_text: str,
        image_path: str | None = None,
    ) -> StreamCollector:
        context = self._memory.assemble_context(lang, session_id)
        context.append({"role": "user", "content": user_text})
        system_prompt = self._pb.chat_system_prompt(native_lang=native_lang, target_lang=lang)
        if image_path:
            vlm = self._mm.get_vlm()
            raw = vlm.generate(context, image=image_path, system_prompt=system_prompt)

            def _wrap(t: str) -> Iterator[str]:
                yield t

            return StreamCollector(_wrap(raw))
        llm = self._mm.get_llm()
        return StreamCollector(
            llm.stream(context, system_prompt=system_prompt, enable_thinking=False)
        )

    def commit_message(
        self,
        lang: str,
        session_id: str,
        native_lang: str,
        user_text: str,
        raw_response: str,
    ) -> dict:
        messages = self._store.load_chat_messages(lang, session_id)
        messages.append({"role": "user", "content": user_text})
        clean_response, word_suggestions = extract_word_suggestions(raw_response)
        messages.append({"role": "assistant", "content": clean_response})
        self._store.save_chat_messages(lang, session_id, messages)
        self._memory.maybe_summarize(lang, session_id, native_lang)
        return {"response": clean_response, "word_suggestions": word_suggestions}

    def get_history(self, lang: str, session_id: str) -> list[dict]:
        return self._store.load_chat_messages(lang, session_id)
