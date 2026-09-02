"""
Phase 10 — Hatırlatıcı & Alarm servisi.

Arka planda (ayrı thread) hatırlatıcıları periyodik kontrol eder;
zamanı gelen hatırlatıcıyı on_due callback'i (varsayılan: konsola yazdırma) ile tetikler.
Hatırlatıcılar data/reminders.json dosyasında kalıcı tutulur.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_REMINDERS_FILE = _DATA_DIR / "reminders.json"
_POLL_INTERVAL = 5.0


class ReminderService:
    """Hatırlatıcıları diskte saklayan ve zamanı gelince tetikleyen thread-safe servis."""

    def __init__(self, poll_interval: float = _POLL_INTERVAL) -> None:
        self._lock = threading.RLock()
        self._reminders: Dict[str, dict] = {}
        self._poll_interval = poll_interval
        self._on_due: Optional[Callable[[dict], None]] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._load()

    def start(self, on_due: Optional[Callable[[dict], None]] = None) -> None:
        """Arka plan kontrol thread'ini başlatır. on_due: hatırlatıcı zamanı gelince çağrılır."""
        with self._lock:
            self._on_due = on_due
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def add(self, message: str, when: datetime) -> dict:
        reminder = {
            "id": uuid.uuid4().hex[:8],
            "mesaj": message,
            "zaman": when.strftime("%Y-%m-%d %H:%M:%S"),
            "oluşturulma": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tetiklendi": False,
        }
        with self._lock:
            self._reminders[reminder["id"]] = reminder
            self._save()
        return reminder

    def list_active(self) -> List[dict]:
        with self._lock:
            items = [r for r in self._reminders.values() if not r["tetiklendi"]]
        return sorted(items, key=lambda r: r["zaman"])

    def cancel(self, reminder_id: str) -> bool:
        with self._lock:
            if reminder_id not in self._reminders:
                return False
            del self._reminders[reminder_id]
            self._save()
        return True

    # ── İç mantık ─────────────────────────────────────────────────────────────

    def _run(self) -> None:
        while not self._stop_event.is_set():
            now = datetime.now()
            due: List[dict] = []
            with self._lock:
                for reminder in self._reminders.values():
                    if reminder["tetiklendi"]:
                        continue
                    try:
                        when = datetime.strptime(reminder["zaman"], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
                    if when <= now:
                        reminder["tetiklendi"] = True
                        due.append(reminder)
                if due:
                    self._save()

            for reminder in due:
                if self._on_due:
                    try:
                        self._on_due(reminder)
                    except Exception as exc:
                        print(f"[REMINDER ERR] Callback hatasi: {exc}")
                else:
                    print(f"\n🔔 HATIRLATICI: {reminder['mesaj']}\n")

            self._stop_event.wait(self._poll_interval)

    def _load(self) -> None:
        if not _REMINDERS_FILE.exists():
            return
        try:
            data = json.loads(_REMINDERS_FILE.read_text(encoding="utf-8"))
            for item in data:
                self._reminders[item["id"]] = item
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    def _save(self) -> None:
        try:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            _REMINDERS_FILE.write_text(
                json.dumps(list(self._reminders.values()), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass


# ── Modül seviyesi tekil örnek (singleton) ────────────────────────────────────
_service = ReminderService()


def start_reminder_service(on_due: Optional[Callable[[dict], None]] = None) -> None:
    """Uygulama başlangıcında çağrılarak arka plan kontrolünü başlatır."""
    _service.start(on_due=on_due)


def stop_reminder_service() -> None:
    _service.stop()


def get_reminder_service() -> ReminderService:
    return _service
