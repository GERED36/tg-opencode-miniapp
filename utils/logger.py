import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = LOG_DIR / "bot.log"


class PollFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "/agent/poll" in msg or "/agent/response" in msg or "/agent/register" in msg:
            return False
        return True


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        str(LOG_FILE), maxBytes=5_000_000, backupCount=2, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    aiohttp_logger = logging.getLogger("aiohttp.access")
    aiohttp_logger.addFilter(PollFilter())
    aiohttp_logger.setLevel(logging.INFO)
