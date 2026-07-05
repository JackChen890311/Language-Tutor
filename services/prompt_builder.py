LANG_NAMES = {
    "zh-TW": "Traditional Chinese (繁體中文, 台灣用語)",
    "ja": "Japanese",
    "en": "English",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}

DIFFICULTY_INSTRUCTIONS = {
    "Easy": "Use simpler vocabulary, shorter sentences, and provide more hints and encouragement.",
    "Normal": "Use natural, moderately-paced language and everyday vocabulary.",
    "Hard": "Use complex grammar, native-speed examples, and provide minimal hand-holding.",
}


class PromptBuilder:
    def _lang_name(self, code: str) -> str:
        return LANG_NAMES.get(code, code)

    def _chinese_rule(self, native_lang: str) -> str:
        if native_lang in ("zh-TW", "zh"):
            return (
                "- IMPORTANT: Always use Traditional Chinese (繁體中文) with 台灣用語 and "
                "Taiwanese terminology. Never use Simplified Chinese.\n"
            )
        return ""

    def chat_system_prompt(self, native_lang: str, target_lang: str) -> str:
        return (
            f"You are a patient and encouraging language tutor.\n\n"
            f"Native language: {self._lang_name(native_lang)} ({native_lang})\n"
            f"Target language: {self._lang_name(target_lang)} ({target_lang})\n\n"
            f"Rules:\n"
            f"- Respond in {self._lang_name(native_lang)} for explanations and feedback\n"
            f"- Use {self._lang_name(target_lang)} for language practice\n"
            f"- When the user makes a mistake, always correct it: note the error, "
            f"explain why it is wrong, give the correct form, then continue naturally\n"
            f"- Tone: encouraging and patient; corrections are matter-of-fact, never condescending\n"
            f"- When you write {self._lang_name(target_lang)} sentences or phrases for the user "
            f"to hear or practice, wrap them in <speak>…</speak> tags. "
            f"Do NOT tag explanations, translations, or {self._lang_name(native_lang)} text.\n"
            f"- When you introduce a single vocabulary word (not a phrase or sentence) "
            f"likely to be new to a learner, append exactly one marker per unique word:\n"
            f'  <!--WORD_SUGGESTION:{{"word": "<single word>", "reading": "<reading/pronunciation>"}}-->\n'
            f"  Do NOT repeat the same word marker twice.\n"
            f"{self._chinese_rule(native_lang)}"
        )

    def test_system_prompt(self, native_lang: str, target_lang: str, n_questions: int = 8) -> str:
        return (
            f"You are creating a {self._lang_name(target_lang)} ({target_lang}) "
            f"practice quiz.\n\n"
            f"Generate exactly {n_questions} multiple choice questions covering vocabulary, "
            f"grammar, and reading comprehension.\n\n"
            f"For each question, write two explanations of why the correct answer is right: "
            f"one in {self._lang_name(target_lang)}, one in {self._lang_name(native_lang)}.\n\n"
            f"Respond ONLY with a JSON array, no other text:\n"
            f"[\n"
            f"  {{\n"
            f'    "question": "...",\n'
            f'    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],\n'
            f'    "correct": "A",\n'
            f'    "explanation_target": "... (in {self._lang_name(target_lang)})",\n'
            f'    "explanation_native": "... (in {self._lang_name(native_lang)})"\n'
            f"  }}\n"
            f"]\n"
        )

    def word_enrichment_prompt(self, target_lang: str, native_lang: str) -> str:
        return (
            f"You are a dictionary assistant for {self._lang_name(target_lang)}.\n\n"
            f"Given a word, return a JSON object with these exact fields:\n"
            f"{{\n"
            f'  "translation": "string (concise 1-5 word {self._lang_name(native_lang)} translation)",\n'
            f'  "definition": "string",\n'
            f'  "part_of_speech": "string",\n'
            f'  "formality": "casual|neutral|formal",\n'
            f'  "synonyms": ["string"],\n'
            f'  "antonyms": ["string"],\n'
            f'  "collocations": ["string"],\n'
            f'  "conjugations": {{}} or null,\n'
            f'  "tense_notes": "string" or null,\n'
            f'  "examples": ["string"],\n'
            f'  "grammar_notes": "string",\n'
            f'  "proficiency_level": "string",\n'
            f'  "language_specific": {{}}\n'
            f"}}\n\n"
            f"All definitions, notes, and examples must be in {self._lang_name(native_lang)}. "
            f"Respond ONLY with the JSON object."
        )

    def summarization_prompt(self, native_lang: str) -> str:
        return (
            f"Summarize the following conversation in under 300 words.\n"
            f"Focus on: key topics discussed, vocabulary and grammar points introduced, "
            f"the user's mistakes and corrections, and overall progress.\n"
            f"Write the summary in {self._lang_name(native_lang)} ({native_lang}).\n"
            f"Be concise and factual."
        )

    def lesson_system_prompt(
        self,
        native_lang: str,
        target_lang: str,
        topic: str,
        phase: str,
        difficulty: str = "Normal",
    ) -> str:
        difficulty_note = DIFFICULTY_INSTRUCTIONS.get(difficulty, DIFFICULTY_INSTRUCTIONS["Normal"])

        if phase == "structured":
            phase_instructions = (
                f'You are guiding a structured lesson on "{topic}". Follow this sequence:\n'
                f'1. Introduce 5-8 key vocabulary items relevant to "{topic}"\n'
                f"2. Explain one relevant grammar point\n"
                f"3. Give the user 3 practice exercises (fill-in-the-blank or translation)\n"
                f"4. After the exercises, invite the user to move to free conversation\n"
                f"Pace yourself — one step at a time. Wait for the user's response before moving on.\n"
            )
        else:
            phase_instructions = (
                f"The structured lesson is complete. Now have a natural free conversation "
                f'on the topic "{topic}".\n'
                f"Encourage use of the vocabulary and grammar from the lesson.\n"
                f"Gently correct mistakes as they occur.\n"
            )

        return (
            f"You are teaching a {self._lang_name(target_lang)} lesson.\n\n"
            f"Topic: {topic}\n"
            f"Difficulty: {difficulty} — {difficulty_note}\n"
            f"Native language: {self._lang_name(native_lang)} ({native_lang})\n\n"
            f"{phase_instructions}\n"
            f"Always explain in {self._lang_name(native_lang)}. Practice in {self._lang_name(target_lang)}.\n"
            f"When you write {self._lang_name(target_lang)} sentences or phrases for the user "
            f"to hear or practice, wrap them in <speak>…</speak> tags. "
            f"Do NOT tag explanations, translations, or {self._lang_name(native_lang)} text.\n"
            f"When you introduce a single vocabulary word (not a phrase or sentence) "
            f"likely to be new to a learner, append exactly one marker per unique word:\n"
            f'<!--WORD_SUGGESTION:{{"word": "<single word>", "reading": "<reading/pronunciation>"}}-->\n'
            f"Do NOT repeat the same word marker twice.\n"
            f"{self._chinese_rule(native_lang)}"
        )
