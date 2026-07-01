from functools import lru_cache

from deep_translator import GoogleTranslator

from src.helpers.conf_loader import server_config_loader
from src.helpers.logger import logger

# Map a server language code (e.g. "en-US") base to a deep_translator target code.
_LANG_TARGET = {
    "ja": "ja",
    "en": "en",
    "zh": "zh-CN",
    "ko": "ko",
    "es": "es",
}


@lru_cache(maxsize=256)
def _translate_cached(text_ja: str, target: str) -> str:
    """Translate Japanese -> target, cached so static strings translate only once."""
    try:
        return GoogleTranslator(source="ja", target=target).translate(text_ja)
    except Exception as e:
        logger.error(f"[translate] ja->{target} failed: {e}")
        return text_ja


def localize_from_ja(text_ja: str, language: str = None) -> str:
    """Translate a Japanese string into the current server language.

    Used for fixed strings that are sent to the client WITHOUT passing through the
    agent LLM (e.g. return_direct tools, direct WebSocket messages). Returns the
    original text for Japanese or if translation fails.
    """
    lang = (language or server_config_loader.get_language() or "ja").split("-")[0].lower()
    if lang == "ja":
        return text_ja
    target = _LANG_TARGET.get(lang, "en")
    return _translate_cached(text_ja, target)
