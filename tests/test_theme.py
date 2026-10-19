from ui.labels import language_flag, language_name, language_pair_label
from ui.theme import _token_css, activity_days, greeting_for_hour


def test_greeting_morning():
    assert greeting_for_hour(8) == "Good morning"


def test_greeting_afternoon():
    assert greeting_for_hour(14) == "Good afternoon"


def test_greeting_evening():
    assert greeting_for_hour(20) == "Good evening"


def test_greeting_late_night():
    assert greeting_for_hour(2) == "Late-night study session"
    assert greeting_for_hour(23) == "Late-night study session"


def test_greeting_boundaries():
    assert greeting_for_hour(5) == "Good morning"
    assert greeting_for_hour(11) == "Good morning"
    assert greeting_for_hour(12) == "Good afternoon"
    assert greeting_for_hour(18) == "Good evening"


def test_activity_days_length_and_today_flag():
    days = activity_days([], "2026-10-19")
    assert len(days) == 7
    assert days[-1] == ("Mon", False, True)
    assert days[0][0] == "Tue"


def test_activity_days_marks_reviewed_dates():
    days = activity_days(["2026-10-19", "2026-10-17"], "2026-10-19")
    flags = {name: active for name, active, _ in days}
    assert flags["Mon"] is True
    assert flags["Sat"] is True
    assert flags["Sun"] is False


def test_activity_days_ignores_duplicates_and_garbage():
    days = activity_days(
        ["2026-10-19", "2026-10-19", "not-a-date", "", "2026-10-19T10:00:00"],
        "2026-10-19",
    )
    assert days[-1] == ("Mon", True, True)
    assert sum(1 for _, active, _ in days if active) == 1


def test_activity_days_invalid_today_returns_empty():
    assert activity_days(["2026-10-19"], "nope") == []


def test_activity_days_honours_window():
    days = activity_days(["2026-10-01"], "2026-10-19", days=5)
    assert len(days) == 5
    assert not any(active for _, active, _ in days)


def test_language_name_and_flag():
    assert language_name("ja") == "Japanese"
    assert language_name("xx") == "xx"
    assert language_flag("ja") == "🇯🇵"
    assert language_pair_label("zh-TW", "ja") == "🇹🇼 → 🇯🇵"


def test_tokens_switch_with_color_scheme_without_rerun():
    css = _token_css()
    assert css.startswith(".stApp {")
    # Every token carries both palettes so a client-side theme switch is instant.
    assert css.count("light-dark(") == css.count("--lt-")
    assert "--lt-bg: light-dark(#FBFAF8, #141310);" in css
    assert "--lt-text: light-dark(#1F1B16, #F2EDE6);" in css
    assert "--lt-accent: light-dark(#A85E12, #E8A44C);" in css


def test_shadow_tokens_are_colours_not_full_shadows():
    css = _token_css()
    assert "--lt-shadow: " not in css
    assert "--lt-shadow-color: light-dark(rgba(31, 27, 22, 0.06), rgba(0, 0, 0, 0.40));" in css
