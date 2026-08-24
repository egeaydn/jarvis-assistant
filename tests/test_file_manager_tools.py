"""Dosya yönetimi araçlarının güvenlik odaklı birim testleri."""

from pathlib import Path

import pytest

from app.tools.file_manager_tools import copy_file, move_file


def test_copy_file_does_not_overwrite_an_existing_destination(tmp_path: Path) -> None:
    """Kopyalama işleminin mevcut hedef dosyayı koruduğunu doğrular."""
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination.txt"
    source.write_text("new content", encoding="utf-8")
    destination.write_text("existing content", encoding="utf-8")

    with pytest.raises(FileExistsError):
        copy_file(str(source), str(destination))

    assert destination.read_text(encoding="utf-8") == "existing content"


def test_move_file_does_not_overwrite_an_existing_destination(tmp_path: Path) -> None:
    """Taşıma işleminin mevcut hedef dosyayı koruduğunu doğrular."""
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination.txt"
    source.write_text("new content", encoding="utf-8")
    destination.write_text("existing content", encoding="utf-8")

    with pytest.raises(FileExistsError):
        move_file(str(source), str(destination))

    assert source.exists()
    assert destination.read_text(encoding="utf-8") == "existing content"
