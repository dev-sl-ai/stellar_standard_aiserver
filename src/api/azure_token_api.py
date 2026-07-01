import time

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from src.helpers.env_loader import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION
from src.helpers.logger import logger

router = APIRouter()

# Azure issued tokens are valid for ~10 minutes; refresh after 9 to stay ahead of expiry.
_TOKEN_TTL_SECONDS = 540
_cache = {"token": None, "ts": 0.0}


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
    if not _cache["token"] or now - _cache["ts"] > _TOKEN_TTL_SECONDS:
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

        _cache.update(token=response.text, ts=now)
        logger.debug("[azure-token] Refreshed Azure Speech token.")

    return PlainTextResponse(content=_cache["token"], media_type="text/plain")
