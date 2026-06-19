import os
from pathlib import Path

# Single source of truth for where server logs are written.
# Defaults to the on-desktop folder (unchanged Windows/PyInstaller behavior);
# override with the LOG_DIR env var (e.g. /app/logs in Docker, bind-mounted to the host).
_DEFAULT_BASE = Path.home() / "Desktop" / "AIアバターSTELLAデモ版" / "logs"
LOGS_BASE_DIR = Path(os.getenv("LOG_DIR", str(_DEFAULT_BASE)))

DEV_LOG_DIR = LOGS_BASE_DIR / "dev"
USER_LOG_DIR = LOGS_BASE_DIR / "user"
UNITY_LOG_DIR = LOGS_BASE_DIR / "unity"
