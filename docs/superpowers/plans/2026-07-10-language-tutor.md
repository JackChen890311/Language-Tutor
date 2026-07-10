# Language Tutor Implementation Plan — 2026-07-10 Update

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Status:** All tasks below complete.
>
> Extends `docs/superpowers/plans/2026-07-09-language-tutor.md`. See `docs/superpowers/specs/2026-07-10-language-tutor-design.md` for the design rationale behind this change.

**Goal:** Fix a `ValueError: Failed to load image from <bos><|turn>user...` crash on any Chat message that attaches an image, caused by an `mlx-vlm` library upgrade silently changing `generate()`'s positional argument order.

## Task 41: Fix `mlx_vlm.generate()` argument order and return type in `MLXVLMModel.generate`

**Files:**
- Modify: `models/mlx_vlm.py`

**Bug:** `mlx-vlm` is pinned loosely (`mlx-vlm>=0.1.9` in `pyproject.toml`); the installed version resolved to 0.5.0. In that version, the top-level `mlx_vlm.generate()` function's signature is `generate(model, processor, prompt, image=None, ...)` — `prompt` is the third positional parameter and `image` the fourth. `models/mlx_vlm.py`'s `MLXVLMModel.generate` called `generate(self._model, self._processor, image_path, prompt, ...)` positionally, so `image_path` landed in the `prompt` slot and the actual (huge, formatted) prompt string landed in the `image` slot. `mlx_vlm.utils.load_image` then tried to open that prompt string as a file path and raised `ValueError: Failed to load image from <bos><|turn>user...: [Errno 63] File name too long`.

A second latent bug in the same version: `generate()` returns a `GenerationResult` dataclass (with a `.text` field), not a plain string. `MLXVLMModel.generate` returned that object directly, which would have broken `ChatService`'s `extract_word_suggestions(raw_response)` (expects `str`) immediately after the first bug was fixed.

- [x] **Step 1: Root-cause investigation**

Read the installed `mlx_vlm.generate.generate()` source (`.venv/lib/python3.11/site-packages/mlx_vlm/generate.py`) to confirm the current signature and return type, rather than guessing from the error message alone. Confirmed via `superpowers:systematic-debugging`: the error's "file name" is exactly the prompt text our code built, proving the two arguments were swapped — not a corrupt image, encoding issue, or file-system problem.

- [x] **Step 2: Fix the call site**

In `models/mlx_vlm.py`, changed:

```python
return generate(
    self._model, self._processor, image_path, prompt, max_tokens=1024, verbose=False
)
```

to:

```python
result = generate(
    self._model,
    self._processor,
    prompt=prompt,
    image=image_path,
    max_tokens=1024,
    verbose=False,
)
return result.text
```

Using keyword arguments for `prompt`/`image` (rather than just swapping positional order) so a future signature reorder fails loudly instead of silently swapping again.

- [x] **Step 3: Verify against the real model**

No existing test coverage calls the real `mlx_vlm` library (`grep -rn "mlx_vlm" tests/` returns nothing — `MLXVLMModel` is a thin wrapper around a heavyweight local-inference library, not something to unit-test with a mock that would hide exactly this kind of signature drift). Verified manually instead: generated a solid-red 64×64 test JPEG, called `MLXVLMModel("mlx-community/gemma-4-26b-a4b-it-4bit").generate(...)` directly against it, and confirmed the call returns a plain `str` (not a `GenerationResult`) and correctly identifies the image's color — proving both the argument swap and the return-type fix.

- [x] **Step 4: Run the full test suite**

Run: `make test`
Result: PASS, all 99 tests green (no existing test exercised this code path, so none were expected to change).

- [x] **Step 5: Commit and push**

```bash
git add models/mlx_vlm.py docs/superpowers/plans/2026-07-10-language-tutor.md docs/superpowers/specs/2026-07-10-language-tutor-design.md
git commit -m "fix: correct mlx_vlm.generate() argument order and unwrap GenerationResult.text"
git push origin main
```

## Task 42: Suppress benign mel-filter warning on VLM load

**Files:**
- Modify: `models/mlx_vlm.py`

**Warning:** Loading the VLM (`mlx_vlm.load(...)` inside `MLXVLMModel._ensure_loaded`) printed `UserWarning: At least one mel filter has all zero values. The value for num_mel_filters (128) may be set too high. Or, the value for num_frequency_bins (257) may be set too low.` on every load.

- [x] **Step 1: Root-cause investigation**

Traced the warning to `transformers.audio_utils.mel_filter_bank` (`.venv/.../transformers/audio_utils.py:549`), called from `Gemma4AudioFeatureExtractor.__init__` (`.venv/.../transformers/models/gemma4/feature_extraction_gemma4.py:149`), which builds its mel filterbank eagerly at construction time. `mlx-community/gemma-4-26b-a4b-it-4bit`'s `processor_config.json` bundles this audio feature extractor (`num_mel_filters: 128`, `fft_length: 512` → `num_frequency_bins = fft_length // 2 + 1 = 257`) as part of its `Gemma4Processor`, even though nothing in this codebase ever sends audio to the VLM (`grep -rn "audio" models/mlx_vlm.py services/chat_service.py` — no hits). Those specific filter dimensions are the model repo's own published config, not a value this codebase sets or should edit. So the warning fires purely from loading the processor, is unrelated to our code path, and is otherwise-harmless noise.

- [x] **Step 2: Suppress narrowly at the load call**

In `models/mlx_vlm.py`'s `_ensure_loaded`, wrapped the `load(self._model_path)` call in `warnings.catch_warnings()` with `warnings.filterwarnings("ignore", message="At least one mel filter has all zero values")` — scoped to just that call and matched by message text, so no other warning category is silenced.

- [x] **Step 3: Verify**

Ran `MLXVLMModel.load()` under `warnings.catch_warnings(record=True)` with `simplefilter("always")`: zero mel-filter warnings recorded (previously always fired once per load). Re-ran the same red-test-image `generate()` check as Task 41 to confirm the model still loads and produces a correct answer.

- [x] **Step 4: Run tests and lint, commit**

Run: `make test` (99 passed), `make lint` (no new errors on `models/mlx_vlm.py`; pre-existing out-of-scope `ui/pages/word_list.py` F401 unchanged).

```bash
git add models/mlx_vlm.py docs/superpowers/plans/2026-07-10-language-tutor.md docs/superpowers/specs/2026-07-10-language-tutor-design.md
git commit -m "fix: suppress benign mel-filter-all-zero warning on VLM load"
git push origin main
```
