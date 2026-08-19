import os
import shutil
import subprocess
from typing import Dict, List, Optional

import psutil


APP_ALIASES: Dict[str, List[str]] = {
    # ── Tarayıcılar ───────────────────────────────────────────────────
    "chrome":       ["chrome", "google chrome", "googlechrome", "chrome.exe"],
    "edge":         ["edge", "microsoft edge", "msedge", "msedge.exe"],
    "firefox":      ["firefox", "firefox developer", "firefox dev", "firefox developer edition", "firefoxdeveloper"],
    # ── Geliştirici Araçları ───────────────────────────────────────
    "vscode":       ["vscode", "visual studio code", "code", "vs code", "code.exe"],
    "visualstudio": ["visual studio", "visualstudio", "devenv", "vs2022", "vs2019"],
    "cursor":       ["cursor", "cursor editor", "cursor.exe"],
    "androidstudio":["android studio", "androidstudio"],
    "notepad":      ["notepad", "notepad.exe"],
    "notepad++":    ["notepad++", "notepadpp", "npp"],
    "ssms":         ["ssms", "sql server management studio", "sqlservermanagementstudio", "sqlserver"],
    "dbeaver":      ["dbeaver", "dbeaver-ce"],
    "postman":      ["postman"],
    "github":       ["github desktop", "githubdesktop", "github"],
    "xampp":        ["xampp", "xampp control panel", "xamppcontrol"],
    # ── Sosyal / İletişim ─────────────────────────────────────────
    "discord":      ["discord", "discord.exe"],
    "zoom":         ["zoom", "zoom workplace", "zoomworkplace", "zoom.exe"],
    "whatsapp":     ["whatsapp", "whatsapp.exe"],
    # ── Microsoft Office ────────────────────────────────────────
    "word":         ["word", "microsoft word", "winword", "word.exe"],
    "excel":        ["excel", "microsoft excel", "excel.exe"],
    "powerpoint":   ["powerpoint", "microsoft powerpoint", "powerpnt", "ppt"],
    "outlook":      ["outlook", "microsoft outlook", "outlook.exe"],
    # ── Müzik / Eğlence ──────────────────────────────────────────
    "spotify":      ["spotify", "spotify.exe"],
    "steam":        ["steam", "steam.exe"],
    "epic":         ["epic", "epic games", "epicgames", "epic games launcher", "epicgameslauncher"],
    "xbox":         ["xbox", "xbox app", "xboxapp"],
    "notion":       ["notion", "notion.exe"],
    # ── Sistem / Yardımcı ───────────────────────────────────────────
    "explorer":     ["explorer", "dosyagezgini", "file explorer", "dosya gezgini", "explorer.exe"],
    "calculator":   ["calculator", "hesap makinesi", "calc", "calc.exe"],
    "paint":        ["paint", "mspaint", "mspaint.exe"],
    "wordpad":      ["wordpad", "wordpad.exe"],
    "lghub":        ["lghub", "logitech g hub", "logitechghub", "logitech"],
    "geforce":      ["geforce", "geforce experience", "nvidia", "nvidia geforce", "geforcexperience"],
    "settings":     ["settings", "ayarlar", "windows settings"],
}


# Her uygulama için psutil üzerinden aranılacak process isimleri
PROCESS_NAMES: Dict[str, List[str]] = {
    # Tarayıcılar
    "chrome":       ["chrome.exe"],
    "edge":         ["msedge.exe"],
    "firefox":      ["firefox.exe"],
    # Geliştirici
    "vscode":       ["code.exe"],
    "visualstudio": ["devenv.exe"],
    "cursor":       ["cursor.exe"],
    "androidstudio":["studio64.exe", "studio.exe"],
    "notepad":      ["notepad.exe"],
    "notepad++":    ["notepad++.exe"],
    "ssms":         ["ssms.exe"],
    "dbeaver":      ["dbeaver.exe"],
    "postman":      ["postman.exe"],
    "github":       ["githubdesktop.exe"],
    "xampp":        ["xampp-control.exe"],
    # İletişim
    "discord":      ["discord.exe", "discordptb.exe", "discordcanary.exe"],
    "zoom":         ["zoom.exe"],
    "whatsapp":     ["whatsapp.exe"],
    # Office
    "word":         ["winword.exe"],
    "excel":        ["excel.exe"],
    "powerpoint":   ["powerpnt.exe"],
    "outlook":      ["outlook.exe", "olk.exe"],
    # Eğlence
    "spotify":      ["spotify.exe"],
    "steam":        ["steam.exe"],
    "epic":         ["epicgameslauncher.exe"],
    "xbox":         ["xboxapp.exe", "gamingservices.exe"],
    "notion":       ["notion.exe"],
    # Sistem
    "explorer":     ["explorer.exe"],
    "calculator":   ["calculatorapp.exe", "calc.exe"],
    "paint":        ["mspaint.exe"],
    "wordpad":      ["wordpad.exe"],
    "lghub":        ["lghub.exe"],
    "geforce":      ["nvcontainer.exe", "nvidia geforce experience.exe"],
    "settings":     ["systemsettings.exe"],
}


# Ortam değişkeni destekli aday yollar
_LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
_APPDATA      = os.environ.get("APPDATA", "")
_PROGRAMFILES = os.environ.get("ProgramFiles", r"C:\Program Files")
_PROGRAMFILES86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

APP_PATHS: Dict[str, List[str]] = {
    # ── Tarayıcılar ───────────────────────────────────────────────────
    "chrome": [
        rf"{_PROGRAMFILES}\Google\Chrome\Application\chrome.exe",
        rf"{_PROGRAMFILES86}\Google\Chrome\Application\chrome.exe",
    ],
    "edge": [
        rf"{_PROGRAMFILES}\Microsoft\Edge\Application\msedge.exe",
        rf"{_PROGRAMFILES86}\Microsoft\Edge\Application\msedge.exe",
    ],
    "firefox": [
        rf"{_PROGRAMFILES}\Firefox Developer Edition\firefox.exe",
        rf"{_PROGRAMFILES86}\Firefox Developer Edition\firefox.exe",
        rf"{_PROGRAMFILES}\Mozilla Firefox\firefox.exe",
        rf"{_PROGRAMFILES86}\Mozilla Firefox\firefox.exe",
    ],
    # ── Geliştirici Araçları ───────────────────────────────────────
    "vscode": [
        rf"{_PROGRAMFILES}\Microsoft VS Code\Code.exe",
        rf"{_PROGRAMFILES86}\Microsoft VS Code\Code.exe",
        rf"{_LOCALAPPDATA}\Programs\Microsoft VS Code\Code.exe",
    ],
    "visualstudio": [
        rf"{_PROGRAMFILES}\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",
        rf"{_PROGRAMFILES}\Microsoft Visual Studio\2022\Professional\Common7\IDE\devenv.exe",
        rf"{_PROGRAMFILES}\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\devenv.exe",
        rf"{_PROGRAMFILES86}\Microsoft Visual Studio\2019\Community\Common7\IDE\devenv.exe",
        rf"{_PROGRAMFILES86}\Microsoft Visual Studio\2019\Professional\Common7\IDE\devenv.exe",
    ],
    "cursor": [
        rf"{_LOCALAPPDATA}\Programs\cursor\Cursor.exe",
        rf"{_LOCALAPPDATA}\cursor\Cursor.exe",
    ],
    "androidstudio": [
        rf"{_PROGRAMFILES}\Android\Android Studio\bin\studio64.exe",
        rf"{_PROGRAMFILES86}\Android\Android Studio\bin\studio64.exe",
    ],
    "notepad":    ["notepad.exe"],
    "notepad++": [
        rf"{_PROGRAMFILES}\Notepad++\notepad++.exe",
        rf"{_PROGRAMFILES86}\Notepad++\notepad++.exe",
    ],
    "ssms": [
        rf"{_PROGRAMFILES86}\Microsoft SQL Server Management Studio 20\Common7\IDE\Ssms.exe",
        rf"{_PROGRAMFILES86}\Microsoft SQL Server Management Studio 19\Common7\IDE\Ssms.exe",
        rf"{_PROGRAMFILES}\Microsoft SQL Server Management Studio 20\Common7\IDE\Ssms.exe",
        rf"{_PROGRAMFILES}\Microsoft SQL Server Management Studio 19\Common7\IDE\Ssms.exe",
    ],
    "dbeaver": [
        rf"{_PROGRAMFILES}\DBeaver\dbeaver.exe",
        rf"{_PROGRAMFILES86}\DBeaver\dbeaver.exe",
        rf"{_LOCALAPPDATA}\DBeaver\dbeaver.exe",
    ],
    "postman": [
        rf"{_LOCALAPPDATA}\Postman\Postman.exe",
        rf"{_APPDATA}\Postman\Postman.exe",
    ],
    "github": [
        rf"{_LOCALAPPDATA}\GitHubDesktop\GitHubDesktop.exe",
        rf"{_LOCALAPPDATA}\GitHubDesktop\Update.exe",
    ],
    "xampp": [
        r"C:\xampp\xampp-control.exe",
        r"D:\xampp\xampp-control.exe",
    ],
    # ── İletişim ──────────────────────────────────────────────────────
    "discord":    [rf"{_LOCALAPPDATA}\Discord\Update.exe"],
    "zoom": [
        rf"{_APPDATA}\Zoom\bin\Zoom.exe",
        rf"{_PROGRAMFILES}\Zoom\bin\Zoom.exe",
        rf"{_PROGRAMFILES86}\Zoom\bin\Zoom.exe",
        rf"{_LOCALAPPDATA}\Zoom\bin\Zoom.exe",
    ],
    "whatsapp": [
        rf"{_LOCALAPPDATA}\WhatsApp\WhatsApp.exe",
        rf"{_APPDATA}\WhatsApp\WhatsApp.exe",
    ],
    "_whatsapp_store": "explorer shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    # ── Microsoft Office ─────────────────────────────────────────────
    "word": [
        rf"{_PROGRAMFILES}\Microsoft Office\root\Office16\WINWORD.EXE",
        rf"{_PROGRAMFILES86}\Microsoft Office\root\Office16\WINWORD.EXE",
        rf"{_PROGRAMFILES}\Microsoft Office\Office16\WINWORD.EXE",
        rf"{_PROGRAMFILES86}\Microsoft Office\Office16\WINWORD.EXE",
    ],
    "excel": [
        rf"{_PROGRAMFILES}\Microsoft Office\root\Office16\EXCEL.EXE",
        rf"{_PROGRAMFILES86}\Microsoft Office\root\Office16\EXCEL.EXE",
        rf"{_PROGRAMFILES}\Microsoft Office\Office16\EXCEL.EXE",
        rf"{_PROGRAMFILES86}\Microsoft Office\Office16\EXCEL.EXE",
    ],
    "powerpoint": [
        rf"{_PROGRAMFILES}\Microsoft Office\root\Office16\POWERPNT.EXE",
        rf"{_PROGRAMFILES86}\Microsoft Office\root\Office16\POWERPNT.EXE",
        rf"{_PROGRAMFILES}\Microsoft Office\Office16\POWERPNT.EXE",
        rf"{_PROGRAMFILES86}\Microsoft Office\Office16\POWERPNT.EXE",
    ],
    "outlook": [
        rf"{_PROGRAMFILES}\Microsoft Office\root\Office16\OUTLOOK.EXE",
        rf"{_PROGRAMFILES86}\Microsoft Office\root\Office16\OUTLOOK.EXE",
        rf"{_LOCALAPPDATA}\Microsoft\Olk\Olk.exe",
    ],
    # ── Müzik / Eğlence ───────────────────────────────────────────────
    "spotify":    [rf"{_APPDATA}\Spotify\Spotify.exe"],
    "steam": [
        rf"{_PROGRAMFILES86}\Steam\steam.exe",
        rf"{_PROGRAMFILES}\Steam\steam.exe",
    ],
    "epic": [
        rf"{_PROGRAMFILES86}\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
        rf"{_PROGRAMFILES}\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
        rf"{_PROGRAMFILES86}\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
        rf"{_PROGRAMFILES}\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
    ],
    "notion": [
        rf"{_LOCALAPPDATA}\Programs\Notion\Notion.exe",
        rf"{_APPDATA}\Notion\Notion.exe",
    ],
    # ── Sistem / Yardımcı ───────────────────────────────────────────────
    "explorer":   ["explorer.exe"],
    "calculator": ["calc.exe"],
    "paint":      ["mspaint.exe"],
    "wordpad":    ["wordpad.exe"],
    "lghub": [
        rf"{_PROGRAMFILES}\LGHUB\lghub.exe",
        rf"{_LOCALAPPDATA}\LGHUB\lghub.exe",
    ],
    "geforce": [
        rf"{_PROGRAMFILES}\NVIDIA Corporation\NVIDIA GeForce Experience\NVIDIA GeForce Experience.exe",
    ],
    "settings":   ["ms-settings:"],   # Windows Settings URI şeması
    "xbox":       [],                  # Microsoft Store — URI ile açılır
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

    # Özel başlatma mantığı gerektiren uygulamalar
    if app_key == "discord":
        update_exe = rf"{os.environ.get('LOCALAPPDATA', '')}\Discord\Update.exe"
        if os.path.exists(update_exe):
            return update_exe
        return shutil.which("discord")

    if app_key == "github":
        update_exe = rf"{os.environ.get('LOCALAPPDATA', '')}\GitHubDesktop\Update.exe"
        if os.path.exists(update_exe):
            return update_exe

    if app_key == "whatsapp":
        # Microsoft Store versiyonu
        return "whatsapp:"

    if app_key == "settings":
        return "ms-settings:"   # Windows URI şeması

    if app_key == "xbox":
        return "xbox:"           # Windows URI şeması

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
        # Windows URI şeması (ms-settings:, xbox:, whatsapp: vb.)
        if executable.endswith(":"):
            subprocess.Popen(["cmd", "/c", "start", "", executable], shell=False)
            return True
        # Discord: özel argümanla başlat
        if app_key == "discord":
            subprocess.Popen([executable, "--processStart", "Discord.exe"], shell=False)
        # GitHub Desktop: Update.exe üzerinden başlat
        elif app_key == "github" and executable.endswith("Update.exe"):
            subprocess.Popen([executable, "--processStart", "GitHubDesktop.exe"], shell=False)
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
