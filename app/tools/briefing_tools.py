"""
Phase 10 — Sabah Brifingi / Günlük Özet.

get_daily_briefing: Hava durumu, sistem durumu ve bugüne ait bekleyen
hatırlatıcıları tek bir sesli/metinsel özet olarak birleştirir.
"""

import os
from datetime import datetime
from typing import Dict, Optional

import requests

from app.tools.reminder_tools import list_reminders
from app.tools.system_tools import get_system_info

_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
_DEFAULT_CITY = "Istanbul"


def _get_weather(city: str) -> str:
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Hava durumu bilgisi yok (WEATHER_API_KEY tanımlı değil)."
    try:
        resp = requests.get(
            _WEATHER_URL,
            params={"q": city, "appid": api_key, "units": "metric", "lang": "tr"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        return f"{city}: {desc}, {temp:.0f}°C (hissedilen {feels:.0f}°C)"
    except requests.RequestException as exc:
        return f"Hava durumu alınamadı: {exc}"
    except (KeyError, IndexError):
        return "Hava durumu verisi anlaşılamadı."


def get_daily_briefing(city: Optional[str] = None) -> Dict[str, str]:
    """
    Hava durumu, CPU/RAM/Disk özeti ve bugüne ait bekleyen hatırlatıcıları
    tek bir sözlük olarak döndürür.
    """
    target_city = city or os.getenv("WEATHER_CITY", _DEFAULT_CITY)
    weather = _get_weather(target_city)

    sys_info = get_system_info()
    sistem = (
        f"CPU %{sys_info['cpu_percent']}, RAM %{sys_info['ram_percent']}, "
        f"Disk %{sys_info['disk_percent']}"
    )

    today = datetime.now().strftime("%Y-%m-%d")
    todays_reminders = [r for r in list_reminders() if r["zaman"].startswith(today)]
    if todays_reminders:
        hatirlaticilar = "; ".join(f"{r['zaman'][11:]} - {r['mesaj']}" for r in todays_reminders)
    else:
        hatirlaticilar = "Bugün için bekleyen hatırlatıcı yok."

    return {
        "hava_durumu": weather,
        "sistem_durumu": sistem,
        "hatırlatıcılar": hatirlaticilar,
    }
