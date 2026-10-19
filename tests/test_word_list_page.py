from ui.pages.word_list import _pills_html


def test_pills_include_metadata_and_tags():
    word = {
        "part_of_speech": "名詞",
        "formality": "formal",
        "proficiency_level": "N1",
        "tags": ["business", "daily"],
    }
    html = _pills_html(word)
    assert "名詞" in html
    assert "formal" in html
    assert "N1" in html
    assert "#business" in html
    assert "#daily" in html


def test_pills_skip_missing_or_dash_values():
    word = {"part_of_speech": "-", "formality": None, "proficiency_level": ""}
    assert _pills_html(word) == ""
