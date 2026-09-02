"""
Phase 10 — Hatırlatıcı & Alarm tool'ları.

set_reminder    : Doğal dil zaman ifadesiyle ('yarın 15:00', '10 dakika sonra') hatırlatıcı kurar.
list_reminders  : Bekleyen hatırlatıcıları listeler.
cancel_reminder : Bir hatırlatıcıyı iptal eder.
"""

import re
from datetime import datetime
from typing import Dict, List

import dateparser

from app.services.reminder_service import get_reminder_service

_HAS_RELATIVE = re.compile(r"\b(sonra|önce|once)\b", re.IGNORECASE)
_HAS_SAAT = re.compile(r"\bsaat\b", re.IGNORECASE)


def _parse_when(when: str) -> datetime:
    """
    'yarın 15:00', 'yarın saat 15:00', '10 dakika sonra' gibi doğal dil
    zaman ifadelerini datetime nesnesine çevirir.
    """
    settings = {"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()}
    candidates = []
    # dateparser 'saat' kelimesini yanlış yorumlayabiliyor; mutlak zamanlarda önce onu çıkarıp deniyoruz.
    if _HAS_SAAT.search(when) and not _HAS_RELATIVE.search(when):
        candidates.append(_HAS_SAAT.sub("", when).strip())
    candidates.append(when)

    for candidate in candidates:
        parsed = dateparser.parse(candidate, languages=["tr"], settings=settings)
        if parsed:
            return parsed

    raise ValueError(f"'{when}' zaman ifadesi anlaşılamadı. Örnek: 'yarın 15:00', '10 dakika sonra'")


def set_reminder(message: str, when: str) -> Dict[str, str]:
    """Belirtilen doğal dil zaman ifadesinde tetiklenecek bir hatırlatıcı kurar."""
    if not message or not message.strip():
        raise ValueError("Hatırlatıcı mesajı boş olamaz.")

    parsed_when = _parse_when(when)
    if parsed_when <= datetime.now():
        raise ValueError(f"'{when}' geçmişte bir zaman ifade ediyor. Gelecekteki bir zaman belirtin.")

    reminder = get_reminder_service().add(message.strip(), parsed_when)
    return {
        "id": reminder["id"],
        "mesaj": reminder["mesaj"],
        "zaman": reminder["zaman"],
    }


def list_reminders() -> List[Dict[str, str]]:
    """Bekleyen (henüz tetiklenmemiş) tüm hatırlatıcıları listeler."""
    return [
        {"id": r["id"], "mesaj": r["mesaj"], "zaman": r["zaman"]}
        for r in get_reminder_service().list_active()
    ]


def cancel_reminder(reminder_id: str) -> str:
    """Belirtilen ID'ye sahip hatırlatıcıyı iptal eder."""
    if get_reminder_service().cancel(reminder_id.strip()):
        return f"'{reminder_id}' hatırlatıcısı iptal edildi."
    raise KeyError(f"'{reminder_id}' ID'li hatırlatıcı bulunamadı.")
