from ui.components import word_chip
from ui.components.word_chip import merge_word_suggestions


def test_merge_empty_existing():
    result = merge_word_suggestions([], [{"word": "食べる", "reading": "たべる"}])
    assert result == [{"word": "食べる", "reading": "たべる"}]


def test_merge_no_new_suggestions():
    existing = [{"word": "食べる", "reading": "たべる"}]
    assert merge_word_suggestions(existing, []) == existing


def test_merge_new_suggestions_go_first():
    existing = [{"word": "食べる", "reading": "たべる"}]
    new = [{"word": "飲む", "reading": "のむ"}]
    result = merge_word_suggestions(existing, new)
    assert result == [{"word": "飲む", "reading": "のむ"}, {"word": "食べる", "reading": "たべる"}]


def test_merge_dedupes_repeated_word_and_moves_to_front():
    existing = [
        {"word": "飲む", "reading": "のむ"},
        {"word": "食べる", "reading": "たべる"},
    ]
    new = [{"word": "食べる", "reading": "たべる (updated)"}]
    result = merge_word_suggestions(existing, new)
    assert result == [
        {"word": "食べる", "reading": "たべる (updated)"},
        {"word": "飲む", "reading": "のむ"},
    ]


def test_merge_caps_at_limit():
    existing = [{"word": f"word{i}"} for i in range(10)]
    new = [{"word": "new_word"}]
    result = merge_word_suggestions(existing, new, cap=10)
    assert len(result) == 10
    assert result[0] == {"word": "new_word"}
    assert result[-1] == {"word": "word8"}


def test_clear_word_suggestions_empties_shared_list(monkeypatch):
    fake_state: dict = {"word_suggestions": [{"word": "食べる"}]}
    monkeypatch.setattr(word_chip.st, "session_state", fake_state)
    word_chip.clear_word_suggestions()
    assert fake_state["word_suggestions"] == []
    assert word_chip.get_word_suggestions() == []


def test_clear_word_suggestions_when_already_empty(monkeypatch):
    fake_state: dict = {}
    monkeypatch.setattr(word_chip.st, "session_state", fake_state)
    word_chip.clear_word_suggestions()
    assert word_chip.get_word_suggestions() == []
