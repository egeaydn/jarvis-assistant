"""
Phase v1.0 — Jarvis.exe Tek Tıkla Derleme (PyInstaller) Betiği.

Sanal ortamdaki PyInstaller'ı kullanarak uygulamayı tek bir Windows
çalıştırılabilir dosyasına (.exe) dönüştürür.
"""

import os
import subprocess
import sys


def build_executable() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    print("=" * 60)
    print("  JARVIS BUILD ENGINE — DERLEME BAŞLIYOR")
    print("=" * 60)


    # Sanal ortamdaki pyinstaller.exe yolunu bul
    venv_bin = os.path.dirname(sys.executable)
    pyinstaller_exe = os.path.join(venv_bin, "pyinstaller.exe")

    if not os.path.exists(pyinstaller_exe):
        pyinstaller_exe = "pyinstaller"  # Global fallback

    cmd = [
        pyinstaller_exe,
        "--name=Jarvis",
        "--onefile",           # Tek bir .exe dosyası üret
        "--windowed",          # Çalışırken arkada CMD/Siyah konsol penceresi açılmasın
        "--clean",             # Geçici build önbelleklerini temizle
        "--noconfirm",         # Üzerine yazma sorularını otomatik onayla
        "main.py"
    ]

    print(f"Komut: {' '.join(cmd)}\n")
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("  🎉 DERLEME BAŞARIYLA TAMAMLANDI!")
        print("  Gidilecek Klasör: 'dist/'")
        print("  Dosya           : 'dist/Jarvis.exe'")
        print("=" * 60)
    except subprocess.CalledProcessError as exc:
        print(f"\n❌ Derleme başarısız oldu: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
