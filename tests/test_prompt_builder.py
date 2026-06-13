from services.prompt_builder import PromptBuilder


def test_chat_prompt_includes_languages():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja", level="N4")
    assert "zh-TW" in prompt or "Traditional Chinese" in prompt
    assert "ja" in prompt or "Japanese" in prompt
    assert "N4" in prompt


def test_chat_prompt_chinese_native_includes_traditional_chinese_rule():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja", level="N4")
    assert "繁體中文" in prompt or "Traditional Chinese" in prompt
    assert "台灣" in prompt


def test_chat_prompt_english_native_no_chinese_rule():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="en", target_lang="ja", level="N4")
    assert "台灣" not in prompt


def test_level_test_prompt_includes_target_lang():
    pb = PromptBuilder()
    prompt = pb.level_test_system_prompt(target_lang="ja", n_questions=5)
    assert "ja" in prompt or "Japanese" in prompt
    assert "5" in prompt
    assert "JSON" in prompt


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
        level="N4",
        topic="food",
        phase="structured",
        difficulty="Normal",
    )
    assert "food" in prompt
    assert "structured" in prompt or "vocabulary" in prompt.lower()


def test_lesson_prompt_conversation_phase():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW",
        target_lang="ja",
        level="N4",
        topic="food",
        phase="conversation",
        difficulty="Hard",
    )
    assert "conversation" in prompt.lower() or "free" in prompt.lower()
    assert "Hard" in prompt or "minimal" in prompt.lower()


def test_chat_prompt_includes_speak_tag_instruction():
    pb = PromptBuilder()
    prompt = pb.chat_system_prompt(native_lang="zh-TW", target_lang="ja", level="N4")
    assert "<speak>" in prompt


def test_lesson_prompt_includes_speak_tag_instruction():
    pb = PromptBuilder()
    prompt = pb.lesson_system_prompt(
        native_lang="zh-TW",
        target_lang="ja",
        level="N4",
        topic="food",
        phase="structured",
    )
    assert "<speak>" in prompt
