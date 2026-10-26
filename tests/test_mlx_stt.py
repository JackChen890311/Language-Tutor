import sys
from unittest.mock import MagicMock, patch

from models.mlx_stt import WhisperModel

MODEL_ID = "mlx-community/whisper-large-v3-turbo"


def _stub(by_language: dict[str | None, dict]) -> MagicMock:
    stub = MagicMock()

    def fake_transcribe(audio, *, path_or_hf_repo, task, **kwargs):
        return by_language[kwargs.get("language")]

    stub.transcribe.side_effect = fake_transcribe
    return stub


def _result(text: str, logprob: float) -> dict:
    return {"text": text, "segments": [{"avg_logprob": logprob}]}


def test_transcribe_pins_requested_language():
    stub = _stub({"ja": _result("  こんにちは  ", -0.2)})
    model = WhisperModel(MODEL_ID)
    with patch.dict(sys.modules, {"mlx_whisper": stub}):
        text = model.transcribe("clip.wav", lang="ja")

    assert text == "こんにちは"
    stub.transcribe.assert_called_once_with(
        "clip.wav", path_or_hf_repo=MODEL_ID, task="transcribe", language="ja"
    )


def test_transcribe_maps_regional_chinese_to_zh():
    stub = _stub({"zh": _result("你好", -0.2)})
    model = WhisperModel(MODEL_ID)
    with patch.dict(sys.modules, {"mlx_whisper": stub}):
        model.transcribe("clip.wav", lang="zh-TW")

    assert stub.transcribe.call_args.kwargs["language"] == "zh"


def test_transcribe_without_language_lets_whisper_detect():
    stub = _stub({None: _result("hello", -0.2)})
    model = WhisperModel(MODEL_ID)
    with patch.dict(sys.modules, {"mlx_whisper": stub}):
        model.transcribe("clip.wav")

    assert "language" not in stub.transcribe.call_args.kwargs
    assert stub.transcribe.call_args.kwargs["task"] == "transcribe"


def test_transcribe_uses_fallback_when_more_confident():
    stub = _stub(
        {
            "ja": _result("ニーハオ", -1.2),
            "zh": _result("你好，今天天氣很好。", -0.3),
        }
    )
    model = WhisperModel(MODEL_ID)
    with patch.dict(sys.modules, {"mlx_whisper": stub}):
        text = model.transcribe("clip.wav", lang="ja", fallback_lang="zh-TW")

    assert text == "你好，今天天氣很好。"
    assert stub.transcribe.call_count == 2


def test_transcribe_keeps_target_language_when_close():
    stub = _stub(
        {
            "ja": _result("今日はいい天気ですね。", -0.4),
            "zh": _result("今日是好天气", -0.45),
        }
    )
    model = WhisperModel(MODEL_ID)
    with patch.dict(sys.modules, {"mlx_whisper": stub}):
        text = model.transcribe("clip.wav", lang="ja", fallback_lang="zh-TW")

    assert text == "今日はいい天気ですね。"


def test_transcribe_skips_second_pass_for_same_language():
    stub = _stub({"zh": _result("你好", -0.2)})
    model = WhisperModel(MODEL_ID)
    with patch.dict(sys.modules, {"mlx_whisper": stub}):
        model.transcribe("clip.wav", lang="zh-TW", fallback_lang="zh-CN")

    assert stub.transcribe.call_count == 1
