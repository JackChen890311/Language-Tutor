def test_settings_round_trip(tmp_store):
    tmp_store.save_settings({"native_lang": "zh-TW", "target_lang": "ja"})
    result = tmp_store.load_settings()
    assert result["native_lang"] == "zh-TW"
    assert result["target_lang"] == "ja"


def test_load_settings_returns_empty_dict_when_missing(tmp_store):
    assert tmp_store.load_settings() == {}


def test_streak_round_trip(tmp_store):
    tmp_store.save_streak("ja", {"streak": 3, "last_active": "2026-07-05"})
    result = tmp_store.load_streak("ja")
    assert result["streak"] == 3


def test_quiz_history_empty_when_missing(tmp_store):
    assert tmp_store.load_quiz_history("ja") == []


def test_quiz_history_round_trip(tmp_store):
    tmp_store.append_quiz_result("ja", {"id": "abc123", "score": 100})
    tmp_store.append_quiz_result("ja", {"id": "def456", "score": 50})
    history = tmp_store.load_quiz_history("ja")
    assert len(history) == 2
    assert history[0]["id"] == "abc123"
    assert history[1]["score"] == 50


def test_create_and_list_chat_sessions(tmp_store):
    session_id = tmp_store.create_chat_session("ja", "Shopping trip")
    sessions = tmp_store.list_chat_sessions("ja")
    assert len(sessions) == 1
    assert sessions[0]["name"] == "Shopping trip"
    assert sessions[0]["id"] == session_id


def test_chat_messages_round_trip(tmp_store):
    sid = tmp_store.create_chat_session("ja", "Test")
    messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
    tmp_store.save_chat_messages("ja", sid, messages)
    result = tmp_store.load_chat_messages("ja", sid)
    assert result == messages


def test_chat_summary_appends(tmp_store):
    sid = tmp_store.create_chat_session("ja", "Test")
    tmp_store.append_chat_summary("ja", sid, "First summary.")
    tmp_store.append_chat_summary("ja", sid, "Second summary.")
    summary = tmp_store.load_chat_summary("ja", sid)
    assert "First summary." in summary
    assert "Second summary." in summary


def test_delete_chat_session(tmp_store):
    sid = tmp_store.create_chat_session("ja", "To delete")
    tmp_store.delete_chat_session("ja", sid)
    assert tmp_store.list_chat_sessions("ja") == []


def test_wordlist_round_trip(tmp_store):
    words = [{"id": "abc", "word": "食べる", "definition": "to eat"}]
    tmp_store.save_wordlist("ja", words)
    result = tmp_store.load_wordlist("ja")
    assert result[0]["word"] == "食べる"


def test_lessons_progress_round_trip(tmp_store):
    tmp_store.save_lessons_progress("ja", {"completed": ["food"], "topics": ["food"]})
    result = tmp_store.load_lessons_progress("ja")
    assert "food" in result["completed"]


def test_lesson_notes_round_trip(tmp_store):
    tmp_store.save_lesson_notes("ja", "lesson-001", "# Lesson notes\nVocab: ...")
    result = tmp_store.load_lesson_notes("ja", "lesson-001")
    assert "Lesson notes" in result
