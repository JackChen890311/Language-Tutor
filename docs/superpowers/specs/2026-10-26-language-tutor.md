# 2026-10-26 Language Tutor Spec

## Summary

Two deltas vs the 2026-10-20 spec. Voice input now pins Whisper to the target
language and only switches to the native language when that pass is clearly more
confident. Chat's four input controls — image attach, record, word suggestions
and send — are consolidated into one composer, with the suggestion toggle pinned
just above it.

Phase A was already complete in the working tree when Phase B began; it was
committed first so the composer refactor could pass `lang` / `fallback_lang`
through the existing STT interface.

---

## Phase A — Whisper language handling

### Problem

Whisper's auto-detect is unreliable on short clips. In practice a short Japanese
recording was labelled English and transcribed as English text, which then went
to the chat model as the user's message. The reverse case mattered too: a learner
asking a question in their native language (for example Chinese while studying
Japanese) should not be forced into the target language.

### Design

- `BaseSTT.transcribe(audio, lang=None, fallback_lang=None)` replaces the
  one-argument signature. Existing callers remain valid.
- `WhisperModel._LANG_MAP` collapses `zh-TW`, `zh-HK` and `zh-CN` to `zh`, the
  bare ISO-639-1 code Whisper expects.
- The primary decode is pinned to the target language via `language=<code>` and
  `task="transcribe"`.
- When a distinct `fallback_lang` is supplied, a second decode runs in that
  language. Its text replaces the primary text only when its mean per-segment
  `avg_logprob` exceeds the primary mean by `_FALLBACK_MARGIN` (0.15). The margin
  keeps plausible target-language clips from being replaced by a marginally more
  confident native-language decode.
- The second pass is skipped when there is no fallback, or when both languages
  collapse to the same Whisper code.
- The default STT model is now `mlx-community/whisper-large-v3-turbo`.

### Behaviour

- Japanese study clips are decoded as Japanese even when they are short.
- Chinese questions can win the fallback pass when their confidence is clearly
  higher.
- A confidence tie or a small native-language lead keeps the target language.
- Requests without a language keep the old auto-detect behaviour.
- `config/models.json`, the README model table and the README architecture tree
  all point at `whisper-large-v3-turbo`.

### Testing

- `tests/test_mlx_stt.py` covers requested-language pinning, regional Chinese
  mapping, auto-detect when no language is supplied, fallback selection, the
  confidence margin and the same-language shortcut.

---

## Phase B — Chat composer consolidation

### Problem

The four chat input actions lived in three different layers:

1. The image uploader sat at the end of the scrolling transcript, so it drifted
   away as the conversation grew.
2. `st.audio_input` occupied a full-width row above the composer and sent the
   transcript as soon as recording stopped, with no review step.
3. The Suggestions toggle was a fixed-position floating button whose position
   was calculated from viewport width and sidebar state, with a separate mobile
   media query.
4. `st.chat_input` owned the text field and send button by itself.

### Design

#### One composer

`st.chat_input()` now enables:

- `accept_file=True` with `file_type=["jpg", "jpeg", "png"]`;
- `accept_audio=stt_available` at `audio_sample_rate=16000`.

Streamlit renders attach (`+`), record (mic), the text field and send (`↑`) as
one widget. Their internal order is Streamlit-owned: attach on the left, mic
beside it, text in the middle, send on the right. This is the conventional
"tools left, primary action right" layout.

The return value is a `ChatInputValue`:

- `.text` — typed text;
- `.files` — zero or one image;
- `.audio` — present only when `accept_audio` is enabled, hence
  `getattr(submission, "audio", None)`.

#### Suggestions toggle

The toggle moves into `with st.bottom:`, the container Streamlit pins directly
above the chat input. It renders as a compact right-aligned pill containing the
lightbulb icon and, when there are suggestions, the count (`💡` / `💡 N`). The
pill sits above the send button, so the whole bottom area — toggle, composer —
is one visual block and stays put while the transcript scrolls.

The word "Suggestions" was removed from the visible label at the user's request;
the tooltip still reads "Show/Hide word suggestions (N)" so the icon remains
self-explanatory on hover.

The rail itself is unchanged: the button still flips the shared
`show_word_suggestions` preference and the right-hand rail still closes from its
own ✕ button.

#### Audio

`render_stt_input()` is replaced by `transcribe_audio(audio, lang=None,
fallback_lang=None)`. The new helper accepts any file-like object with
`getvalue()`, writes a temporary WAV, calls STT and removes the file in a
`finally` block.

The caller checks `is_model_available("stt")` once and decides whether to show
the mic. The old SHA-256 consumed-audio guard is removed: `st.chat_input` returns
a recording only on the submission rerun, unlike `st.audio_input` which kept
returning the last recording on every rerun.

Recording now follows a review-then-send flow: record, press send, then the
transcript is produced and used for the turn.

#### Images

`_save_uploaded_image()` writes the submitted image to a temp file for the VLM.
The file is removed in a `finally` block after streaming and committing, so a
turn no longer leaks temp files. An image submitted without text uses `📷` as the
stored user message.

#### Styling

The fixed-position rules for `chat_toggle` are deleted, including the
`--lt-sidebar-w` / `--lt-chat-input-w` calculations and the mobile media query.
`theme.py` now styles `chat_toolbar` as a compact pill row: full-width element
container, flex-end alignment and a 2rem-high rounded button with a surface
background and border.

### Behaviour

- Image, voice, suggestions and send share one bottom area; nothing input-related
  is left in the scrolling transcript.
- The suggestion pill is visible at all times, shows the current count, and is
  right-aligned above send.
- Audio stops recording on demand and is transcribed only after the user presses
  send.
- Images can be attached and removed inside the composer before sending.
- Switching chats recreates the composer under a per-session key.
- No fixed pixel maths or media queries are needed for the suggestion button.

### Testing

- `make test`: **149 passed**
- `make lint`: clean
- Streamlit `AppTest` smoke run for the Chat page:
  - one `st.chat_input` rendered;
  - `toggle_suggestions` present in the bottom container;
  - no runtime exceptions.
- Headless Chrome at 1440×900, dark theme, using a temporary demo data directory:
  - composer order is attach (`+`), mic, text, send;
  - the Suggestions pill is right-aligned directly above send;
  - the refreshed `docs/screenshots/chat-dark.png` uses demo data only.
- Temporary image files are removed after a turn; the demo data directory lives
  outside the repository.

### Rationale

User request (2026-10-26): reorder the record, file upload, word suggestion and
enter controls and make them feel more consolidated. `st.chat_input` already
supports file and audio input in Streamlit 1.57, and `st.bottom` already provides
a pinned container above the composer, so the right fix was to remove the three
bespoke layers rather than restyle them.
