import os
import logging
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from logging.handlers import TimedRotatingFileHandler

class Logger:
    def __init__(self, name: str = None):
        """Logger with rich console and daily developer log files."""
        self.console = Console()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # Set log directory
        desktop_path = Path.home() / "Desktop"
        log_dir = desktop_path / "AIアバターSTELLAデモ版" / "logs" / "dev"
        os.makedirs(log_dir, exist_ok=True)

        # Developer file log: daily, named with date
        dev_log_path = log_dir / "stellar_developer用.log"
        dev_handler = TimedRotatingFileHandler(
            filename=str(dev_log_path),
            when="midnight",
            backupCount=30,  # Keep logs for 30 days
            encoding="utf-8",
            utc=False
        )
        dev_handler.suffix = "%Y-%m-%d"  # 👈 Add date to filename
        dev_handler.setLevel(logging.DEBUG)
        dev_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))

        # Console handler
        rich_handler = RichHandler(console=self.console, show_time=True, show_level=True, show_path=False)
        rich_handler.setLevel(logging.DEBUG)

        # Attach both
        self.logger.addHandler(rich_handler)
        self.logger.addHandler(dev_handler)

    def debug(self, msg: str): self.logger.debug(msg)
    def info(self, msg: str): self.logger.info(msg)
    def warning(self, msg: str): self.logger.warning(msg)
    def error(self, msg: str): self.logger.error(msg)
    def critical(self, msg: str): self.logger.critical(msg)

# Global instance
logger = Logger(name="AIServerLogger")
