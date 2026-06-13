import base64

from ui.components.audio_controls import extract_speak_text, parse_message_segments, autoplay_audio_html


def test_no_tags_returns_original():
    assert extract_speak_text("Hello world") == "Hello world"


def test_single_tag_returns_content():
    text = "解釋一下。<speak>こんにちは</speak> 意思是你好。"
    assert extract_speak_text(text) == "こんにちは"


def test_multiple_tags_joined_with_space():
    text = "先說 <speak>おはよう</speak> 然後說 <speak>ありがとう</speak>"
    assert extract_speak_text(text) == "おはよう ありがとう"


def test_empty_content_falls_back_to_original():
    assert extract_speak_text("<speak></speak>") == "<speak></speak>"


def test_strips_whitespace_inside_tags():
    text = "<speak>  おやすみ  </speak>"
    assert extract_speak_text(text) == "おやすみ"


# --- parse_message_segments ---

def test_parse_plain_text_returns_single_text_segment():
    segs = parse_message_segments("Hello world")
    assert segs == [{"type": "text", "content": "Hello world"}]


def test_parse_single_speak_returns_two_segments():
    text = "意思是你好。<speak>こんにちは</speak>"
    segs = parse_message_segments(text)
    assert segs == [
        {"type": "text", "content": "意思是你好。"},
        {"type": "speak", "content": "こんにちは"},
    ]


def test_parse_multiple_speaks_alternates_correctly():
    text = "前文 <speak>おはよう</speak> 中間 <speak>ありがとう</speak> 後文"
    segs = parse_message_segments(text)
    assert segs == [
        {"type": "text", "content": "前文 "},
        {"type": "speak", "content": "おはよう"},
        {"type": "text", "content": " 中間 "},
        {"type": "speak", "content": "ありがとう"},
        {"type": "text", "content": " 後文"},
    ]


def test_parse_empty_speak_tag_excluded():
    segs = parse_message_segments("前文 <speak>  </speak> 後文")
    types = [s["type"] for s in segs]
    assert "speak" not in types


def test_parse_speak_only_message():
    segs = parse_message_segments("<speak>いただきます</speak>")
    assert segs == [{"type": "speak", "content": "いただきます"}]


# --- autoplay_audio_html ---

def test_autoplay_html_contains_base64_audio():
    audio_bytes = b"RIFF"  # minimal fake wav header
    html = autoplay_audio_html(audio_bytes)
    encoded = base64.b64encode(audio_bytes).decode()
    assert encoded in html
    assert "audio/wav" in html
    assert "autoplay" in html


def test_autoplay_html_is_invisible():
    html = autoplay_audio_html(b"RIFF")
    assert 'height="0"' in html or "height:0" in html or 'display:none' in html
