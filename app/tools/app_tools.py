import os
import shutil
import subprocess
from typing import Dict, List, Optional

import psutil


APP_ALIASES: Dict[str, List[str]] = {
    "chrome":   ["chrome", "google chrome", "googlechrome", "chrome.exe"],
    "vscode":   ["vscode", "visual studio code", "code", "vs code", "code.exe"],
    "notepad":  ["notepad", "notepad.exe"],
    "discord":  ["discord", "discord.exe"],
    "spotify":  ["spotify", "spotify.exe"],
    "steam":    ["steam", "steam.exe"],
}

# Her uygulama için psutil üzerinden aranacak process isimleri
PROCESS_NAMES: Dict[str, List[str]] = {
    "chrome":   ["chrome.exe"],
    "vscode":   ["code.exe"],
    "notepad":  ["notepad.exe"],
    "discord":  ["discord.exe", "discordptb.exe", "discordcanary.exe"],
    "spotify":  ["spotify.exe"],
    "steam":    ["steam.exe"],
}


def _normalize_app_name(app_name: str) -> str:
    """Uygulama adını standart formata çevirir."""
    cleaned = app_name.strip().lower().replace(" ", "")
    return cleaned


def _resolve_executable(app_name: str) -> Optional[str]:
    """Windows üzerinde çalıştırılabilir uygulama yolunu bulur."""
    normalized = _normalize_app_name(app_name)

    for app_key, aliases in APP_ALIASES.items():
        if normalized in [_normalize_app_name(alias) for alias in aliases]:
            if app_key == "chrome":
                candidates = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                ]
            elif app_key == "vscode":
                candidates = [
                    r"C:\Program Files\Microsoft VS Code\Code.exe",
                    r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
                ]
            else:
                candidates = ["notepad.exe"]

            for candidate in candidates:
                if os.path.exists(candidate):
                    return candidate

            if app_key == "vscode":
                path_from_env = shutil.which("code")
                if path_from_env:
                    return path_from_env
            if app_key == "chrome":
                path_from_env = shutil.which("chrome")
                if path_from_env:
                    return path_from_env
            if app_key == "notepad":
                path_from_env = shutil.which("notepad")
                if path_from_env:
                    return path_from_env

    return None


def open_application(app_name: str) -> bool:
    """Belirtilen Windows uygulamasını açar."""
    executable = _resolve_executable(app_name)

    if not executable:
        raise FileNotFoundError(f"'{app_name}' uygulaması bulunamadı veya PATH üzerinde yok.")

    try:
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
