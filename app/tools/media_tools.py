"""Medya oynatma ve Spotify API entegrasyon araçları."""

import os
import pyautogui
from app.config.logger import get_logger

log = get_logger(__name__)


def play_pause_media() -> str:
    """İşletim sistemindeki varsayılan medya oynatıcıyı (Spotify, YouTube vb.) durdurur veya başlatır."""
    try:
        pyautogui.press('playpause')
        return "Medya oynatma/duraklatma tuşuna basıldı."
    except Exception as exc:
        return f"Medya kontrol hatası: {exc}"


def next_track() -> str:
    """İşletim sistemindeki varsayılan medya oynatıcıda sonraki şarkıya geçer."""
    try:
        pyautogui.press('nexttrack')
        return "Sonraki şarkıya geçildi."
    except Exception as exc:
        return f"Medya kontrol hatası: {exc}"


def previous_track() -> str:
    """İşletim sistemindeki varsayılan medya oynatıcıda önceki şarkıya geçer."""
    try:
        pyautogui.press('prevtrack')
        return "Önceki şarkıya dönüldü."
    except Exception as exc:
        return f"Medya kontrol hatası: {exc}"


def play_music_on_spotify(query: str) -> str:
    """
    Belirtilen şarkıyı/sanatçıyı Spotify API üzerinden arar ve çalmaya başlar.
    Gereksinimler: .env içerisinde SPOTIPY_CLIENT_ID ve SPOTIPY_CLIENT_SECRET
    """
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")

    if not client_id or not client_secret:
        return (
            "Spotify API bilgileri (.env içinde SPOTIPY_CLIENT_ID ve SPOTIPY_CLIENT_SECRET) eksik. "
            "Sadece standart play/pause/next komutlarını (örn: 'müziği durdur') kullanabilirsiniz."
        )

    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth

        # Kapsamlı oynatma yetkisi
        scope = "user-modify-playback-state,user-read-playback-state"
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            open_browser=False  # Sunucu modunda konsola link yazar
        ))

        # Şarkı arama
        results = sp.search(q=query, limit=1, type='track')
        tracks = results.get('tracks', {}).get('items', [])
        
        if not tracks:
            return f"'{query}' için Spotify'da sonuç bulunamadı."
            
        track = tracks[0]
        track_uri = track['uri']
        track_name = track['name']
        artist_name = track['artists'][0]['name']

        # Aktif cihazı kontrol et
        devices = sp.devices()
        active_devices = [d for d in devices.get('devices', []) if d['is_active']]
        
        device_id = None
        if not active_devices:
            # Eğer aktif yoksa ilk müsait olanı seç
            all_devices = devices.get('devices', [])
            if all_devices:
                device_id = all_devices[0]['id']
            else:
                return "Spotify açık cihaz bulunamadı. Lütfen cihazınızda Spotify'ı manuel başlatın."

        # Çalmayı başlat
        if device_id:
            sp.start_playback(device_id=device_id, uris=[track_uri])
        else:
            sp.start_playback(uris=[track_uri])
            
        return f"Spotify'da '{track_name} - {artist_name}' çalınıyor."

    except spotipy.exceptions.SpotifyException as exc:
        if exc.http_status == 403:
            return "Spotify yetkilendirme hatası. Hesabınız Spotify Premium değilse API ile doğrudan şarkı başlatılamaz."
        return f"Spotify API hatası: {exc}"
    except Exception as exc:
        log.error("Spotify entegrasyon hatasi: %s", exc)
        return f"Şarkı oynatılırken beklenmeyen bir hata oluştu: {exc}"
