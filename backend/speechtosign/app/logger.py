"""
logger.py — Simple timestamped logger for every request and response.
"""

import logging
from datetime import datetime

# Configure one root logger for the whole app
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",       # we build the full message ourselves
)

_log = logging.getLogger("arise_iva")


def log_request(text: str) -> None:
    """Log an incoming input sentence."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _log.info(f"[{ts}] Input: {text}")


def log_response(gloss: list[str]) -> None:
    """Log the produced ISL gloss sequence."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _log.info(f"[{ts}] Gloss: {' '.join(gloss)}")


def log_error(error: str) -> None:
    """Log an unexpected error."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _log.error(f"[{ts}] ERROR: {error}")