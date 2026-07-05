# Language Tutor Implementation Plan — 2026-07-05 Update

> Extends `docs/superpowers/plans/2026-06-13-language-tutor.md`. See `docs/superpowers/specs/2026-07-05-language-tutor-design.md` for the design rationale behind these changes.

**Status:** All tasks below complete and merged to `main`.

---

## Task 24: Makefile

**Files:** `Makefile`

- [x] **Step 1:** Add `make run` / `make test` / `make lint` wrapping the `uv run` commands already documented in the README
- [x] **Step 2:** Commit — `chore: add Makefile with run, test, and lint commands` (`d22c7e8`)

## Task 25: Fix TTS/STT model id wiring bug

**Files:** `models/mlx_tts.py`, `models/mlx_stt.py`, `config/models.json`, `README.md`, `tests/test_model_manager.py`

- [x] **Step 1:** Diagnose — the `5f2028e` "align model IDs" commit (2026-06-13) changed `config/models.json`'s `tts`/`stt` values, but `models/mlx_tts.py` hardcoded a different repo id (`prince-canuma/Kokoro-82M`) regardless of config, and `models/mlx_stt.py` prefixed the configured STT id with `mlx-community/`, producing the invalid id `mlx-community/openai/whisper-large-v3` for the then-current config value. The configured value, the download command shown to the user, and the id actually loaded at runtime all disagreed.
- [x] **Step 2:** Make `config/models.json` the single source of truth: `MLXTTSModel._ensure_loaded` now calls `load(self._model_name)` instead of a hardcoded string; `WhisperModel.transcribe` passes `self._model_name` straight through as `path_or_hf_repo` with no added prefix
- [x] **Step 3:** Set `config/models.json` to the exact, working, full repo ids: `tts.model = "prince-canuma/Kokoro-82M"` (the mlx-audio-compatible Kokoro port), `stt.model = "mlx-community/whisper-large-v3"`
- [x] **Step 4:** Update constructor defaults in `MLXTTSModel`/`WhisperModel` to match, so instantiating without an explicit config still works
- [x] **Step 5:** Update README's Optional Models / Changing Models sections to the corrected ids and drop the "known inconsistency" callouts
- [x] **Step 6:** Fix `tests/test_model_manager.py::test_get_download_command`, which still asserted the pre-`hf`-CLI-migration string `huggingface-cli` (a pre-existing gap from Task 21, caught while re-running the suite for this fix)
- [x] **Step 7:** Run full test suite — 77 passed
- [x] **Step 8:** Commit — `fix: wire TTS/STT model ids from config instead of hardcoding` (this update)

## Task 26: Reorganize dated docs by commit date; add CLAUDE.md

**Files:** `docs/superpowers/plans/*`, `docs/superpowers/specs/*`, `CLAUDE.md`

- [x] **Step 1:** Roll back the 2026-05-10 plan/spec docs to their original MVP-era content — no retroactive edits to that historical record
- [x] **Step 2:** Add this 2026-06-13 plan+spec pair, covering that day's 4 commits
- [x] **Step 3:** Add this 2026-07-05 plan+spec pair, covering the Makefile, the model-id bug fix, and this doc reorganization itself
- [x] **Step 4:** Add `CLAUDE.md` at the repo root pointing future sessions at the dated docs and requiring a new dated plan+spec pair (plus a commit) for future feature work
- [x] **Step 5:** Commit — `docs: reorganize plans/specs by commit date, add CLAUDE.md` (this update)

---

## Update: Remove the level/proficiency concept; add a standalone "Test" section

> See `docs/superpowers/specs/2026-07-05-language-tutor-design.md` (final section) for the design rationale.
>
> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to run Tasks 27–29 below.
>
> **Commit strategy for this update:** `level` and `test` are threaded through `PromptBuilder` → `ChatService`/`LessonService`/`QuizService`, and `DataStore`'s level storage → `LanguageService`. These are mutually coupled — renaming one in isolation breaks its callers — so Task 27 changes the whole service layer together and is verified as one unit (run each test file as you touch it, then the full service-layer sweep at the end of the task). **Do not `git commit` after Task 27 or Task 28** — the working tree is intentionally not independently committable mid-refactor. Task 29 runs the full suite and does the single commit + push for this whole update.

### Task 27: Remove the level concept from the service layer

**Files:**
- Modify: `data_store/data_store.py` (rename `load_level`/`save_level` → `load_streak`/`save_streak`)
- Modify: `tests/test_data_store.py`
- Modify: `services/language_service.py` (drop `PROFICIENCY_FRAMEWORKS`/`_CEFR`/`get_proficiency_framework`; use streak storage; drop `"level"` from `get_stats`)
- Modify: `tests/test_language_service.py`
- Modify: `services/prompt_builder.py` (drop `level` param from `chat_system_prompt`/`lesson_system_prompt`; reword `DIFFICULTY_INSTRUCTIONS["Normal"]`; rename `level_test_system_prompt` → `test_system_prompt` and reword its copy)
- Modify: `tests/test_prompt_builder.py`
- Modify: `services/chat_service.py` (drop `level` param from `send_message`/`stream_message`)
- Modify: `tests/test_chat_service.py`
- Modify: `services/lesson_service.py` (drop `level` param from `suggest_topics`/`start_lesson`/`continue_lesson`/`stream_start_lesson`/`stream_continue_lesson`)
- Modify: `tests/test_lesson_service.py`
- Create: `services/quiz_service.py` (renamed/rewritten from `services/level_test_service.py`, dropping level scoring and persistence)
- Delete: `services/level_test_service.py`
- Create: `tests/test_quiz_service.py` (renamed/rewritten from `tests/test_level_test_service.py`)
- Delete: `tests/test_level_test_service.py`
- Migrate: `data/ja/progress/level.json` → `data/ja/progress/streak.json` (local dev data, gitignored — not a code change)

**Interfaces:**
- Produces: `DataStore.load_streak(lang) -> dict`, `DataStore.save_streak(lang, data) -> None`
- Produces: `PromptBuilder.chat_system_prompt(native_lang, target_lang) -> str`, `PromptBuilder.lesson_system_prompt(native_lang, target_lang, topic, phase, difficulty="Normal") -> str`, `PromptBuilder.test_system_prompt(target_lang, n_questions=8) -> str`
- Produces: `ChatService.send_message(lang, session_id, native_lang, user_text, image_path=None) -> dict`, `ChatService.stream_message(lang, session_id, native_lang, user_text, image_path=None) -> StreamCollector`
- Produces: `LessonService.suggest_topics(target_lang, n=5) -> list[str]`, `.start_lesson(target_lang, native_lang, topic, difficulty="Normal") -> dict`, `.continue_lesson(target_lang, session_id, lesson_id, native_lang, topic, phase, difficulty, user_text) -> dict`, `.stream_start_lesson(target_lang, native_lang, topic, difficulty="Normal") -> tuple`, `.stream_continue_lesson(target_lang, session_id, native_lang, topic, phase, difficulty, user_text) -> StreamCollector`
- Produces: `QuizService(model_manager, prompt_builder)` with `.generate_questions(target_lang, n_questions=8) -> list[dict]` and `.evaluate(questions, answers) -> dict` (returns `{score, correct, total, tested_at}` — no `level` key, nothing persisted)
- Consumes (Task 28 UI layer will call these): all of the above

- [x] **Step 1: Rename `DataStore`'s level storage to streak storage**

Edit `data_store/data_store.py`, replacing:

```python
    def load_level(self, lang: str) -> dict:
        path = self._progress_dir(lang) / "level.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def save_level(self, lang: str, data: dict) -> None:
        path = self._progress_dir(lang) / "level.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
```

with:

```python
    def load_streak(self, lang: str) -> dict:
        path = self._progress_dir(lang) / "streak.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def save_streak(self, lang: str, data: dict) -> None:
        path = self._progress_dir(lang) / "streak.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
```

- [x] **Step 2: Update the DataStore test**

Edit `tests/test_data_store.py`, replacing:

```python
def test_level_round_trip(tmp_store):
    tmp_store.save_level("ja", {"level": "N4", "score": 80})
    result = tmp_store.load_level("ja")
    assert result["level"] == "N4"
```

with:

```python
def test_streak_round_trip(tmp_store):
    tmp_store.save_streak("ja", {"streak": 3, "last_active": "2026-07-05"})
    result = tmp_store.load_streak("ja")
    assert result["streak"] == 3
```

- [x] **Step 3: Run the DataStore tests**

Run: `uv run pytest tests/test_data_store.py -v`
Expected: PASS (all tests, including the new `test_streak_round_trip`)

- [x] **Step 4: Migrate the local data file**

This is a one-time local filesystem fix (not code) for existing dev data at `data/ja/progress/level.json`, which is gitignored:

```bash
python3 -c "
import json
from pathlib import Path
p = Path('data/ja/progress/level.json')
data = json.loads(p.read_text())
streak_data = {k: data[k] for k in ('streak', 'last_active') if k in data}
Path('data/ja/progress/streak.json').write_text(json.dumps(streak_data, ensure_ascii=False, indent=2))
p.unlink()
"
```

- [x] **Step 5: Remove the proficiency framework tables from `LanguageService`, switch to streak storage**

Rewrite `services/language_service.py` in full:

```python
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
```

- [x] **Step 6: Update the LanguageService tests**

Rewrite `tests/test_language_service.py` in full:

```python
from services.language_service import LanguageService
from freezegun import freeze_time


def test_get_set_language_pair(tmp_store):
    svc = LanguageService(tmp_store)
    svc.set_language_pair(native="zh-TW", target="ja")
    native, target = svc.get_language_pair()
    assert native == "zh-TW"
    assert target == "ja"


def test_default_language_pair(tmp_store):
    svc = LanguageService(tmp_store)
    native, target = svc.get_language_pair()
    assert native == "en"
    assert target == "ja"


def test_update_streak_first_day(tmp_store):
    svc = LanguageService(tmp_store)
    svc.update_streak("ja")
    stats = svc.get_stats("ja")
    assert stats["streak"] == 1


def test_get_stats_defaults(tmp_store):
    svc = LanguageService(tmp_store)
    stats = svc.get_stats("ja")
    assert stats["words_saved"] == 0
    assert stats["lessons_completed"] == 0


def test_update_streak_same_day_no_double_count(tmp_store):
    with freeze_time("2026-05-10"):
        svc = LanguageService(tmp_store)
        svc.update_streak("ja")
        svc.update_streak("ja")
        stats = svc.get_stats("ja")
        assert stats["streak"] == 1


def test_update_streak_consecutive_days(tmp_store):
    svc = LanguageService(tmp_store)
    with freeze_time("2026-05-09"):
        svc.update_streak("ja")
    with freeze_time("2026-05-10"):
        svc.update_streak("ja")
        stats = svc.get_stats("ja")
        assert stats["streak"] == 2


def test_update_streak_gap_resets(tmp_store):
    svc = LanguageService(tmp_store)
    with freeze_time("2026-05-08"):
        svc.update_streak("ja")
    with freeze_time("2026-05-10"):
        svc.update_streak("ja")
        stats = svc.get_stats("ja")
        assert stats["streak"] == 1
```

- [x] **Step 7: Run the LanguageService tests**

Run: `uv run pytest tests/test_language_service.py -v`
Expected: PASS

- [x] **Step 8: Drop `level` from the prompt builder; rename the test prompt**

Rewrite `services/prompt_builder.py` in full:

```python
LANG_NAMES = {
    "zh-TW": "Traditional Chinese (繁體中文, 台灣用語)",
    "ja": "Japanese",
    "en": "English",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}

DIFFICULTY_INSTRUCTIONS = {
    "Easy": "Use simpler vocabulary, shorter sentences, and provide more hints and encouragement.",
    "Normal": "Use natural, moderately-paced language and everyday vocabulary.",
    "Hard": "Use complex grammar, native-speed examples, and provide minimal hand-holding.",
}


class PromptBuilder:
    def _lang_name(self, code: str) -> str:
        return LANG_NAMES.get(code, code)

    def _chinese_rule(self, native_lang: str) -> str:
        if native_lang in ("zh-TW", "zh"):
            return (
                "- IMPORTANT: Always use Traditional Chinese (繁體中文) with 台灣用語 and "
                "Taiwanese terminology. Never use Simplified Chinese.\n"
            )
        return ""

    def chat_system_prompt(self, native_lang: str, target_lang: str) -> str:
        return (
            f"You are a patient and encouraging language tutor.\n\n"
            f"Native language: {self._lang_name(native_lang)} ({native_lang})\n"
            f"Target language: {self._lang_name(target_lang)} ({target_lang})\n\n"
            f"Rules:\n"
            f"- Respond in {self._lang_name(native_lang)} for explanations and feedback\n"
            f"- Use {self._lang_name(target_lang)} for language practice\n"
            f"- When the user makes a mistake, always correct it: note the error, "
            f"explain why it is wrong, give the correct form, then continue naturally\n"
            f"- Tone: encouraging and patient; corrections are matter-of-fact, never condescending\n"
            f"- When you write {self._lang_name(target_lang)} sentences or phrases for the user "
            f"to hear or practice, wrap them in <speak>…</speak> tags. "
            f"Do NOT tag explanations, translations, or {self._lang_name(native_lang)} text.\n"
            f"- When you introduce a single vocabulary word (not a phrase or sentence) "
            f"likely to be new to a learner, append exactly one marker per unique word:\n"
            f'  <!--WORD_SUGGESTION:{{"word": "<single word>", "reading": "<reading/pronunciation>"}}-->\n'
            f"  Do NOT repeat the same word marker twice.\n"
            f"{self._chinese_rule(native_lang)}"
        )

    def test_system_prompt(self, target_lang: str, n_questions: int = 8) -> str:
        return (
            f"You are creating a {self._lang_name(target_lang)} ({target_lang}) "
            f"practice quiz.\n\n"
            f"Generate exactly {n_questions} multiple choice questions covering vocabulary, "
            f"grammar, and reading comprehension.\n\n"
            f"Respond ONLY with a JSON array, no other text:\n"
            f"[\n"
            f"  {{\n"
            f'    "question": "...",\n'
            f'    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],\n'
            f'    "correct": "A",\n'
            f'    "explanation": "..."\n'
            f"  }}\n"
            f"]\n"
        )

    def word_enrichment_prompt(self, target_lang: str, native_lang: str) -> str:
        return (
            f"You are a dictionary assistant for {self._lang_name(target_lang)}.\n\n"
            f"Given a word, return a JSON object with these exact fields:\n"
            f"{{\n"
            f'  "translation": "string (concise 1-5 word {self._lang_name(native_lang)} translation)",\n'
            f'  "definition": "string",\n'
            f'  "part_of_speech": "string",\n'
            f'  "formality": "casual|neutral|formal",\n'
            f'  "synonyms": ["string"],\n'
            f'  "antonyms": ["string"],\n'
            f'  "collocations": ["string"],\n'
            f'  "conjugations": {{}} or null,\n'
            f'  "tense_notes": "string" or null,\n'
            f'  "examples": ["string"],\n'
            f'  "grammar_notes": "string",\n'
            f'  "proficiency_level": "string",\n'
            f'  "language_specific": {{}}\n'
            f"}}\n\n"
            f"All definitions, notes, and examples must be in {self._lang_name(native_lang)}. "
            f"Respond ONLY with the JSON object."
        )

    def summarization_prompt(self, native_lang: str) -> str:
        return (
            f"Summarize the following conversation in under 300 words.\n"
            f"Focus on: key topics discussed, vocabulary and grammar points introduced, "
            f"the user's mistakes and corrections, and overall progress.\n"
            f"Write the summary in {self._lang_name(native_lang)} ({native_lang}).\n"
            f"Be concise and factual."
        )

    def lesson_system_prompt(
        self,
        native_lang: str,
        target_lang: str,
        topic: str,
        phase: str,
        difficulty: str = "Normal",
    ) -> str:
        difficulty_note = DIFFICULTY_INSTRUCTIONS.get(difficulty, DIFFICULTY_INSTRUCTIONS["Normal"])

        if phase == "structured":
            phase_instructions = (
                f'You are guiding a structured lesson on "{topic}". Follow this sequence:\n'
                f'1. Introduce 5-8 key vocabulary items relevant to "{topic}"\n'
                f"2. Explain one relevant grammar point\n"
                f"3. Give the user 3 practice exercises (fill-in-the-blank or translation)\n"
                f"4. After the exercises, invite the user to move to free conversation\n"
                f"Pace yourself — one step at a time. Wait for the user's response before moving on.\n"
            )
        else:
            phase_instructions = (
                f"The structured lesson is complete. Now have a natural free conversation "
                f'on the topic "{topic}".\n'
                f"Encourage use of the vocabulary and grammar from the lesson.\n"
                f"Gently correct mistakes as they occur.\n"
            )

        return (
            f"You are teaching a {self._lang_name(target_lang)} lesson.\n\n"
            f"Topic: {topic}\n"
            f"Difficulty: {difficulty} — {difficulty_note}\n"
            f"Native language: {self._lang_name(native_lang)} ({native_lang})\n\n"
            f"{phase_instructions}\n"
            f"Always explain in {self._lang_name(native_lang)}. Practice in {self._lang_name(target_lang)}.\n"
            f"When you write {self._lang_name(target_lang)} sentences or phrases for the user "
            f"to hear or practice, wrap them in <speak>…</speak> tags. "
            f"Do NOT tag explanations, translations, or {self._lang_name(native_lang)} text.\n"
            f"When you introduce a single vocabulary word (not a phrase or sentence) "
            f"likely to be new to a learner, append exactly one marker per unique word:\n"
            f'<!--WORD_SUGGESTION:{{"word": "<single word>", "reading": "<reading/pronunciation>"}}-->\n'
            f"Do NOT repeat the same word marker twice.\n"
            f"{self._chinese_rule(native_lang)}"
        )
```

- [x] **Step 9: Update the PromptBuilder tests**

Rewrite `tests/test_prompt_builder.py` in full:

```python
from services.prompt_builder import PromptBuilder


def test_chat_prompt_includes_languages():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja")
    assert "zh-TW" in prompt or "Traditional Chinese" in prompt
    assert "ja" in prompt or "Japanese" in prompt


def test_chat_prompt_chinese_native_includes_traditional_chinese_rule():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja")
    assert "繁體中文" in prompt or "Traditional Chinese" in prompt
    assert "台灣" in prompt


def test_chat_prompt_english_native_no_chinese_rule():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="en", target_lang="ja")
    assert "台灣" not in prompt


def test_test_prompt_includes_target_lang():
    pb = PromptBuilder()
    prompt = pb.test_system_prompt(target_lang="ja", n_questions=5)
    assert "ja" in prompt or "Japanese" in prompt
    assert "5" in prompt
    assert "JSON" in prompt


def test_word_enrichment_prompt():
    pb = PromptBuilder()
    prompt = pb.word_enrichment_prompt(target_lang="ja", native_lang="zh-TW")
    assert "JSON" in prompt
    assert "definition" in prompt
    assert "translation" in prompt


def test_summarization_prompt():
    pb = PromptBuilder()
    prompt = pb.summarization_prompt(native_lang="zh-TW")
    assert "300" in prompt
    assert "zh-TW" in prompt or "Traditional Chinese" in prompt


def test_lesson_prompt_includes_phase():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW",
        target_lang="ja",
        topic="food",
        phase="structured",
        difficulty="Normal",
    )
    assert "food" in prompt
    assert "structured" in prompt or "vocabulary" in prompt.lower()


def test_lesson_prompt_conversation_phase():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW",
        target_lang="ja",
        topic="food",
        phase="conversation",
        difficulty="Hard",
    )
    assert "conversation" in prompt.lower() or "free" in prompt.lower()
    assert "Hard" in prompt or "minimal" in prompt.lower()


def test_chat_prompt_includes_speak_tag_instruction():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja")
    assert "<speak>" in prompt


def test_lesson_prompt_includes_speak_tag_instruction():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW",
        target_lang="ja",
        topic="food",
        phase="structured",
    )
    assert "<speak>" in prompt
```

- [x] **Step 10: Run the PromptBuilder tests**

Run: `uv run pytest tests/test_prompt_builder.py -v`
Expected: PASS

- [x] **Step 11: Drop `level` from `ChatService`**

Edit `services/chat_service.py`. In `send_message`, replace the signature and system-prompt call:

```python
    def send_message(
        self,
        lang: str,
        session_id: str,
        native_lang: str,
        user_text: str,
        image_path: str | None = None,
    ) -> dict:
```

(dropping the `level: str,` parameter), and replace:

```python
        system_prompt = self._pb.chat_system_prompt(
            native_lang=native_lang, target_lang=lang, level=level
        )
```

with:

```python
        system_prompt = self._pb.chat_system_prompt(native_lang=native_lang, target_lang=lang)
```

In `stream_message`, make the same two changes: drop `level: str,` from the signature, and replace the same `chat_system_prompt(...)` call the same way.

- [x] **Step 12: Update the ChatService tests**

Rewrite `tests/test_chat_service.py` in full:

```python
from unittest.mock import MagicMock
from services.chat_service import ChatService, extract_word_suggestions
from services.memory_service import MemoryService
from services.prompt_builder import PromptBuilder


def _make_services(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    memory_svc = MemoryService(tmp_store, mm, pb)
    return ChatService(tmp_store, mm, pb, memory_svc), pb


def test_extract_word_suggestions_found():
    text = 'Hello <!--WORD_SUGGESTION:{"word": "食べる", "reading": "たべる"}--> world'
    clean, suggestions = extract_word_suggestions(text)
    assert len(suggestions) == 1
    assert suggestions[0]["word"] == "食べる"
    assert "<!--" not in clean


def test_extract_word_suggestions_none():
    clean, suggestions = extract_word_suggestions("No suggestions here")
    assert suggestions == []
    assert clean == "No suggestions here"


def test_send_message_returns_response(tmp_store, mock_llm):
    mock_llm.generate.return_value = "いいですね。"
    svc, _ = _make_services(tmp_store, mock_llm)
    sid = tmp_store.create_chat_session("ja", "Test")
    result = svc.send_message("ja", sid, "zh-TW", "Hello", image_path=None)
    assert result["response"] == "いいですね。"
    assert result["word_suggestions"] == []


def test_send_message_saves_messages(tmp_store, mock_llm):
    mock_llm.generate.return_value = "こんにちは。"
    svc, _ = _make_services(tmp_store, mock_llm)
    sid = tmp_store.create_chat_session("ja", "Test")
    svc.send_message("ja", sid, "zh-TW", "Hi", image_path=None)
    messages = tmp_store.load_chat_messages("ja", sid)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_send_message_extracts_word_suggestions(tmp_store, mock_llm):
    mock_llm.generate.return_value = (
        'Try 食べる <!--WORD_SUGGESTION:{"word": "食べる", "reading": "たべる"}-->'
    )
    svc, _ = _make_services(tmp_store, mock_llm)
    sid = tmp_store.create_chat_session("ja", "Test")
    result = svc.send_message("ja", sid, "zh-TW", "What does eat mean?", image_path=None)
    assert len(result["word_suggestions"]) == 1
    assert "<!--" not in result["response"]


def test_send_message_with_image_uses_vlm(tmp_store, mock_llm, mock_vlm):
    mock_vlm.generate.return_value = "画像に猫がいます。"
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    mm.get_vlm.return_value = mock_vlm
    memory_svc = MemoryService(tmp_store, mm, pb)
    svc = ChatService(tmp_store, mm, pb, memory_svc)
    sid = tmp_store.create_chat_session("ja", "Test")
    result = svc.send_message("ja", sid, "zh-TW", "What is this?", image_path="/tmp/fake.jpg")
    assert result["response"] == "画像に猫がいます。"
    mm.get_vlm.assert_called_once()
    mm.get_llm.assert_not_called()
```

- [x] **Step 13: Run the ChatService tests**

Run: `uv run pytest tests/test_chat_service.py -v`
Expected: PASS

- [x] **Step 14: Drop `level` from `LessonService`**

Rewrite `services/lesson_service.py` in full:

```python
import json
import uuid

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.chat_service import StreamCollector, extract_word_suggestions
from services.prompt_builder import PromptBuilder


class LessonService:
    def __init__(
        self, store: DataStore, model_manager: ModelManager, prompt_builder: PromptBuilder
    ):
        self._store = store
        self._mm = model_manager
        self._pb = prompt_builder

    def suggest_topics(self, target_lang: str, n: int = 5) -> list[str]:
        progress = self._store.load_lessons_progress(target_lang)
        completed = progress.get("completed", [])
        completed_note = f"Already covered: {', '.join(completed)}. " if completed else ""
        llm = self._mm.get_llm()
        raw = llm.generate(
            [
                {
                    "role": "user",
                    "content": (
                        f"{completed_note}Suggest {n} lesson topics for a {target_lang} learner."
                        f" Return a JSON array of topic name strings only."
                    ),
                }
            ],
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
        topic: str,
        difficulty: str = "Normal",
    ) -> dict:
        lesson_id = f"lesson-{uuid.uuid4().hex[:8]}"
        session_id = self._store.create_chat_session(
            target_lang, f"📝 {topic}", lesson_id=lesson_id
        )

        system_prompt = self._pb.lesson_system_prompt(
            native_lang=native_lang,
            target_lang=target_lang,
            topic=topic,
            phase="structured",
            difficulty=difficulty,
        )
        llm = self._mm.get_llm()
        raw_response = llm.generate(
            [{"role": "user", "content": "Please start the lesson."}],
            system_prompt=system_prompt,
            enable_thinking=False,
        )
        clean_response, word_suggestions = extract_word_suggestions(raw_response)
        self._store.save_chat_messages(
            target_lang, session_id, [{"role": "assistant", "content": clean_response}]
        )
        self._store.save_lesson_notes(
            target_lang, lesson_id, f"# Lesson: {topic}\n\n{clean_response}"
        )

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
        topic: str,
        phase: str,
        difficulty: str,
        user_text: str,
    ) -> dict:
        messages = self._store.load_chat_messages(target_lang, session_id)
        messages.append({"role": "user", "content": user_text})

        system_prompt = self._pb.lesson_system_prompt(
            native_lang=native_lang,
            target_lang=target_lang,
            topic=topic,
            phase=phase,
            difficulty=difficulty,
        )
        llm = self._mm.get_llm()
        raw_response = llm.generate(messages, system_prompt=system_prompt, enable_thinking=False)
        clean_response, word_suggestions = extract_word_suggestions(raw_response)

        messages.append({"role": "assistant", "content": clean_response})
        self._store.save_chat_messages(target_lang, session_id, messages)

        existing_notes = self._store.load_lesson_notes(target_lang, lesson_id)
        self._store.save_lesson_notes(
            target_lang,
            lesson_id,
            existing_notes + f"\n\n**User:** {user_text}\n\n**Tutor:** {clean_response}",
        )

        return {"response": clean_response, "word_suggestions": word_suggestions, "phase": phase}

    def stream_start_lesson(
        self,
        target_lang: str,
        native_lang: str,
        topic: str,
        difficulty: str = "Normal",
    ) -> tuple[str, str, StreamCollector]:
        lesson_id = f"lesson-{uuid.uuid4().hex[:8]}"
        session_id = self._store.create_chat_session(
            target_lang, f"📝 {topic}", lesson_id=lesson_id
        )
        system_prompt = self._pb.lesson_system_prompt(
            native_lang=native_lang,
            target_lang=target_lang,
            topic=topic,
            phase="structured",
            difficulty=difficulty,
        )
        llm = self._mm.get_llm()
        collector = StreamCollector(
            llm.stream(
                [{"role": "user", "content": "Please start the lesson."}],
                system_prompt=system_prompt,
                enable_thinking=False,
            )
        )
        return lesson_id, session_id, collector

    def commit_start_lesson(
        self, target_lang: str, session_id: str, lesson_id: str, topic: str, raw_response: str
    ) -> dict:
        clean_response, word_suggestions = extract_word_suggestions(raw_response)
        self._store.save_chat_messages(
            target_lang, session_id, [{"role": "assistant", "content": clean_response}]
        )
        self._store.save_lesson_notes(
            target_lang, lesson_id, f"# Lesson: {topic}\n\n{clean_response}"
        )
        return {
            "lesson_id": lesson_id,
            "session_id": session_id,
            "response": clean_response,
            "word_suggestions": word_suggestions,
            "phase": "structured",
        }

    def stream_continue_lesson(
        self,
        target_lang: str,
        session_id: str,
        native_lang: str,
        topic: str,
        phase: str,
        difficulty: str,
        user_text: str,
    ) -> StreamCollector:
        messages = self._store.load_chat_messages(target_lang, session_id)
        messages.append({"role": "user", "content": user_text})
        system_prompt = self._pb.lesson_system_prompt(
            native_lang=native_lang,
            target_lang=target_lang,
            topic=topic,
            phase=phase,
            difficulty=difficulty,
        )
        llm = self._mm.get_llm()
        return StreamCollector(
            llm.stream(messages, system_prompt=system_prompt, enable_thinking=False)
        )

    def commit_continue_lesson(
        self,
        target_lang: str,
        session_id: str,
        lesson_id: str,
        user_text: str,
        raw_response: str,
        phase: str,
    ) -> dict:
        messages = self._store.load_chat_messages(target_lang, session_id)
        messages.append({"role": "user", "content": user_text})
        clean_response, word_suggestions = extract_word_suggestions(raw_response)
        messages.append({"role": "assistant", "content": clean_response})
        self._store.save_chat_messages(target_lang, session_id, messages)
        existing_notes = self._store.load_lesson_notes(target_lang, lesson_id)
        self._store.save_lesson_notes(
            target_lang,
            lesson_id,
            existing_notes + f"\n\n**User:** {user_text}\n\n**Tutor:** {clean_response}",
        )
        return {"response": clean_response, "word_suggestions": word_suggestions, "phase": phase}

    def finish_lesson(self, target_lang: str, topic: str) -> None:
        progress = self._store.load_lessons_progress(target_lang)
        if topic not in progress["completed"]:
            progress["completed"].append(topic)
        if topic not in progress.get("topics", []):
            progress.setdefault("topics", []).append(topic)
        self._store.save_lessons_progress(target_lang, progress)
```

- [x] **Step 15: Update the LessonService tests**

Rewrite `tests/test_lesson_service.py` in full:

```python
import json
from unittest.mock import MagicMock
from services.lesson_service import LessonService
from services.prompt_builder import PromptBuilder


def _make_svc(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return LessonService(tmp_store, mm, pb)


def test_suggest_topics(tmp_store, mock_llm):
    mock_llm.generate.return_value = json.dumps(["Food", "Travel", "Shopping", "Weather", "Family"])
    svc = _make_svc(tmp_store, mock_llm)
    topics = svc.suggest_topics("ja")
    assert len(topics) == 5
    assert "Food" in topics


def test_start_lesson_creates_session(tmp_store, mock_llm):
    mock_llm.generate.return_value = "Let's start with vocabulary for food..."
    svc = _make_svc(tmp_store, mock_llm)
    result = svc.start_lesson("ja", "zh-TW", "Food", difficulty="Normal")
    assert "lesson_id" in result
    assert "session_id" in result
    assert "response" in result


def test_continue_lesson_structured(tmp_store, mock_llm):
    mock_llm.generate.return_value = "Good! Now let's do exercises."
    svc = _make_svc(tmp_store, mock_llm)
    lesson_id = "lesson-001"
    session_id = tmp_store.create_chat_session("ja", "Food Lesson", lesson_id=lesson_id)
    tmp_store.save_chat_messages(
        "ja", session_id, [{"role": "assistant", "content": "Let's start."}]
    )
    result = svc.continue_lesson(
        "ja",
        session_id,
        lesson_id,
        "zh-TW",
        "Food",
        phase="structured",
        difficulty="Normal",
        user_text="I understand.",
    )
    assert "response" in result
    assert "phase" in result


def test_finish_lesson_saves_progress(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    svc.finish_lesson("ja", "Food")
    progress = tmp_store.load_lessons_progress("ja")
    assert "Food" in progress["completed"]
```

- [x] **Step 16: Run the LessonService tests**

Run: `uv run pytest tests/test_lesson_service.py -v`
Expected: PASS

- [x] **Step 17: Rename and rewrite the level test service into a plain `QuizService`**

Deviation from the original plan draft: this class was drafted as `TestService`, but pytest treats any class named `Test*` as a test class to collect, which emits a spurious `PytestCollectionWarning` on every run once it's imported into a test file. Named `QuizService` instead (file `services/quiz_service.py`) to avoid that permanently — the UI nav label and page title stay "Test" as designed; only the internal class/module name changed.

Create `services/quiz_service.py`:

```python
import json
from datetime import datetime

from model_manager import ModelManager
from services.prompt_builder import PromptBuilder


class QuizService:
    def __init__(self, model_manager: ModelManager, prompt_builder: PromptBuilder):
        self._mm = model_manager
        self._pb = prompt_builder

    def generate_questions(self, target_lang: str, n_questions: int = 8) -> list[dict]:
        system_prompt = self._pb.test_system_prompt(target_lang, n_questions)
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
            raise ValueError(f"LLM returned invalid JSON for test: {e}") from e

    def evaluate(self, questions: list[dict], answers: list[str]) -> dict:
        correct = sum(1 for q, a in zip(questions, answers) if q["correct"] == a)
        score = round(correct / len(questions) * 100) if questions else 0
        return {
            "score": score,
            "correct": correct,
            "total": len(questions),
            "tested_at": datetime.now().isoformat(),
        }
```

Delete `services/level_test_service.py`:

```bash
rm services/level_test_service.py
```

- [x] **Step 18: Rename and rewrite the level test service tests**

Create `tests/test_quiz_service.py`:

```python
import json
from unittest.mock import MagicMock
from services.quiz_service import QuizService
from services.prompt_builder import PromptBuilder


def _make_svc(mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return QuizService(mm, pb)


def _mock_questions():
    return json.dumps(
        [
            {
                "question": "What does 食べる mean?",
                "options": ["A) to eat", "B) to drink", "C) to sleep", "D) to walk"],
                "correct": "A",
                "explanation": "食べる means to eat.",
            },
            {
                "question": "Which particle marks the subject?",
                "options": ["A) を", "B) に", "C) が", "D) で"],
                "correct": "C",
                "explanation": "が marks the subject.",
            },
        ]
    )


def test_generate_questions(mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(mock_llm)
    questions = svc.generate_questions("ja")
    assert len(questions) == 2
    assert questions[0]["question"] == "What does 食べる mean?"


def test_evaluate_perfect_score(mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(mock_llm)
    questions = svc.generate_questions("ja")
    result = svc.evaluate(questions, ["A", "C"])
    assert result["score"] == 100
    assert result["correct"] == 2
    assert result["total"] == 2
    assert "level" not in result


def test_evaluate_zero_score(mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(mock_llm)
    questions = svc.generate_questions("ja")
    result = svc.evaluate(questions, ["B", "A"])
    assert result["score"] == 0
    assert result["correct"] == 0
```

Delete `tests/test_level_test_service.py`:

```bash
rm tests/test_level_test_service.py
```

- [x] **Step 19: Run the service-layer test sweep for this task**

Run: `uv run pytest tests/test_data_store.py tests/test_language_service.py tests/test_prompt_builder.py tests/test_chat_service.py tests/test_lesson_service.py tests/test_quiz_service.py tests/test_word_list_service.py -v`
Expected: PASS — all tests green (`test_word_list_service.py` is included as a regression check; it doesn't reference `level` and needs no edits)

Do not commit yet — continue to Task 28.

### Task 28: Move the Test UI into its own nav section; remove level display from Home

**Files:**
- Modify: `ui/state.py`
- Modify: `ui/app.py`
- Create: `ui/pages/test.py`
- Modify: `ui/pages/settings.py`
- Modify: `ui/pages/chat.py`
- Modify: `ui/pages/lesson.py`
- Modify: `ui/pages/word_list.py`
- Modify: `ui/pages/home.py`

**Interfaces:**
- Consumes: `QuizService(model_manager, prompt_builder)` from Task 27, registered in `ui/state.py` as `quiz_svc`
- Consumes: `ChatService.send_message`/`stream_message`, `LessonService.*`, `PromptBuilder.*` from Task 27 (all now level-free)

No new automated tests in this task — this repo's `tests/` suite only covers `services/`/`data_store/`, not `ui/pages/` (there are no existing `test_*.py` files for any page). Verify this task by running the app (Step 9).

- [x] **Step 1: Wire `QuizService` into `ui/state.py`**

Rewrite `ui/state.py` in full:

```python
import streamlit as st
from data_store.data_store import DataStore
from model_manager import ModelManager
from services.prompt_builder import PromptBuilder
from services.language_service import LanguageService
from services.memory_service import MemoryService
from services.chat_service import ChatService
from services.word_list_service import WordListService
from services.lesson_service import LessonService
from services.quiz_service import QuizService


def init_services() -> None:
    store = DataStore()
    mm = st.session_state.get("mm") or ModelManager()  # reuse to keep models loaded
    pb = PromptBuilder()
    memory_svc = MemoryService(store, mm, pb)

    st.session_state.store = store
    st.session_state.mm = mm
    st.session_state.pb = pb
    st.session_state.language_svc = LanguageService(store)
    st.session_state.memory_svc = memory_svc
    st.session_state.chat_svc = ChatService(store, mm, pb, memory_svc)
    st.session_state.word_svc = WordListService(store, mm, pb)
    st.session_state.lesson_svc = LessonService(store, mm, pb)
    st.session_state.quiz_svc = QuizService(mm, pb)


def get(key: str):
    return st.session_state[key]
```

- [x] **Step 2: Add the "Test" nav entry to `ui/app.py`**

In `ui/app.py`, replace:

```python
_NAV = [
    ("🏠", "Home"),
    ("📝", "Lesson"),
    ("💬", "Chat"),
    ("📚", "Word List"),
    ("⚙️", "Settings"),
]
```

with:

```python
_NAV = [
    ("🏠", "Home"),
    ("📝", "Lesson"),
    ("💬", "Chat"),
    ("📚", "Word List"),
    ("🧪", "Test"),
    ("⚙️", "Settings"),
]
```

Then replace:

```python
    elif page == "Word List":
        from ui.pages import word_list

        word_list.render()
    elif page == "Settings":
        from ui.pages import settings

        settings.render()
```

with:

```python
    elif page == "Word List":
        from ui.pages import word_list

        word_list.render()
    elif page == "Test":
        from ui.pages import test

        test.render()
    elif page == "Settings":
        from ui.pages import settings

        settings.render()
```

- [x] **Step 3: Create the Test page**

Create `ui/pages/test.py`:

```python
import streamlit as st
from ui.state import get


def render() -> None:
    st.title("🧪 Test")
    st.caption("Practice with a random quiz — no proficiency level involved.")

    language_svc = get("language_svc")
    quiz_svc = get("quiz_svc")
    _, target_lang = language_svc.get_language_pair()

    if st.button("🎲 Generate Test"):
        st.session_state.test_questions = quiz_svc.generate_questions(target_lang)
        st.session_state.test_answers = {}
        st.session_state.pop("test_result", None)
        st.rerun()

    if "test_questions" not in st.session_state:
        st.info("Click **Generate Test** to get a fresh set of random questions.")
        return

    questions = st.session_state.test_questions
    result = st.session_state.get("test_result")

    if result:
        st.success(f"Score: **{result['correct']}/{result['total']}** ({result['score']}%)")
        for i, q in enumerate(questions):
            given = st.session_state.test_answers.get(i)
            correct = q["correct"]
            icon = "✅" if given == correct else "❌"
            st.write(f"{icon} **Q{i + 1}.** {q['question']}")
            st.caption(f"Correct answer: {correct} — {q.get('explanation', '')}")
        if st.button("🔄 Try Another Test"):
            for key in ("test_questions", "test_answers", "test_result"):
                st.session_state.pop(key, None)
            st.rerun()
        return

    st.subheader(f"Test ({len(questions)} questions)")
    for i, q in enumerate(questions):
        st.write(f"**Q{i + 1}.** {q['question']}")
        answer = st.radio(f"q{i}", q["options"], key=f"test_q_{i}", label_visibility="collapsed")
        st.session_state.test_answers[i] = answer[0]

    if st.button("✅ Submit Test"):
        answers = [st.session_state.test_answers.get(i, "A") for i in range(len(questions))]
        st.session_state.test_result = quiz_svc.evaluate(questions, answers)
        language_svc.update_streak(target_lang)
        st.rerun()
```

- [x] **Step 4: Remove the Level Test section from Settings**

Rewrite `ui/pages/settings.py` in full:

```python
import streamlit as st
from ui.state import get

SUPPORTED_LANGUAGES = {
    "zh-TW": "繁體中文 (Traditional Chinese)",
    "en": "English",
    "ja": "日本語 (Japanese)",
    "ko": "한국어 (Korean)",
    "es": "Español (Spanish)",
    "fr": "Français (French)",
    "de": "Deutsch (German)",
}


def render() -> None:
    st.title("⚙️ Settings")

    language_svc = get("language_svc")
    mm = get("mm")
    native_lang, target_lang = language_svc.get_language_pair()

    st.subheader("🌐 Language Pair")
    lang_codes = list(SUPPORTED_LANGUAGES.keys())
    lang_labels = list(SUPPORTED_LANGUAGES.values())

    col1, col2 = st.columns(2)
    with col1:
        native_idx = lang_codes.index(native_lang) if native_lang in lang_codes else 0
        new_native = st.selectbox("Native Language", lang_labels, index=native_idx)
    with col2:
        target_idx = lang_codes.index(target_lang) if target_lang in lang_codes else 2
        new_target = st.selectbox("Learning Language", lang_labels, index=target_idx)

    if st.button("💾 Save Language Settings"):
        new_native_code = lang_codes[lang_labels.index(new_native)]
        new_target_code = lang_codes[lang_labels.index(new_target)]
        language_svc.set_language_pair(native=new_native_code, target=new_target_code)
        st.success("Language settings saved!")
        st.rerun()

    st.divider()
    st.subheader("🤖 Model Status")

    for slot in ("llm", "vlm", "tts", "stt"):
        available = mm.is_model_available(slot)
        model_id = mm.config[slot]["model"]
        icon = "✅" if available else "⬇️"
        st.write(f"**{slot.upper()}** {icon} — `{model_id}`")
        if not available:
            st.code(mm.get_download_command(slot), language="bash")

    st.divider()
    st.subheader("⚠️ Danger Zone")
    store = get("store")
    st.caption(
        f"Permanently delete all chats, word list, lessons, and progress for **{target_lang}**."
    )

    if not st.session_state.get("_confirm_clear"):
        if st.button("🗑️ Clear All History", type="secondary"):
            st.session_state._confirm_clear = True
            st.rerun()
    else:
        st.warning(
            "This will delete **all** chat history, saved words, lesson notes, and progress "
            "for this language. This cannot be undone."
        )
        col_yes, col_no = st.columns([1, 3])
        with col_yes:
            if st.button("Yes, delete everything", type="primary"):
                store.clear_language_history(target_lang)
                for key in [
                    "_confirm_clear",
                    "active_lesson",
                    "suggested_topics",
                    "test_questions",
                    "test_answers",
                    "test_result",
                ]:
                    st.session_state.pop(key, None)
                st.success("All history cleared.")
                st.rerun()
        with col_no:
            if st.button("Cancel"):
                st.session_state._confirm_clear = False
                st.rerun()
```

- [x] **Step 5: Drop `level` from `ui/pages/chat.py`**

In `ui/pages/chat.py`, remove:

```python
    level_data = store.load_level(target_lang)
    level = level_data.get("level", "N4")

```

(the blank line that follows it stays), and in the `chat_svc.stream_message(...)` call, remove the `level=level,` line:

```python
        collector = chat_svc.stream_message(
            lang=target_lang,
            session_id=active_session,
            native_lang=native_lang,
            user_text=final_input,
            image_path=image_path,
        )
```

- [x] **Step 6: Drop `level` from `ui/pages/lesson.py`**

Rewrite `ui/pages/lesson.py` in full:

```python
import streamlit as st
from ui.state import get
from ui.components.word_chip import render_word_chips
from ui.components.stream_display import stream_with_thinking
from ui.components.audio_controls import render_tts_button


def render() -> None:
    st.title("📝 Lesson")

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    lesson_svc = get("lesson_svc")

    if "active_lesson" not in st.session_state:
        _render_topic_picker(lesson_svc, target_lang, native_lang)
    else:
        _render_active_lesson(lesson_svc, language_svc, target_lang, native_lang)


def _render_topic_picker(lesson_svc, target_lang, native_lang) -> None:
    st.subheader("Choose a topic")

    difficulty = st.select_slider("Difficulty", options=["Easy", "Normal", "Hard"], value="Normal")

    col1, col2 = st.columns([3, 1])
    with col1:
        custom_topic = st.text_input("Or enter a custom topic:", placeholder="e.g. ordering coffee")
    with col2:
        if st.button("🎲 Suggest Topics"):
            with st.spinner("Getting suggestions..."):
                st.session_state.suggested_topics = lesson_svc.suggest_topics(target_lang)

    suggested = st.session_state.get("suggested_topics", [])
    if suggested:
        st.write("**Suggested topics:**")
        cols = st.columns(min(len(suggested), 5))
        for i, topic in enumerate(suggested):
            with cols[i % 5]:
                if st.button(topic, key=f"topic_{i}"):
                    _start_lesson(lesson_svc, target_lang, native_lang, topic, difficulty)

    if custom_topic and st.button("▶️ Start Lesson"):
        _start_lesson(lesson_svc, target_lang, native_lang, custom_topic, difficulty)


def _start_lesson(lesson_svc, target_lang, native_lang, topic, difficulty) -> None:
    lesson_id, session_id, collector = lesson_svc.stream_start_lesson(
        target_lang, native_lang, topic, difficulty=difficulty
    )
    with st.chat_message("assistant"):
        stream_with_thinking(collector)
    result = lesson_svc.commit_start_lesson(
        target_lang, session_id, lesson_id, topic, collector.full_text
    )
    st.session_state.active_lesson = {
        "lesson_id": lesson_id,
        "session_id": session_id,
        "topic": topic,
        "difficulty": difficulty,
        "phase": result["phase"],
        "messages": [{"role": "assistant", "content": result["response"]}],
        "word_suggestions": result.get("word_suggestions", []),
    }
    st.rerun()


def _render_active_lesson(lesson_svc, language_svc, target_lang, native_lang) -> None:
    lesson = st.session_state.active_lesson
    topic = lesson["topic"]
    phase = lesson["phase"]
    phase_label = "📖 Structured Lesson" if phase == "structured" else "💬 Free Conversation"

    col1, col2, col3 = st.columns([4, 2, 1])
    with col1:
        st.subheader(f"Topic: {topic} — {phase_label}")
    with col2:
        if phase == "structured":
            if st.button("➡️ Move to Free Conversation"):
                lesson["phase"] = "conversation"
                st.rerun()
    with col3:
        if st.button("✅ Finish"):
            lesson_svc.finish_lesson(target_lang, topic)
            language_svc.update_streak(target_lang)
            del st.session_state.active_lesson
            st.session_state.pop("suggested_topics", None)
            st.rerun()

    for msg in lesson["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                render_tts_button(msg["content"], lang=target_lang, key=msg["content"][:20])

    render_word_chips(lesson.get("word_suggestions", []), lang=target_lang, native_lang=native_lang)

    user_input = st.chat_input("Your response...")
    if user_input:
        lesson["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        collector = lesson_svc.stream_continue_lesson(
            target_lang=target_lang,
            session_id=lesson["session_id"],
            native_lang=native_lang,
            topic=topic,
            phase=lesson["phase"],
            difficulty=lesson["difficulty"],
            user_text=user_input,
        )
        with st.chat_message("assistant"):
            stream_with_thinking(collector)
            render_tts_button(collector.full_text, lang=target_lang, key="lesson_latest")
        result = lesson_svc.commit_continue_lesson(
            target_lang=target_lang,
            session_id=lesson["session_id"],
            lesson_id=lesson["lesson_id"],
            user_text=user_input,
            raw_response=collector.full_text,
            phase=lesson["phase"],
        )

        lesson["messages"].append({"role": "assistant", "content": result["response"]})
        lesson["word_suggestions"] = result.get("word_suggestions", [])
        st.rerun()
```

- [x] **Step 7: Drop `level` from the Word List sentence-construction review**

In `ui/pages/word_list.py`, inside `_render_review`'s `elif mode == "Sentence construction":` block, replace:

```python
        if st.button("Submit for feedback"):
            chat_svc = get("chat_svc")
            language_svc = get("language_svc")
            native_lang_local, target_lang_local = language_svc.get_language_pair()
            store = get("store")
            level_data = store.load_level(target_lang)
            level = level_data.get("level", "N4")
            tmp_session = store.create_chat_session(target_lang, "_review_tmp")
            result = chat_svc.send_message(
                lang=target_lang,
                session_id=tmp_session,
                native_lang=native_lang_local,
                level=level,
                user_text=f"Please evaluate this sentence using the word {word['word']}: {user_sentence}",
                image_path=None,
            )
            store.delete_chat_session(target_lang, tmp_session)
```

with:

```python
        if st.button("Submit for feedback"):
            chat_svc = get("chat_svc")
            language_svc = get("language_svc")
            native_lang_local, target_lang_local = language_svc.get_language_pair()
            store = get("store")
            tmp_session = store.create_chat_session(target_lang, "_review_tmp")
            result = chat_svc.send_message(
                lang=target_lang,
                session_id=tmp_session,
                native_lang=native_lang_local,
                user_text=f"Please evaluate this sentence using the word {word['word']}: {user_sentence}",
                image_path=None,
            )
            store.delete_chat_session(target_lang, tmp_session)
```

- [x] **Step 8: Remove the level suffix from the Home subheader**

In `ui/pages/home.py`, replace:

```python
    st.subheader(f"Learning **{target_name}** · {stats['level'] or 'Level not set'}")
```

with:

```python
    st.subheader(f"Learning **{target_name}**")
```

- [x] **Step 9: Manually verify the UI**

Run: `make run`

In the browser: confirm the sidebar shows a "🧪 Test" entry between "Word List" and "Settings"; open it, click "Generate Test", answer the questions, submit, and confirm you see a score with per-question explanations and no level/proficiency label anywhere. Open "Settings" and confirm the Level Test section is gone. Open "Home" and confirm the subheader no longer shows a level suffix. Open "Chat" and "Lesson" and confirm they still work (send a message / start a lesson).

Do not commit yet — continue to Task 29.

### Task 29: Final verification, commit, push

**Files:** none (verification + git only)

- [x] **Step 1: Run the full test suite**

Run: `make test`
Expected: all tests pass, 0 failed

- [x] **Step 2: Run lint**

Run: `make lint`
Expected: no errors

- [x] **Step 3: Check off Tasks 27–28 above and fill in commit hash placeholders**

Change every `- [x]` under Tasks 27 and 28 in this file to `- [x]`.

- [x] **Step 4: Commit**

```bash
git add data_store/data_store.py tests/test_data_store.py \
  services/language_service.py tests/test_language_service.py \
  services/prompt_builder.py tests/test_prompt_builder.py \
  services/chat_service.py tests/test_chat_service.py \
  services/lesson_service.py tests/test_lesson_service.py \
  services/quiz_service.py tests/test_quiz_service.py \
  ui/state.py ui/app.py ui/pages/test.py ui/pages/settings.py \
  ui/pages/chat.py ui/pages/lesson.py ui/pages/word_list.py ui/pages/home.py \
  docs/superpowers/plans/2026-07-05-language-tutor.md
git rm services/level_test_service.py tests/test_level_test_service.py
git commit -m "$(cat <<'EOF'
feat: move Test out of Settings into its own nav section; drop the level concept

The level test previously lived inside Settings, scored answers against
JLPT/HSK/TOPIK/CEFR tables, and fed that level into Chat, Lesson, and Word
List personalization plus a Home subheader. It's now a standalone "Test"
nav entry that just grades a random practice quiz (score only, nothing
persisted) — the level concept is removed end-to-end so nothing is left
silently pinned to a stale default.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

- [x] **Step 5: Push**

```bash
git push origin main
```

---

## Update: Stream test generation, bilingual explanations, persisted test history

> See `docs/superpowers/specs/2026-07-05-language-tutor-design.md` (final section) for the design rationale.
>
> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to run Tasks 30–32 below.
>
> **Commit strategy:** Task 30's steps run only their own scoped test files (`test_system_prompt`'s new required `native_lang` param only has one caller — `QuizService`, rewritten later in the same task — so nothing else breaks mid-task). Task 31 has no automated tests (this repo's `tests/` suite only covers `services/`/`data_store/`, not `ui/pages/`). **Do not `git commit` after Task 30 or Task 31** — Task 32 runs the full suite and does the single commit + push for this whole update.

### Task 30: Stream generation, bilingual explanations, persisted history in the service layer

**Files:**
- Modify: `data_store/data_store.py` (add `load_quiz_history`/`append_quiz_result`)
- Modify: `tests/test_data_store.py`
- Modify: `services/prompt_builder.py` (`test_system_prompt` gains `native_lang` param and requests bilingual explanations)
- Modify: `tests/test_prompt_builder.py`
- Modify: `services/quiz_service.py` (constructor regains a `store` param; `generate_questions` splits into `stream_questions` + `parse_questions`; `evaluate` gains `target_lang`, builds a per-question breakdown, and persists it)
- Modify: `tests/test_quiz_service.py`

**Interfaces:**
- Produces: `DataStore.load_quiz_history(lang) -> list[dict]`, `DataStore.append_quiz_result(lang, result) -> None`
- Produces: `PromptBuilder.test_system_prompt(native_lang, target_lang, n_questions=8) -> str`
- Produces: `QuizService(store, model_manager, prompt_builder)` with `.stream_questions(native_lang, target_lang, n_questions=8) -> StreamCollector`, `.parse_questions(raw: str) -> list[dict]`, `.evaluate(questions, answers, target_lang) -> dict` (returns `{id, tested_at, score, correct, total, questions: [{question, options, correct, given, is_correct, explanation_target, explanation_native}, ...]}`, and persists that dict via `append_quiz_result`)
- Consumes: `StreamCollector` from `services/chat_service.py` (already used by `ChatService`/`LessonService` — no changes to it)

- [x] **Step 1: Add quiz history storage to `DataStore`**

Edit `data_store/data_store.py`. Add these two methods directly after `save_streak` (before `load_lessons_progress`):

```python
    def load_quiz_history(self, lang: str) -> list[dict]:
        path = self._progress_dir(lang) / "quiz_history.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def append_quiz_result(self, lang: str, result: dict) -> None:
        history = self.load_quiz_history(lang)
        history.append(result)
        path = self._progress_dir(lang) / "quiz_history.json"
        path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
```

- [x] **Step 2: Add the DataStore tests**

Add to `tests/test_data_store.py`:

```python
def test_quiz_history_empty_when_missing(tmp_store):
    assert tmp_store.load_quiz_history("ja") == []


def test_quiz_history_round_trip(tmp_store):
    tmp_store.append_quiz_result("ja", {"id": "abc123", "score": 100})
    tmp_store.append_quiz_result("ja", {"id": "def456", "score": 50})
    history = tmp_store.load_quiz_history("ja")
    assert len(history) == 2
    assert history[0]["id"] == "abc123"
    assert history[1]["score"] == 50
```

- [x] **Step 3: Run the DataStore tests**

Run: `uv run pytest tests/test_data_store.py -v`
Expected: PASS (all tests, including the two new ones)

- [x] **Step 4: Add `native_lang` and bilingual explanations to the test prompt**

In `services/prompt_builder.py`, replace:

```python
    def test_system_prompt(self, target_lang: str, n_questions: int = 8) -> str:
        return (
            f"You are creating a {self._lang_name(target_lang)} ({target_lang}) "
            f"practice quiz.\n\n"
            f"Generate exactly {n_questions} multiple choice questions covering vocabulary, "
            f"grammar, and reading comprehension.\n\n"
            f"Respond ONLY with a JSON array, no other text:\n"
            f"[\n"
            f"  {{\n"
            f'    "question": "...",\n'
            f'    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],\n'
            f'    "correct": "A",\n'
            f'    "explanation": "..."\n'
            f"  }}\n"
            f"]\n"
        )
```

with:

```python
    def test_system_prompt(self, native_lang: str, target_lang: str, n_questions: int = 8) -> str:
        return (
            f"You are creating a {self._lang_name(target_lang)} ({target_lang}) "
            f"practice quiz.\n\n"
            f"Generate exactly {n_questions} multiple choice questions covering vocabulary, "
            f"grammar, and reading comprehension.\n\n"
            f"For each question, write two explanations of why the correct answer is right: "
            f"one in {self._lang_name(target_lang)}, one in {self._lang_name(native_lang)}.\n\n"
            f"Respond ONLY with a JSON array, no other text:\n"
            f"[\n"
            f"  {{\n"
            f'    "question": "...",\n'
            f'    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],\n'
            f'    "correct": "A",\n'
            f'    "explanation_target": "... (in {self._lang_name(target_lang)})",\n'
            f'    "explanation_native": "... (in {self._lang_name(native_lang)})"\n'
            f"  }}\n"
            f"]\n"
        )
```

- [x] **Step 5: Update the PromptBuilder test**

In `tests/test_prompt_builder.py`, replace:

```python
def test_test_prompt_includes_target_lang():
    pb = PromptBuilder()
    prompt = pb.test_system_prompt(target_lang="ja", n_questions=5)
    assert "ja" in prompt or "Japanese" in prompt
    assert "5" in prompt
    assert "JSON" in prompt
```

with:

```python
def test_test_prompt_includes_target_lang():
    pb = PromptBuilder()
    prompt = pb.test_system_prompt(native_lang="zh-TW", target_lang="ja", n_questions=5)
    assert "ja" in prompt or "Japanese" in prompt
    assert "5" in prompt
    assert "JSON" in prompt


def test_test_prompt_requests_bilingual_explanations():
    pb = PromptBuilder()
    prompt = pb.test_system_prompt(native_lang="zh-TW", target_lang="ja", n_questions=5)
    assert "explanation_target" in prompt
    assert "explanation_native" in prompt
    assert "Traditional Chinese" in prompt or "zh-TW" in prompt
```

- [x] **Step 6: Run the PromptBuilder tests**

Run: `uv run pytest tests/test_prompt_builder.py -v`
Expected: PASS

- [x] **Step 7: Rewrite `QuizService` for streaming, bilingual data, and persisted history**

Rewrite `services/quiz_service.py` in full:

```python
import json
import uuid
from datetime import datetime

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.chat_service import StreamCollector
from services.prompt_builder import PromptBuilder


class QuizService:
    def __init__(
        self, store: DataStore, model_manager: ModelManager, prompt_builder: PromptBuilder
    ):
        self._store = store
        self._mm = model_manager
        self._pb = prompt_builder

    def stream_questions(
        self, native_lang: str, target_lang: str, n_questions: int = 8
    ) -> StreamCollector:
        system_prompt = self._pb.test_system_prompt(native_lang, target_lang, n_questions)
        llm = self._mm.get_llm()
        return StreamCollector(
            llm.stream(
                [{"role": "user", "content": "Generate the test questions now."}],
                system_prompt=system_prompt,
                enable_thinking=False,
            )
        )

    def parse_questions(self, raw: str) -> list[dict]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON for test: {e}") from e

    def evaluate(self, questions: list[dict], answers: list[str], target_lang: str) -> dict:
        breakdown = []
        correct_count = 0
        for q, given in zip(questions, answers):
            is_correct = q["correct"] == given
            correct_count += int(is_correct)
            breakdown.append(
                {
                    "question": q["question"],
                    "options": q["options"],
                    "correct": q["correct"],
                    "given": given,
                    "is_correct": is_correct,
                    "explanation_target": q.get("explanation_target", ""),
                    "explanation_native": q.get("explanation_native", ""),
                }
            )
        score = round(correct_count / len(questions) * 100) if questions else 0
        result = {
            "id": uuid.uuid4().hex[:8],
            "tested_at": datetime.now().isoformat(),
            "score": score,
            "correct": correct_count,
            "total": len(questions),
            "questions": breakdown,
        }
        self._store.append_quiz_result(target_lang, result)
        return result
```

- [x] **Step 8: Rewrite the QuizService tests**

Rewrite `tests/test_quiz_service.py` in full:

```python
import json
from unittest.mock import MagicMock
from services.quiz_service import QuizService
from services.prompt_builder import PromptBuilder


def _make_svc(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return QuizService(tmp_store, mm, pb)


def _mock_questions():
    return json.dumps(
        [
            {
                "question": "What does 食べる mean?",
                "options": ["A) to eat", "B) to drink", "C) to sleep", "D) to walk"],
                "correct": "A",
                "explanation_target": "食べるは食べることを意味します。",
                "explanation_native": "食べる的意思是吃。",
            },
            {
                "question": "Which particle marks the subject?",
                "options": ["A) を", "B) に", "C) が", "D) で"],
                "correct": "C",
                "explanation_target": "がは主語を示します。",
                "explanation_native": "が用來標示主語。",
            },
        ]
    )


def test_stream_questions_then_parse(tmp_store, mock_llm):
    mock_llm.stream.return_value = iter([_mock_questions()])
    svc = _make_svc(tmp_store, mock_llm)
    collector = svc.stream_questions("zh-TW", "ja")
    list(collector)  # consume the stream, filling collector.full_text
    questions = svc.parse_questions(collector.full_text)
    assert len(questions) == 2
    assert questions[0]["question"] == "What does 食べる mean?"


def test_parse_questions_strips_code_fence(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    fenced = f"```json\n{_mock_questions()}\n```"
    questions = svc.parse_questions(fenced)
    assert len(questions) == 2


def test_evaluate_perfect_score(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.parse_questions(_mock_questions())
    result = svc.evaluate(questions, ["A", "C"], "ja")
    assert result["score"] == 100
    assert result["correct"] == 2
    assert result["total"] == 2
    assert result["questions"][0]["is_correct"] is True
    assert result["questions"][0]["explanation_native"] == "食べる的意思是吃。"


def test_evaluate_zero_score(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.parse_questions(_mock_questions())
    result = svc.evaluate(questions, ["B", "A"], "ja")
    assert result["score"] == 0
    assert result["questions"][0]["is_correct"] is False


def test_evaluate_persists_to_history(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.parse_questions(_mock_questions())
    result = svc.evaluate(questions, ["A", "C"], "ja")
    history = tmp_store.load_quiz_history("ja")
    assert len(history) == 1
    assert history[0]["id"] == result["id"]
    assert history[0]["score"] == 100
```

- [x] **Step 9: Run the QuizService tests**

Run: `uv run pytest tests/test_quiz_service.py -v`
Expected: PASS

Do not commit yet — continue to Task 31.

### Task 31: Wire streaming, bilingual review, and history into the Test page

**Files:**
- Modify: `ui/state.py` (`QuizService` now takes `store` as its first constructor argument)
- Modify: `ui/pages/test.py` (streaming generation, bilingual review, Past Attempts section)

**Interfaces:**
- Consumes: `QuizService(store, model_manager, prompt_builder)` from Task 30, with `.stream_questions(native_lang, target_lang, n_questions=8)`, `.parse_questions(raw)`, `.evaluate(questions, answers, target_lang)`
- Consumes: `stream_with_thinking(collector)` from `ui/components/stream_display.py` (already used by Lesson — unchanged)
- Consumes: `DataStore.load_quiz_history(lang)` from Task 30

No new automated tests in this task, matching this repo's existing convention — `tests/` covers `services/`/`data_store/` only, not `ui/pages/`. Verify with `make run` (Step 3).

- [x] **Step 1: Pass `store` into `QuizService` in `ui/state.py`**

In `ui/state.py`, replace:

```python
    st.session_state.quiz_svc = QuizService(mm, pb)
```

with:

```python
    st.session_state.quiz_svc = QuizService(store, mm, pb)
```

- [x] **Step 2: Rewrite the Test page**

Rewrite `ui/pages/test.py` in full:

```python
import streamlit as st
from ui.state import get
from ui.components.stream_display import stream_with_thinking


def render() -> None:
    st.title("🧪 Test")
    st.caption("Practice with a random quiz — no proficiency level involved.")

    language_svc = get("language_svc")
    quiz_svc = get("quiz_svc")
    store = get("store")
    native_lang, target_lang = language_svc.get_language_pair()

    if st.button("🎲 Generate Test"):
        collector = quiz_svc.stream_questions(native_lang, target_lang)
        stream_with_thinking(collector)
        st.session_state.test_questions = quiz_svc.parse_questions(collector.full_text)
        st.session_state.test_answers = {}
        st.session_state.pop("test_result", None)
        st.rerun()

    questions = st.session_state.get("test_questions")
    result = st.session_state.get("test_result")

    if questions and not result:
        st.subheader(f"Test ({len(questions)} questions)")
        for i, q in enumerate(questions):
            st.write(f"**Q{i + 1}.** {q['question']}")
            answer = st.radio(
                f"q{i}", q["options"], key=f"test_q_{i}", label_visibility="collapsed"
            )
            st.session_state.test_answers[i] = answer[0]

        if st.button("✅ Submit Test"):
            answers = [st.session_state.test_answers.get(i, "A") for i in range(len(questions))]
            st.session_state.test_result = quiz_svc.evaluate(questions, answers, target_lang)
            language_svc.update_streak(target_lang)
            st.rerun()
        return

    if result:
        st.success(f"Score: **{result['correct']}/{result['total']}** ({result['score']}%)")
        _render_review(result["questions"])
        if st.button("🔄 Try Another Test"):
            for key in ("test_questions", "test_answers", "test_result"):
                st.session_state.pop(key, None)
            st.rerun()

    _render_history(store, target_lang)


def _render_review(questions: list[dict]) -> None:
    for i, q in enumerate(questions):
        icon = "✅" if q["is_correct"] else "❌"
        st.write(f"{icon} **Q{i + 1}.** {q['question']}")
        st.caption(f"Correct answer: {q['correct']}")
        st.caption(f"🎯 {q.get('explanation_target', '')}")
        st.caption(f"🏠 {q.get('explanation_native', '')}")


def _render_history(store, target_lang: str) -> None:
    history = store.load_quiz_history(target_lang)
    st.divider()
    st.subheader("📜 Past Attempts")
    if not history:
        st.info("No attempts yet — click **Generate Test** above to start.")
        return
    for attempt in reversed(history):
        label = (
            f"{attempt['tested_at'][:16].replace('T', ' ')} — "
            f"{attempt['score']}% ({attempt['correct']}/{attempt['total']})"
        )
        with st.expander(label):
            _render_review(attempt["questions"])
```

- [x] **Step 3: Manually verify the UI**

Run: `make run`

In the browser: open "Test", click "Generate Test", and confirm you see the thinking-dots animation followed by streaming JSON text before the quiz questions appear. Answer and submit; confirm the result shows a score plus, per question, both a 🎯 target-language and a 🏠 native-language explanation line. Scroll down and confirm a "📜 Past Attempts" section lists the attempt you just took, expandable to the same review. Click "Generate Test" again, take a second quiz, and confirm both attempts now appear in Past Attempts (most recent first).

Do not commit yet — continue to Task 32.

### Task 32: Final verification, commit, push

**Files:** none (verification + git only)

- [x] **Step 1: Run the full test suite**

Run: `make test`
Expected: all tests pass, 0 failed

- [x] **Step 2: Run lint**

Run: `make lint`
Expected: no new errors (the 2 pre-existing unused-import warnings in `ui/pages/chat.py` and `ui/pages/word_list.py` are unrelated to this change — leave them)

- [x] **Step 3: Check off Tasks 30–31 above**

Change every `- [x]` under Tasks 30 and 31 in this file to `- [x]`.

- [x] **Step 4: Commit**

```bash
git add data_store/data_store.py tests/test_data_store.py \
  services/prompt_builder.py tests/test_prompt_builder.py \
  services/quiz_service.py tests/test_quiz_service.py \
  ui/state.py ui/pages/test.py \
  docs/superpowers/plans/2026-07-05-language-tutor.md
git commit -m "$(cat <<'EOF'
feat: stream test generation, add bilingual explanations, persist test history

Quiz generation now streams live (thinking dots -> streaming JSON,
matching Chat/Lesson) instead of blocking behind a spinner. Each
question's explanation is written in both the target and native
language. Every graded attempt is now saved with a full per-question
breakdown and shown in a new Past Attempts section on the Test page.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

- [x] **Step 5: Push**

```bash
git push origin main
```

---

## Fix: streaming quiz generation leaked answers and broke rendering

See `docs/superpowers/specs/2026-07-05-language-tutor-design.md` (final section) for the root-cause writeup.

- [x] **Step 1:** Diagnose — `stream_with_thinking` renders every accumulated chunk via `st.markdown`, which for Chat/Lesson is safe (prose) but for the quiz JSON exposed `"correct"` and both explanation fields live on screen, and raw JSON through Markdown mid-stream rendered garbled
- [x] **Step 2:** Add `stream_silently(collector)` to `ui/components/stream_display.py` — same thinking-dots animation, drains the stream without ever displaying its content
- [x] **Step 3:** Swap `ui/pages/test.py`'s quiz-generation call from `stream_with_thinking` to `stream_silently`; `stream_with_thinking` itself is unchanged and still used by Lesson
- [x] **Step 4:** Run full test suite — 77 passed; `make lint` unchanged (same 2 pre-existing unrelated warnings)
- [x] **Step 5:** Commit — `fix: stop leaking quiz answers during streaming generation` (this update)
- [x] **Step 6:** Push

---

## Fix: Lesson topic picker skipped confirmation; `<speak>` tags leaked as raw text

See `docs/superpowers/specs/2026-07-05-language-tutor-design.md` (final section) for the design rationale.

**Files:** `ui/pages/lesson.py`

- [x] **Step 1:** Diagnose — clicking a suggested topic called `_start_lesson` immediately with no confirmation step; separately, Lesson rendered assistant messages via `st.write` + a whole-message `render_tts_button` instead of `render_message_with_tts` (what Chat uses), so `<speak>` tags were never parsed out of the displayed text
- [x] **Step 2:** Rework `_render_topic_picker` — suggested-topic buttons now populate the `lesson_topic_input`-keyed text box via an `on_click` callback instead of starting the lesson; a shared `pending_topic` session-state flag (set by the text box's `on_change` callback on Enter, or by the "▶️ Start Lesson" button) is checked once at the end of the function as the single call site for `_start_lesson`
- [x] **Step 3:** Swap both assistant-message render sites in `_render_active_lesson` (the history loop and the just-streamed response) from `st.write`/`render_tts_button` to `render_message_with_tts`, matching `ui/pages/chat.py`; drop the now-unused `render_tts_button` import
- [x] **Step 4:** Verify with Streamlit's `AppTest` harness (no browser available in this environment) driving the real `ui/pages/lesson.py` against faked `language_svc`/`lesson_svc`/`mm` services — confirmed a suggested-topic click only populates the text box (no lesson start), both Enter-to-submit and the Start Lesson button correctly start the lesson, and a message containing `<speak>こんにちは</speak>` renders as three clean segments with no raw tag visible
- [x] **Step 5:** Run full test suite — 77 passed (no service-layer changes); `make lint` clean
- [x] **Step 6:** Commit — `fix: require explicit confirmation for suggested lesson topics; fix speak tag leak in lesson` (this update)
- [x] **Step 7:** Push

---

## Feature: fine-grained per-language difficulty for Lesson and Test

See `docs/superpowers/specs/2026-07-05-language-tutor-design.md` (final section) for the design rationale, including why this is not a reintroduction of the removed level/proficiency concept.

**Files:** `services/prompt_builder.py`, `services/lesson_service.py`, `services/quiz_service.py`, `ui/pages/lesson.py`, `ui/pages/test.py`, `tests/test_prompt_builder.py`, `tests/test_lesson_service.py`, `tests/test_quiz_service.py`

- [x] **Step 1:** Add `DIFFICULTY_FRAMEWORKS` (ja→JLPT N5-N1, zh-TW/zh→HSK1-6, ko→TOPIK1-6) and `_CEFR_FRAMEWORK` fallback (A1-C2) plus `get_difficulty_levels(target_lang) -> dict` to `services/prompt_builder.py`; delete the old `DIFFICULTY_INSTRUCTIONS` (Easy/Normal/Hard) dict, now unused
- [x] **Step 2:** Rewrite `lesson_system_prompt`'s difficulty line to `"Target proficiency: {framework} {level} — calibrate vocabulary, grammar complexity, and pace..."`, drop its `difficulty="Normal"` default (now required); add the same framework-lookup difficulty line to `test_system_prompt`, adding a required `difficulty` parameter positioned before `n_questions=8`
- [x] **Step 3:** Drop `difficulty="Normal"` defaults from `LessonService.start_lesson`/`stream_start_lesson` (now required, matching `continue_lesson`/`stream_continue_lesson`); add the matching required `difficulty` parameter to `QuizService.stream_questions`, forwarded to `test_system_prompt`
- [x] **Step 4:** Replace `ui/pages/lesson.py`'s `st.select_slider("Difficulty", options=["Easy","Normal","Hard"])` with one built from `get_difficulty_levels(target_lang)`, labeled `f"Difficulty ({framework['name']})"`, defaulting to the middle level
- [x] **Step 5:** Add the identical difficulty slider to `ui/pages/test.py` above "🎲 Generate Test", wired into `quiz_svc.stream_questions(...)`; update the page caption from "no proficiency level involved" to "Practice with a random quiz at your chosen difficulty" (the old wording no longer described the page)
- [x] **Step 6:** Update tests: `test_prompt_builder.py` (real level strings instead of Easy/Normal/Hard, new `test_get_difficulty_levels_known_language`/`test_get_difficulty_levels_falls_back_to_cefr`/`test_*_includes_difficulty_framework` tests), `test_lesson_service.py` and `test_quiz_service.py` (pass real level strings)
- [x] **Step 7:** Verify with Streamlit's `AppTest` harness (no browser in this environment): Lesson's slider shows `Difficulty (JLPT)` with `[N5,N4,N3,N2,N1]` for target `ja` and falls back to `Difficulty (CEFR)` for target `es`; Test's slider shows `Difficulty (TOPIK)` for target `ko`; selecting `N1` on Test and clicking Generate Test calls `stream_questions` with that exact difficulty
- [x] **Step 8:** Run full test suite — 81 passed (4 new); `make lint`/`make format` clean (same 2 pre-existing unrelated warnings)
- [x] **Step 9:** Commit — `feat: add fine-grained per-language difficulty levels to Lesson and Test` (this update)
- [x] **Step 10:** Push
