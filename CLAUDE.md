# CLAUDE.md

Project-specific instructions for Claude Code. See `README.md` for user-facing setup/architecture docs.

## Where the docs live

`docs/superpowers/plans/` and `docs/superpowers/specs/` hold dated pairs of documents, one pair per day of shipped work, in commit-date order:

- `2026-05-10-language-tutor*.md` — original MVP build (19 tasks, ~46 commits). Historical record — **do not edit these**, even to fix inaccuracies. If something in them is wrong, correct it in a later dated doc instead.
- `2026-06-13-language-tutor*.md` — TTS engine rewrite, per-segment `<speak>`-tag TTS with autoplay, word list `translation` field, `hf` CLI migration.
- `2026-07-05-language-tutor*.md` — Makefile, TTS/STT model-id bug fix, this doc reorganization.

Each dated `plans/` file is a checklist of what was done that day (checkboxes already checked — these are retrospective records, not to-do lists to re-run). Each dated `specs/` file documents only the *deltas* from the previous date's spec — read the whole chain in date order to understand current behavior, since later docs assume earlier ones as context and don't repeat unchanged sections.

**Before starting new feature work**, read the most recent dated plan+spec pair to know current state — don't assume the 2026-05-10 docs describe what's actually running today.

## Workflow for new feature work

When the user asks for a new feature or nontrivial fix:

1. Implement it (follow the user's usual process — brainstorm/plan/TDD skills as normal).
2. Add a **new dated plan+spec pair** for today's date (`docs/superpowers/plans/YYYY-MM-DD-language-tutor.md` and the matching `specs/` file), following the format of the existing dated docs: the plan is a checked-off task list with commit hashes, the spec documents only what changed/why relative to the previous dated spec.
3. Run the full test suite (`make test`) before committing.
4. Commit the code and the new docs. Don't leave feature work uncommitted across sessions unless the user says otherwise.

Do not retroactively edit an already-committed dated doc for a past date — if you find something wrong in it, note the correction in the next new dated doc instead (see how the 2026-07-05 docs handle the 2026-06-13 model-id bug for the pattern).

## Commands

```bash
make run    # uv run streamlit run main.py
make test   # uv run pytest
make lint   # uv run ruff check . && uv run ruff format --check .
```

## Architecture

Four layers, no layer imports from the layer above it: `ui/` (Streamlit, zero business logic) → `services/` (business logic, no Streamlit imports) → `models/` (LLM/VLM/TTS/STT abstractions, lazy-loaded) → `data_store/` (sole filesystem I/O class). All model slots are swappable via `config/models.json` — the `model` field for every slot must be the exact HF repo id, passed straight through to the loader with no hidden prefixing (see the 2026-07-05 spec for why this matters — it was broken once).
