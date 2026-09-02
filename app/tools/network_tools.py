"""
Phase 10 — Ağ/Firewall Kontrolü.

toggle_wifi(enable=False)  : Güvenlik onayı gerektirir (bağlantı kesme riski).
toggle_wifi(enable=True)   : Onay gerektirmez (agent.py'de parametre bazlı istisna yapılmalı).
block_app_network(app_path): Güvenlik onayı gerektirir.
"""

import subprocess
from pathlib import Path


def toggle_wifi(enable: bool, interface_name: str = "Wi-Fi") -> str:
    """Belirtilen ağ arayüzünü açar veya kapatır (varsayılan arayüz: 'Wi-Fi')."""
    state = "enabled" if enable else "disabled"
    try:
        subprocess.run(
            ["netsh", "interface", "set", "interface", interface_name, state],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"'{interface_name}' arayüzü {state} yapılamadı: {exc.stderr or exc}") from exc
    return f"'{interface_name}' arayüzü {'açıldı' if enable else 'kapatıldı'}."


def block_app_network(app_path: str) -> str:
    """Belirtilen uygulamanın giden ağ trafiğini Windows Firewall ile engeller."""
    path = Path(app_path)
    if not path.exists():
        raise FileNotFoundError(f"Uygulama bulunamadı: '{app_path}'")

    rule_name = f"EgeAssistant_Block_{path.stem}"
    try:
        subprocess.run(
            ["netsh", "advfirewall", "firewall", "add", "rule",
             f"name={rule_name}", "dir=out", "action=block", f"program={path}", "enable=yes"],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"'{app_path}' engellenemedi: {exc.stderr or exc}") from exc
    return f"'{path.name}' için ağ erişimi engellendi (kural: {rule_name})."
