"""
Phase 10 — Pencere Yönetimi.

maximize_window, minimize_window, close_window, list_open_windows, focus_window
"""

from typing import List

import pygetwindow as gw

from app.tools.app_tools import APP_ALIASES


def _normalize(text: str) -> str:
    return text.strip().lower().replace(" ", "")


def _find_windows(app_name: str) -> List[gw.Window]:
    """Verilen uygulama adına/alias'ına göre açık pencereleri bulur (başlık substring eşleşmesi)."""
    normalized = _normalize(app_name)

    # Alias listesini genişletiyoruz: 'chrome' -> ['chrome', 'google chrome', ...]
    search_terms = {normalized}
    for key, aliases in APP_ALIASES.items():
        normalized_aliases = [_normalize(a) for a in aliases]
        if normalized == _normalize(key) or normalized in normalized_aliases:
            search_terms.update(normalized_aliases)
            search_terms.add(_normalize(key))
            break

    try:
        all_windows = gw.getAllWindows()
    except Exception as exc:
        raise RuntimeError(f"Pencereler listelenemedi: {exc}") from exc

    matches = []
    for win in all_windows:
        if not win.title:
            continue
        title_normalized = _normalize(win.title)
        if any(term and term in title_normalized for term in search_terms):
            matches.append(win)
    return matches


def maximize_window(app_name: str) -> str:
    """Belirtilen uygulamanın penceresini tam ekran yapar."""
    windows = _find_windows(app_name)
    if not windows:
        raise RuntimeError(f"'{app_name}' icin acik pencere bulunamadi.")
    try:
        windows[0].maximize()
    except Exception as exc:
        raise RuntimeError(f"'{app_name}' penceresi buyutulemedi: {exc}") from exc
    return f"'{windows[0].title}' tam ekran yapildi."


def minimize_window(app_name: str) -> str:
    """Belirtilen uygulamanın penceresini küçültür (görev çubuğuna indirir)."""
    windows = _find_windows(app_name)
    if not windows:
        raise RuntimeError(f"'{app_name}' icin acik pencere bulunamadi.")
    try:
        windows[0].minimize()
    except Exception as exc:
        raise RuntimeError(f"'{app_name}' penceresi kucultulemedi: {exc}") from exc
    return f"'{windows[0].title}' kucultuldu."


def close_window(app_name: str) -> str:
    """Belirtilen uygulamanın penceresini kapatır (uygulamayı sonlandırmaz)."""
    windows = _find_windows(app_name)
    if not windows:
        raise RuntimeError(f"'{app_name}' icin acik pencere bulunamadi.")
    try:
        windows[0].close()
    except Exception as exc:
        raise RuntimeError(f"'{app_name}' penceresi kapatilamadi: {exc}") from exc
    return f"'{windows[0].title}' kapatildi."


def focus_window(app_name: str) -> str:
    """Belirtilen uygulamanın penceresini öne getirir ve odaklar."""
    windows = _find_windows(app_name)
    if not windows:
        raise RuntimeError(f"'{app_name}' icin acik pencere bulunamadi.")
    win = windows[0]
    try:
        if win.isMinimized:
            win.restore()
        win.activate()
    except Exception as exc:
        raise RuntimeError(f"'{app_name}' penceresine odaklanilamadi: {exc}") from exc
    return f"'{win.title}' penceresine odaklanildi."


def list_open_windows() -> List[str]:
    """Başlığı boş olmayan tüm açık pencerelerin başlıklarını döndürür."""
    try:
        all_windows = gw.getAllWindows()
    except Exception as exc:
        raise RuntimeError(f"Pencereler listelenemedi: {exc}") from exc
    return [w.title for w in all_windows if w.title and w.title.strip()]
