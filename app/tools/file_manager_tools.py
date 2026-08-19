"""
Phase 5 — Klasör yönetimi araçları.

Agent'ın çok adımlı görevlerde klasörlere göz atabilmesi,
yeni klasör oluşturabilmesi için.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

_COMMON: Dict[str, Path] = {
    "desktop":      Path.home() / "Desktop",
    "masaüstü":     Path.home() / "Desktop",
    "downloads":    Path.home() / "Downloads",
    "indirilenler": Path.home() / "Downloads",
    "documents":    Path.home() / "Documents",
    "belgeler":     Path.home() / "Documents",
    "pictures":     Path.home() / "Pictures",
    "resimler":     Path.home() / "Pictures",
    "music":        Path.home() / "Music",
    "müzik":        Path.home() / "Music",
    "videos":       Path.home() / "Videos",
    "home":         Path.home(),
    "ev":           Path.home(),
}


def get_common_path(location: str) -> str:
    """Desktop, Downloads, Documents gibi yaygın klasörlerin tam yolunu döndürür."""
    key = location.strip().lower()
    path = _COMMON.get(key)
    if path is None:
        valid = ", ".join(sorted({k for k in _COMMON if not k.startswith("/")}))
        raise ValueError(f"'{location}' tanınan bir konum değil. Geçerliler: {valid}")
    return str(path)


def list_directory(path: str, max_items: int = 60) -> List[Dict[str, str]]:
    """Bir klasördeki dosya ve alt klasörleri listeler (ad, tür, uzantı, boyut, tam yol)."""
    key = path.strip().lower()
    resolved = _COMMON.get(key, Path(path))

    if not resolved.exists():
        raise FileNotFoundError(f"'{path}' bulunamadı.")
    if not resolved.is_dir():
        raise ValueError(f"'{path}' bir dosya, klasör değil.")

    entries: List[Dict[str, str]] = []
    # Klasörler önce, sonra dosyalar; alfabetik
    items = sorted(resolved.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    for item in items:
        try:
            if item.is_dir():
                entries.append({
                    "ad": item.name, "tür": "klasör",
                    "uzantı": "-", "boyut": "-",
                    "yol": str(item),
                })
            else:
                entries.append({
                    "ad": item.name, "tür": "dosya",
                    "uzantı": item.suffix.lower() or "-",
                    "boyut": _fmt_size(item.stat().st_size),
                    "yol": str(item),
                })
        except (PermissionError, OSError):
            continue
        if len(entries) >= max_items:
            break

    return entries


def create_folder(folder_name: str, parent_path: Optional[str] = None) -> str:
    """
    Yeni bir klasör oluşturur.
    parent_path verilmezse Masaüstü'nde oluşturur.
    """
    if parent_path:
        key = parent_path.strip().lower()
        parent = _COMMON.get(key, Path(parent_path))
    else:
        parent = Path.home() / "Desktop"

    new_folder = parent / folder_name
    if new_folder.exists():
        raise FileExistsError(f"'{new_folder}' zaten mevcut.")

    new_folder.mkdir(parents=True)
    return str(new_folder)


def _fmt_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"
