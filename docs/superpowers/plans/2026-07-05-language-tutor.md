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
