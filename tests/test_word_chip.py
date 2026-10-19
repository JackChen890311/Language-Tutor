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


def test_rail_opens_automatically_when_suggestions_exist(monkeypatch):
    fake_state: dict = {"word_suggestions": [{"word": "食べる"}]}
    monkeypatch.setattr(word_chip.st, "session_state", fake_state)
    assert word_chip.rail_is_open() is True


def test_rail_stays_closed_without_suggestions(monkeypatch):
    fake_state: dict = {}
    monkeypatch.setattr(word_chip.st, "session_state", fake_state)
    assert word_chip.rail_is_open() is False


def test_explicit_close_wins_over_auto_open(monkeypatch):
    fake_state: dict = {
        "word_suggestions": [{"word": "食べる"}],
        "show_word_suggestions": False,
    }
    monkeypatch.setattr(word_chip.st, "session_state", fake_state)
    assert word_chip.rail_is_open() is False


def test_set_rail_open_records_explicit_choice(monkeypatch):
    fake_state: dict = {"word_suggestions": [{"word": "食べる"}]}
    monkeypatch.setattr(word_chip.st, "session_state", fake_state)
    word_chip.set_rail_open(False)
    assert fake_state["show_word_suggestions"] is False
    assert word_chip.rail_is_open() is False


def test_reset_word_rail_preference_restores_auto_behaviour(monkeypatch):
    fake_state: dict = {
        "word_suggestions": [{"word": "食べる"}],
        "show_word_suggestions": False,
    }
    monkeypatch.setattr(word_chip.st, "session_state", fake_state)
    word_chip.reset_word_rail_preference()
    assert "show_word_suggestions" not in fake_state
    assert word_chip.rail_is_open() is True
