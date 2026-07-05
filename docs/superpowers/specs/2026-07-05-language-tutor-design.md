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
