import json
import os
import time

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from src.helpers.env_loader import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION
from src.helpers.log_paths import CACHE_DIR
from src.helpers.logger import logger

router = APIRouter()

# Azure issued tokens are valid for ~10 minutes; refresh after 9 to stay ahead of expiry.
_TOKEN_TTL_SECONDS = 540

# A module-level dict would give each uvicorn worker process (WEB_CONCURRENCY > 1) its
# own cache and its own independent refresh schedule, multiplying Azure token requests
# by worker count. A file is shared by every worker instead. Writes go through a
# tmp-then-os.replace swap so a concurrent reader never sees a half-written file; two
# workers racing to refresh at the same instant both still end up writing a valid
# fresh token, so no cross-process lock is needed.
_CACHE_FILE = CACHE_DIR / "azure_token_cache.json"


def _read_cache() -> dict:
    try:
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return {"token": None, "ts": 0.0}


def _write_cache(token: str, ts: float) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = _CACHE_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump({"token": token, "ts": ts}, f)
    os.replace(tmp_path, _CACHE_FILE)


@router.get("/api/azure-token", response_class=PlainTextResponse)
async def azure_token() -> PlainTextResponse:
    """Return a short-lived Azure Speech token so the key never reaches the client.

    The WebGL client calls this and sends `Authorization: Bearer <token>` to Azure
    Speech (STT/TTS) instead of embedding the subscription key.
    """
    if not AZURE_SPEECH_KEY:
        logger.error("[azure-token] AZURE_SPEECH_KEY is not set in the environment.")
        raise HTTPException(status_code=500, detail="Azure Speech key not configured.")

    now = time.time()
    cache = _read_cache()
    if not cache.get("token") or now - cache.get("ts", 0.0) > _TOKEN_TTL_SECONDS:
        url = f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url, headers={"Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY}
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error(f"[azure-token] Failed to fetch token: {exc}")
            raise HTTPException(status_code=502, detail="Failed to fetch Azure token.")

        cache = {"token": response.text, "ts": now}
        _write_cache(cache["token"], cache["ts"])
        logger.debug("[azure-token] Refreshed Azure Speech token.")

    return PlainTextResponse(content=cache["token"], media_type="text/plain")
