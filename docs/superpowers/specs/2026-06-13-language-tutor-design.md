# Language Tutor — Design Update, 2026-06-13

_Supplements `docs/superpowers/specs/2026-05-10-language-tutor-design.md`. Read that first — this document only records deltas from it._

---

## Why

Post-MVP usage surfaced a TTS breakage caused by an upstream `mlx_audio` API change, and revealed two UX gaps: users wanted a fast, at-a-glance native-language gloss distinct from the fuller AI-generated definition, and playing an entire chat message as audio — including the native-language explanation text — was noisy. Only the target-language practice sentences should be spoken.

---

## Changes

### TTS engine (supersedes Section 2.1 implementation detail)

`mlx_audio`'s `KokoroPipeline(model=True)` stopped eagerly loading weights in the version installed; calling it as a pipeline directly raised `TypeError`. `MLXTTSModel` (`models/mlx_tts.py`) was rewritten to use `mlx_audio.tts.utils.load(...)` to obtain a model object, then call `model.generate(text, voice=..., lang_code=...)`. A per-language voice map was added, since Kokoro's default voice is English:

| lang | lang_code | voice |
|---|---|---|
| ja | j | jf_alpha |
| en | a | af_heart |
| zh | z | zf_xiaobei |

### Per-segment TTS (supersedes Section 4.7)

Original design: one 🔊 button per whole AI message. New design: the LLM wraps target-language sentences in `<speak>…</speak>` tags (native-language explanation text is left untagged, per the system prompt rules in `PromptBuilder`). `ui/components/audio_controls.py` parses these tagged segments and renders one autoplaying 🔊 button per segment via `st.html`, replacing `st.components.v1.html` and the old single-player-widget approach. This keeps native-language explanations silent and only speaks practice sentences.

### Word entry: `translation` field (supersedes Section 3.2)

Added a `translation` field to the word enrichment JSON schema — a concise 1–5 word native-language gloss, generated alongside (but distinct from) the fuller `definition`. Rationale: `definition` is often a full explanatory sentence; a user scanning the word list or flipping a flashcard wants a one-glance gloss first. Shown as:
- the primary heading in the Word List → Browse expander, with its own 🔊 button
- the first thing revealed on flashcard flip in Word List → Review

### Download CLI / model id alignment

`huggingface-cli` was replaced by the `hf` CLI across the README and `model_manager.get_download_command`. `config/models.json`'s `tts`/`stt` model ids were updated to match the new CLI's expected id format at the same time.
