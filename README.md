# Language Tutor 🗣️

A local-first AI language tutor that runs entirely on Apple Silicon. No cloud, no subscriptions — all models run on-device via [MLX](https://github.com/ml-explore/mlx).

![Python](https://img.shields.io/badge/python-3.11+-blue) ![Streamlit](https://img.shields.io/badge/streamlit-1.35+-red) ![Platform](https://img.shields.io/badge/platform-Apple%20Silicon-black)

---

## Features

- **Structured lessons** — vocabulary introduction, grammar explanation, and exercises, followed by free conversation
- **AI chat** — real-time streaming conversation with word suggestions and correction
- **Level test** — auto-generated multiple-choice quiz that maps your score to JLPT / HSK / TOPIK / CEFR
- **Word list** — one-click save of suggested words with full AI enrichment (definitions, examples, conjugations, pitch accent, etc.)
- **Rolling memory** — conversations summarize automatically as they grow, keeping context within token limits
- **TTS playback** — hear any response or word pronounced (optional)
- **Voice input** — speak instead of type with Whisper STT (optional)
- **Image chat** — attach a photo and ask questions about it via a vision-language model (optional)
- **Progress tracking** — daily streak, weekly review count, proficiency level history

---

## Supported Languages

| Learning | Native |
|---|---|
| 🇯🇵 Japanese | 🇹🇼 Traditional Chinese |
| 🇨🇳 Chinese (Simplified) | 🇺🇸 English |
| 🇰🇷 Korean | 🇪🇸 Spanish |
| 🇪🇸 Spanish | 🇫🇷 French |
| 🇫🇷 French | 🇩🇪 German |
| 🇩🇪 German | |

Any combination of the above as native ↔ target pair is supported.

---

## Requirements

- Apple Silicon Mac (M1 or later) with macOS 14+
- 32 GB unified memory recommended (48 GB for the default LLM)
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

---

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Download the LLM (required)

```bash
hfdownload mlx-community/Qwen3.6-35B-A3B-4bit
```

The LLM is the only required model. The others (VLM, TTS, STT) are optional and can be downloaded later from the Settings page.

### 3. Run

```bash
uv run streamlit run main.py
```

Open http://localhost:8501 in your browser.

---

## Optional Models

Download any of these from **Settings → Model Status** to unlock additional features.

| Feature | Model | Command |
|---|---|---|
| Image chat (VLM) | `mlx-community/Qwen3-VL-8B-Instruct` | `hfdownload mlx-community/Qwen3-VL-8B-Instruct` |
| TTS playback | `kokoro` | `hfdownload prince-canuma/Kokoro-82M` |
| Voice input (STT) | `whisper-large-v3` | `hfdownload mlx-community/whisper-large-v3` |

---

## Changing Models

Edit `config/models.json` to swap any model slot:

```json
{
  "llm": { "provider": "mlx", "model": "mlx-community/Qwen3.6-35B-A3B-4bit" },
  "vlm": { "provider": "mlx", "model": "mlx-community/Qwen3-VL-8B-Instruct" },
  "tts": { "provider": "mlx-audio", "model": "kokoro" },
  "stt": { "provider": "mlx-audio", "model": "whisper-large-v3" }
}
```

Any `mlx-community` LLM model can be dropped in as a replacement.

---

## Architecture

```
UI (Streamlit)
    │
    ▼
Services (business logic, no UI imports)
    ├── ChatService        — conversation, streaming, word extraction
    ├── LessonService      — topic suggestion, structured + free lessons
    ├── LevelTestService   — quiz generation, score → proficiency mapping
    ├── WordListService    — word storage, AI enrichment, review tracking
    ├── MemoryService      — rolling window summarization
    ├── LanguageService    — language pair, streak, stats
    └── PromptBuilder      — system prompt assembly
    │
    ▼
Models (MLX inference, lazy-loaded)
    ├── MLXLLMModel        — Qwen3 LLM (thinking-mode aware)
    ├── MLXVLMModel        — Qwen3-VL vision model
    ├── MLXTTSModel        — Kokoro TTS
    └── WhisperModel       — Whisper STT
    │
    ▼
DataStore (local JSON + Markdown files)
    └── data/
        ├── settings.json
        └── {lang}/
            ├── chats/         — session index + message history + summaries
            ├── words/         — enriched word list
            ├── lessons/       — lesson notes (Markdown)
            └── progress/      — level assessment + completed topics
```

**Design principles:**
- Services have no Streamlit imports — they could back a CLI or Telegram bot
- Models are lazy-loaded and can be unloaded individually to reclaim RAM
- All data is plain JSON/Markdown — human-readable and easy to back up

---

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

---

## Data & Privacy

All data stays on your machine:
- Conversation history: `data/{lang}/chats/`
- Word list: `data/{lang}/words/wordlist.json`
- Progress: `data/{lang}/progress/`

To delete everything for a language, go to **Settings → Danger Zone → Clear All History**.
