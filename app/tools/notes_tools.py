"""
Phase 10 — Hızlı Not Alma.

add_note    : data/notes.md dosyasına zaman damgasıyla not ekler.
list_notes  : Kayıtlı notları (isteğe bağlı etikete göre) listeler.
search_notes: Notlar içinde basit metin araması yapar.
"""

import re
import time
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_NOTES_FILE = _DATA_DIR / "notes.md"

_ENTRY_PATTERN = re.compile(
    r"^- \[(?P<zaman>.+?)\](?: \[(?P<tag>.+?)\])? (?P<icerik>.+)$"
)


def _ensure_file() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _NOTES_FILE.exists():
        _NOTES_FILE.write_text("# Notlar\n\n", encoding="utf-8")


def _read_entries() -> List[Dict[str, str]]:
    if not _NOTES_FILE.exists():
        return []
    entries: List[Dict[str, str]] = []
    for line in _NOTES_FILE.read_text(encoding="utf-8").splitlines():
        match = _ENTRY_PATTERN.match(line)
        if match:
            entries.append({
                "zaman": match.group("zaman"),
                "tag": match.group("tag") or "",
                "içerik": match.group("icerik"),
            })
    return entries


def add_note(content: str, tag: Optional[str] = None) -> str:
    """Zaman damgalı bir not ekler ve data/notes.md dosyasına kaydeder."""
    if not content or not content.strip():
        raise ValueError("Not içeriği boş olamaz.")

    _ensure_file()
    timestamp = time.strftime("%Y-%m-%d %H:%M")
    tag_part = f" [{tag.strip()}]" if tag else ""
    line = f"- [{timestamp}]{tag_part} {content.strip()}\n"

    try:
        with _NOTES_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError as exc:
        raise RuntimeError(f"Not kaydedilemedi: {exc}") from exc

    return f"Not kaydedildi: '{content.strip()[:60]}'"


def list_notes(tag: Optional[str] = None, limit: int = 10) -> List[Dict[str, str]]:
    """Kayıtlı notları en yeniden eskiye doğru listeler; tag verilirse filtreler."""
    entries = _read_entries()
    if tag:
        entries = [e for e in entries if e["tag"].lower() == tag.strip().lower()]
    return list(reversed(entries))[:limit]


def search_notes(query: str) -> List[Dict[str, str]]:
    """Not içeriğinde basit (büyük/küçük harf duyarsız) metin araması yapar."""
    if not query or not query.strip():
        raise ValueError("Arama sorgusu boş olamaz.")
    needle = query.strip().lower()
    entries = _read_entries()
    matches = [e for e in entries if needle in e["içerik"].lower()]
    return list(reversed(matches))
