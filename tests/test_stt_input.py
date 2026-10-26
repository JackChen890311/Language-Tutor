import os
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import ui.components.audio_controls as audio_controls


class FakeAudio:
    def __init__(self, data: bytes):
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


class FakeStreamlit:
    @contextmanager
    def spinner(self, *_args, **_kwargs):
        yield


def _mm(transcript: str = "こんにちは"):
    mm = MagicMock()
    stt = MagicMock()
    stt.transcribe.return_value = transcript
    mm.get_stt.return_value = stt
    return mm, stt


def test_audio_is_transcribed():
    mm, stt = _mm()

    with (
        patch.object(audio_controls, "st", FakeStreamlit()),
        patch.object(audio_controls, "get", return_value=mm),
    ):
        assert audio_controls.transcribe_audio(FakeAudio(b"fake-wav"), lang="ja") == "こんにちは"

    assert stt.transcribe.call_count == 1


def test_language_hints_are_forwarded_and_temp_file_removed():
    mm, stt = _mm()

    with (
        patch.object(audio_controls, "st", FakeStreamlit()),
        patch.object(audio_controls, "get", return_value=mm),
    ):
        audio_controls.transcribe_audio(FakeAudio(b"fake-wav"), lang="ja", fallback_lang="zh-TW")

    call = stt.transcribe.call_args
    assert call.kwargs == {"lang": "ja", "fallback_lang": "zh-TW"}
    assert not os.path.exists(call.args[0])
