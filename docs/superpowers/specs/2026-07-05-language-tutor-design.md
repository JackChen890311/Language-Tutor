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
