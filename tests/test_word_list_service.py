import json
from datetime import date
from unittest.mock import MagicMock

from services.prompt_builder import PromptBuilder
from services.word_list_service import (
    WordListService,
    filter_and_sort_words,
    is_word_due,
)


def _make_svc(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return WordListService(tmp_store, mm, pb)


def _mock_enrichment():
    return json.dumps(
        {
            "reading": "たべる",
            "definition": "to eat",
            "part_of_speech": "動詞",
            "formality": "casual",
            "synonyms": ["食う"],
            "antonyms": [],
            "collocations": ["ご飯を食べる"],
            "conjugations": {"masu": "食べます", "te": "食べて"},
            "tense_notes": "Group 2 verb",
            "examples": ["毎日ご飯を食べる。"],
            "grammar_notes": "Ichidan verb",
            "proficiency_level": "N5",
            "language_specific": {"on_yomi": None, "kun_yomi": "た.べる", "pitch_accent": "LHL"},
        }
    )


def test_add_word_enriches_and_saves(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    word = svc.add_word("ja", "zh-TW", "食べる", reading="たべる", source="chat")
    assert word["definition"] == "to eat"
    assert word["word"] == "食べる"
    assert "id" in word
    saved = tmp_store.load_wordlist("ja")
    assert len(saved) == 1


def test_add_word_no_duplicate(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    svc.add_word("ja", "zh-TW", "食べる", source="chat")
    svc.add_word("ja", "zh-TW", "食べる", source="manual")
    saved = tmp_store.load_wordlist("ja")
    assert len(saved) == 1


def test_search_by_word(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    svc.add_word("ja", "zh-TW", "食べる", source="chat")
    results = svc.search("ja", query="食べ")
    assert len(results) == 1


def test_filter_by_tag(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    svc.add_word("ja", "zh-TW", "食べる", source="chat", tags=["food"])
    results = svc.filter_by_tag("ja", "food")
    assert len(results) == 1


def test_has_stale_words_true(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    svc.add_word("ja", "zh-TW", "食べる", source="chat")
    assert svc.has_stale_words("ja") is True


def test_update_review_stats(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    word = svc.add_word("ja", "zh-TW", "食べる", source="chat")
    svc.update_review_stats("ja", word["id"], correct=True)
    updated = svc.get_word("ja", word["id"])
    assert updated["review_stats"]["correct"] == 1
    assert updated["review_stats"]["last_reviewed"] == date.today().isoformat()


def test_get_stale_words_returns_unreviewed(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    svc.add_word("ja", "zh-TW", "食べる", source="chat")
    stale = svc.get_stale_words("ja")
    assert len(stale) == 1
    assert stale[0]["word"] == "食べる"


def test_has_stale_words_false_after_review(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    word = svc.add_word("ja", "zh-TW", "食べる", source="chat")
    svc.update_review_stats("ja", word["id"], correct=True)
    assert svc.has_stale_words("ja") is False


def test_add_word_auto_reading_from_enrichment(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    word = svc.add_word("ja", "zh-TW", "食べる", source="manual")
    assert word["reading"] == "たべる"


def test_add_word_user_reading_takes_priority(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    word = svc.add_word("ja", "zh-TW", "食べる", reading="タベル", source="manual")
    assert word["reading"] == "タベル"


TODAY = date(2026, 10, 20)


def _word(
    word_id: str,
    word: str,
    *,
    reading: str = "",
    added: str = "2026-01-01",
    level: str = "",
    tags: list[str] | None = None,
    last_reviewed: str | None = None,
    correct: int = 0,
    incorrect: int = 0,
) -> dict:
    return {
        "id": word_id,
        "word": word,
        "reading": reading,
        "added_date": added,
        "proficiency_level": level,
        "tags": tags or [],
        "review_stats": {
            "last_reviewed": last_reviewed,
            "correct": correct,
            "incorrect": incorrect,
        },
    }


def test_is_word_due_boundary_and_never_reviewed():
    assert is_word_due(_word("old", "a", last_reviewed="2026-10-12"), today=TODAY) is True
    assert is_word_due(_word("edge", "a", last_reviewed="2026-10-13"), today=TODAY) is False
    assert is_word_due(_word("fresh", "a", last_reviewed="2026-10-19"), today=TODAY) is False
    assert is_word_due(_word("new", "a"), today=TODAY) is True


def test_filter_words_by_query_tag_and_level():
    words = [
        _word("food", "食べる", reading="たべる", level="N5", tags=["food"]),
        _word("drink", "飲む", reading="のむ", level="N3", tags=["food"]),
        _word("run", "走る", reading="はしる", level="N5", tags=["sport"]),
    ]

    assert [w["id"] for w in filter_and_sort_words(words, query="たべ")] == ["food"]
    assert [w["id"] for w in filter_and_sort_words(words, query="食")] == ["food"]
    assert [w["id"] for w in filter_and_sort_words(words, tag="food", sort="oldest")] == [
        "food",
        "drink",
    ]
    assert [w["id"] for w in filter_and_sort_words(words, level="N5", sort="oldest")] == [
        "food",
        "run",
    ]
    assert [w["id"] for w in filter_and_sort_words(words, tag="food", level="N5")] == ["food"]


def test_filter_words_by_review_status():
    words = [
        _word("never", "a", last_reviewed=None),
        _word("fresh", "b", last_reviewed="2026-10-19"),
        _word("stale", "c", last_reviewed="2026-10-01"),
    ]

    due = filter_and_sort_words(words, review_status="due", today=TODAY)
    never = filter_and_sort_words(words, review_status="never", today=TODAY)
    reviewed = filter_and_sort_words(words, review_status="reviewed", today=TODAY)

    assert {w["id"] for w in due} == {"never", "stale"}
    assert {w["id"] for w in never} == {"never"}
    assert {w["id"] for w in reviewed} == {"fresh", "stale"}


def test_sort_newest_then_oldest():
    words = [
        _word("first", "a", added="2026-01-01"),
        _word("second", "b", added="2026-01-01"),
        _word("third", "c", added="2026-02-01"),
    ]

    assert [w["id"] for w in filter_and_sort_words(words, sort="newest")] == [
        "third",
        "second",
        "first",
    ]
    assert [w["id"] for w in filter_and_sort_words(words, sort="oldest")] == [
        "first",
        "second",
        "third",
    ]


def test_sort_alphabetically_uses_reading_then_word():
    words = [
        _word("ta", "食べる", reading="たべる"),
        _word("i", "行く", reading="いく"),
        _word("no", "飲む", reading="のむ"),
    ]
    no_reading = [_word("b", "banana"), _word("a", "apple")]

    assert [w["id"] for w in filter_and_sort_words(words, sort="az")] == ["i", "ta", "no"]
    assert [w["id"] for w in filter_and_sort_words(words, sort="za")] == ["no", "ta", "i"]
    assert [w["id"] for w in filter_and_sort_words(no_reading, sort="az")] == ["a", "b"]


def test_sort_most_reviewed_by_total_attempts():
    words = [
        _word("few", "a", correct=1),
        _word("many", "b", correct=3, incorrect=2),
        _word("none", "c"),
    ]

    assert [w["id"] for w in filter_and_sort_words(words, sort="most_reviewed")] == [
        "many",
        "few",
        "none",
    ]


def test_browse_applies_filters_and_sort(tmp_store, mock_llm):
    mock_llm.generate.return_value = _mock_enrichment()
    svc = _make_svc(tmp_store, mock_llm)
    svc.add_word("ja", "zh-TW", "食べる", reading="たべる", source="chat", tags=["food"])
    svc.add_word("ja", "zh-TW", "飲む", reading="のむ", source="manual", tags=["food"])

    result = svc.browse("ja", tag="food", level="N5", sort="az")

    assert [w["word"] for w in result] == ["食べる", "飲む"]
