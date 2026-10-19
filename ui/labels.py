"""Human-readable names and flags for the languages the tutor supports."""

LANG_NAMES = {
    "zh-TW": "Traditional Chinese",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}

LANG_FLAGS = {
    "zh-TW": "🇹🇼",
    "zh": "🇨🇳",
    "ja": "🇯🇵",
    "ko": "🇰🇷",
    "en": "🇺🇸",
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "de": "🇩🇪",
}


def language_name(code: str) -> str:
    return LANG_NAMES.get(code, code)


def language_flag(code: str) -> str:
    return LANG_FLAGS.get(code, "🌐")


def language_pair_label(native: str, target: str) -> str:
    """e.g. ``🇹🇼 → 🇯🇵``."""
    return f"{language_flag(native)} → {language_flag(target)}"
