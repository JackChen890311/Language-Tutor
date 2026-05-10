import json
from datetime import date, timedelta
from unittest.mock import MagicMock
from services.word_list_service import WordListService
from services.prompt_builder import PromptBuilder


def _make_svc(tmp_store, mock_llm):
    pb = PromptBuilder()
    mm = MagicMock()
    mm.get_llm.return_value = mock_llm
    return WordListService(tmp_store, mm, pb)


def _mock_enrichment():
    return json.dumps({
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
    })


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
