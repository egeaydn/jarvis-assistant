import os
import shutil
import subprocess
from typing import Dict, List, Optional

import psutil


APP_ALIASES: Dict[str, List[str]] = {
    "chrome":    ["chrome", "google chrome", "googlechrome", "chrome.exe"],
    "vscode":    ["vscode", "visual studio code", "code", "vs code", "code.exe"],
    "notepad":   ["notepad", "notepad.exe"],
    "discord":   ["discord", "discord.exe"],
    "spotify":   ["spotify", "spotify.exe"],
    "steam":     ["steam", "steam.exe"],
    "explorer":  ["explorer", "dosyagezgini", "file explorer", "dosya gezgini", "explorer.exe"],
    "edge":      ["edge", "microsoft edge", "msedge", "msedge.exe"],
    "notepad++": ["notepad++", "notepadpp", "npp"],
    "calculator":["calculator", "hesap makinesi", "calc", "calc.exe"],
    "paint":     ["paint", "mspaint", "mspaint.exe"],
    "wordpad":   ["wordpad", "wordpad.exe"],
}

# Her uygulama için psutil üzerinden aranacak process isimleri
PROCESS_NAMES: Dict[str, List[str]] = {
    "chrome":    ["chrome.exe"],
    "vscode":    ["code.exe"],
    "notepad":   ["notepad.exe"],
    "discord":   ["discord.exe", "discordptb.exe", "discordcanary.exe"],
    "spotify":   ["spotify.exe"],
    "steam":     ["steam.exe"],
    "explorer":  ["explorer.exe"],
    "edge":      ["msedge.exe"],
    "notepad++": ["notepad++.exe"],
    "calculator":["calculatorapp.exe", "calc.exe"],
    "paint":     ["mspaint.exe"],
    "wordpad":   ["wordpad.exe"],
}

# Ortam değişkeni destekli aday yollar
_LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
_APPDATA      = os.environ.get("APPDATA", "")
_PROGRAMFILES = os.environ.get("ProgramFiles", r"C:\Program Files")
_PROGRAMFILES86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

APP_PATHS: Dict[str, List[str]] = {
    "chrome": [
        rf"{_PROGRAMFILES}\Google\Chrome\Application\chrome.exe",
        rf"{_PROGRAMFILES86}\Google\Chrome\Application\chrome.exe",
    ],
    "vscode": [
        rf"{_PROGRAMFILES}\Microsoft VS Code\Code.exe",
        rf"{_PROGRAMFILES86}\Microsoft VS Code\Code.exe",
    ],
    "notepad":    ["notepad.exe"],
    "discord":    [rf"{_LOCALAPPDATA}\Discord\Update.exe"],
    "spotify":    [rf"{_APPDATA}\Spotify\Spotify.exe"],
    "steam": [
        rf"{_PROGRAMFILES86}\Steam\steam.exe",
        rf"{_PROGRAMFILES}\Steam\steam.exe",
    ],
    "explorer":   ["explorer.exe"],
    "edge": [
        rf"{_PROGRAMFILES}\Microsoft\Edge\Application\msedge.exe",
        rf"{_PROGRAMFILES86}\Microsoft\Edge\Application\msedge.exe",
    ],
    "notepad++": [
        rf"{_PROGRAMFILES}\Notepad++\notepad++.exe",
        rf"{_PROGRAMFILES86}\Notepad++\notepad++.exe",
    ],
    "calculator": ["calc.exe"],
    "paint":      ["mspaint.exe"],
    "wordpad":    ["wordpad.exe"],
}


def _normalize_app_name(app_name: str) -> str:
    """Uygulama adını standart formata çevirir."""
    cleaned = app_name.strip().lower().replace(" ", "")
    return cleaned


def _resolve_executable(app_name: str) -> Optional[str]:
    """Windows üzerinde çalıştırılabilir uygulama yolunu bulur."""
    normalized = _normalize_app_name(app_name)

    app_key = None
    for key, aliases in APP_ALIASES.items():
        if normalized in [_normalize_app_name(a) for a in aliases]:
            app_key = key
            break

    if app_key is None:
        return None

    # Discord: update.exe üzerinden başlat
    if app_key == "discord":
        update_exe = rf"{os.environ.get('LOCALAPPDATA', '')}\Discord\Update.exe"
        if os.path.exists(update_exe):
            return update_exe
        return shutil.which("discord")

    for candidate in APP_PATHS.get(app_key, []):
        if os.path.exists(candidate):
            return candidate

    # PATH'te basit yürütülebilir isimle ara (Microsoft Store uygulamaları vb.)
    for proc_name in PROCESS_NAMES.get(app_key, []):
        found = shutil.which(proc_name)
        if found:
            return found

    return None


def open_application(app_name: str) -> bool:
    """Belirtilen Windows uygulamasını açar."""
    normalized = _normalize_app_name(app_name)
    app_key = next(
        (k for k, aliases in APP_ALIASES.items()
         if normalized in [_normalize_app_name(a) for a in aliases]),
        None,
    )

    executable = _resolve_executable(app_name)
    if not executable:
        raise FileNotFoundError(f"'{app_name}' uygulaması bulunamadı.")

    try:
        # Discord, Update.exe üzerinden özel argümanla başlatılır
        if app_key == "discord":
            subprocess.Popen([executable, "--processStart", "Discord.exe"], shell=False)
        else:
            subprocess.Popen([executable], shell=False)
        return True
    except OSError as exc:
        raise RuntimeError(f"'{app_name}' başlatılamadı: {exc}") from exc


def close_application(app_name: str) -> bool:
    """Çalışan bir uygulamayı ismiyle kapatır."""
    normalized = _normalize_app_name(app_name)

    # Canonical key'i bul
    target_processes: Optional[List[str]] = None
    for app_key, aliases in APP_ALIASES.items():
        if normalized in [_normalize_app_name(a) for a in aliases]:
            target_processes = PROCESS_NAMES.get(app_key, [])
            break

    if not target_processes:
        proc_name = normalized if normalized.endswith(".exe") else normalized + ".exe"
        target_processes = [proc_name]

    killed = False
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() in [p.lower() for p in target_processes]:
                proc.terminate()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if not killed:
        raise RuntimeError(f"'{app_name}' çalışır durumda bulunamadı.")

    return True


def get_running_apps() -> List[str]:
    """Sistemde çalışan benzersiz uygulama (process) isimlerini döndürür."""
    seen: set = set()
    apps: List[str] = []
    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info["name"]
            if name and name.lower() not in seen:
                seen.add(name.lower())
                apps.append(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return sorted(apps, key=str.lower)
