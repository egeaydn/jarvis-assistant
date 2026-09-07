"""Browser araçlarının birim testleri (browser_tools.py)."""

from unittest.mock import patch

import pytest

from app.tools.browser_tools import open_website, search_web


# ── open_website ──────────────────────────────────────────────────────────────

def test_open_website_opens_valid_url() -> None:
    """Geçerli URL için webbrowser.open çağrılmalı."""
    with patch("app.tools.browser_tools.webbrowser.open") as mock_open:
        result = open_website("https://www.google.com")
    mock_open.assert_called_once_with("https://www.google.com")
    assert result is True


def test_open_website_adds_https_prefix_when_missing() -> None:
    """http/https eki olmayan URL'ye otomatik https:// eklenmeli."""
    with patch("app.tools.browser_tools.webbrowser.open") as mock_open:
        open_website("google.com")
    called_url = mock_open.call_args[0][0]
    assert called_url.startswith("https://")
    assert "google.com" in called_url


def test_open_website_keeps_http_prefix() -> None:
    """http:// ile başlayan URL'ye dokunulmamalı."""
    with patch("app.tools.browser_tools.webbrowser.open") as mock_open:
        open_website("http://example.com")
    assert mock_open.call_args[0][0] == "http://example.com"


def test_open_website_raises_on_empty_url() -> None:
    """Boş URL ValueError fırlatmalı."""
    with pytest.raises(ValueError):
        open_website("   ")


# ── search_web ────────────────────────────────────────────────────────────────

def test_search_web_builds_google_url() -> None:
    """Arama sorgusu Google URL'sine doğru encode edilmeli."""
    with patch("app.tools.browser_tools.webbrowser.open") as mock_open:
        result = search_web("python logging")
    called_url = mock_open.call_args[0][0]
    assert "google.com/search" in called_url
    assert "python" in called_url
    assert result is True


def test_search_web_encodes_special_characters() -> None:
    """Özel karakterler URL encode edilmeli."""
    with patch("app.tools.browser_tools.webbrowser.open") as mock_open:
        search_web("hava durumu & sıcaklık")
    called_url = mock_open.call_args[0][0]
    # Boşluk encode edilmeli (+veya %20)
    assert " " not in called_url


def test_search_web_raises_on_empty_query() -> None:
    """Boş arama sorgusu ValueError fırlatmalı."""
    with pytest.raises(ValueError):
        search_web("")
