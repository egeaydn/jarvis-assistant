"""
Jarvis — Merkezi Loglama Yapılandırması.

Tüm modüller bu modülden logger alır:
    from app.config.logger import get_logger
    log = get_logger(__name__)

Loglar hem konsola (renkli) hem de data/jarvis.log
dosyasına (RotatingFileHandler) yazılır.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parents[2] / "data"
_LOG_FILE = _LOG_DIR / "jarvis.log"
_MAX_BYTES = 1_000_000   # 1 MB
_BACKUP_COUNT = 3
_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # ── Konsol Handler ──────────────────────────────────────────────────────────
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(_FMT, _DATE_FMT))
    root.addHandler(stream_handler)

    # ── Dosya Handler (Rotating) ─────────────────────────────────────────────────
    try:
        file_handler = RotatingFileHandler(
            _LOG_FILE,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(_FMT, _DATE_FMT))
        root.addHandler(file_handler)
    except OSError as exc:
        root.warning("Log dosyasi acilamadi, yalnizca konsola yazilacak: %s", exc)

    # Üçüncü parti kütüphanelerin gürültüsünü bastır
    for noisy in ("urllib3", "httpx", "httpcore", "google", "grpc"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Verilen isim için yapılandırılmış bir Logger döndürür."""
    _configure()
    return logging.getLogger(name)
