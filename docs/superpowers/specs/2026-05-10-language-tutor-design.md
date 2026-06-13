# Language Tutor — Design Spec
_Date: 2026-05-10_

---

## 1. Goal

A local-first AI language tutor that runs entirely on a MacBook M4 Pro. The user can select any native language and any target learning language, study through structured lessons and free conversation, build a rich personal vocabulary, and review progress — all with data stored locally and models running on-device.

---

## 2. Architecture

Four layers. No layer may import from a layer above it.

```
ui/          ← Streamlit pages (Telegram / CLI ready later)
services/    ← Business logic, UI-agnostic
models/      ← LLM / VLM / TTS / STT abstract interfaces
data/        ← JSON (structured) + Markdown (narrative)
```

### 2.1 Model Layer

Each model type has an abstract base class. Concrete implementations inherit from it. Swapping models means changing one value in `config/models.json`.

| Slot | Abstract Class | Default Implementation |
|------|---------------|----------------------|
| LLM | `BaseLLM` | `MLXLLMModel` — Qwen3.6-35B-A3B (MoE, 4-bit) |
| VLM | `BaseVLM` | `MLXVLMModel` — Qwen3-VL-8B-Instruct |
| TTS | `BaseTTS` | `MLXTTSModel` — Kokoro (via mlx-audio) |
| STT | `BaseSTT` | `WhisperModel` — whisper-large-v3 (via mlx-audio) |

**Loading policy:** Models are lazy-loaded on first use. Only the LLM stays resident. VLM, TTS, and STT load on demand and may be unloaded when not in use to free memory.

### 2.2 Service Layer

One service class per feature domain. No UI framework imports.

- `LanguageService` — language pair management, progress tracking
- `LevelTestService` — quiz generation and evaluation
- `LessonService` — lesson planning, structured exercises, session flow
- `ChatService` — conversation management, rolling window memory, word suggestions
- `WordListService` — word storage, AI enrichment, review exercises
- `MemoryService` — summarization, context assembly

### 2.3 Data Layer

A single `DataStore` class handles all filesystem reads and writes. No other class accesses files directly.

- **JSON** for structured data: settings, word lists, progress, quiz results, lesson records
- **Markdown** for narrative content: chat summaries, lesson notes, memory context

### 2.4 UI Layer

Thin Streamlit pages. Zero business logic. Each page calls services and renders results. The service layer has no knowledge of Streamlit — a future Telegram bot or CLI adapter calls the same services unchanged.

---

## 3. Data Storage Structure

```
config/
  models.json                    # model provider and model IDs per slot

data/
  settings.json                  # language pair, UI preferences
  {lang}/                        # one folder per target language (e.g. "ja", "es")
    progress/
      level.json                 # CEFR level, quiz history
      lessons.json               # completed lessons, topics covered
    chats/
      {session_id}/
        messages.json            # last 15 messages (full fidelity)
        summary.md               # rolling summary of older messages
    words/
      wordlist.json              # all saved words with AI enrichment
    lessons/
      {lesson_id}.md             # structured lesson notes
```

### 3.1 Model Configuration

```json
{
  "llm": { "provider": "mlx", "model": "mlx-community/Qwen3.6-35B-A3B-4bit" },
  "vlm": { "provider": "mlx", "model": "mlx-community/Qwen3-VL-8B-Instruct" },
  "tts": { "provider": "mlx-audio", "model": "kokoro" },
  "stt": { "provider": "mlx-audio", "model": "whisper-large-v3" }
}
```

### 3.2 Word Entry Structure

```json
{
  "id": "uuid",
  "word": "食べる",
  "reading": "たべる",
  "definition": "to eat",
  "part_of_speech": "動詞",
  "formality": "casual",
  "synonyms": ["食う"],
  "antonyms": [],
  "collocations": ["ご飯を食べる", "薬を食べる"],
  "conjugations": {
    "dictionary": "食べる",
    "masu": "食べます",
    "te": "食べて",
    "ta": "食べた",
    "nai": "食べない",
    "potential": "食べられる"
  },
  "tense_notes": "Group 2 verb (一段動詞)",
  "examples": ["毎日ご飯を食べる。"],
  "grammar_notes": "...",
  "proficiency_level": "N5",
  "related_words": ["飲む", "料理する"],
  "review_stats": {
    "last_reviewed": null,
    "correct": 0,
    "incorrect": 0
  },
  "tags": ["food", "lesson-3"],
  "source": "chat",
  "added_date": "2026-05-10",
  "language_specific": {
    "on_yomi": "ショク",
    "kun_yomi": "た.べる",
    "pitch_accent": "LHL",
    "counter": null
  }
}
```

**Notes:**
- `conjugations`, `tense_notes`, and `language_specific` are nullable — the AI fills only what is relevant for the word type and language
- `language_specific` is a free-form dict: Japanese gets pitch accent and readings; Spanish gets verb class; Mandarin gets tone and stroke count
- `proficiency_level` is language-agnostic: N1–N5 for Japanese, HSK 1–6 for Chinese, A1–C2 for European languages
- `related_words` stores word strings; the UI renders them as clickable chips that navigate to that word's detail view
- `review_stats` is kept separate from linguistic data; used for spaced repetition later

---

## 4. Features

### 4.1 Language Selection & Progress

On first launch, user selects a **native language** and a **target learning language**. Both can be changed at any time from Settings. Each target language gets a fully isolated `data/{lang}/` folder — progress, chats, and word lists never mix across languages.

All AI output (explanations, feedback, lesson content, word definitions) is in both target language and the user's native language. When native language is set to Chinese, the system always uses Traditional Chinese (繁體中文) with 台灣用語 and Taiwanese terminology throughout, with no exceptions.

### 4.2 Level Test

The LLM generates 5–10 multiple choice questions covering vocabulary, grammar, and reading comprehension, calibrated to the target language. Results map to the standard proficiency framework for that language — JLPT (N5–N1) for Japanese, HSK (1–6) for Chinese, TOPIK (1–6) for Korean, CEFR (A1–C2) for European languages and all others as a fallback. The assessed level is saved to `progress/level.json` and used to calibrate lesson difficulty, chat complexity, and word list filtering. The user can re-test at any time from Settings.

### 4.3 Lesson System

User picks a topic from an AI-suggested list or enters a custom topic. A lesson has two phases:

1. **Structured phase** — vocabulary introduction → grammar point → exercises (fill-in-the-blank, translation, short answers). The AI guides the user step by step.
2. **Free conversation phase** — flows naturally after the exercises complete, within the same Lesson page. The user can stay on the lesson topic or explore freely. This conversation is powered by `ChatService` and saved as a named chat session linked to the lesson, so it persists and appears in the Chat page history too.

Lesson notes are saved to `lessons/{lesson_id}.md`. Completed topics are logged in `progress/lessons.json` for tracking and future lesson suggestions.

### 4.4 Chat System

Multiple named sessions per language. Sessions are listed and can be created, renamed, or deleted. Each session maintains its own rolling window memory (see Section 4.6).

Mid-chat features:
- AI can suggest words to save — appears as a dismissible chip, user confirms with one click
- Optional image upload triggers the VLM automatically
- Optional STT mic input (toggleable per session)
- Optional TTS read-aloud per message

### 4.5 Word List & Review

Words are saved with the full enriched entry (Section 3.2). The AI populates all fields automatically on save; the user can edit any field.

**Sources:** AI-suggested during chat (user confirms) or manually added at any time.

**Review modes:**
- Flashcard — show word, reveal definition and notes
- Fill-in-the-blank — AI generates a sentence with the word missing
- Sentence construction — user constructs a sentence using the word; AI evaluates

**Filtering:** by tag, topic, proficiency level, formality, source, or date added.

**Navigation:** clicking a related word in any word detail view navigates directly to that word's entry.

### 4.6 Memory & Summarization

Rolling window per chat session, tuned for local model context limits:

- **Full fidelity:** last 15 messages stored in `messages.json`
- **Trigger:** when session hits 35 messages, summarize the oldest 20
- **Summary target:** ≤300 words, covering key topics, vocabulary introduced, grammar points, and notable mistakes
- **Storage:** summary appended to `summary.md` (summaries are additive, not replaced)
- **Context fed to LLM:** `summary.md` + last 15 messages — total well under 4k tokens

Summarization uses the LLM itself and only triggers occasionally, not on every turn.

### 4.7 TTS & STT

**TTS (supplemental):**
- Play pronunciation button next to every saved word
- Play button next to any AI message in chat
- Uses `BaseTTS` — swappable via config

**STT (optional input):**
- Mic button in chat input, toggleable
- Transcription fed into chat as text
- Uses `BaseSTT` — swappable via config

Both are disabled by default and enabled per-session. Neither is required for any core feature.

### 4.8 AI Persona & Prompt Strategy

A `PromptBuilder` class assembles the LLM system prompt from modular components. No service constructs raw prompt strings directly — all prompt logic lives in `PromptBuilder`.

**System prompt components (assembled per context):**
- User's native language and target language
- Current proficiency level (e.g., JLPT N4)
- Active context: lesson topic, chat session name, or review mode
- Behaviour rules (see below)

**Behaviour rules baked into every prompt:**
- Always explain in the user's native language; practice in the target language
- Never skip a mistake silently — note the error, explain why it's wrong, give the correct form, then continue naturally
- Tone: encouraging and patient; corrections are matter-of-fact, never condescending
- When native language is Chinese, always use Traditional Chinese (繁體中文) with 台灣用語

**Word suggestion rule (chat context only):**
When the AI introduces a word likely to be new for the user's level, it appends a structured suggestion block that the UI parses to render the one-click save chip.

### 4.9 Lesson Difficulty Calibration

The user's proficiency level is always injected into the lesson system prompt automatically. The user can also set a manual difficulty override per lesson:

| Setting | Behaviour |
|---------|-----------|
| **Easy** | Simpler vocabulary, shorter sentences, more hints and encouragement |
| **Normal** (default) | Matches assessed proficiency level |
| **Hard** | Less guidance, complex grammar, native-speed examples, minimal hand-holding |

Default is Normal. The override is per-lesson, not a global setting.

### 4.10 Word Review Triggering

No full spaced repetition in v1. A simple 7-day nudge:

- A **"Review Due" badge** appears on the Word List nav item when any word has `review_stats.last_reviewed` older than 7 days (or null)
- A **"Start Review" button** on the Word List page filters to stale words and launches a review session
- After each review session, `review_stats.last_reviewed` and correct/incorrect counts are updated
- Spaced repetition (using review_stats data) is a natural future upgrade with no schema changes needed

### 4.11 First-Run & Model Setup

A `ModelManager` class runs on every app startup and checks whether each configured model is available locally (by verifying the expected mlx-community cache path).

**Startup flow:**
1. Check LLM — if missing, block app launch and show setup screen with the exact download command (e.g., `hfdownload mlx-community/Qwen3.6-35B-A3B-4bit`)
2. Check VLM, TTS, STT — if missing, mark as unavailable but do not block launch; features that depend on them show a "Model not downloaded" prompt with the download command when triggered
3. Once LLM is confirmed present, load `settings.json` (create with defaults if first run) and proceed to main UI

This means the app is usable immediately after downloading only the LLM; voice and image features can be set up later.

---

## 5. UI Flow & Navigation

Streamlit multi-page app with sidebar navigation:

```
🏠 Home       ← language selector, proficiency level, stats dashboard
📝 Lesson     ← topic picker, difficulty override, structured lesson, free conversation
💬 Chat       ← named sessions list, open / create sessions
📚 Word List  ← browse, search, filter, review modes, Review Due badge
⚙️ Settings   ← language pair, model config, re-take level test
```

**Home page stats:**
- Current proficiency level (e.g., JLPT N4)
- Total words saved
- Words reviewed this week
- Lessons completed
- Study streak (consecutive days active)
- Last session date

**UX rules:**
- Language switcher always visible in sidebar
- Word save is a single click from chat
- TTS play button next to every word and AI message
- STT mic button in chat input (optional, toggleable)
- Image upload in chat triggers VLM automatically
- "Review Due" badge on Word List nav item when stale words exist
- Emoji used throughout to make the UI approachable

---

## 6. Design Principles

- **OOP throughout** — every model slot, service, and data type is a class with a clear interface
- **Swappable by design** — changing any model requires editing one line in `config/models.json`
- **UI-agnostic services** — the service layer has no Streamlit imports; a Telegram bot adapter is a future drop-in
- **Local-first** — all data and models run on-device; no external API calls required
- **Memory-conscious** — lazy model loading, rolling window context, summarization tuned for local hardware
- **Language-agnostic** — all features work for any language pair; CJK, RTL, and Latin scripts handled uniformly

---

## 7. Tech Stack

| Concern | Choice |
|---------|--------|
| Frontend | Streamlit |
| Language | Python 3 |
| Package manager | uv |
| Formatter | ruff |
| Model runtime | mlx-community |
| Version control | git |
| Structured storage | JSON |
| Narrative storage | Markdown |
