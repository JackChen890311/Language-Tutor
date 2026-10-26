# 2026-10-26 Language Tutor Plan

## Phase A — Whisper language handling (pre-existing WIP, committed first)

### Features Implemented

- [x] Pinned Whisper decoding to the requested target language instead of
      relying on auto-detect, which mislabels short Japanese clips as English
- [x] Added an optional native-language second pass that is kept only when it is
      clearly more confident than the target-language pass
- [x] Collapsed regional Chinese variants (`zh-TW`, `zh-HK`, `zh-CN`) to the
      bare `zh` code Whisper expects
- [x] Raised the default STT model to `mlx-community/whisper-large-v3-turbo`
- [x] Extended `BaseSTT.transcribe()` with `lang` and `fallback_lang`
- [x] Added unit coverage for pinning, mapping, fallback selection, the
      confidence margin and the same-language shortcut
- [x] Committed the already-complete working-tree changes first, so the composer
      refactor could rely on the extended `transcribe()` signature

### Changes Made

#### models/base.py

- `BaseSTT.transcribe(audio, lang=None, fallback_lang=None)` replaces the
  one-argument abstract signature.

#### models/mlx_stt.py

- `_LANG_MAP` maps `zh-TW` / `zh-HK` / `zh-CN` to `zh`.
- `_decode()` passes `task="transcribe"` and, when a language is supplied,
  `language=<mapped code>` to the underlying MLX Whisper call.
- `_confidence()` averages per-segment `avg_logprob`.
- `transcribe()` runs the target-language pass first, then an optional fallback
  pass. The fallback wins only if its confidence exceeds the primary pass by
  `_FALLBACK_MARGIN` (0.15). The second pass is skipped when no fallback is
  supplied or both languages collapse to the same Whisper code.
- The default model id is now `mlx-community/whisper-large-v3-turbo`.

#### config/models.json, README.md

- STT slot and documentation updated to `whisper-large-v3-turbo`.
- README explains target-language pinning and native-language fallback.

#### tests/test_mlx_stt.py

- Added six tests covering requested-language pinning, Chinese mapping,
  auto-detect when no language is given, fallback selection, the confidence
  margin and the same-language shortcut.

### Commit

- `fix: improve Whisper language handling for voice input` (`8418adf`)

## Phase B — Chat composer consolidation

### Features Implemented

- [x] Replaced the separate image uploader, full-width audio input, floating
      suggestion button and chat input with one consolidated composer
- [x] `st.chat_input(accept_file=True, accept_audio=...)` now provides attach,
      record, text and send in one widget
- [x] Moved the Suggestions toggle into `st.bottom`, right-aligned directly
      above the send button, with a live count in the label
- [x] Trimmed the button to `💡` / `💡 N` at the user's request; the
      "Suggestions" wording now lives only in the tooltip
- [x] Removed the fixed-position `chat_toggle` CSS, viewport-width maths and
      mobile media query
- [x] Replaced `render_stt_input()` with `transcribe_audio()`; the caller checks
      STT availability and the consumed-audio hash guard is no longer needed
- [x] Image uploads are copied to a temp file and deleted after the turn;
      image-only submissions use a `📷` placeholder
- [x] Refreshed the README Chat screenshot with demo data

### Changes Made

#### ui/pages/chat.py

- Removed the `st.file_uploader` block and the transcript-level `image_path`
  construction.
- Added `_save_uploaded_image()` and a `try/finally` that removes the temp file
  after streaming/committing.
- Reads `ChatInputValue` from the composer: `.text`, `.files[0]` and
  `getattr(submission, "audio", None)` (the audio attribute only exists when
  `accept_audio` is enabled).
- Transcribes audio through `transcribe_audio()` before sending.
- Renders the Suggestions toggle inside `with st.bottom:`; the button label is
  `💡` or `💡 N` (the tooltip still spells out show/hide), and the rail state
  still comes from `rail_is_open()` / `set_rail_open()`.
- `st.chat_input()` now enables a single image attachment plus optional audio at
  a 16 kHz sample rate.

#### ui/components/audio_controls.py

- `render_stt_input()` is gone. `transcribe_audio(audio, lang=None,
  fallback_lang=None)` accepts any file-like object with `getvalue()`, writes a
  temporary WAV, calls STT and always removes the temp file.
- Added an `AudioUpload` protocol to document the expected interface without
  importing Streamlit's internal `UploadedFile` type.
- Removed the SHA-256 consumed-audio guard: `st.chat_input` returns a recording
  only on the submission rerun, so it cannot loop.

#### ui/theme.py

- Removed the fixed-position `chat_toggle` rules and the `--lt-sidebar-w` /
  `--lt-chat-input-w` calculations.
- Added compact pill styling for `chat_toolbar`, including full-width element
  containers and right alignment via `.stButton`.

#### tests/test_stt_input.py

- Rewritten around `transcribe_audio()`: transcription, forwarded language hints
  and temp-file cleanup.

#### docs/screenshots/chat-dark.png

- Recaptured at 1440×900 in dark mode using a temporary demo data directory, so
  no real chat names are included.

### Testing Performed

- `make test`: **149 passed**
- `make lint`: clean
- Streamlit `AppTest` smoke run on the Chat page: one `st.chat_input`, the
  `toggle_suggestions` button present, no exceptions
- Headless Chrome at 1440×900 in dark mode: verified the composer order
  (`+` attach / mic / text / send) and the Suggestions pill aligned above send
- Confirmed the temp image file is removed and the demo data directory is
  outside the repository

### Commit

- `feat: consolidate chat composer controls` (`f3ad8ac`)
