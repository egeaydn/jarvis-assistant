"""
Phase v1.0 — Windows Başlangıcında Otomatik Çalışma (Boot Autostart) Ayarları.

winreg kütüphanesini kullanarak kayıt defterine (registry) Jarvis assistant ekler.
Kayıt girdisi, bilgisayar açıldığında uygulamayı arka planda (tray modunda) başlatır.
"""

import os
import sys
import winreg
from typing import Tuple

REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_VAL_NAME = "JarvisAssistant"


def set_autostart(enabled: bool) -> Tuple[bool, str]:
    """
    Kayıt defterini güncelleyerek otomatik başlatmayı açar veya kapatır.
    Sanal ortam (venv) ve ana kod dosyasını otomatik algılar.
    """
    if getattr(sys, 'frozen', False):
        # Derlenmiş .exe versiyonu çalışıyorsa doğrudan kendi yolunu ekle
        exe_path = sys.executable
        cmd = f'"{exe_path}" --minimized'
    else:
        # Geliştirme/Python modundaysak, konsol penceresi açılmaması için
        # python.exe yerine pythonw.exe ile çalıştır
        python_exe = sys.executable
        pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
        
        main_py = os.path.abspath(sys.argv[0])
        # Çalışma dizinini projenin kök dizini yap
        cwd = os.path.dirname(main_py)
        cmd = f'"{pythonw_exe}" "{main_py}" --minimized'

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY_PATH,
            0,
            winreg.KEY_ALL_ACCESS
        )
        
        if enabled:
            winreg.SetValueEx(key, REG_VAL_NAME, 0, winreg.REG_SZ, cmd)
            message = "Jarvis başlangıç programlarına eklendi."
        else:
            try:
                winreg.DeleteValue(key, REG_VAL_NAME)
                message = "Jarvis başlangıç programlarından kaldırıldı."
            except FileNotFoundError:
                message = "Zaten başlangıçta çalışacak şekilde ayarlı değil."
        
        winreg.CloseKey(key)
        return True, message

    except Exception as exc:
        return False, f"Başlangıç ayarı güncellenirken hata oluştu: {exc}"


def is_autostart_enabled() -> bool:
    """Başlangıçta çalıştırma kaydının olup olmadığını kontrol eder."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY_PATH,
            0,
            winreg.KEY_READ
        )
        _, _ = winreg.QueryValueEx(key, REG_VAL_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
