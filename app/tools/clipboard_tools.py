"""
Phase 10 — Pano (Clipboard) Yönetimi.

copy_to_clipboard : Metni panoya kopyalar.
read_clipboard     : Panodaki güncel metni okur.
get_clipboard_history : Arka planda biriktirilen pano geçmişini döndürür.
"""

from typing import Dict, List

import pyperclip

from app.services.clipboard_listener import get_clipboard_history as _get_history


def copy_to_clipboard(text: str) -> str:
    """Verilen metni sistem panosuna kopyalar."""
    try:
        pyperclip.copy(text)
    except Exception as exc:
        raise RuntimeError(f"Panoya kopyalanamadı: {exc}") from exc
    return f"Panoya kopyalandı: '{text[:60]}{'...' if len(text) > 60 else ''}'"


def read_clipboard() -> Dict[str, str]:
    """Panodaki güncel metni okur."""
    try:
        content = pyperclip.paste()
    except Exception as exc:
        raise RuntimeError(f"Pano okunamadı: {exc}") from exc
    if not content:
        return {"içerik": "(Pano boş)"}
    return {"içerik": content}


def get_clipboard_history(limit: int = 5) -> List[Dict[str, str]]:
    """
    Arka planda pano değişikliklerini izleyen servisin biriktirdiği son N kaydı döndürür.
    Servis henüz başlatılmadıysa boş liste döner.
    """
    return _get_history(limit=limit)
