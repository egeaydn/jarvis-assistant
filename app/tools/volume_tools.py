"""
Phase 10 — Ses Seviyesi Kontrolü.

set_volume, mute_volume, get_volume — pycaw (Windows Core Audio API) üzerinden.
"""

from typing import Dict

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


def _get_volume_interface() -> IAudioEndpointVolume:
    try:
        speakers = AudioUtilities.GetSpeakers()
        return speakers.EndpointVolume
    except Exception as exc:
        raise RuntimeError(f"Ses arayüzüne erişilemedi: {exc}") from exc


def set_volume(percent: int) -> str:
    """Sistem ses seviyesini yüzde (0-100) olarak ayarlar."""
    if not 0 <= percent <= 100:
        raise ValueError("percent 0 ile 100 arasında olmalı.")

    volume = _get_volume_interface()
    try:
        volume.SetMasterVolumeLevelScalar(percent / 100, None)
    except Exception as exc:
        raise RuntimeError(f"Ses seviyesi ayarlanamadı: {exc}") from exc
    return f"Ses seviyesi %{percent} olarak ayarlandı."


def mute_volume(mute: bool = True) -> str:
    """Sistem sesini sessize alır veya açar."""
    volume = _get_volume_interface()
    try:
        volume.SetMute(1 if mute else 0, None)
    except Exception as exc:
        raise RuntimeError(f"Sessiz modu değiştirilemedi: {exc}") from exc
    return "Ses sessize alındı." if mute else "Ses açıldı."


def get_volume() -> Dict[str, object]:
    """Mevcut ses seviyesini (%) ve sessiz durumunu döndürür."""
    volume = _get_volume_interface()
    try:
        level = round(volume.GetMasterVolumeLevelScalar() * 100)
        muted = bool(volume.GetMute())
    except Exception as exc:
        raise RuntimeError(f"Ses bilgisi okunamadı: {exc}") from exc
    return {"seviye": level, "sessiz": muted}
