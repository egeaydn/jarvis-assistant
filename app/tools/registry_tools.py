"""
Phase 10 — Kayıt Defteri (Registry) Düzenleme.

Güvenlik nedeniyle yalnızca HKEY_CURRENT_USER (HKCU) desteklenir.

⚠️ Her iki fonksiyon da güvenlik onayı gerektirir (agent.py tarafından kontrol edilir).
"""

import winreg
from typing import Any, Dict

_ALLOWED_HIVES: Dict[str, int] = {
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
    "HKCU": winreg.HKEY_CURRENT_USER,
}

_VALUE_TYPES: Dict[str, int] = {
    "REG_SZ": winreg.REG_SZ,
    "REG_DWORD": winreg.REG_DWORD,
    "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
    "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
}


def _resolve_hive(hive: str) -> int:
    key = hive.strip().upper()
    if key not in _ALLOWED_HIVES:
        raise ValueError(
            f"Güvenlik nedeniyle yalnızca HKEY_CURRENT_USER (HKCU) desteklenir. Verilen: '{hive}'"
        )
    return _ALLOWED_HIVES[key]


def set_registry_value(
    hive: str,
    key_path: str,
    value_name: str,
    value_data: Any,
    value_type: str = "REG_SZ",
) -> str:
    """HKCU altında bir registry değeri oluşturur/günceller."""
    hive_const = _resolve_hive(hive)
    reg_type = _VALUE_TYPES.get(value_type.strip().upper())
    if reg_type is None:
        raise ValueError(f"Desteklenmeyen değer türü: '{value_type}'. Geçerliler: {list(_VALUE_TYPES)}")

    try:
        with winreg.CreateKeyEx(hive_const, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, value_name, 0, reg_type, value_data)
    except OSError as exc:
        raise RuntimeError(f"Registry değeri yazılamadı: {exc}") from exc

    return f"HKCU\\{key_path}\\{value_name} = {value_data!r} olarak ayarlandı."


def delete_registry_key(hive: str, key_path: str) -> str:
    """HKCU altında alt anahtarı olmayan bir registry anahtarını siler."""
    hive_const = _resolve_hive(hive)
    try:
        winreg.DeleteKey(hive_const, key_path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"'{key_path}' anahtarı bulunamadı.") from exc
    except OSError as exc:
        raise RuntimeError(f"'{key_path}' silinemedi (alt anahtarları olabilir): {exc}") from exc

    return f"HKCU\\{key_path} anahtarı silindi."
