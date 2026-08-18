"""
Komut çözümleyici — Phase 2 (string eşleştirme) + Phase 3 (yeni aksiyonlar).

Gerçek AI kullanmadan, string eşleştirme yöntemiyle kullanıcının
doğal dil benzeri komutlarını anlayıp bir dict döndürür.

Phase 4'te bu modül kaldırılıp yerine LLM tool-calling gelecek.

Dönen sözlük:
    {
        "action" : "open" | "close" | "list_apps" | "system_info"
                 | "open_web" | "search_web" | "find_file" | "exit" | "unknown",
        "target" : uygulama adı veya URL  (yoksa None),
        "query"  : arama/dosya sorgusu    (yoksa None),
        "raw"    : orijinal girdi
    }
"""

import re
from typing import Any, Dict, Optional


# ── Aksiyon anahtar kelimeleri ──────────────────────────────────────────────
ACTION_KEYWORDS: Dict[str, str] = {
    "aç":        "open",
    "başlat":    "open",
    "çalıştır":  "open",
    "kapat":     "close",
    "kapa":      "close",
    "durdur":    "close",
    "sonlandır": "close",
    "göster":    "show",
    "listele":   "show",
}

# ── Uygulama anahtar kelimeleri ─────────────────────────────────────────────
APP_KEYWORDS: Dict[str, str] = {
    "chrome":         "chrome",
    "tarayıcı":       "chrome",
    "browser":        "chrome",
    "spotify":        "spotify",
    "müzik":          "spotify",
    "discord":        "discord",
    "vscode":         "vscode",
    "visual studio":  "vscode",
    "notepad":        "notepad",
    "not defteri":    "notepad",
    "steam":          "steam",
}

# ── Web sitesi kısayolları ───────────────────────────────────────────────────
WEBSITE_SHORTCUTS: Dict[str, str] = {
    "youtube":       "https://youtube.com",
    "google":        "https://google.com",
    "github":        "https://github.com",
    "stackoverflow": "https://stackoverflow.com",
    "reddit":        "https://reddit.com",
}

# ── Özel ifadeler (uzundan kısaya sıralanacak) ──────────────────────────────
SPECIAL_PHRASES: Dict[str, str] = {
    "açık uygulamaları göster":    "list_apps",
    "çalışan uygulamaları göster": "list_apps",
    "açık uygulamalar":            "list_apps",
    "çalışan uygulamalar":         "list_apps",
    "uygulamaları listele":        "list_apps",
    "running apps":                "list_apps",
    "sistem bilgilerini göster":   "system_info",
    "sistem bilgisi":              "system_info",
    "sistem durumu":               "system_info",
    "cpu kullanımı":               "system_info",
    "ram kullanımı":               "system_info",
    "çıkış":                       "exit",
    "exit":                        "exit",
    "quit":                        "exit",
    "çık":                         "exit",
}


def _strip_turkish_suffixes(text: str) -> str:
    """'chrome'u', 'discord'u' gibi Türkçe hal eklerini temizler."""
    return re.sub(r"['\u2019][a-z\u00fc\u00f6\u0131\u015f\u011f\u00e7]{1,4}\b", "", text)


def _has_open_verb(text: str) -> bool:
    """Metinde aç/gir/git gibi açma fiili var mı kontrol eder."""
    return text == "aç" or text.endswith(" aç") or " aç " in text


def _is_search_command(text: str) -> bool:
    """Metinde web arama tetikleyicisi var mı kontrol eder."""
    return (
        text == "ara"
        or text.endswith(" ara")
        or "web'de" in text
        or "internette" in text
        or "google'da" in text
    )


def _extract_search_query(text: str) -> str:
    """Arama tetikleyicilerini çıkararak sorgu metnini döndürür."""
    result = text
    for kw in ["web'de ", "internette ", "google'da "]:
        result = result.replace(kw, "")
    if result.endswith(" ara"):
        result = result[:-4]
    return result.strip()


def _extract_file_query(text: str) -> str:
    """Dosya arama tetikleyicilerini çıkararak dosya adını döndürür."""
    result = text
    for kw in [
        "dosyasını bul", "dosyayı bul", "dosyasını ara", "dosyayı ara",
        "dosya bul", "dosya ara", "bul", "ara",
    ]:
        result = result.replace(kw, "")
    return result.strip()


def parse(user_input: str) -> Dict[str, Any]:
    """Kullanıcı girdisini analiz edip komut sözlüğü döndürür."""
    text = user_input.strip().lower()

    # 1. Özel ifadeler (en uzun eşleşme önce)
    for phrase in sorted(SPECIAL_PHRASES, key=len, reverse=True):
        if phrase in text:
            return {
                "action": SPECIAL_PHRASES[phrase],
                "target": None, "query": None, "raw": user_input,
            }

    cleaned = _strip_turkish_suffixes(text)

    # 2. Dosya arama
    if "dosya" in cleaned and ("bul" in cleaned or cleaned.endswith(" ara")):
        query = _extract_file_query(cleaned)
        return {
            "action": "find_file",
            "target": query or None, "query": query or None, "raw": user_input,
        }

    # 3. Web arama  ("python ara", "web'de python öğren")
    #    Orijinal text kullanılır — "web'de" suffix stripping'den zarar görür.
    if _is_search_command(text):
        query = _extract_search_query(text)
        return {
            "action": "search_web",
            "target": None, "query": query or None, "raw": user_input,
        }

    # 4. Web sitesi açma ("youtube aç", "github'ı aç")
    if _has_open_verb(cleaned):
        for site_key, url in WEBSITE_SHORTCUTS.items():
            if site_key in cleaned:
                return {
                    "action": "open_web",
                    "target": url, "query": None, "raw": user_input,
                }

    # 5. Uygulama aksiyonu + hedef
    action: Optional[str] = None
    for keyword, mapped in ACTION_KEYWORDS.items():
        if keyword in cleaned:
            action = mapped
            break

    target: Optional[str] = None
    for keyword in sorted(APP_KEYWORDS, key=len, reverse=True):
        if keyword in cleaned:
            target = APP_KEYWORDS[keyword]
            break

    if action and target:
        return {"action": action, "target": target, "query": None, "raw": user_input}

    return {"action": "unknown", "target": None, "query": None, "raw": user_input}

