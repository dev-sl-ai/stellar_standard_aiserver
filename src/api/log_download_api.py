import io
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import List, Tuple

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.helpers.log_paths import DEV_LOG_DIR, UNITY_LOG_DIR, USER_LOG_DIR
from src.helpers.logger import logger

router = APIRouter()

# Active (un-rotated) developer log; rotated backups are "<name>.YYYY-MM-DD".
_DEV_LOG_BASENAME = "stellar_developer用.log"
_DATE_FMT = "%Y-%m-%d"


def _parse_range(start: str, end: str) -> Tuple[date, date]:
    """Validate the YYYY-MM-DD range, returning (start, end) with start <= end."""
    try:
        start_date = datetime.strptime(start, _DATE_FMT).date()
        end_date = datetime.strptime(end, _DATE_FMT).date()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="日付は YYYY-MM-DD 形式で指定してください。")
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="開始日は終了日以前にしてください。")
    return start_date, end_date


def _in_range(d: date, start: date, end: date) -> bool:
    return start <= d <= end


def _collect_unity(start: date, end: date) -> List[Tuple[Path, str]]:
    """Unity files are named <sessionId>_<YYYY-MM-DD>.log."""
    selected: List[Tuple[Path, str]] = []
    if not UNITY_LOG_DIR.exists():
        return selected
    for f in UNITY_LOG_DIR.glob("*.log"):
        suffix = f.stem.rsplit("_", 1)[-1]  # the <date> part
        try:
            file_date = datetime.strptime(suffix, _DATE_FMT).date()
        except ValueError:
            continue
        if _in_range(file_date, start, end):
            selected.append((f, f"unity/{f.name}"))
    return selected


def _collect_server(start: date, end: date) -> List[Tuple[Path, str]]:
    """Dev rotating log (filtered by rotation-date suffix) + user logs (by mtime)."""
    selected: List[Tuple[Path, str]] = []
    today = date.today()

    if DEV_LOG_DIR.exists():
        for f in DEV_LOG_DIR.glob(f"{_DEV_LOG_BASENAME}*"):
            if f.name == _DEV_LOG_BASENAME:
                # Active file holds today's entries.
                if _in_range(today, start, end):
                    selected.append((f, f"dev/{f.name}"))
                continue
            suffix = f.name[len(_DEV_LOG_BASENAME) + 1:]  # strip "<name>."
            try:
                file_date = datetime.strptime(suffix, _DATE_FMT).date()
            except ValueError:
                continue
            if _in_range(file_date, start, end):
                selected.append((f, f"dev/{f.name}"))

    if USER_LOG_DIR.exists():
        # User logs have no date in the filename -> filter by modification time.
        for f in USER_LOG_DIR.glob("*.log"):
            file_date = datetime.fromtimestamp(f.stat().st_mtime).date()
            if _in_range(file_date, start, end):
                selected.append((f, f"user/{f.name}"))

    return selected


@router.get("/api/logs/download")
async def download_logs(
    type: str = Query(..., pattern="^(unity|server)$"),
    start: str = Query(...),
    end: str = Query(...),
):
    """Stream a ZIP of the requested log type within the given date range."""
    start_date, end_date = _parse_range(start, end)

    if type == "unity":
        files = _collect_unity(start_date, end_date)
    else:
        files = _collect_server(start_date, end_date)

    if not files:
        raise HTTPException(status_code=404, detail="指定期間のログが見つかりませんでした。")

    buffer = io.BytesIO()
    try:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, arcname in files:
                zf.write(path, arcname)
    except OSError as exc:
        logger.error(f"[log-download] Failed to build zip for {type}: {exc}")
        raise HTTPException(status_code=500, detail="ログの圧縮中にエラーが発生しました。")

    buffer.seek(0)
    filename = f"{type}_logs_{start}_to_{end}.zip"
    logger.info(f"[log-download] {type}: {len(files)} file(s) -> {filename}")
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
