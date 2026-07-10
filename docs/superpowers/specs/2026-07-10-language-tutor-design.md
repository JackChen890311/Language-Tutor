# Language Tutor — Design Update, 2026-07-10

_Supplements `docs/superpowers/specs/2026-07-09-language-tutor-design.md`._

---

## Fix: `ValueError: Failed to load image from <bos><|turn>user...` on any Chat message with an attached image

**Bug found:** `mlx-vlm` is pinned loosely as `mlx-vlm>=0.1.9` (`pyproject.toml`); the version actually resolved and installed is 0.5.0. Between whatever version `models/mlx_vlm.py` was originally written against and 0.5.0, the top-level `mlx_vlm.generate()` function's signature changed so that `prompt` is now the third positional parameter and `image` the fourth: `generate(model, processor, prompt, image=None, audio=None, video=None, verbose=False, **kwargs)`. `MLXVLMModel.generate` (`models/mlx_vlm.py`) called it as `generate(self._model, self._processor, image_path, prompt, max_tokens=1024, verbose=False)` — purely positionally, and in the old order. That put `image_path` into the `prompt` slot and the full formatted prompt string (system prompt + chat template + user text) into the `image` slot. Deep inside `mlx_vlm.utils.prepare_inputs` → `process_image` → `load_image`, the library tried to open that prompt string as an image file path, which is why the `ValueError`'s "file name" in the traceback is visibly the entire prompt text, truncated by `OSError: [Errno 63] File name too long`.

This is the same class of bug the "all model slots are swappable... exact HF repo id, passed straight through with no hidden prefixing" note in `CLAUDE.md`'s Architecture section warns about generally: a thin wrapper's contract with its underlying library silently drifting after a dependency upgrade, since nothing pins the exact `mlx-vlm` version and nothing in this codebase's test suite exercises the real library call.

**Second bug caught in the same investigation:** `mlx_vlm.generate()` in 0.5.0 returns a `GenerationResult` dataclass (fields: `text`, `token`, `logprobs`, `prompt_tokens`, `generation_tokens`, `total_tokens`, `prompt_tps`, `generation_tps`, `peak_memory`), not a plain string. `MLXVLMModel.generate` (type-annotated to return `str`) returned that object directly. This is latent — it never got a chance to surface because the code raised on the image-loading bug first — but would have broken `ChatService.stream_message`/`send_message` immediately afterward, since `extract_word_suggestions(raw_response)` (`services/chat_service.py`) calls regex methods on `raw_response` expecting a `str`.

**Fix:** `models/mlx_vlm.py`'s `generate` method now calls the library with explicit keyword arguments (`prompt=prompt, image=image_path`) instead of relying on positional order, and unwraps the result via `.text` before returning:

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

Keyword arguments were chosen over just fixing the positional order so that a future `mlx-vlm` upgrade that reorders parameters again raises a clear `TypeError` (unexpected/missing keyword) instead of silently swapping values a second time.

**Verification:** No test in `tests/` calls into the real `mlx_vlm` library — `MLXVLMModel` is a thin adapter over a heavyweight local-inference library (loads a multi-GB model file), and a mocked unit test would not have caught this exact failure mode (a real signature/return-type mismatch in the dependency). Verified by direct exercise instead: generated a solid-red 64×64 JPEG, called `MLXVLMModel("mlx-community/gemma-4-26b-a4b-it-4bit").generate(...)` against it directly (bypassing Streamlit), and confirmed the call both loads the actual image (rather than the error path) and returns a plain `str` — the model correctly answered that the image is red.

**Scope note:** `config/models.json` had an uncommitted, pre-existing change (switching both `llm` and `vtm` model slots to `mlx-community/gemma-4-26b-a4b-it-4bit`) already present in the working tree before this investigation started. That change is the user's own in-progress experiment, unrelated to this bug (the argument-order bug applies to whichever model is configured in the `vlm` slot, since it's in the shared `mlx_vlm.generate()` call path), and was left untouched.

## Fix: benign `UserWarning: At least one mel filter has all zero values` on every VLM load

**Warning found:** every call to `MLXVLMModel._ensure_loaded` (i.e. every VLM load) printed a `transformers` `UserWarning` about an all-zero mel filter. This comes from `transformers.audio_utils.mel_filter_bank`, invoked eagerly inside `Gemma4AudioFeatureExtractor.__init__` when `mlx_vlm.load(...)` constructs the `Gemma4Processor` for `mlx-community/gemma-4-26b-a4b-it-4bit`. The processor's `processor_config.json` (published on the model's HF repo, cached locally after `mlx_vlm.load`) bundles an audio feature extractor with `num_mel_filters: 128` and `fft_length: 512` (→ `num_frequency_bins = 512 // 2 + 1 = 257`); with those specific dimensions, `mel_filter_bank`'s slaney-normalized triangular filterbank legitimately produces at least one all-zero-valued filter row, which the library warns about.

This is inherent to the model repo's own bundled audio-extractor config — not a value this codebase sets, computes, or should edit (editing the cached `processor_config.json` directly would violate the same "pass the HF repo id straight through, no hidden overrides" principle noted in `CLAUDE.md`'s Architecture section, and would be silently reverted by a fresh `mlx_vlm.load()`/re-download anyway). It is also functionally irrelevant here: nothing in this codebase ever sends audio through the VLM (confirmed via `grep -rn "audio" models/mlx_vlm.py services/chat_service.py` — no hits); the audio feature extractor is unused dead weight bundled inside the multimodal processor, and its filterbank is built once at construction regardless of whether audio ever flows through it.

**Fix:** narrowly suppressed the specific warning around the `load()` call site in `models/mlx_vlm.py`'s `_ensure_loaded`:

```python
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="At least one mel filter has all zero values")
    self._model, self._processor = load(self._model_path)
```

Scoped via `catch_warnings()` (restored after the `with` block) and matched by message text, so no other warning category — from this call or elsewhere — is silenced.

**Verification:** loaded the model under `warnings.catch_warnings(record=True)` with `simplefilter("always")` and asserted zero mel-filter warnings were recorded (previously always exactly one per load); re-ran the same direct `generate()` check against a solid-red test image used in the prior fix to confirm model loading and image understanding still work correctly.
