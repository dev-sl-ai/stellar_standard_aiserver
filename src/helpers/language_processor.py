import os
import json
from src.llm.translator import translation_chain
from src.helpers.conf_loader import TRANSLATION_CACHE_FILE

os.makedirs(os.path.dirname(TRANSLATION_CACHE_FILE), exist_ok=True)

def _load_translation_cache() -> dict:
    if os.path.exists(TRANSLATION_CACHE_FILE):
        with open(TRANSLATION_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_translation_cache(cache: dict) -> None:
    with open(TRANSLATION_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

translation_cache: dict = _load_translation_cache()

def _translate_cached(message: str, target_language: str) -> str:
    cache_key = f"{message}::{target_language}"

    if cache_key in translation_cache:
        return translation_cache[cache_key]

    result = translation_chain.invoke({
        "message": message,
        "target_language": target_language
    })
    translated = result.content.strip().strip('"')

    translation_cache[cache_key] = translated
    _save_translation_cache(translation_cache)

    return translated