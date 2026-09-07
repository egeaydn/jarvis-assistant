"""Bağımsız hava durumu aracı (API key gerektirmez)."""

import json
import urllib.request
import urllib.error
from urllib.parse import quote

def get_weather(city: str) -> str:
    """
    wttr.in servisini kullanarak belirtilen şehrin anlık hava durumunu döndürür.
    API key gerektirmez, tamamen ücretsizdir.
    
    Args:
        city: Şehir adı (örn: "İstanbul", "Ankara")
        
    Returns:
        str: Okunabilir hava durumu özeti veya hata mesajı
    """
    if not city or not city.strip():
        return "Lütfen geçerli bir şehir adı belirtin."

    city_safe = quote(city.strip())
    # j1 formatı JSON çıktısı verir
    url = f"https://wttr.in/{city_safe}?format=j1"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Güncel durum
            current = data["current_condition"][0]
            temp_c = current["temp_C"]
            desc = current["lang_tr"][0]["value"] if "lang_tr" in current else current["weatherDesc"][0]["value"]
            feels_like = current["FeelsLikeC"]
            humidity = current["humidity"]
            
            return (
                f"{city.title()} için güncel hava durumu:\n"
                f"Sıcaklık: {temp_c}°C (Hissedilen: {feels_like}°C)\n"
                f"Durum: {desc}\n"
                f"Nem: %{humidity}"
            )
            
    except urllib.error.URLError as exc:
        return f"Hava durumu servisine ulaşılamadı (İnternet bağlantısını kontrol edin): {exc}"
    except Exception as exc:
        return f"Hava durumu alınırken beklenmeyen bir hata oluştu: {exc}"
