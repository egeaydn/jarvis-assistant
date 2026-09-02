"""
Phase 10 — Pano geçmişi izleme servisi.

Arka planda (ayrı thread) sistem panosunu periyodik olarak kontrol eder,
değişiklik olursa dairesel bir tampon içine ekler ve diske (data/clipboard_history.json)
kalıcı olarak kaydeder.
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from pathlib import Path
from typing import Deque, Dict, List, Optional

import pyperclip

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_HISTORY_FILE = _DATA_DIR / "clipboard_history.json"
_MAX_HISTORY = 50
_POLL_INTERVAL = 1.0


class ClipboardListener:
    """Panoyu polling ile izleyen thread-safe servis."""

    def __init__(self, max_history: int = _MAX_HISTORY, poll_interval: float = _POLL_INTERVAL) -> None:
        self._lock = threading.RLock()
        self._history: Deque[Dict[str, str]] = deque(maxlen=max_history)
        self._poll_interval = poll_interval
        self._last_value: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._load()

    def start(self) -> None:
        """Arka plan izleme thread'ini başlatır (zaten çalışıyorsa tekrar başlatmaz)."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """İzleme thread'ini durdurur."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def get_history(self, limit: int = 5) -> List[Dict[str, str]]:
        with self._lock:
            items = list(self._history)
        return items[-limit:][::-1]

    # ── İç mantık ─────────────────────────────────────────────────────────────

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                current = pyperclip.paste()
            except Exception:
                current = None

            if current and current != self._last_value:
                self._last_value = current
                with self._lock:
                    self._history.append({
                        "içerik": current,
                        "zaman": time.strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    self._save()

            self._stop_event.wait(self._poll_interval)

    def _load(self) -> None:
        if not _HISTORY_FILE.exists():
            return
        try:
            data = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
            for item in data:
                self._history.append(item)
        except (json.JSONDecodeError, OSError):
            pass

    def _save(self) -> None:
        try:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            _HISTORY_FILE.write_text(
                json.dumps(list(self._history), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass


# ── Modül seviyesi tekil örnek (singleton) ────────────────────────────────────
_listener = ClipboardListener()


def start_clipboard_listener() -> None:
    """Uygulama başlangıcında çağrılarak arka plan izlemeyi başlatır."""
    _listener.start()


def stop_clipboard_listener() -> None:
    _listener.stop()


def get_clipboard_history(limit: int = 5) -> List[Dict[str, str]]:
    """En son N pano kaydını (en yeni önce) döndürür."""
    return _listener.get_history(limit=limit)
