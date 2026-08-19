"""
Phase 5 — Genişletilmiş klasör/dosya yönetimi araçları.

Yeni tool'lar:
    move_file(src, dst)                  — Dosya taşır (güvenlik onayı ile)
    copy_file(src, dst)                  — Dosya kopyalar
    delete_file(filepath)                — Dosya siler (güvenlik onayı ile)
    get_file_info(filepath)              — Dosya meta bilgisini döndürür
    filter_files_by_extension(path, ext) — Klasörü uzantıya göre filtreler
"""

import os
import shutil
from datetime import datetime
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


def _resolve(path: str) -> Path:
    """Kısa isimden (indirilenler) veya tam yoldan Path nesnesi üretir."""
    key = path.strip().lower()
    return _COMMON.get(key, Path(path))


# ── Mevcut tool'lar (Phase 3/4'ten geliyor) ───────────────────────────────────

def get_common_path(location: str) -> str:
    """Desktop, Downloads, Documents gibi yaygın klasörlerin tam yolunu döndürür."""
    key = location.strip().lower()
    path = _COMMON.get(key)
    if path is None:
        valid = ", ".join(sorted({k for k in _COMMON}))
        raise ValueError(f"'{location}' tanınan bir konum değil. Geçerliler: {valid}")
    return str(path)


def list_directory(path: str, max_items: int = 60) -> List[Dict[str, str]]:
    """Bir klasördeki dosya ve alt klasörleri listeler (ad, tür, uzantı, boyut, tam yol)."""
    resolved = _resolve(path)

    if not resolved.exists():
        raise FileNotFoundError(f"'{path}' bulunamadı.")
    if not resolved.is_dir():
        raise ValueError(f"'{path}' bir dosya, klasör değil.")

    entries: List[Dict[str, str]] = []
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
        parent = _resolve(parent_path)
    else:
        parent = Path.home() / "Desktop"

    new_folder = parent / folder_name
    if new_folder.exists():
        raise FileExistsError(f"'{new_folder}' zaten mevcut.")

    new_folder.mkdir(parents=True)
    return str(new_folder)


# ── Phase 5 — Yeni tool'lar ───────────────────────────────────────────────────

def move_file(src: str, dst: str) -> str:
    """
    Bir dosyayı veya klasörü kaynak yoldan hedef yola taşır.
    dst bir klasör yolu ise dosyayı o klasörün içine taşır.

    ⚠️ Güvenlik onayı gerektiren işlem (agent.py tarafından kontrol edilir).
    """
    src_path = _resolve(src)
    dst_path = _resolve(dst)

    if not src_path.exists():
        raise FileNotFoundError(f"Kaynak bulunamadı: '{src}'")

    # Hedef bir klasörse dosyayı içine taşı
    if dst_path.is_dir():
        dst_path = dst_path / src_path.name

    shutil.move(str(src_path), str(dst_path))
    return f"'{src_path.name}' → '{dst_path}' taşındı."


def copy_file(src: str, dst: str) -> str:
    """
    Bir dosyayı kaynak yoldan hedef yola kopyalar.
    dst bir klasör yolu ise dosyayı o klasörün içine kopyalar.
    """
    src_path = _resolve(src)
    dst_path = _resolve(dst)

    if not src_path.exists():
        raise FileNotFoundError(f"Kaynak bulunamadı: '{src}'")
    if src_path.is_dir():
        raise ValueError("Klasör kopyalama desteklenmiyor. Sadece dosya kopyalayabilirsiniz.")

    # Hedef bir klasörse dosyayı içine kopyala
    if dst_path.is_dir():
        dst_path = dst_path / src_path.name

    shutil.copy2(str(src_path), str(dst_path))
    return f"'{src_path.name}' → '{dst_path}' kopyalandı."


def delete_file(filepath: str) -> str:
    """
    Belirtilen dosyayı kalıcı olarak siler.

    ⚠️ Güvenlik onayı gerektiren işlem (agent.py tarafından kontrol edilir).
    """
    path = _resolve(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: '{filepath}'")
    if path.is_dir():
        raise ValueError(f"'{filepath}' bir klasör. Klasör silme desteklenmiyor.")

    path.unlink()
    return f"'{path.name}' silindi."


def get_file_info(filepath: str) -> Dict[str, str]:
    """
    Bir dosya veya klasör hakkında meta bilgi döndürür.
    (ad, tür, boyut, uzantı, oluşturma tarihi, değiştirilme tarihi, tam yol)
    """
    path = _resolve(filepath)

    if not path.exists():
        raise FileNotFoundError(f"'{filepath}' bulunamadı.")

    stat = path.stat()
    created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M")
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

    if path.is_dir():
        try:
            item_count = sum(1 for _ in path.iterdir())
        except PermissionError:
            item_count = "?"
        return {
            "ad": path.name,
            "tür": "klasör",
            "içerik_sayısı": str(item_count),
            "oluşturulma": created,
            "değiştirilme": modified,
            "tam_yol": str(path),
        }

    return {
        "ad": path.name,
        "tür": "dosya",
        "uzantı": path.suffix.lower() or "-",
        "boyut": _fmt_size(stat.st_size),
        "oluşturulma": created,
        "değiştirilme": modified,
        "tam_yol": str(path),
    }


def filter_files_by_extension(path: str, extension: str) -> List[Dict[str, str]]:
    """
    Bir klasördeki dosyaları uzantıya göre filtreler.

    Örnek: filter_files_by_extension("indirilenler", ".pdf")
    Döndürür: [{ad, boyut, yol}, ...]
    """
    resolved = _resolve(path)

    if not resolved.exists():
        raise FileNotFoundError(f"'{path}' bulunamadı.")
    if not resolved.is_dir():
        raise ValueError(f"'{path}' bir klasör değil.")

    # Uzantıyı normalize et: "pdf" → ".pdf"
    ext = extension.strip().lower()
    if ext and not ext.startswith("."):
        ext = "." + ext

    results: List[Dict[str, str]] = []
    try:
        for item in sorted(resolved.iterdir(), key=lambda p: p.name.lower()):
            if item.is_file() and item.suffix.lower() == ext:
                try:
                    results.append({
                        "ad": item.name,
                        "boyut": _fmt_size(item.stat().st_size),
                        "yol": str(item),
                    })
                except (PermissionError, OSError):
                    continue
    except PermissionError:
        raise PermissionError(f"'{path}' klasörüne erişim reddedildi.")

    return results


# ── Yardımcı ──────────────────────────────────────────────────────────────────

def _fmt_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"
