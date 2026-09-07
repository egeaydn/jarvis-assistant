"""Not alma araçlarının birim testleri (notes_tools.py)."""

from pathlib import Path

import pytest

from app.tools.notes_tools import add_note, list_notes, search_notes


# ── add_note ──────────────────────────────────────────────────────────────────

def test_add_note_creates_file_if_not_exists(tmp_path: Path, monkeypatch) -> None:
    """Not dosyası yoksa otomatik oluşturulmalı."""
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", tmp_path / "notes.md")
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    result = add_note("Test notu")
    assert "Test notu" in result
    assert (tmp_path / "notes.md").exists()


def test_add_note_appends_content(tmp_path: Path, monkeypatch) -> None:
    """İkinci çağrıda dosyaya ekleme (append) yapılmalı, üzerine yazılmamalı."""
    notes_file = tmp_path / "notes.md"
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", notes_file)
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    add_note("İlk not")
    add_note("İkinci not")

    content = notes_file.read_text(encoding="utf-8")
    assert "İlk not" in content
    assert "İkinci not" in content


def test_add_note_with_tag(tmp_path: Path, monkeypatch) -> None:
    """Etiketli not doğru formatta kaydedilmeli."""
    notes_file = tmp_path / "notes.md"
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", notes_file)
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    add_note("Alışveriş listesi", tag="alışveriş")
    content = notes_file.read_text(encoding="utf-8")
    assert "[alışveriş]" in content


def test_add_note_raises_on_empty_content(tmp_path: Path, monkeypatch) -> None:
    """Boş içerik geçilemez."""
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", tmp_path / "notes.md")
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    with pytest.raises(ValueError):
        add_note("   ")


# ── list_notes ────────────────────────────────────────────────────────────────

def test_list_notes_returns_most_recent_first(tmp_path: Path, monkeypatch) -> None:
    """Notlar en yeniden eskiye sıralı döndürülmeli."""
    notes_file = tmp_path / "notes.md"
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", notes_file)
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    add_note("Birinci")
    add_note("İkinci")
    add_note("Üçüncü")

    entries = list_notes(limit=10)
    # En son eklenen başta olmalı
    assert entries[0]["içerik"] == "Üçüncü"
    assert entries[-1]["içerik"] == "Birinci"


def test_list_notes_filters_by_tag(tmp_path: Path, monkeypatch) -> None:
    """Etiket filtresi yalnızca eşleşen notları döndürmeli."""
    notes_file = tmp_path / "notes.md"
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", notes_file)
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    add_note("İş toplantısı", tag="iş")
    add_note("Market alışverişi", tag="alışveriş")
    add_note("Sunum hazırla", tag="iş")

    is_entries = list_notes(tag="iş")
    assert len(is_entries) == 2
    assert all(e["tag"] == "iş" for e in is_entries)


def test_list_notes_returns_empty_when_no_file(tmp_path: Path, monkeypatch) -> None:
    """Dosya yoksa boş liste döndürülmeli (hata fırlatılmamalı)."""
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", tmp_path / "missing.md")
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    result = list_notes()
    assert result == []


# ── search_notes ──────────────────────────────────────────────────────────────

def test_search_notes_finds_matching_content(tmp_path: Path, monkeypatch) -> None:
    """Arama sorgusu içerikte geçen notları bulmalı."""
    notes_file = tmp_path / "notes.md"
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", notes_file)
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    add_note("Python öğren")
    add_note("Alışveriş listesi yap")
    add_note("Python projesi bitir")

    results = search_notes("python")
    assert len(results) == 2
    assert all("python" in r["içerik"].lower() for r in results)


def test_search_notes_is_case_insensitive(tmp_path: Path, monkeypatch) -> None:
    """Arama büyük/küçük harf duyarsız olmalı."""
    notes_file = tmp_path / "notes.md"
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", notes_file)
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    add_note("JARVIS güncellendi")
    results = search_notes("jarvis")
    assert len(results) == 1


def test_search_notes_raises_on_empty_query(tmp_path: Path, monkeypatch) -> None:
    """Boş arama sorgusu ValueError fırlatmalı."""
    monkeypatch.setattr("app.tools.notes_tools._NOTES_FILE", tmp_path / "notes.md")
    monkeypatch.setattr("app.tools.notes_tools._DATA_DIR", tmp_path)

    with pytest.raises(ValueError):
        search_notes("")
