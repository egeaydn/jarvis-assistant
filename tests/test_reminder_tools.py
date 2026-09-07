"""Hatırlatıcı araçlarının birim testleri (reminder_tools.py)."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.tools.reminder_tools import cancel_reminder, list_reminders, set_reminder


# ── set_reminder ──────────────────────────────────────────────────────────────

def test_set_reminder_returns_reminder_dict() -> None:
    """Başarılı hatırlatıcı kurulumu dict döndürmeli."""
    future_time = datetime.now() + timedelta(hours=2)
    mock_reminder = {
        "id": "abc12345",
        "mesaj": "Toplantı",
        "zaman": future_time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    mock_service = MagicMock()
    mock_service.add.return_value = mock_reminder

    with patch("app.tools.reminder_tools.get_reminder_service", return_value=mock_service), \
         patch("app.tools.reminder_tools._parse_when", return_value=future_time):
        result = set_reminder("Toplantı", "2 saat sonra")

    assert result["id"] == "abc12345"
    assert result["mesaj"] == "Toplantı"
    mock_service.add.assert_called_once()


def test_set_reminder_raises_on_empty_message() -> None:
    """Boş mesaj ValueError fırlatmalı."""
    with pytest.raises(ValueError):
        set_reminder("", "yarın 10:00")


def test_set_reminder_raises_on_whitespace_message() -> None:
    """Sadece boşluk içeren mesaj da reddedilmeli."""
    with pytest.raises(ValueError):
        set_reminder("   ", "yarın 10:00")


def test_set_reminder_raises_when_time_is_in_past() -> None:
    """Geçmiş zaman ifadesi ValueError fırlatmalı."""
    past_time = datetime.now() - timedelta(hours=1)
    with patch("app.tools.reminder_tools._parse_when", return_value=past_time):
        with pytest.raises(ValueError, match="geçmişte"):
            set_reminder("Test", "1 saat önce")


# ── list_reminders ────────────────────────────────────────────────────────────

def test_list_reminders_returns_active_reminders() -> None:
    """Aktif hatırlatıcılar döndürülmeli."""
    mock_items = [
        {"id": "r1", "mesaj": "Birinci", "zaman": "2099-01-01 10:00:00"},
        {"id": "r2", "mesaj": "İkinci", "zaman": "2099-01-01 11:00:00"},
    ]
    mock_service = MagicMock()
    mock_service.list_active.return_value = mock_items

    with patch("app.tools.reminder_tools.get_reminder_service", return_value=mock_service):
        result = list_reminders()

    assert len(result) == 2
    assert result[0]["id"] == "r1"


def test_list_reminders_returns_empty_list_when_none() -> None:
    """Aktif hatırlatıcı yoksa boş liste dönmeli."""
    mock_service = MagicMock()
    mock_service.list_active.return_value = []

    with patch("app.tools.reminder_tools.get_reminder_service", return_value=mock_service):
        result = list_reminders()

    assert result == []


# ── cancel_reminder ───────────────────────────────────────────────────────────

def test_cancel_reminder_returns_success_message() -> None:
    """Mevcut hatırlatıcı iptal edildiğinde başarı mesajı dönmeli."""
    mock_service = MagicMock()
    mock_service.cancel.return_value = True

    with patch("app.tools.reminder_tools.get_reminder_service", return_value=mock_service):
        result = cancel_reminder("abc123")

    assert "abc123" in result
    assert "iptal" in result.lower()


def test_cancel_reminder_raises_keyerror_when_not_found() -> None:
    """Var olmayan ID için KeyError fırlatılmalı."""
    mock_service = MagicMock()
    mock_service.cancel.return_value = False

    with patch("app.tools.reminder_tools.get_reminder_service", return_value=mock_service):
        with pytest.raises(KeyError):
            cancel_reminder("nonexistent")


# ── _parse_when ───────────────────────────────────────────────────────────────

def test_parse_when_returns_future_datetime() -> None:
    """Geçerli zaman ifadesi gelecekte bir datetime döndürmeli."""
    from app.tools.reminder_tools import _parse_when

    result = _parse_when("yarın 10:00")
    assert isinstance(result, datetime)
    assert result > datetime.now()


def test_parse_when_raises_on_unparseable_string() -> None:
    """Anlaşılamayan zaman ifadesi ValueError fırlatmalı."""
    from app.tools.reminder_tools import _parse_when

    with patch("app.tools.reminder_tools.dateparser.parse", return_value=None):
        with pytest.raises(ValueError, match="anlaşılamadı"):
            _parse_when("xyzabc")
