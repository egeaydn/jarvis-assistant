import webbrowser
from urllib.parse import quote_plus


def open_website(url: str) -> bool:
    """Verilen URL'yi varsayılan tarayıcıda açar."""
    if not url or not url.strip():
        raise ValueError("URL boş olamaz.")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url.strip()
    webbrowser.open(url)
    return True


def search_web(query: str) -> bool:
    """Google üzerinden web araması yapar."""
    if not query or not query.strip():
        raise ValueError("Arama sorgusu boş olamaz.")
    search_url = f"https://www.google.com/search?q={quote_plus(query.strip())}"
    webbrowser.open(search_url)
    return True
