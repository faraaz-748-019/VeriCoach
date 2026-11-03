"""Multilingual translator stub (en / hi / te)."""

from __future__ import annotations

from typing import Literal

Locale = Literal["en", "hi", "te"]

# Locale display names
LOCALE_NAMES: dict[Locale, str] = {
    "en": "English",
    "hi": "हिन्दी",
    "te": "తెలుగు",
}

# Simple phrase dictionary for system messages.
# Extend per-feature; real translation uses a proper i18n library.
_PHRASES: dict[str, dict[Locale, str]] = {
    "greeting": {
        "en": "Hello! I'm your personal finance assistant. How can I help you today?",
        "hi": "नमस्ते! मैं आपका व्यक्तिगत वित्त सहायक हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
        "te": "నమస్కారం! నేను మీ వ్యక్తిగత ఆర్థిక సహాయకుడిని. ఈ రోజు నేను మీకు ఎలా సహాయపడగలను?",
    },
    "no_context": {
        "en": "I don't have enough context to answer that. Could you provide more details?",
        "hi": "मेरे पास इसका उत्तर देने के लिए पर्याप्त संदर्भ नहीं है। क्या आप अधिक विवरण दे सकते हैं?",
        "te": "దానికి సమాధానమివ్వడానికి నాకు తగినంత సందర్భం లేదు. మీరు మరిన్ని వివరాలు అందించగలరా?",
    },
    "error": {
        "en": "Sorry, an error occurred. Please try again.",
        "hi": "क्षमा करें, एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
        "te": "క్షమించండి, ఒక లోపం సంభవించింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    },
}


def t(key: str, locale: Locale = "en") -> str:
    """Look up a translated phrase by *key* and *locale*."""
    phrases = _PHRASES.get(key)
    if phrases is None:
        return key  # fallback: return the key itself
    return phrases.get(locale, phrases.get("en", key))


def supported_locales() -> list[Locale]:
    return ["en", "hi", "te"]
