"""Ek özellik — Çoklu site ürün arama (Shopping Search).

Kullanıcının almak istediği bir ürünü Türkiye'de yaygın kullanılan
alışveriş sitelerinde arar ve sonuç sayfalarını Chrome'da ayrı
sekmeler olarak açar. Gerçek veri kazıma (scraping) yapılmaz;
yalnızca doğru arama URL'si oluşturulup tarayıcıda açılır.
"""

import os
import subprocess
import webbrowser
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from app.tools.app_tools import APP_PATHS

# Faz 1 — doğrulanmış arama URL şablonları ({q} = url-encode edilmiş sorgu)
SHOPPING_SITES: Dict[str, str] = {
    "trendyol": "https://www.trendyol.com/sr?q={q}",
    "hepsiburada": "https://www.hepsiburada.com/ara?q={q}",
    "amazon": "https://www.amazon.com.tr/s?k={q}",
    "n11": "https://www.n11.com/arama?q={q}",
}


def build_search_urls(query: str, sites: Optional[List[str]] = None) -> Dict[str, str]:
    """Sorgu için istenen sitelerin arama URL'lerini üretir.

    Bilinmeyen site adları sessizce atlanır.
    """
    if not query or not query.strip():
        raise ValueError("Arama sorgusu boş olamaz.")

    site_names = sites if sites else list(SHOPPING_SITES.keys())
    # quote (%20) kullanılır; quote_plus'ın ürettiği '+' bazı sitelerin arama
    # kutusunda kelime ayracı olarak değil literal karakter olarak görünüyor.
    encoded_query = quote(query.strip())

    urls: Dict[str, str] = {}
    for site in site_names:
        template = SHOPPING_SITES.get(site.strip().lower())
        if template:
            urls[site.strip().lower()] = template.format(q=encoded_query)
    return urls


def _find_chrome_path() -> Optional[str]:
    """Sistemde kurulu chrome.exe yolunu döndürür, bulunamazsa None."""
    for candidate in APP_PATHS.get("chrome", []):
        if os.path.exists(candidate):
            return candidate
    return None


def search_products(query: str, sites: Optional[List[str]] = None) -> Dict[str, Any]:
    """Ürünü alışveriş sitelerinde arar ve sonuçları Chrome'da sekme olarak açar.

    Chrome bulunamazsa, sistemin varsayılan tarayıcısı (webbrowser modülü)
    ile açmaya geri döner.
    """
    urls = build_search_urls(query, sites)
    requested = [s.strip().lower() for s in sites] if sites else list(SHOPPING_SITES.keys())
    failed = [s for s in requested if s not in urls]

    if not urls:
        return {"opened": [], "failed": failed, "query": query}

    chrome_path = _find_chrome_path()
    if chrome_path:
        try:
            subprocess.Popen([chrome_path, *urls.values()])
            return {"opened": list(urls.keys()), "failed": failed, "query": query}
        except OSError:
            pass  # Chrome başlatılamadıysa varsayılan tarayıcı fallback'ine düş

    for url in urls.values():
        webbrowser.open(url, new=2)
    return {"opened": list(urls.keys()), "failed": failed, "query": query}
