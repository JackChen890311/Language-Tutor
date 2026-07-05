# Language Tutor — Design Update, 2026-07-05

_Supplements `docs/superpowers/specs/2026-06-13-language-tutor-design.md`._

---

## Makefile

Added thin `make run` / `make test` / `make lint` targets wrapping the `uv run` commands already documented in the README's Development section. No behavior change.

## Fix: TTS/STT model id wiring (resolves bug introduced 2026-06-13)

Three places have to agree on a model id, and after `5f2028e` they didn't:

1. `config/models.json` — meant to be the source of truth, per the original design's Section 6 principle: "Swappable by design — changing any model requires editing one line in `config/models.json`"
2. `models/mlx_tts.py` / `models/mlx_stt.py` — the actual load path
3. `README.md` — the download command shown to the user

After `5f2028e`, (1) said `hexgrad/Kokoro-82M` / `openai/whisper-large-v3` (the original, non-MLX-converted upstream repos), but (2) ignored that value entirely for TTS (hardcoded `prince-canuma/Kokoro-82M`) and mangled it for STT (prepended `mlx-community/`, producing the invalid id `mlx-community/openai/whisper-large-v3`).

**Fix:** `config/models.json` now holds the exact, full repo id that gets passed straight through to `mlx_audio` / `mlx_whisper` with no hidden prefixing or hardcoding — restoring the "one line in config" swap guarantee from the original design.

Final values:

```json
{
  "tts": { "provider": "mlx-audio", "model": "prince-canuma/Kokoro-82M" },
  "stt": { "provider": "mlx-audio", "model": "mlx-community/whisper-large-v3" }
}
```

## Documentation reorganization

Dated docs now mirror the actual commit history: 2026-05-10 (MVP build, 46 commits), 2026-06-13 (TTS fix + per-segment TTS + translation field + CLI migration, 4 commits), 2026-07-05 (Makefile + this bugfix + this reorg). The 2026-05-10 plan/spec are left untouched as a historical record of the original MVP scope; each later date gets its own plan+spec pair documenting only that day's deltas against the previous one. `CLAUDE.md` at the repo root tells future sessions where to look and requires a new dated plan+spec pair — plus a commit — for any new feature work.

## Remove the level/proficiency concept; add a standalone "Test" section

Previously, a Level Test lived inside Settings: it graded an 8-question quiz against JLPT/HSK/TOPIK/CEFR tables (`PROFICIENCY_FRAMEWORKS` in `services/language_service.py`), stored the resulting level in `data/<lang>/progress/level.json`, and that stored level fed proficiency-based personalization into Chat, Lesson (topic suggestions + system prompt), and Word List's sentence-construction review. Home displayed the level in its subheader (`"Learning **Japanese** · N4"`).

This removes the level concept end-to-end rather than just relocating the quiz UI, because leaving Chat/Lesson/Word List reading a level that can never be set again would silently freeze their personalization at a hardcoded default forever.

**Storage:** `level.json` mixed two unrelated things — test results (`level`, `score`, `correct`, `total`, `tested_at`) and daily streak tracking (`streak`, `last_active`). Since only the streak fields survive, `DataStore.load_level`/`save_level` are renamed `load_streak`/`save_streak`, and the file is renamed `streak.json`, holding only `{streak, last_active}`. Existing `data/<lang>/progress/level.json` files are hand-migrated to `streak.json` with the level/score/tested_at fields dropped.

**Language service:** `PROFICIENCY_FRAMEWORKS`, `_CEFR`, and `get_proficiency_framework` are deleted entirely — nothing computes a level anymore, so nothing needs a JLPT/HSK/TOPIK/CEFR table. `get_stats()` no longer returns a `"level"` key.

**Prompts & services:** `level` is dropped as a parameter from `PromptBuilder.chat_system_prompt`, `PromptBuilder.lesson_system_prompt`, `ChatService.send_message`/`stream_message`, and `LessonService.suggest_topics`/`start_lesson`/`continue_lesson`/`stream_start_lesson`/`stream_continue_lesson`. The "User proficiency: {level}" line is removed from both system prompts; the word-introduction clause changes from "likely to be new at {level}" to "likely to be new to a learner". `DIFFICULTY_INSTRUCTIONS["Normal"]` no longer says "Match the user's assessed proficiency level naturally" (there's no assessment anymore) — it now reads "Use natural, moderately-paced language and everyday vocabulary." Lesson's manual Easy/Normal/Hard difficulty picker is untouched; it was never level-derived.

Left alone: each saved vocabulary word still carries its own `proficiency_level` tag (e.g. "N5") from `word_enrichment_prompt` in Word List — that's the LLM's difficulty rating of *that word*, independent of the (now-removed) user-level concept.

**Test feature:** `services/level_test_service.py` is renamed `services/quiz_service.py`, `LevelTestService` → `QuizService` (named `Quiz`, not `Test`, so pytest doesn't try to collect it as a test class once it's imported into a test file — the UI nav label and page title stay "Test"). `generate_questions` is unchanged in behavior (it already only asked for generic vocabulary/grammar/reading-comprehension MCQs with no level input) but its system prompt (`PromptBuilder.level_test_system_prompt` → `test_system_prompt`) is reworded from "administering a proficiency test" to "creating a practice quiz". `evaluate()` drops the level computation (`_score_to_level`) and no longer calls `save_streak`/persists anything — it returns `{score, correct, total, tested_at}` and the quiz is fully ephemeral: each attempt is graded once and shown, nothing is saved, taking it again starts fresh.

**UI:** A new sidebar entry `("🧪", "Test")` is added to `ui/app.py`'s `_NAV`, positioned after "Word List" and before "Settings". A new `ui/pages/test.py` hosts the quiz flow moved out of `settings.py::_run_level_test`: generate → answer → submit → a score only (e.g. "7/8 correct — 88%") with per-question explanations for missed answers, no level label. `settings.py` loses its "📊 Level Test" section entirely (its Danger Zone clear-history key list is updated to match the session-state keys now owned by `test.py`). `home.py`'s subheader drops the level suffix, becoming `"Learning **{target_name}**"` with no `· N4` / `· Level not set`.

## Stream test generation, bilingual explanations, persisted test history

Three follow-on changes to the Test feature added in the previous section, none of which reintroduce any level concept.

**Streaming generation:** `QuizService.generate_questions` (one blocking `llm.generate()` call) is replaced by two methods: `stream_questions(native_lang, target_lang, n_questions=8) -> StreamCollector` — using `llm.stream()`, reusing the same `StreamCollector` class from `services/chat_service.py` that Chat and Lesson already stream through — and `parse_questions(raw_text) -> list[dict]`, which is the old JSON-parsing logic pulled out so it can run once the stream finishes. `ui/pages/test.py` calls `stream_with_thinking(collector)` (the existing thinking-dots-then-live-tokens widget from `ui/components/stream_display.py`, already used by Lesson) while the quiz JSON streams in, then parses `collector.full_text` and reveals the quiz. What's visible while streaming is the raw JSON text, not rendered question cards — accepted trade-off for reusing the existing single-call generation and existing streaming widget as-is, rather than issuing one LLM call per question.

**Bilingual explanations:** each question's JSON schema changes from a single `explanation` field to two: `explanation_target` (why the answer is correct, written in the target language) and `explanation_native` (the same explanation, written in the native language). `PromptBuilder.test_system_prompt` gains a `native_lang` parameter (signature becomes `test_system_prompt(native_lang, target_lang, n_questions=8)`) and instructs the model to produce both fields per question. The question text and the four answer options remain target-language-only — only the post-grading explanation is bilingual, per explicit scope decision. `ui/pages/test.py`'s review view shows both explanation lines per question, each labeled by language.

**Persisted history:** `DataStore` gains `load_quiz_history(lang) -> list[dict]` and `append_quiz_result(lang, result) -> None`, backed by a new `data/<lang>/progress/quiz_history.json` file — already covered by the existing "Clear All History" danger-zone wipe (`clear_language_history` deletes the whole `data/<lang>` tree), so no change needed there. `QuizService` regains a `store` dependency (constructor becomes `QuizService(store, model_manager, prompt_builder)`, matching `WordListService`/`LessonService`'s constructor shape — it had been dropped when nothing used it) and `evaluate(questions, answers, target_lang)` now builds a full per-question breakdown (`{question, options, correct, given, is_correct, explanation_target, explanation_native}` per question) wrapped in `{id, tested_at, score, correct, total, questions: [...]}`, appends it via `append_quiz_result`, and returns it — so grading a quiz is no longer purely ephemeral. `ui/pages/test.py` adds a "📜 Past Attempts" section below the quiz flow (hidden while a quiz is in progress, shown otherwise): each past attempt renders as a collapsed `st.expander` labeled by date and score, expanding to the same per-question review view used for a just-completed quiz — a shared `_render_review(questions)` helper avoids duplicating that rendering logic.

## Fix: streaming quiz generation leaked answers and broke rendering

The previous section's accepted trade-off ("what's visible while streaming is the raw JSON text") turned out to be a real bug, not just a cosmetic quirk: `ui/pages/test.py` called `stream_with_thinking(collector)`, which renders every accumulated chunk to the page via `st.markdown(buf + "▌")`. The quiz JSON contains `"correct"` and both `explanation_target`/`explanation_native` for every question, so streaming it live rendered the full answer key onto the screen before the quiz form even existed — and raw JSON (unbalanced quotes/braces, underscores in field names) pushed through Markdown mid-stream renders garbled.

`stream_with_thinking` is correct for Chat/Lesson, where the streamed text is safe-to-display prose. Quiz generation is the only stream in this codebase whose raw content is a spoiler, so it needed a different helper, not a fix to `stream_with_thinking` itself.

**Fix:** added `stream_silently(collector)` to `ui/components/stream_display.py` — shows the same thinking-dots animation, drains the stream chunk by chunk to fill `collector.full_text`, but never calls `st.markdown` on any of its content, then clears the placeholder. `ui/pages/test.py` now calls `stream_silently` instead of `stream_with_thinking` for quiz generation. `stream_with_thinking` itself is unchanged and still used by Lesson.

## Fix: Lesson topic picker skipped confirmation; `<speak>` tags leaked as raw text

Two independent UI-only bugs in `ui/pages/lesson.py`, found by inspection while working on the Lesson page.

**Suggested-topic buttons skipped confirmation:** clicking a suggested topic in `_render_topic_picker` called `_start_lesson` immediately — there was no way to review or edit the topic before committing to it, unlike the custom-topic text box which required an explicit "▶️ Start Lesson" click. Clicking a suggestion now populates the "Or enter a custom topic" text box instead (via an `on_click` callback keyed to `lesson_topic_input`), and the lesson starts only on an explicit confirmation: pressing Enter in the text box (`on_change` callback) or clicking "▶️ Start Lesson". Both paths set a `pending_topic` session-state flag that's checked once at the end of `_render_topic_picker`, giving `_start_lesson` a single call site.

**`<speak>` tags leaked as raw text in Lesson:** `chat_system_prompt` and `lesson_system_prompt` both instruct the model to wrap spoken phrases in `<speak>…</speak>` tags (Section "Chat" of the original design). `ui/pages/chat.py` has always rendered assistant messages through `render_message_with_tts`, which splits a message on those tags into text/speak segments and renders each spoken segment as bold text next to its own 🔊 button — the tags themselves are never shown. `ui/pages/lesson.py`, however, rendered assistant messages with plain `st.write(msg["content"])` plus a separate whole-message `render_tts_button`, so the literal `<speak>` / `</speak>` tags showed up in the lesson transcript. Lesson's two assistant-message render sites (the message-history loop, and the just-streamed response after `stream_with_thinking`) now call `render_message_with_tts`, matching Chat exactly. `render_tts_button` is no longer imported in `lesson.py`.

Verified with Streamlit's `AppTest` harness (no browser available in this environment) driving the real `ui/pages/lesson.py` against faked services: confirmed a suggested-topic click only populates the text box, both Enter and the Start Lesson button correctly start the lesson, and a message containing `<speak>こんにちは</speak>` renders as three clean segments with no raw tag visible — matching Chat's rendering.

## Fine-grained difficulty: per-language proficiency frameworks for Lesson and Test

The Easy/Normal/Hard difficulty picker (Lesson only) is replaced by a language-appropriate proficiency scale, and the same picker is added to the Test page (which previously had no difficulty concept at all). This is **not** a reintroduction of the level/proficiency concept removed earlier in this file: that removal deleted a *stored, assessed* user proficiency that silently fed every feature forever once it could no longer be updated. This is a manual, ephemeral, per-lesson/per-test selection — the same role Easy/Normal/Hard already played, just with finer, language-native granularity. Nothing is persisted across sessions.

**Framework table:** `services/prompt_builder.py` gains a module-level `DIFFICULTY_FRAMEWORKS` dict (`ja` → JLPT N5–N1, `zh-TW`/`zh` → HSK1–6, `ko` → TOPIK1–6) plus a `_CEFR_FRAMEWORK` fallback (A1–C2) for every other target language, and `get_difficulty_levels(target_lang) -> {"name": str, "levels": [str]}` to look it up. This mirrors the shape of the now-deleted `PROFICIENCY_FRAMEWORKS`/`_CEFR`/`get_proficiency_framework` from `language_service.py`, but lives in `prompt_builder.py` (a plain lookup function, not a service method) since it's purely UI/prompt-facing data with no storage behind it.

**Prompt instructions:** rather than hand-writing pedagogical descriptions for every level of every framework, both `lesson_system_prompt` and `test_system_prompt` now emit a single line — `"Target proficiency: {framework} {level} — calibrate {vocabulary/question difficulty} ... to match this level on the {framework} scale."` — and trust the model's own training-data knowledge of what JLPT N3, HSK4, TOPIK2, or CEFR B1 actually mean. This avoids a combinatorial table of framework×level descriptions and keeps the calibration current with whatever the model actually knows about each standard. `DIFFICULTY_INSTRUCTIONS` (the old Easy/Normal/Hard text) is deleted.

**Signature changes:** `lesson_system_prompt`'s `difficulty` parameter loses its `"Normal"` default (now a required level string like `"N3"`); `LessonService.start_lesson`/`stream_start_lesson` follow suit (their sibling `continue_lesson`/`stream_continue_lesson` already required `difficulty`, unchanged). `test_system_prompt` gains a required `difficulty` parameter, inserted before the existing `n_questions=8`: `test_system_prompt(native_lang, target_lang, difficulty, n_questions=8)`. `QuizService.stream_questions` gains the matching required `difficulty` parameter in the same position.

**UI:** `ui/pages/lesson.py`'s difficulty `select_slider` now reads `get_difficulty_levels(target_lang)` and shows `f"Difficulty ({framework['name']})"` with that framework's levels as options, defaulting to the middle level. `ui/pages/test.py` gains the identical slider above the "🎲 Generate Test" button, and its selected value is threaded into `quiz_svc.stream_questions(...)`. Test's caption changes from "no proficiency level involved" (no longer accurate) to "Practice with a random quiz at your chosen difficulty." The chosen difficulty is not persisted to quiz history — it only shapes generation for that one attempt, matching the ephemeral-selection scope described above.

Verified with Streamlit's `AppTest` harness: the Lesson slider shows `Difficulty (JLPT)` with `[N5, N4, N3, N2, N1]` for a Japanese target and falls back to `Difficulty (CEFR)` with `[A1..C2]` for an unmapped target (Spanish); the Test page shows `Difficulty (TOPIK)` for a Korean target; and selecting a level (e.g. N1) on the Test page and clicking Generate Test calls `stream_questions` with that exact level.
