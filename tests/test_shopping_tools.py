"""Shopping search araçlarının birim testleri."""

from unittest.mock import patch

import pytest

from app.tools.shopping_tools import SHOPPING_SITES, build_search_urls, search_products


def test_build_search_urls_returns_all_default_sites() -> None:
    urls = build_search_urls("masa lambası")

    assert set(urls.keys()) == set(SHOPPING_SITES.keys())
    assert urls["trendyol"] == "https://www.trendyol.com/sr?q=masa%20lambas%C4%B1"
    assert urls["hepsiburada"] == "https://www.hepsiburada.com/ara?q=masa%20lambas%C4%B1"
    assert urls["amazon"] == "https://www.amazon.com.tr/s?k=masa%20lambas%C4%B1"
    assert urls["n11"] == "https://www.n11.com/arama?q=masa%20lambas%C4%B1"


def test_build_search_urls_raises_on_empty_query() -> None:
    with pytest.raises(ValueError):
        build_search_urls("   ")


def test_build_search_urls_filters_to_requested_sites() -> None:
    urls = build_search_urls("masa lambası", sites=["trendyol"])

    assert list(urls.keys()) == ["trendyol"]


def test_build_search_urls_skips_unknown_sites() -> None:
    urls = build_search_urls("masa lambası", sites=["trendyol", "xyz"])

    assert list(urls.keys()) == ["trendyol"]


def test_search_products_reports_unknown_sites_as_failed() -> None:
    with patch("app.tools.shopping_tools._find_chrome_path", return_value=None), \
         patch("app.tools.shopping_tools.webbrowser.open") as mock_open:
        result = search_products("masa lambası", sites=["trendyol", "xyz"])

    assert result["opened"] == ["trendyol"]
    assert result["failed"] == ["xyz"]
    mock_open.assert_called_once()


def test_search_products_uses_chrome_when_available() -> None:
    with patch("app.tools.shopping_tools._find_chrome_path", return_value=r"C:\chrome.exe"), \
         patch("app.tools.shopping_tools.subprocess.Popen") as mock_popen:
        result = search_products("masa lambası", sites=["trendyol", "n11"])

    assert result["opened"] == ["trendyol", "n11"]
    assert result["failed"] == []
    mock_popen.assert_called_once()
    called_args = mock_popen.call_args[0][0]
    assert called_args[0] == r"C:\chrome.exe"
    assert len(called_args) == 3


def test_search_products_falls_back_to_webbrowser_on_chrome_launch_error() -> None:
    with patch("app.tools.shopping_tools._find_chrome_path", return_value=r"C:\chrome.exe"), \
         patch("app.tools.shopping_tools.subprocess.Popen", side_effect=OSError("no")), \
         patch("app.tools.shopping_tools.webbrowser.open") as mock_open:
        result = search_products("masa lambası", sites=["trendyol"])

    assert result["opened"] == ["trendyol"]
    mock_open.assert_called_once()
