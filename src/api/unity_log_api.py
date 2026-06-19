import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.helpers.logger import logger
from src.helpers.log_paths import LOGS_BASE_DIR, UNITY_LOG_DIR

router = APIRouter()

# Guard against path traversal / odd characters in the client-supplied session id.
_SAFE_SESSION_ID = re.compile(r"[^A-Za-z0-9_.-]")
_MAX_LINES_PER_REQUEST = 1000


class UnityLogPayload(BaseModel):
    """JSON body posted by the WebGL WriteLogController flush coroutine."""
    sessionId: str = Field(..., min_length=1, max_length=200)
    lines: List[str] = Field(default_factory=list)


def _sanitize_session_id(session_id: str) -> str:
    """Strip anything that could escape the log directory."""
    cleaned = _SAFE_SESSION_ID.sub("_", session_id.strip())
    return cleaned or "unknown"


def _log_file_for(session_id: str) -> Path:
    date = datetime.now().strftime("%Y-%m-%d")
    return UNITY_LOG_DIR / f"{session_id}_{date}.log"


@router.post("/api/unity-log")
async def receive_unity_log(payload: UnityLogPayload):
    """Append Unity WebGL DevLog lines to a per-session file on the server.

    The WebGL build cannot persist files (they only reach IndexedDB), so it
    batches DevLog lines and POSTs them here. We append them verbatim so the
    Unity client log sits alongside the server's own logs.
    """
    if not payload.lines:
        return {"status": "ok", "written": 0}

    session_id = _sanitize_session_id(payload.sessionId)
    lines = payload.lines[:_MAX_LINES_PER_REQUEST]

    try:
        os.makedirs(UNITY_LOG_DIR, exist_ok=True)
        log_file = _log_file_for(session_id)
        with open(log_file, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line.rstrip("\n") + "\n")
    except OSError as exc:
        logger.error(f"[unity-log] Failed to write log for {session_id}: {exc}")
        return {"status": "error", "written": 0}

    logger.debug(f"[unity-log] {session_id}: appended {len(lines)} line(s)")
    return {"status": "ok", "written": len(lines)}
