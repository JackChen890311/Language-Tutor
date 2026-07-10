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
