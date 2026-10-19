from services.language_service import LanguageService
from freezegun import freeze_time


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


def test_update_streak_same_day_no_double_count(tmp_store):
    with freeze_time("2026-05-10"):
        svc = LanguageService(tmp_store)
        svc.update_streak("ja")
        svc.update_streak("ja")
        stats = svc.get_stats("ja")
        assert stats["streak"] == 1


def test_update_streak_consecutive_days(tmp_store):
    svc = LanguageService(tmp_store)
    with freeze_time("2026-05-09"):
        svc.update_streak("ja")
    with freeze_time("2026-05-10"):
        svc.update_streak("ja")
        stats = svc.get_stats("ja")
        assert stats["streak"] == 2


def test_update_streak_gap_resets(tmp_store):
    svc = LanguageService(tmp_store)
    with freeze_time("2026-05-08"):
        svc.update_streak("ja")
    with freeze_time("2026-05-10"):
        svc.update_streak("ja")
        stats = svc.get_stats("ja")
        assert stats["streak"] == 1


def test_get_active_dates_includes_streak_days(tmp_store):
    svc = LanguageService(tmp_store)
    with freeze_time("2026-10-18"):
        svc.update_streak("ja")
    with freeze_time("2026-10-19"):
        svc.update_streak("ja")
        assert svc.get_active_dates("ja") == ["2026-10-18", "2026-10-19"]


def test_get_active_dates_includes_word_reviews(tmp_store):
    svc = LanguageService(tmp_store)
    tmp_store.save_wordlist(
        "ja",
        [{"id": "w1", "word": "食べる", "review_stats": {"last_reviewed": "2026-10-17"}}],
    )
    with freeze_time("2026-10-19"):
        assert "2026-10-17" in svc.get_active_dates("ja")


def test_get_active_dates_includes_quizzes_and_chats(tmp_store):
    svc = LanguageService(tmp_store)
    tmp_store.append_quiz_result("ja", {"tested_at": "2026-10-16T10:00:00", "score": 50})
    with freeze_time("2026-10-15"):
        tmp_store.create_chat_session("ja", "lesson")
    with freeze_time("2026-10-19"):
        dates = svc.get_active_dates("ja")
    assert "2026-10-16" in dates
    assert "2026-10-15" in dates


def test_get_active_dates_respects_window(tmp_store):
    svc = LanguageService(tmp_store)
    tmp_store.append_quiz_result("ja", {"tested_at": "2026-09-01T10:00:00", "score": 50})
    with freeze_time("2026-10-19"):
        assert svc.get_active_dates("ja", days=7) == []
