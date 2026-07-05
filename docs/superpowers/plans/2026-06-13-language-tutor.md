# Language Tutor Implementation Plan — 2026-06-13 Update

> Extends `docs/superpowers/plans/2026-05-10-language-tutor.md` after Task 19 (MVP complete). See `docs/superpowers/specs/2026-06-13-language-tutor-design.md` for the design rationale behind these changes.

**Status:** All tasks below complete and merged to `main`.

---

## Task 20: Fix TTS playback (Kokoro pipeline break)

**Files:** `models/mlx_tts.py`

- [x] **Step 1:** Diagnose — `mlx_audio`'s `KokoroPipeline(model=True)` no longer eagerly loads the model in the installed `mlx_audio` version; calling the pipeline as before now raises `TypeError`
- [x] **Step 2:** Rewrite `MLXTTSModel._ensure_loaded` to use `mlx_audio.tts.utils.load(...)`, and `synthesize` to call `model.generate(text, voice=..., lang_code=...)`
- [x] **Step 3:** Add a per-language voice map so Japanese uses `jf_alpha` instead of the English `af_heart` voice (eliminates the "language mismatch" warning)
- [x] **Step 4:** Commit — `fix: rewrite TTS to use mlx_audio.tts.utils.load with Japanese voice` (`590d067`)

## Task 21: Align download CLI + model ids

**Files:** `README.md`, `config/models.json`, `model_manager.py`, `docs/superpowers/plans/2026-05-10-language-tutor.md`, `docs/superpowers/specs/2026-05-10-language-tutor-design.md`

- [x] **Step 1:** Replace `huggingface-cli`/`hfdownload` references with the `hf` CLI (`hf download <model>`)
- [x] **Step 2:** Update `config/models.json` model ids
- [x] **Step 3:** Commit — `fix: update download CLI to hf and align model IDs` (`5f2028e`)

## Task 22: Per-segment TTS with autoplay

**Files:** `services/prompt_builder.py`, `ui/components/audio_controls.py`, `ui/pages/chat.py`, `tests/test_speak_extraction.py`

- [x] **Step 1:** Prompt: instruct the LLM to wrap target-language sentences in `<speak>…</speak>` tags; native-language explanations must not be tagged
- [x] **Step 2:** `audio_controls`: add `parse_message_segments`, `autoplay_audio_html`, `render_message_with_tts`; replace `st.components.v1.html` with `st.html`
- [x] **Step 3:** `chat` page: render assistant messages via `render_message_with_tts` so each tagged segment gets its own 🔊 button that autoplays without a secondary player widget
- [x] **Step 4:** Commit — `feat: per-segment TTS with <speak> tags and autoplay` (`39a23a2`)

## Task 23: Native language translation field in word list

**Files:** `services/prompt_builder.py`, `ui/pages/word_list.py`

- [x] **Step 1:** Add a `translation` field (concise 1–5 word native-language translation) as the first field in the word enrichment schema, separate from the full `definition`
- [x] **Step 2:** Word List Browse tab: show translation in the expander header and as a bold heading inside; dedicated 🔊 autoplay button next to the word heading
- [x] **Step 3:** Word List Review tab (flashcard mode): 🔊 button inline with the word; show translation prominently on reveal, before the full definition
- [x] **Step 4:** Commit — `feat: native language translation field and audio button in word list` (`de46aac`)
