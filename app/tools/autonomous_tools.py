"""
Phase 9 — Otonom Asistan Araçları.

run_terminal_command: Terminal komutları çalıştırıp hata analizi yapmak için.
organize_folder      : Dosyaları türlerine göre alt klasörlere taşımak için.
"""

import os
import shutil
import subprocess
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

# Dosya kategorileri ve ilgili uzantıları
FILE_GROUPS = {
    "Belgeler":    [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".csv", ".epub", ".rtf"],
    "Resimler":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"],
    "Arsivler":    [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Videolar":    [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "Sesler":      [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"],
    "Kurulumlar":  [".exe", ".msi", ".bat", ".cmd"],
}


def _resolve(path: str) -> Path:
    key = path.strip().lower()
    return _COMMON.get(key, Path(path))


def run_terminal_command(command: str, cwd: Optional[str] = None) -> str:
    """
    Belirtilen dizinde bir Windows terminal (PowerShell/CMD) komutu çalıştırır.
    Komutun stdout ve stderr çıktılarını döndürür.

    ⚠️ Güvenlik onayı gerektirir.
    """
    work_dir = _resolve(cwd) if cwd else Path.cwd()
    if not work_dir.exists():
        raise FileNotFoundError(f"Çalışma dizini bulunamadı: '{cwd}'")

    try:
        # PowerShell veya cmd aracılığıyla çalıştır
        res = subprocess.run(
            ["powershell", "-Command", command],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30  # Sonsuz döngü engeli
        )

        output = []
        if res.stdout and res.stdout.strip():
            output.append(f"Stdout:\n{res.stdout.strip()}")
        if res.stderr and res.stderr.strip():
            output.append(f"Stderr (Hatalar):\n{res.stderr.strip()}")

        if not output:
            return f"Komut başarıyla çalıştırıldı (çıkış kodu: {res.returncode}), çıktı üretmedi."

        return f"Çıkış Kodu: {res.returncode}\n" + "\n\n".join(output)

    except subprocess.TimeoutExpired:
        return "HATA: Komut 30 saniye içinde yanıt vermediği için zaman aşımına uğradı."
    except Exception as exc:
        return f"HATA: Komut çalıştırılamadı: {exc}"


def organize_folder(folder_path: str, rule: str = "tür") -> str:
    """
    Belirtilen klasördeki dosyaları analiz eder ve türlerine (Belgeler, Resimler vb.)
    göre gruplayarak alt klasörlere taşır.

    ⚠️ Güvenlik onayı gerektirir.
    """
    target_dir = _resolve(folder_path)
    if not target_dir.exists():
        raise FileNotFoundError(f"Klasör bulunamadı: '{folder_path}'")
    if not target_dir.is_dir():
        raise ValueError(f"'{folder_path}' bir klasör değil.")

    moved_count = 0
    moved_details = []

    # Sadece o dizindeki dosyaları al (alt klasörleri atla)
    items = [p for p in target_dir.iterdir() if p.is_file()]

    for item in items:
        ext = item.suffix.lower()
        if not ext:
            continue

        # Dosyanın hangi gruba girdiğini bul
        group_folder = "Diger"
        for folder_name, extensions in FILE_GROUPS.items():
            if ext in extensions:
                group_folder = folder_name
                break

        # Hedef klasörü oluştur
        dest_folder = target_dir / group_folder
        dest_folder.mkdir(exist_ok=True)

        dest_file = dest_folder / item.name

        # Taşıma işlemi
        try:
            # Dosya zaten hedefte yoksa taşı
            if not dest_file.exists():
                shutil.move(str(item), str(dest_file))
                moved_count += 1
                moved_details.append(f"  - '{item.name}' -> '{group_folder}/'")
        except Exception as exc:
            moved_details.append(f"  - '{item.name}' taşınırken hata: {exc}")

    if moved_count == 0:
        return f"'{target_dir.name}' klasöründe taşınacak veya düzenlenecek dosya bulunamadı."

    details_str = "\n".join(moved_details)
    return (
        f"'{target_dir.name}' klasörü başarıyla düzenlendi.\n"
        f"Toplam {moved_count} dosya taşındı:\n{details_str}"
    )
