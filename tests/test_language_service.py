from datetime import date
from services.language_service import LanguageService, PROFICIENCY_FRAMEWORKS


def test_get_set_language_pair(tmp_store):
    svc = LanguageService(tmp_store)
    svc.set_language_pair(native="zh-TW", target="ja")
    native, target = svc.get_language_pair()
    assert native == "zh-TW"
    assert target == "ja"


def test_default_language_pair(tmp_store):
    svc = LanguageService(tmp_store)
    native, target = svc.get_language_pair()
    assert native == "en"
    assert target == "ja"


def test_get_proficiency_framework_japanese(tmp_store):
    svc = LanguageService(tmp_store)
    framework = svc.get_proficiency_framework("ja")
    assert framework["name"] == "JLPT"
    assert "N5" in framework["levels"]


def test_get_proficiency_framework_chinese(tmp_store):
    svc = LanguageService(tmp_store)
    framework = svc.get_proficiency_framework("zh")
    assert framework["name"] == "HSK"


def test_get_proficiency_framework_fallback(tmp_store):
    svc = LanguageService(tmp_store)
    framework = svc.get_proficiency_framework("es")
    assert framework["name"] == "CEFR"


def test_update_streak_first_day(tmp_store):
    svc = LanguageService(tmp_store)
    svc.update_streak("ja")
    stats = svc.get_stats("ja")
    assert stats["streak"] == 1


def test_get_stats_defaults(tmp_store):
    svc = LanguageService(tmp_store)
    stats = svc.get_stats("ja")
    assert stats["words_saved"] == 0
    assert stats["lessons_completed"] == 0
    assert stats["level"] == ""
