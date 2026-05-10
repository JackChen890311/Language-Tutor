# Language Tutor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first AI language tutor that runs entirely on a MacBook M4 Pro with Streamlit UI, MLX models, and local JSON/Markdown storage.

**Architecture:** Four-layer system — UI (Streamlit) → Services (business logic) → Models (LLM/VLM/TTS/STT abstractions) → Data (DataStore). No layer imports from a layer above it. Services are UI-agnostic. All model slots are swappable via `config/models.json`.

**Tech Stack:** Python 3.11+, uv, ruff, streamlit, mlx-lm, mlx-vlm, mlx-audio, pytest

---

## File Map

```
language_tutor/
├── config/
│   └── models.json
├── models/
│   ├── __init__.py
│   ├── base.py              # BaseLLM, BaseVLM, BaseTTS, BaseSTT
│   ├── mlx_llm.py           # MLXLLMModel
│   ├── mlx_vlm.py           # MLXVLMModel
│   ├── mlx_tts.py           # MLXTTSModel (Kokoro)
│   └── mlx_stt.py           # WhisperModel
├── data_store/
│   ├── __init__.py
│   └── data_store.py        # DataStore — sole filesystem I/O class
├── services/
│   ├── __init__.py
│   ├── prompt_builder.py    # PromptBuilder — all system prompt assembly
│   ├── language_service.py  # LanguageService
│   ├── memory_service.py    # MemoryService — rolling window + summarization
│   ├── chat_service.py      # ChatService
│   ├── level_test_service.py
│   ├── lesson_service.py
│   └── word_list_service.py
├── model_manager.py         # ModelManager — startup checks + lazy loading
├── ui/
│   ├── __init__.py
│   ├── app.py               # Streamlit entry point
│   ├── state.py             # Session state helpers
│   ├── pages/
│   │   ├── home.py
│   │   ├── chat.py
│   │   ├── lesson.py
│   │   ├── word_list.py
│   │   └── settings.py
│   └── components/
│       ├── word_chip.py     # One-click word save chip
│       └── audio_controls.py
├── tests/
│   ├── conftest.py
│   ├── test_data_store.py
│   ├── test_prompt_builder.py
│   ├── test_language_service.py
│   ├── test_memory_service.py
│   ├── test_chat_service.py
│   ├── test_level_test_service.py
│   ├── test_lesson_service.py
│   └── test_word_list_service.py
├── pyproject.toml
├── .gitignore
└── .python-version
```

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.python-version`
- Create: `config/models.json`
- Create all `__init__.py` stubs

- [ ] **Step 1: Initialize git and uv project**

```bash
git init
uv init --name language-tutor --python 3.11
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "language-tutor"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "streamlit>=1.35.0",
    "mlx-lm>=0.21.0",
    "mlx-vlm>=0.1.9",
    "mlx-audio>=0.2.0",
    "misaki[ja]>=0.9.0",
]

[dependency-groups]
dev = [
    "pytest>=8.2.0",
    "ruff>=0.6.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Write `.python-version`**

```
3.11
```

- [ ] **Step 4: Write `.gitignore`**

```
data/
__pycache__/
*.pyc
.venv/
*.egg-info/
.ruff_cache/
.pytest_cache/
*.DS_Store
```

- [ ] **Step 5: Write `config/models.json`**

```json
{
  "llm": { "provider": "mlx", "model": "mlx-community/Qwen3.6-35B-A3B-4bit" },
  "vlm": { "provider": "mlx", "model": "mlx-community/Qwen3-VL-8B-Instruct" },
  "tts": { "provider": "mlx-audio", "model": "kokoro" },
  "stt": { "provider": "mlx-audio", "model": "whisper-large-v3" }
}
```

- [ ] **Step 6: Create directory structure and empty `__init__.py` files**

```bash
mkdir -p models data_store services ui/pages ui/components tests config
touch models/__init__.py data_store/__init__.py services/__init__.py
touch ui/__init__.py ui/pages/__init__.py ui/components/__init__.py
touch tests/__init__.py
```

- [ ] **Step 7: Install dependencies**

```bash
uv sync --dev
```

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: initialize project structure"
```

---

## Task 2: Abstract Model Base Classes

**Files:**
- Create: `models/base.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write `models/base.py`**

```python
from abc import ABC, abstractmethod
from typing import Iterator


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages: list[dict], system_prompt: str = "") -> str: ...

    @abstractmethod
    def stream(self, messages: list[dict], system_prompt: str = "") -> Iterator[str]: ...

    @abstractmethod
    def unload(self) -> None: ...


class BaseVLM(ABC):
    @abstractmethod
    def generate(self, messages: list[dict], image_path: str, system_prompt: str = "") -> str: ...

    @abstractmethod
    def unload(self) -> None: ...


class BaseTTS(ABC):
    @abstractmethod
    def synthesize(self, text: str, lang: str = "en-us") -> bytes: ...

    @abstractmethod
    def unload(self) -> None: ...


class BaseSTT(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> str: ...

    @abstractmethod
    def unload(self) -> None: ...
```

- [ ] **Step 2: Write `tests/conftest.py`**

```python
import pytest
from unittest.mock import MagicMock
from models.base import BaseLLM, BaseVLM, BaseTTS, BaseSTT
from data_store.data_store import DataStore


@pytest.fixture
def tmp_store(tmp_path):
    return DataStore(str(tmp_path))


@pytest.fixture
def mock_llm():
    mock = MagicMock(spec=BaseLLM)
    mock.generate.return_value = "mock response"
    mock.stream.return_value = iter(["mock", " ", "response"])
    return mock


@pytest.fixture
def mock_vlm():
    mock = MagicMock(spec=BaseVLM)
    mock.generate.return_value = "mock vlm response"
    return mock


@pytest.fixture
def mock_tts():
    mock = MagicMock(spec=BaseTTS)
    mock.synthesize.return_value = b"mock audio bytes"
    return mock


@pytest.fixture
def mock_stt():
    mock = MagicMock(spec=BaseSTT)
    mock.transcribe.return_value = "mock transcription"
    return mock
```

- [ ] **Step 3: Write a quick smoke test**

```python
# tests/test_base_models.py
from unittest.mock import MagicMock
from models.base import BaseLLM, BaseVLM, BaseTTS, BaseSTT


def test_base_classes_are_abstract():
    import inspect
    assert inspect.isabstract(BaseLLM)
    assert inspect.isabstract(BaseVLM)
    assert inspect.isabstract(BaseTTS)
    assert inspect.isabstract(BaseSTT)


def test_mock_llm_conforms_to_interface(mock_llm):
    result = mock_llm.generate([{"role": "user", "content": "hi"}])
    assert isinstance(result, str)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_base_models.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add models/base.py tests/conftest.py tests/test_base_models.py
git commit -m "feat: add abstract model base classes"
```

---

## Task 3: DataStore

**Files:**
- Create: `data_store/data_store.py`
- Create: `tests/test_data_store.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_data_store.py
import pytest
from data_store.data_store import DataStore


def test_settings_round_trip(tmp_store):
    tmp_store.save_settings({"native_lang": "zh-TW", "target_lang": "ja"})
    result = tmp_store.load_settings()
    assert result["native_lang"] == "zh-TW"
    assert result["target_lang"] == "ja"


def test_load_settings_returns_empty_dict_when_missing(tmp_store):
    assert tmp_store.load_settings() == {}


def test_level_round_trip(tmp_store):
    tmp_store.save_level("ja", {"level": "N4", "score": 80})
    result = tmp_store.load_level("ja")
    assert result["level"] == "N4"


def test_create_and_list_chat_sessions(tmp_store):
    session_id = tmp_store.create_chat_session("ja", "Shopping trip")
    sessions = tmp_store.list_chat_sessions("ja")
    assert len(sessions) == 1
    assert sessions[0]["name"] == "Shopping trip"
    assert sessions[0]["id"] == session_id


def test_chat_messages_round_trip(tmp_store):
    sid = tmp_store.create_chat_session("ja", "Test")
    messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
    tmp_store.save_chat_messages("ja", sid, messages)
    result = tmp_store.load_chat_messages("ja", sid)
    assert result == messages


def test_chat_summary_appends(tmp_store):
    sid = tmp_store.create_chat_session("ja", "Test")
    tmp_store.append_chat_summary("ja", sid, "First summary.")
    tmp_store.append_chat_summary("ja", sid, "Second summary.")
    summary = tmp_store.load_chat_summary("ja", sid)
    assert "First summary." in summary
    assert "Second summary." in summary


def test_delete_chat_session(tmp_store):
    sid = tmp_store.create_chat_session("ja", "To delete")
    tmp_store.delete_chat_session("ja", sid)
    assert tmp_store.list_chat_sessions("ja") == []


def test_wordlist_round_trip(tmp_store):
    words = [{"id": "abc", "word": "食べる", "definition": "to eat"}]
    tmp_store.save_wordlist("ja", words)
    result = tmp_store.load_wordlist("ja")
    assert result[0]["word"] == "食べる"


def test_lessons_progress_round_trip(tmp_store):
    tmp_store.save_lessons_progress("ja", {"completed": ["food"], "topics": ["food"]})
    result = tmp_store.load_lessons_progress("ja")
    assert "food" in result["completed"]


def test_lesson_notes_round_trip(tmp_store):
    tmp_store.save_lesson_notes("ja", "lesson-001", "# Lesson notes\nVocab: ...")
    result = tmp_store.load_lesson_notes("ja", "lesson-001")
    assert "Lesson notes" in result
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_data_store.py -v
```
Expected: ImportError or multiple FAILs

- [ ] **Step 3: Write `data_store/data_store.py`**

```python
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

    def load_level(self, lang: str) -> dict:
        path = self._progress_dir(lang) / "level.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def save_level(self, lang: str, data: dict) -> None:
        path = self._progress_dir(lang) / "level.json"
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
        sessions.append({
            "id": session_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "lesson_id": lesson_id,
        })
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
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_data_store.py -v
```
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add data_store/data_store.py tests/test_data_store.py
git commit -m "feat: add DataStore with full file I/O"
```

---

## Task 4: ModelManager

**Files:**
- Create: `model_manager.py`
- Create: `tests/test_model_manager.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_model_manager.py
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from model_manager import ModelManager


@pytest.fixture
def config_file(tmp_path):
    cfg = {
        "llm": {"provider": "mlx", "model": "mlx-community/Qwen3.6-35B-A3B-4bit"},
        "vlm": {"provider": "mlx", "model": "mlx-community/Qwen3-VL-8B-Instruct"},
        "tts": {"provider": "mlx-audio", "model": "kokoro"},
        "stt": {"provider": "mlx-audio", "model": "whisper-large-v3"},
    }
    p = tmp_path / "models.json"
    p.write_text(json.dumps(cfg))
    return str(p)


def test_loads_config(config_file):
    mgr = ModelManager(config_file)
    assert mgr.config["llm"]["model"] == "mlx-community/Qwen3.6-35B-A3B-4bit"


def test_get_download_command(config_file):
    mgr = ModelManager(config_file)
    cmd = mgr.get_download_command("llm")
    assert "mlx-community/Qwen3.6-35B-A3B-4bit" in cmd
    assert "huggingface-cli" in cmd


def test_check_model_available_missing(config_file, tmp_path):
    mgr = ModelManager(config_file)
    with patch.object(Path, "exists", return_value=False):
        assert mgr.is_model_available("llm") is False


def test_check_model_available_present(config_file):
    mgr = ModelManager(config_file)
    with patch.object(Path, "exists", return_value=True):
        assert mgr.is_model_available("llm") is True
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_model_manager.py -v
```
Expected: ImportError

- [ ] **Step 3: Write `model_manager.py`**

```python
import json
from pathlib import Path

from models.base import BaseLLM, BaseVLM, BaseTTS, BaseSTT


class ModelManager:
    def __init__(self, config_path: str = "config/models.json"):
        with open(config_path, encoding="utf-8") as f:
            self.config: dict = json.load(f)
        self._llm: BaseLLM | None = None
        self._vlm: BaseVLM | None = None
        self._tts: BaseTTS | None = None
        self._stt: BaseSTT | None = None

    def is_model_available(self, slot: str) -> bool:
        model_id: str = self.config[slot]["model"]
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        dir_name = "models--" + model_id.replace("/", "--")
        return (cache_dir / dir_name).exists()

    def get_download_command(self, slot: str) -> str:
        model_id: str = self.config[slot]["model"]
        return f"huggingface-cli download {model_id}"

    def get_llm(self) -> BaseLLM:
        if self._llm is None:
            from models.mlx_llm import MLXLLMModel
            self._llm = MLXLLMModel(self.config["llm"]["model"])
        return self._llm

    def get_vlm(self) -> BaseVLM:
        if self._vlm is None:
            from models.mlx_vlm import MLXVLMModel
            self._vlm = MLXVLMModel(self.config["vlm"]["model"])
        return self._vlm

    def get_tts(self) -> BaseTTS:
        if self._tts is None:
            from models.mlx_tts import MLXTTSModel
            self._tts = MLXTTSModel(self.config["tts"]["model"])
        return self._tts

    def get_stt(self) -> BaseSTT:
        if self._stt is None:
            from models.mlx_stt import WhisperModel
            self._stt = WhisperModel(self.config["stt"]["model"])
        return self._stt

    def unload(self, slot: str) -> None:
        model = getattr(self, f"_{slot}")
        if model is not None:
            model.unload()
            setattr(self, f"_{slot}", None)
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_model_manager.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add model_manager.py tests/test_model_manager.py
git commit -m "feat: add ModelManager with lazy loading and availability checks"
```

---

## Task 5: MLX Model Implementations

**Files:**
- Create: `models/mlx_llm.py`
- Create: `models/mlx_vlm.py`
- Create: `models/mlx_tts.py`
- Create: `models/mlx_stt.py`

These wrap real hardware-dependent libraries. Tests mock the underlying calls.

- [ ] **Step 1: Write `models/mlx_llm.py`**

```python
import gc
from typing import Iterator

from models.base import BaseLLM


class MLXLLMModel(BaseLLM):
    def __init__(self, model_path: str):
        self._model_path = model_path
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from mlx_lm import load
            self._model, self._tokenizer = load(self._model_path)

    def _build_prompt(self, messages: list[dict], system_prompt: str) -> str:
        self._ensure_loaded()
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)
        return self._tokenizer.apply_chat_template(
            all_messages, tokenize=False, add_generation_prompt=True
        )

    def generate(self, messages: list[dict], system_prompt: str = "") -> str:
        from mlx_lm import generate
        self._ensure_loaded()
        prompt = self._build_prompt(messages, system_prompt)
        return generate(self._model, self._tokenizer, prompt=prompt, max_tokens=2048, verbose=False)

    def stream(self, messages: list[dict], system_prompt: str = "") -> Iterator[str]:
        from mlx_lm import stream_generate
        self._ensure_loaded()
        prompt = self._build_prompt(messages, system_prompt)
        for token in stream_generate(self._model, self._tokenizer, prompt=prompt, max_tokens=2048):
            yield token

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        gc.collect()
```

- [ ] **Step 2: Write `models/mlx_vlm.py`**

```python
import gc
from models.base import BaseVLM


class MLXVLMModel(BaseVLM):
    def __init__(self, model_path: str):
        self._model_path = model_path
        self._model = None
        self._processor = None
        self._config = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from mlx_vlm import load
            from mlx_vlm.utils import load_config
            self._model, self._processor = load(self._model_path)
            self._config = load_config(self._model_path)

    def generate(self, messages: list[dict], image_path: str, system_prompt: str = "") -> str:
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template
        self._ensure_loaded()
        user_text = messages[-1]["content"] if messages else ""
        prompt = apply_chat_template(
            self._processor, self._config, user_text, num_images=1
        )
        return generate(
            self._model, self._processor, image_path, prompt, max_tokens=1024, verbose=False
        )

    def unload(self) -> None:
        self._model = None
        self._processor = None
        self._config = None
        gc.collect()
```

- [ ] **Step 3: Write `models/mlx_tts.py`**

```python
import gc
from models.base import BaseTTS


class MLXTTSModel(BaseTTS):
    def __init__(self, model_name: str = "kokoro"):
        self._model_name = model_name
        self._pipeline = None

    def _ensure_loaded(self) -> None:
        if self._pipeline is None:
            from mlx_audio.tts.models.kokoro import KokoroPipeline
            self._pipeline = KokoroPipeline(lang_code="j")  # multilingual

    def synthesize(self, text: str, lang: str = "en-us") -> bytes:
        import io
        import wave
        import numpy as np
        self._ensure_loaded()
        audio_chunks = []
        for _, _, audio in self._pipeline(text):
            if audio is not None:
                audio_chunks.append(audio)
        if not audio_chunks:
            return b""
        combined = np.concatenate(audio_chunks)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes((combined * 32767).astype(np.int16).tobytes())
        return buf.getvalue()

    def unload(self) -> None:
        self._pipeline = None
        gc.collect()
```

- [ ] **Step 4: Write `models/mlx_stt.py`**

```python
import gc
from models.base import BaseSTT


class WhisperModel(BaseSTT):
    def __init__(self, model_name: str = "whisper-large-v3"):
        self._model_name = model_name
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            import mlx_whisper
            self._model = mlx_whisper

    def transcribe(self, audio_path: str) -> str:
        self._ensure_loaded()
        result = self._model.transcribe(audio_path, path_or_hf_repo=f"mlx-community/{self._model_name}")
        return result.get("text", "").strip()

    def unload(self) -> None:
        self._model = None
        gc.collect()
```

- [ ] **Step 5: Run a smoke import test**

```bash
uv run python -c "from models.mlx_llm import MLXLLMModel; print('OK')"
uv run python -c "from models.mlx_vlm import MLXVLMModel; print('OK')"
uv run python -c "from models.mlx_tts import MLXTTSModel; print('OK')"
uv run python -c "from models.mlx_stt import WhisperModel; print('OK')"
```
Expected: OK printed four times (no import errors at module level — mlx libs are imported lazily)

- [ ] **Step 6: Commit**

```bash
git add models/
git commit -m "feat: add MLX model implementations (LLM, VLM, TTS, STT)"
```

---

## Task 6: PromptBuilder

**Files:**
- Create: `services/prompt_builder.py`
- Create: `tests/test_prompt_builder.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_prompt_builder.py
from services.prompt_builder import PromptBuilder


def test_chat_prompt_includes_languages():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja", level="N4")
    assert "zh-TW" in prompt or "Traditional Chinese" in prompt
    assert "ja" in prompt or "Japanese" in prompt
    assert "N4" in prompt


def test_chat_prompt_chinese_native_includes_traditional_chinese_rule():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja", level="N4")
    assert "繁體中文" in prompt or "Traditional Chinese" in prompt
    assert "台灣" in prompt


def test_chat_prompt_english_native_no_chinese_rule():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="en", target_lang="ja", level="N4")
    assert "台灣" not in prompt


def test_level_test_prompt_includes_target_lang():
    pb = PromptBuilder()
    prompt = pb.level_test_system_prompt(target_lang="ja", n_questions=5)
    assert "ja" in prompt or "Japanese" in prompt
    assert "5" in prompt
    assert "JSON" in prompt


def test_word_enrichment_prompt():
    pb = PromptBuilder()
    prompt = pb.word_enrichment_prompt(target_lang="ja", native_lang="zh-TW")
    assert "JSON" in prompt
    assert "definition" in prompt


def test_summarization_prompt():
    pb = PromptBuilder()
    prompt = pb.summarization_prompt(native_lang="zh-TW")
    assert "300" in prompt
    assert "zh-TW" in prompt or "Traditional Chinese" in prompt


def test_lesson_prompt_includes_phase():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW", target_lang="ja", level="N4",
        topic="food", phase="structured", difficulty="Normal"
    )
    assert "food" in prompt
    assert "structured" in prompt or "vocabulary" in prompt.lower()


def test_lesson_prompt_conversation_phase():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW", target_lang="ja", level="N4",
        topic="food", phase="conversation", difficulty="Hard"
    )
    assert "conversation" in prompt.lower() or "free" in prompt.lower()
    assert "Hard" in prompt or "minimal" in prompt.lower()
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_prompt_builder.py -v
```
Expected: ImportError

- [ ] **Step 3: Write `services/prompt_builder.py`**

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
    "Normal": "Match the user's assessed proficiency level naturally.",
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

    def chat_system_prompt(self, native_lang: str, target_lang: str, level: str) -> str:
        return (
            f"You are a patient and encouraging language tutor.\n\n"
            f"Native language: {self._lang_name(native_lang)} ({native_lang})\n"
            f"Target language: {self._lang_name(target_lang)} ({target_lang})\n"
            f"User proficiency: {level}\n\n"
            f"Rules:\n"
            f"- Respond in {self._lang_name(native_lang)} for explanations and feedback\n"
            f"- Use {self._lang_name(target_lang)} for language practice\n"
            f"- When the user makes a mistake, always correct it: note the error, "
            f"explain why it is wrong, give the correct form, then continue naturally\n"
            f"- Tone: encouraging and patient; corrections are matter-of-fact, never condescending\n"
            f"- When you introduce a word likely to be new at {level}, append this marker:\n"
            f"  <!--WORD_SUGGESTION:{{\"word\": \"...\", \"reading\": \"...\"}}-->\n"
            f"{self._chinese_rule(native_lang)}"
        )

    def level_test_system_prompt(self, target_lang: str, n_questions: int = 8) -> str:
        return (
            f"You are administering a {self._lang_name(target_lang)} ({target_lang}) "
            f"proficiency test.\n\n"
            f"Generate exactly {n_questions} multiple choice questions covering vocabulary, "
            f"grammar, and reading comprehension.\n\n"
            f"Respond ONLY with a JSON array, no other text:\n"
            f"[\n"
            f"  {{\n"
            f"    \"question\": \"...\",\n"
            f"    \"options\": [\"A) ...\", \"B) ...\", \"C) ...\", \"D) ...\"],\n"
            f"    \"correct\": \"A\",\n"
            f"    \"explanation\": \"...\"\n"
            f"  }}\n"
            f"]\n"
        )

    def word_enrichment_prompt(self, target_lang: str, native_lang: str) -> str:
        return (
            f"You are a dictionary assistant for {self._lang_name(target_lang)}.\n\n"
            f"Given a word, return a JSON object with these exact fields:\n"
            f"{{\n"
            f"  \"definition\": \"string\",\n"
            f"  \"part_of_speech\": \"string\",\n"
            f"  \"formality\": \"casual|neutral|formal\",\n"
            f"  \"synonyms\": [\"string\"],\n"
            f"  \"antonyms\": [\"string\"],\n"
            f"  \"collocations\": [\"string\"],\n"
            f"  \"conjugations\": {{}} or null,\n"
            f"  \"tense_notes\": \"string\" or null,\n"
            f"  \"examples\": [\"string\"],\n"
            f"  \"grammar_notes\": \"string\",\n"
            f"  \"proficiency_level\": \"string\",\n"
            f"  \"language_specific\": {{}}\n"
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
        level: str,
        topic: str,
        phase: str,
        difficulty: str = "Normal",
    ) -> str:
        difficulty_note = DIFFICULTY_INSTRUCTIONS.get(difficulty, DIFFICULTY_INSTRUCTIONS["Normal"])

        if phase == "structured":
            phase_instructions = (
                f"You are guiding a structured lesson on \"{topic}\". Follow this sequence:\n"
                f"1. Introduce 5-8 key vocabulary items relevant to \"{topic}\"\n"
                f"2. Explain one relevant grammar point\n"
                f"3. Give the user 3 practice exercises (fill-in-the-blank or translation)\n"
                f"4. After the exercises, invite the user to move to free conversation\n"
                f"Pace yourself — one step at a time. Wait for the user's response before moving on.\n"
            )
        else:
            phase_instructions = (
                f"The structured lesson is complete. Now have a natural free conversation "
                f"on the topic \"{topic}\".\n"
                f"Encourage use of the vocabulary and grammar from the lesson.\n"
                f"Gently correct mistakes as they occur.\n"
            )

        return (
            f"You are teaching a {self._lang_name(target_lang)} lesson.\n\n"
            f"Topic: {topic}\n"
            f"User proficiency: {level}\n"
            f"Difficulty: {difficulty} — {difficulty_note}\n"
            f"Native language: {self._lang_name(native_lang)} ({native_lang})\n\n"
            f"{phase_instructions}\n"
            f"Always explain in {self._lang_name(native_lang)}. Practice in {self._lang_name(target_lang)}.\n"
            f"When you introduce a word likely to be new at {level}, append:\n"
            f"<!--WORD_SUGGESTION:{{\"word\": \"...\", \"reading\": \"...\"}}-->\n"
            f"{self._chinese_rule(native_lang)}"
        )
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_prompt_builder.py -v
```
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add services/prompt_builder.py tests/test_prompt_builder.py
git commit -m "feat: add PromptBuilder with all system prompt templates"
```

---

## Task 7: LanguageService

**Files:**
- Create: `services/language_service.py`
- Create: `tests/test_language_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_language_service.py
from datetime import date
from services.language_service import LanguageService, PROFICIENCY_FRAMEWORKS


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


def test_get_proficiency_framework_japanese(tmp_store):
    svc = LanguageService(tmp_store)
    framework = svc.get_proficiency_framework("ja")
    assert framework["name"] == "JLPT"
    assert "N5" in framework["levels"]


def test_get_proficiency_framework_chinese(tmp_store):
    svc = LanguageService(tmp_store)
    framework = svc.get_proficiency_framework("zh")
    assert framework["name"] == "HSK"


def test_get_proficiency_framework_fallback(tmp_store):
    svc = LanguageService(tmp_store)
    framework = svc.get_proficiency_framework("es")
    assert framework["name"] == "CEFR"


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
    assert stats["level"] == ""
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_language_service.py -v
```

- [ ] **Step 3: Write `services/language_service.py`**

```python
from datetime import date
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
        yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()
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
            ),
            "lessons_completed": len(lessons.get("completed", [])),
        }
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_language_service.py -v
```
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add services/language_service.py tests/test_language_service.py
git commit -m "feat: add LanguageService with proficiency frameworks and stats"
```

---

## Task 8: MemoryService

**Files:**
- Create: `services/memory_service.py`
- Create: `tests/test_memory_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_memory_service.py
from unittest.mock import MagicMock
from services.memory_service import MemoryService
from services.prompt_builder import PromptBuilder


def _make_messages(n: int) -> list[dict]:
    return [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
        for i in range(n)
    ]


def test_assemble_context_under_threshold(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    messages = _make_messages(10)
    tmp_store.save_chat_messages("ja", sid, messages)
    context = svc.assemble_context("ja", sid)
    assert len(context) == 10


def test_assemble_context_includes_summary(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    tmp_store.append_chat_summary("ja", sid, "Previous summary.")
    messages = _make_messages(5)
    tmp_store.save_chat_messages("ja", sid, messages)
    context = svc.assemble_context("ja", sid)
    assert context[0]["role"] == "system"
    assert "Previous summary." in context[0]["content"]


def test_maybe_summarize_no_trigger(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    messages = _make_messages(20)
    tmp_store.save_chat_messages("ja", sid, messages)
    svc.maybe_summarize("ja", sid, "zh-TW")
    mock_llm.generate.assert_not_called()


def test_maybe_summarize_triggers_at_35(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    mock_llm.generate.return_value = "Summary of conversation."
    svc = MemoryService(tmp_store, mm, pb)
    sid = tmp_store.create_chat_session("ja", "Test")
    messages = _make_messages(35)
    tmp_store.save_chat_messages("ja", sid, messages)
    svc.maybe_summarize("ja", sid, "zh-TW")
    mock_llm.generate.assert_called_once()
    remaining = tmp_store.load_chat_messages("ja", sid)
    assert len(remaining) == 15
    summary = tmp_store.load_chat_summary("ja", sid)
    assert "Summary of conversation." in summary
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_memory_service.py -v
```

- [ ] **Step 3: Write `services/memory_service.py`**

```python
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
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_memory_service.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add services/memory_service.py tests/test_memory_service.py
git commit -m "feat: add MemoryService with rolling window and summarization"
```

---

## Task 9: ChatService

**Files:**
- Create: `services/chat_service.py`
- Create: `tests/test_chat_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_chat_service.py
import re
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
    result = svc.send_message("ja", sid, "zh-TW", "N4", "Hello", image_path=None)
    assert result["response"] == "いいですね。"
    assert result["word_suggestions"] == []


def test_send_message_saves_messages(tmp_store, mock_llm):
    mock_llm.generate.return_value = "こんにちは。"
    svc, _ = _make_services(tmp_store, mock_llm)
    sid = tmp_store.create_chat_session("ja", "Test")
    svc.send_message("ja", sid, "zh-TW", "N4", "Hi", image_path=None)
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
    result = svc.send_message("ja", sid, "zh-TW", "N4", "What does eat mean?", image_path=None)
    assert len(result["word_suggestions"]) == 1
    assert "<!--" not in result["response"]
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_chat_service.py -v
```

- [ ] **Step 3: Write `services/chat_service.py`**

```python
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
            raw_response = vlm.generate(context, image_path=image_path, system_prompt=system_prompt)
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
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_chat_service.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add services/chat_service.py tests/test_chat_service.py
git commit -m "feat: add ChatService with word suggestion extraction"
```

---

## Task 10: LevelTestService

**Files:**
- Create: `services/level_test_service.py`
- Create: `tests/test_level_test_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_level_test_service.py
import json
from unittest.mock import MagicMock
from services.level_test_service import LevelTestService
from services.prompt_builder import PromptBuilder


def _make_svc(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return LevelTestService(tmp_store, mm, pb)


def _mock_questions():
    return json.dumps([
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
    ])


def test_generate_questions(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.generate_questions("ja")
    assert len(questions) == 2
    assert questions[0]["question"] == "What does 食べる mean?"


def test_evaluate_perfect_score(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.generate_questions("ja")
    answers = ["A", "C"]
    result = svc.evaluate(questions, answers, "ja")
    assert result["score"] == 100
    assert result["level"] in ("N5", "N4", "N3", "N2", "N1")


def test_evaluate_zero_score(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.generate_questions("ja")
    answers = ["B", "A"]
    result = svc.evaluate(questions, answers, "ja")
    assert result["score"] == 0
    assert result["level"] == "N5"


def test_evaluate_saves_result(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_questions()
    svc = _make_svc(tmp_store, mock_llm)
    questions = svc.generate_questions("ja")
    svc.evaluate(questions, ["A", "C"], "ja")
    saved = tmp_store.load_level("ja")
    assert saved["level"] is not None
    assert saved["score"] == 100
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_level_test_service.py -v
```

- [ ] **Step 3: Write `services/level_test_service.py`**

```python
import json
from datetime import datetime

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.language_service import PROFICIENCY_FRAMEWORKS, _CEFR
from services.prompt_builder import PromptBuilder


class LevelTestService:
    def __init__(self, store: DataStore, model_manager: ModelManager, prompt_builder: PromptBuilder):
        self._store = store
        self._mm = model_manager
        self._pb = prompt_builder

    def generate_questions(self, target_lang: str, n_questions: int = 8) -> list[dict]:
        system_prompt = self._pb.level_test_system_prompt(target_lang, n_questions)
        llm = self._mm.get_llm()
        raw = llm.generate(
            [{"role": "user", "content": "Generate the test questions now."}],
            system_prompt=system_prompt,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)

    def evaluate(self, questions: list[dict], answers: list[str], target_lang: str) -> dict:
        correct = sum(1 for q, a in zip(questions, answers) if q["correct"] == a)
        score = round(correct / len(questions) * 100) if questions else 0
        level = self._score_to_level(score, target_lang)
        result = {
            "level": level,
            "score": score,
            "correct": correct,
            "total": len(questions),
            "tested_at": datetime.now().isoformat(),
        }
        self._store.save_level(target_lang, result)
        return result

    def _score_to_level(self, score: int, target_lang: str) -> str:
        framework = PROFICIENCY_FRAMEWORKS.get(target_lang, _CEFR)
        levels = framework["levels"]
        idx = min(int(score / 100 * len(levels)), len(levels) - 1)
        return levels[idx]
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_level_test_service.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add services/level_test_service.py tests/test_level_test_service.py
git commit -m "feat: add LevelTestService with quiz generation and JLPT/HSK/CEFR mapping"
```

---

## Task 11: LessonService

**Files:**
- Create: `services/lesson_service.py`
- Create: `tests/test_lesson_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_lesson_service.py
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
    topics = svc.suggest_topics("ja", "N4")
    assert len(topics) == 5
    assert "Food" in topics


def test_start_lesson_creates_session(tmp_store, mock_llm):
    mock_llm.generate.return_value = "Let's start with vocabulary for food..."
    svc = _make_svc(tmp_store, mock_llm)
    result = svc.start_lesson("ja", "zh-TW", "N4", "Food", difficulty="Normal")
    assert "lesson_id" in result
    assert "session_id" in result
    assert "response" in result


def test_continue_lesson_structured(tmp_store, mock_llm):
    mock_llm.generate.return_value = "Good! Now let's do exercises."
    svc = _make_svc(tmp_store, mock_llm)
    lesson_id = "lesson-001"
    session_id = tmp_store.create_chat_session("ja", "Food Lesson", lesson_id=lesson_id)
    tmp_store.save_chat_messages("ja", session_id, [
        {"role": "assistant", "content": "Let's start."}
    ])
    result = svc.continue_lesson(
        "ja", session_id, lesson_id, "zh-TW", "N4", "Food",
        phase="structured", difficulty="Normal", user_text="I understand."
    )
    assert "response" in result
    assert "phase" in result


def test_finish_lesson_saves_progress(tmp_store, mock_llm):
    svc = _make_svc(tmp_store, mock_llm)
    svc.finish_lesson("ja", "Food")
    progress = tmp_store.load_lessons_progress("ja")
    assert "Food" in progress["completed"]
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_lesson_service.py -v
```

- [ ] **Step 3: Write `services/lesson_service.py`**

```python
import json
import uuid
from datetime import datetime

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
            )}]
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)

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
        raw_response = llm.generate(messages, system_prompt=system_prompt)
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
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_lesson_service.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add services/lesson_service.py tests/test_lesson_service.py
git commit -m "feat: add LessonService with structured and conversation phases"
```

---

## Task 12: WordListService

**Files:**
- Create: `services/word_list_service.py`
- Create: `tests/test_word_list_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_word_list_service.py
import json
from datetime import date, timedelta
from unittest.mock import MagicMock
from services.word_list_service import WordListService
from services.prompt_builder import PromptBuilder


def _make_svc(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return WordListService(tmp_store, mm, pb)


def _mock_enrichment():
    return json.dumps({
        "definition": "to eat",
        "part_of_speech": "動詞",
        "formality": "casual",
        "synonyms": ["食う"],
        "antonyms": [],
        "collocations": ["ご飯を食べる"],
        "conjugations": {"masu": "食べます", "te": "食べて"},
        "tense_notes": "Group 2 verb",
        "examples": ["毎日ご飯を食べる。"],
        "grammar_notes": "Ichidan verb",
        "proficiency_level": "N5",
        "language_specific": {"on_yomi": None, "kun_yomi": "た.べる", "pitch_accent": "LHL"},
    })


def test_add_word_enriches_and_saves(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    word = svc.add_word("ja", "zh-TW", "食べる", reading="たべる", source="chat")
    assert word["definition"] == "to eat"
    assert word["word"] == "食べる"
    assert "id" in word
    saved = tmp_store.load_wordlist("ja")
    assert len(saved) == 1


def test_add_word_no_duplicate(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    svc.add_word("ja", "zh-TW", "食べる", source="chat")
    svc.add_word("ja", "zh-TW", "食べる", source="manual")
    saved = tmp_store.load_wordlist("ja")
    assert len(saved) == 1


def test_search_by_word(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    svc.add_word("ja", "zh-TW", "食べる", source="chat")
    results = svc.search("ja", query="食べ")
    assert len(results) == 1


def test_filter_by_tag(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    w = svc.add_word("ja", "zh-TW", "食べる", source="chat", tags=["food"])
    results = svc.filter_by_tag("ja", "food")
    assert len(results) == 1


def test_has_stale_words_true(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    svc.add_word("ja", "zh-TW", "食べる", source="chat")
    assert svc.has_stale_words("ja") is True


def test_update_review_stats(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    word = svc.add_word("ja", "zh-TW", "食べる", source="chat")
    svc.update_review_stats("ja", word["id"], correct=True)
    updated = svc.get_word("ja", word["id"])
    assert updated["review_stats"]["correct"] == 1
    assert updated["review_stats"]["last_reviewed"] == date.today().isoformat()
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_word_list_service.py -v
```

- [ ] **Step 3: Write `services/word_list_service.py`**

```python
import json
import uuid
from datetime import date, timedelta

from data_store.data_store import DataStore
from model_manager import ModelManager
from services.prompt_builder import PromptBuilder

STALE_DAYS = 7


class WordListService:
    def __init__(self, store: DataStore, model_manager: ModelManager, prompt_builder: PromptBuilder):
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
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)

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
            w for w in words
            if (last := w.get("review_stats", {}).get("last_reviewed")) is None or last < cutoff
        ]

    def get_all_words(self, lang: str) -> list[dict]:
        return self._store.load_wordlist(lang)

    def update_review_stats(self, lang: str, word_id: str, correct: bool) -> None:
        words = self._store.load_wordlist(lang)
        for w in words:
            if w["id"] == word_id:
                stats = w.setdefault("review_stats", {"last_reviewed": None, "correct": 0, "incorrect": 0})
                stats["last_reviewed"] = date.today().isoformat()
                if correct:
                    stats["correct"] = stats.get("correct", 0) + 1
                else:
                    stats["incorrect"] = stats.get("incorrect", 0) + 1
                break
        self._store.save_wordlist(lang, words)
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_word_list_service.py -v
```
Expected: 6 passed

- [ ] **Step 5: Run all tests**

```bash
uv run pytest -v
```
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add services/word_list_service.py tests/test_word_list_service.py
git commit -m "feat: add WordListService with AI enrichment and review tracking"
```

---

## Task 13: Streamlit App Entry Point & State

**Files:**
- Create: `ui/state.py`
- Create: `ui/app.py`

- [ ] **Step 1: Write `ui/state.py`**

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
from services.level_test_service import LevelTestService


def init_services() -> None:
    if st.session_state.get("_initialized"):
        return

    store = DataStore()
    mm = ModelManager()
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
    st.session_state.level_test_svc = LevelTestService(store, mm, pb)
    st.session_state._initialized = True


def get(key: str):
    return st.session_state[key]
```

- [ ] **Step 2: Write `ui/app.py`**

```python
import streamlit as st
from ui.state import init_services, get
from ui.pages import home, chat, lesson, word_list, settings


def main() -> None:
    st.set_page_config(page_title="Language Tutor 🗣️", page_icon="🗣️", layout="wide")
    init_services()

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()

    with st.sidebar:
        st.title("🗣️ Language Tutor")
        st.caption(f"**{native_lang}** → **{target_lang}**")
        st.divider()

        mm = get("mm")
        if not mm.is_model_available("llm"):
            st.error("⚠️ LLM not downloaded")
            st.code(mm.get_download_command("llm"))
            st.stop()

        word_svc = get("word_svc")
        store = get("store")
        has_stale = word_svc.has_stale_words(target_lang)
        word_list_label = "📚 Word List 🔴" if has_stale else "📚 Word List"

        page = st.radio(
            "nav",
            ["🏠 Home", "📝 Lesson", "💬 Chat", word_list_label, "⚙️ Settings"],
            label_visibility="collapsed",
        )

    if page == "🏠 Home":
        home.render()
    elif page == "📝 Lesson":
        lesson.render()
    elif page == "💬 Chat":
        chat.render()
    elif word_list_label in page or page == "📚 Word List":
        word_list.render()
    elif page == "⚙️ Settings":
        settings.render()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify import structure**

```bash
uv run python -c "from ui.app import main; print('OK')"
```
Expected: OK (no import errors)

- [ ] **Step 4: Commit**

```bash
git add ui/state.py ui/app.py
git commit -m "feat: add Streamlit app entry point and session state init"
```

---

## Task 14: Home Page

**Files:**
- Create: `ui/pages/home.py`

- [ ] **Step 1: Write `ui/pages/home.py`**

```python
import streamlit as st
from ui.state import get


def render() -> None:
    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()

    st.title("🏠 Home")
    language_svc.update_streak(target_lang)
    stats = language_svc.get_stats(target_lang)

    st.subheader(f"Learning **{target_lang}** · {stats['level'] or 'Level not set'}")

    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    with col1:
        st.metric("🔥 Streak", f"{stats['streak']} days")
    with col2:
        st.metric("📚 Words Saved", stats["words_saved"])
    with col3:
        st.metric("📖 Lessons", stats["lessons_completed"])
    with col4:
        st.metric("✅ Reviewed This Week", stats["words_reviewed_this_week"])
    with col5:
        st.metric("📅 Last Active", stats["last_active"] or "Today")
    with col6:
        mm = get("mm")
        vlm_ok = "✅" if mm.is_model_available("vlm") else "⬇️"
        tts_ok = "✅" if mm.is_model_available("tts") else "⬇️"
        stt_ok = "✅" if mm.is_model_available("stt") else "⬇️"
        st.metric("Models", f"VLM {vlm_ok} TTS {tts_ok} STT {stt_ok}")

    st.divider()

    store = get("store")
    sessions = store.list_chat_sessions(target_lang)
    if sessions:
        st.subheader("💬 Recent Chats")
        for session in reversed(sessions[-3:]):
            st.write(f"• {session['name']} — {session['created_at'][:10]}")
```

- [ ] **Step 2: Commit**

```bash
git add ui/pages/home.py
git commit -m "feat: add Home page with stats dashboard"
```

---

## Task 15: Settings Page

**Files:**
- Create: `ui/pages/settings.py`

- [ ] **Step 1: Write `ui/pages/settings.py`**

```python
import json
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
    st.subheader("📊 Level Test")
    level_test_svc = get("level_test_svc")
    _, current_target = language_svc.get_language_pair()
    store = get("store")
    level_data = store.load_level(current_target)

    if level_data.get("level"):
        st.info(f"Current level: **{level_data['level']}** (score: {level_data.get('score', '?')}%)")

    if st.button("🎯 Take Level Test"):
        st.session_state._taking_test = True

    if st.session_state.get("_taking_test"):
        _run_level_test(level_test_svc, current_target, language_svc)


def _run_level_test(level_test_svc, target_lang: str, language_svc) -> None:
    if "test_questions" not in st.session_state:
        with st.spinner("Generating test questions..."):
            st.session_state.test_questions = level_test_svc.generate_questions(target_lang)
        st.session_state.test_answers = {}

    questions = st.session_state.test_questions
    st.subheader(f"Level Test ({len(questions)} questions)")

    for i, q in enumerate(questions):
        st.write(f"**Q{i+1}.** {q['question']}")
        answer = st.radio(
            f"q{i}", q["options"], key=f"test_q_{i}", label_visibility="collapsed"
        )
        st.session_state.test_answers[i] = answer[0]  # "A", "B", "C", or "D"

    if st.button("✅ Submit Test"):
        answers = [st.session_state.test_answers.get(i, "A") for i in range(len(questions))]
        result = level_test_svc.evaluate(questions, answers, target_lang)
        st.success(f"Level assessed: **{result['level']}** ({result['score']}%)")
        del st.session_state.test_questions
        del st.session_state.test_answers
        st.session_state._taking_test = False
        language_svc.update_streak(target_lang)
        st.rerun()
```

- [ ] **Step 2: Commit**

```bash
git add ui/pages/settings.py
git commit -m "feat: add Settings page with language pair, model status, and level test"
```

---

## Task 16: Chat Page & Word Chip Component

**Files:**
- Create: `ui/components/word_chip.py`
- Create: `ui/components/audio_controls.py`
- Create: `ui/pages/chat.py`

- [ ] **Step 1: Write `ui/components/word_chip.py`**

```python
import streamlit as st
from ui.state import get


def render_word_chip(suggestion: dict, lang: str, native_lang: str) -> None:
    word = suggestion.get("word", "")
    reading = suggestion.get("reading", "")
    label = f"💾 Save: {word}" + (f" ({reading})" if reading else "")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📌 New word suggestion: **{word}** {reading}")
    with col2:
        if st.button(label, key=f"save_word_{word}"):
            word_svc = get("word_svc")
            word_svc.add_word(lang, native_lang, word, reading=reading, source="chat")
            st.toast(f"✅ Saved: {word}")
```

- [ ] **Step 2: Write `ui/components/audio_controls.py`**

```python
import tempfile
import streamlit as st
from ui.state import get


def render_tts_button(text: str, lang: str, key: str) -> None:
    mm = get("mm")
    if not mm.is_model_available("tts"):
        return
    if st.button("🔊", key=f"tts_{key}", help="Play audio"):
        with st.spinner("Generating audio..."):
            tts = mm.get_tts()
            audio_bytes = tts.synthesize(text, lang=lang)
        st.audio(audio_bytes, format="audio/wav")


def render_stt_input(key: str) -> str | None:
    mm = get("mm")
    if not mm.is_model_available("stt"):
        return None
    audio = st.audio_input("🎤 Speak", key=f"stt_{key}")
    if audio:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio.getvalue())
            tmp_path = f.name
        with st.spinner("Transcribing..."):
            stt = mm.get_stt()
            return stt.transcribe(tmp_path)
    return None
```

- [ ] **Step 3: Write `ui/pages/chat.py`**

```python
import streamlit as st
from ui.state import get
from ui.components.word_chip import render_word_chip
from ui.components.audio_controls import render_tts_button, render_stt_input


def render() -> None:
    st.title("💬 Chat")

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    store = get("store")
    chat_svc = get("chat_svc")

    # Session management sidebar panel
    with st.sidebar:
        st.subheader("Sessions")
        sessions = store.list_chat_sessions(target_lang)

        if st.button("➕ New Chat"):
            name = f"Chat {len(sessions) + 1}"
            st.session_state.active_session = store.create_chat_session(target_lang, name)
            st.rerun()

        for s in reversed(sessions):
            cols = st.columns([4, 1])
            with cols[0]:
                if st.button(s["name"], key=f"sel_{s['id']}"):
                    st.session_state.active_session = s["id"]
                    st.rerun()
            with cols[1]:
                if st.button("🗑", key=f"del_{s['id']}"):
                    store.delete_chat_session(target_lang, s["id"])
                    if st.session_state.get("active_session") == s["id"]:
                        st.session_state.pop("active_session", None)
                    st.rerun()

    active_session = st.session_state.get("active_session")
    if not active_session:
        st.info("Select or create a chat session from the sidebar.")
        return

    session_info = next((s for s in sessions if s["id"] == active_session), None)
    if session_info:
        st.subheader(session_info["name"])

    # Level for system prompt
    level_data = store.load_level(target_lang)
    level = level_data.get("level", "N4")

    # Render message history
    messages = chat_svc.get_history(target_lang, active_session)
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                render_tts_button(msg["content"], lang=target_lang, key=msg["content"][:20])

    # Image upload
    uploaded_image = st.file_uploader(
        "📷 Attach image (optional)", type=["jpg", "jpeg", "png"],
        key=f"img_{active_session}", label_visibility="collapsed"
    )
    image_path = None
    if uploaded_image:
        import tempfile, os
        suffix = os.path.splitext(uploaded_image.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(uploaded_image.getvalue())
            image_path = f.name

    # STT input
    stt_text = render_stt_input(key=active_session)

    # Text input
    user_input = st.chat_input("Type a message...")
    final_input = stt_text or user_input

    if final_input:
        with st.chat_message("user"):
            st.write(final_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = chat_svc.send_message(
                    lang=target_lang,
                    session_id=active_session,
                    native_lang=native_lang,
                    level=level,
                    user_text=final_input,
                    image_path=image_path,
                )
            st.write(result["response"])
            render_tts_button(result["response"], lang=target_lang, key="latest")

        for suggestion in result.get("word_suggestions", []):
            render_word_chip(suggestion, lang=target_lang, native_lang=native_lang)

        language_svc.update_streak(target_lang)
        st.rerun()
```

- [ ] **Step 4: Commit**

```bash
git add ui/components/word_chip.py ui/components/audio_controls.py ui/pages/chat.py
git commit -m "feat: add Chat page with TTS, STT, image upload, and word save chips"
```

---

## Task 17: Lesson Page

**Files:**
- Create: `ui/pages/lesson.py`

- [ ] **Step 1: Write `ui/pages/lesson.py`**

```python
import streamlit as st
from ui.state import get
from ui.components.word_chip import render_word_chip
from ui.components.audio_controls import render_tts_button


def render() -> None:
    st.title("📝 Lesson")

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    lesson_svc = get("lesson_svc")
    store = get("store")
    level_data = store.load_level(target_lang)
    level = level_data.get("level", "N4")

    # Active lesson state
    if "active_lesson" not in st.session_state:
        _render_topic_picker(lesson_svc, target_lang, native_lang, level)
    else:
        _render_active_lesson(lesson_svc, language_svc, target_lang, native_lang, level)


def _render_topic_picker(lesson_svc, target_lang, native_lang, level) -> None:
    st.subheader("Choose a topic")

    difficulty = st.select_slider(
        "Difficulty", options=["Easy", "Normal", "Hard"], value="Normal"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        custom_topic = st.text_input("Or enter a custom topic:", placeholder="e.g. ordering coffee")
    with col2:
        if st.button("🎲 Suggest Topics"):
            with st.spinner("Getting suggestions..."):
                st.session_state.suggested_topics = lesson_svc.suggest_topics(target_lang, level)

    suggested = st.session_state.get("suggested_topics", [])
    if suggested:
        st.write("**Suggested topics:**")
        cols = st.columns(min(len(suggested), 5))
        for i, topic in enumerate(suggested):
            with cols[i % 5]:
                if st.button(topic, key=f"topic_{i}"):
                    _start_lesson(lesson_svc, target_lang, native_lang, level, topic, difficulty)

    if custom_topic and st.button("▶️ Start Lesson"):
        _start_lesson(lesson_svc, target_lang, native_lang, level, custom_topic, difficulty)


def _start_lesson(lesson_svc, target_lang, native_lang, level, topic, difficulty) -> None:
    with st.spinner(f"Preparing lesson on '{topic}'..."):
        result = lesson_svc.start_lesson(target_lang, native_lang, level, topic, difficulty=difficulty)
    st.session_state.active_lesson = {
        "lesson_id": result["lesson_id"],
        "session_id": result["session_id"],
        "topic": topic,
        "difficulty": difficulty,
        "phase": result["phase"],
        "messages": [{"role": "assistant", "content": result["response"]}],
        "word_suggestions": result.get("word_suggestions", []),
    }
    st.rerun()


def _render_active_lesson(lesson_svc, language_svc, target_lang, native_lang, level) -> None:
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

    # Render messages
    for msg in lesson["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                render_tts_button(msg["content"], lang=target_lang, key=msg["content"][:20])

    # Word suggestions
    for suggestion in lesson.get("word_suggestions", []):
        render_word_chip(suggestion, lang=target_lang, native_lang=native_lang)

    # Input
    user_input = st.chat_input("Your response...")
    if user_input:
        lesson["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("..."):
                result = lesson_svc.continue_lesson(
                    target_lang=target_lang,
                    session_id=lesson["session_id"],
                    lesson_id=lesson["lesson_id"],
                    native_lang=native_lang,
                    level=level,
                    topic=topic,
                    phase=lesson["phase"],
                    difficulty=lesson["difficulty"],
                    user_text=user_input,
                )
            st.write(result["response"])
            render_tts_button(result["response"], lang=target_lang, key="lesson_latest")

        lesson["messages"].append({"role": "assistant", "content": result["response"]})
        lesson["word_suggestions"] = result.get("word_suggestions", [])
        st.rerun()
```

- [ ] **Step 2: Commit**

```bash
git add ui/pages/lesson.py
git commit -m "feat: add Lesson page with structured and free conversation phases"
```

---

## Task 18: Word List Page

**Files:**
- Create: `ui/pages/word_list.py`

- [ ] **Step 1: Write `ui/pages/word_list.py`**

```python
import streamlit as st
from ui.state import get
from ui.components.audio_controls import render_tts_button


def render() -> None:
    st.title("📚 Word List")

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    word_svc = get("word_svc")
    store = get("store")

    tab_browse, tab_add, tab_review = st.tabs(["Browse", "Add Word", "Review"])

    with tab_browse:
        _render_browse(word_svc, target_lang, native_lang)

    with tab_add:
        _render_add(word_svc, target_lang, native_lang)

    with tab_review:
        _render_review(word_svc, target_lang, native_lang)


def _render_browse(word_svc, target_lang, native_lang) -> None:
    words = store_words(word_svc, target_lang)
    if not words:
        st.info("No words saved yet. Start chatting or take a lesson!")
        return

    col1, col2 = st.columns(2)
    with col1:
        query = st.text_input("🔍 Search", placeholder="Search words...")
    with col2:
        all_tags = sorted({tag for w in words for tag in w.get("tags", [])})
        tag_filter = st.selectbox("Filter by tag", ["All"] + all_tags)

    if query:
        words = word_svc.search(target_lang, query)
    if tag_filter != "All":
        words = [w for w in words if tag_filter in w.get("tags", [])]

    for word in words:
        with st.expander(f"**{word['word']}** {word.get('reading', '')} — {word.get('definition', '')}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Part of speech:** {word.get('part_of_speech', '-')}")
                st.write(f"**Formality:** {word.get('formality', '-')}")
                st.write(f"**Level:** {word.get('proficiency_level', '-')}")
                if word.get("synonyms"):
                    st.write(f"**Synonyms:** {', '.join(word['synonyms'])}")
                if word.get("collocations"):
                    st.write(f"**Collocations:** {', '.join(word['collocations'])}")
                if word.get("examples"):
                    st.write("**Examples:**")
                    for ex in word["examples"]:
                        st.write(f"  • {ex}")
                if word.get("related_words"):
                    st.write(f"**Related:** {', '.join(word['related_words'])}")
                conj = word.get("conjugations")
                if conj:
                    st.write("**Conjugations:** " + " · ".join(f"{k}: {v}" for k, v in conj.items()))
                ls = word.get("language_specific", {})
                if any(v for v in ls.values() if v):
                    extras = {k: v for k, v in ls.items() if v}
                    st.write("**Language info:** " + " · ".join(f"{k}: {v}" for k, v in extras.items()))
            with col2:
                render_tts_button(word["word"], lang=target_lang, key=word["id"])
                stats = word.get("review_stats", {})
                st.caption(
                    f"✅ {stats.get('correct', 0)} / ❌ {stats.get('incorrect', 0)}\n"
                    f"Last: {stats.get('last_reviewed') or 'never'}"
                )


def _render_add(word_svc, target_lang, native_lang) -> None:
    st.subheader("Add a word manually")
    word_input = st.text_input("Word")
    reading_input = st.text_input("Reading / pronunciation (optional)")
    tags_input = st.text_input("Tags (comma-separated, optional)")

    if st.button("➕ Add & Enrich") and word_input:
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        with st.spinner(f"Enriching '{word_input}'..."):
            entry = word_svc.add_word(
                target_lang, native_lang, word_input,
                reading=reading_input, source="manual", tags=tags
            )
        st.success(f"Added: **{entry['word']}** — {entry.get('definition', '')}")
        st.rerun()


def _render_review(word_svc, target_lang, native_lang) -> None:
    stale = word_svc.get_stale_words(target_lang)

    if not stale:
        st.success("✅ All words reviewed recently!")
        return

    st.info(f"**{len(stale)} words** due for review.")
    mode = st.radio("Review mode", ["Flashcard", "Fill-in-the-blank", "Sentence construction"])

    if "review_queue" not in st.session_state:
        st.session_state.review_queue = list(stale)
        st.session_state.review_idx = 0
        st.session_state.review_revealed = False

    queue = st.session_state.review_queue
    idx = st.session_state.review_idx

    if idx >= len(queue):
        st.success("🎉 Review session complete!")
        del st.session_state.review_queue
        del st.session_state.review_idx
        del st.session_state.review_revealed
        return

    word = queue[idx]
    st.progress((idx) / len(queue), text=f"{idx}/{len(queue)}")

    if mode == "Flashcard":
        st.markdown(f"## {word['word']} {word.get('reading', '')}")
        render_tts_button(word["word"], lang=target_lang, key=f"rev_{word['id']}")
        if st.session_state.review_revealed:
            st.write(f"**{word.get('definition', '')}**")
            st.write(word.get("grammar_notes", ""))
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Got it"):
                    word_svc.update_review_stats(target_lang, word["id"], correct=True)
                    _next_review()
            with col2:
                if st.button("❌ Missed"):
                    word_svc.update_review_stats(target_lang, word["id"], correct=False)
                    _next_review()
        else:
            if st.button("👁️ Reveal"):
                st.session_state.review_revealed = True
                st.rerun()

    elif mode == "Fill-in-the-blank":
        example = (word.get("examples") or [""])[0]
        blanked = example.replace(word["word"], "______") if word["word"] in example else f"______ ({word.get('reading', '')})"
        st.write(f"Fill in the blank: **{blanked}**")
        answer = st.text_input("Your answer:", key=f"fib_{word['id']}_{idx}")
        if st.button("Check"):
            if word["word"] in answer:
                st.success("✅ Correct!")
                word_svc.update_review_stats(target_lang, word["id"], correct=True)
            else:
                st.error(f"❌ Answer: **{word['word']}**")
                word_svc.update_review_stats(target_lang, word["id"], correct=False)
            _next_review()

    elif mode == "Sentence construction":
        st.write(f"Use **{word['word']}** ({word.get('definition', '')}) in a sentence:")
        user_sentence = st.text_area("Your sentence:", key=f"sc_{word['id']}_{idx}")
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
            st.write(result["response"])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Mark correct"):
                    word_svc.update_review_stats(target_lang, word["id"], correct=True)
                    _next_review()
            with col2:
                if st.button("❌ Mark missed"):
                    word_svc.update_review_stats(target_lang, word["id"], correct=False)
                    _next_review()


def _next_review() -> None:
    st.session_state.review_idx += 1
    st.session_state.review_revealed = False
    st.rerun()


def store_words(word_svc, target_lang) -> list[dict]:
    return word_svc.get_all_words(target_lang)
```

- [ ] **Step 2: Commit**

```bash
git add ui/pages/word_list.py
git commit -m "feat: add Word List page with browse, add, and review modes"
```

---

## Task 19: Wire Up & Final Smoke Test

**Files:**
- Modify: `ui/pages/__init__.py`

- [ ] **Step 1: Ensure `ui/pages/__init__.py` is empty**

```python
# intentionally empty
```

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest -v
```
Expected: all tests pass

- [ ] **Step 3: Verify app starts**

```bash
uv run streamlit run ui/app.py
```
Expected: Streamlit opens in browser showing Home page with sidebar navigation. If LLM not downloaded, setup screen shows with download command.

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete language tutor MVP"
```
