from services.prompt_builder import PromptBuilder, get_difficulty_levels


def test_chat_prompt_includes_languages():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja")
    assert "zh-TW" in prompt or "Traditional Chinese" in prompt
    assert "ja" in prompt or "Japanese" in prompt


def test_chat_prompt_chinese_native_includes_traditional_chinese_rule():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja")
    assert "繁體中文" in prompt or "Traditional Chinese" in prompt
    assert "台灣" in prompt


def test_chat_prompt_english_native_no_chinese_rule():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="en", target_lang="ja")
    assert "台灣" not in prompt


def test_test_prompt_includes_target_lang():
    pb = PromptBuilder()
    prompt = pb.test_system_prompt(
        native_lang="zh-TW", target_lang="ja", difficulty="N3", n_questions=5
    )
    assert "ja" in prompt or "Japanese" in prompt
    assert "5" in prompt
    assert "JSON" in prompt


def test_test_prompt_requests_bilingual_explanations():
    pb = PromptBuilder()
    prompt = pb.test_system_prompt(
        native_lang="zh-TW", target_lang="ja", difficulty="N3", n_questions=5
    )
    assert "explanation_target" in prompt
    assert "explanation_native" in prompt
    assert "Traditional Chinese" in prompt or "zh-TW" in prompt


def test_test_prompt_includes_difficulty_framework():
    pb = PromptBuilder()
    prompt = pb.test_system_prompt(
        native_lang="zh-TW", target_lang="ja", difficulty="N2", n_questions=5
    )
    assert "N2" in prompt
    assert "JLPT" in prompt


def test_word_enrichment_prompt():
    pb = PromptBuilder()
    prompt = pb.word_enrichment_prompt(target_lang="ja", native_lang="zh-TW")
    assert "JSON" in prompt
    assert "definition" in prompt
    assert "translation" in prompt


def test_summarization_prompt():
    pb = PromptBuilder()
    prompt = pb.summarization_prompt(native_lang="zh-TW")
    assert "300" in prompt
    assert "zh-TW" in prompt or "Traditional Chinese" in prompt


def test_lesson_prompt_includes_phase():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW",
        target_lang="ja",
        topic="food",
        phase="structured",
        difficulty="N4",
    )
    assert "food" in prompt
    assert "structured" in prompt or "vocabulary" in prompt.lower()


def test_lesson_prompt_conversation_phase():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW",
        target_lang="ja",
        topic="food",
        phase="conversation",
        difficulty="N1",
    )
    assert "conversation" in prompt.lower() or "free" in prompt.lower()
    assert "N1" in prompt


def test_lesson_prompt_includes_difficulty_framework():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="en",
        target_lang="ko",
        topic="food",
        phase="structured",
        difficulty="TOPIK4",
    )
    assert "TOPIK4" in prompt
    assert "TOPIK" in prompt


def test_get_difficulty_levels_known_language():
    framework = get_difficulty_levels("ja")
    assert framework["name"] == "JLPT"
    assert framework["levels"] == ["N5", "N4", "N3", "N2", "N1"]


def test_get_difficulty_levels_falls_back_to_cefr():
    framework = get_difficulty_levels("es")
    assert framework["name"] == "CEFR"
    assert framework["levels"] == ["A1", "A2", "B1", "B2", "C1", "C2"]


def test_chat_prompt_includes_speak_tag_instruction():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja")
    assert "<speak>" in prompt


def test_lesson_prompt_includes_speak_tag_instruction():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW",
        target_lang="ja",
        topic="food",
        phase="structured",
        difficulty="N3",
    )
    assert "<speak>" in prompt
