import glob
import os
from typing import List


def find_file(filename: str, search_dir: str = None) -> List[str]:
    """Dosya adına göre ev dizininde özyinelemeli arama yapar."""
    if not filename or not filename.strip():
        raise ValueError("Aranacak dosya adı boş olamaz.")
    base_dir = search_dir or os.path.expanduser("~")
    pattern = os.path.join(base_dir, "**", f"*{filename.strip()}*")
    try:
        return list(glob.iglob(pattern, recursive=True))[:50]
    except Exception as exc:
        raise RuntimeError(f"Dosya arama hatası: {exc}") from exc


def open_file(filepath: str) -> bool:
    """Dosyayı varsayılan Windows uygulamasıyla açar."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dosya bulunamadı: '{filepath}'")
    try:
        os.startfile(filepath)
        return True
    except OSError as exc:
        raise RuntimeError(f"Dosya açılamadı: {exc}") from exc


def search_files(pattern: str, search_dir: str = None) -> List[str]:
    """Glob pattern'e uyan dosyaları belirtilen dizinde listeler."""
    base_dir = search_dir or os.path.join(os.path.expanduser("~"), "Desktop")
    full_pattern = os.path.join(base_dir, "**", pattern)
    try:
        return list(glob.iglob(full_pattern, recursive=True))[:50]
    except Exception as exc:
        raise RuntimeError(f"Dosya arama hatası: {exc}") from exc
