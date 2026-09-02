"""
Phase 10 — Sistem Güç Yönetimi.

shutdown_system, restart_system, sleep_system : Güvenlik onayı gerektirir.
cancel_shutdown                                : Onay GEREKTİRMEZ (hızlı iptal).
"""

import ctypes
import subprocess
from typing import Dict


def shutdown_system(delay_seconds: int = 30) -> Dict[str, object]:
    """
    Windows'u delay_seconds kadar bekleme süresi ile kapatır.
    Bekleme süresi içinde cancel_shutdown ile iptal edilebilir.
    """
    if delay_seconds < 0:
        raise ValueError("delay_seconds negatif olamaz.")
    try:
        subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Kapatma komutu çalıştırılamadı: {exc.stderr or exc}") from exc
    return {"durum": "zamanlandı", "islem": "kapatma", "saniye": delay_seconds}


def restart_system(delay_seconds: int = 30) -> Dict[str, object]:
    """Windows'u delay_seconds kadar bekleme süresi ile yeniden başlatır."""
    if delay_seconds < 0:
        raise ValueError("delay_seconds negatif olamaz.")
    try:
        subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Yeniden başlatma komutu çalıştırılamadı: {exc.stderr or exc}") from exc
    return {"durum": "zamanlandı", "islem": "yeniden_baslatma", "saniye": delay_seconds}


def sleep_system() -> str:
    """Bilgisayarı uyku moduna alır."""
    try:
        result = ctypes.windll.powrprof.SetSuspendState(False, True, False)
    except (AttributeError, OSError) as exc:
        raise RuntimeError(f"Uyku moduna geçilemedi: {exc}") from exc
    if not result:
        raise RuntimeError("Uyku moduna geçilemedi.")
    return "Bilgisayar uyku moduna alındı."


def cancel_shutdown() -> str:
    """Zamanlanmış kapatma/yeniden başlatma işlemini iptal eder."""
    try:
        subprocess.run(["shutdown", "/a"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"İptal edilecek zamanlanmış işlem bulunamadı: {exc.stderr or exc}") from exc
    return "Zamanlanmış kapatma/yeniden başlatma iptal edildi."
