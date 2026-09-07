"""Merkezi loglama modülünün birim testleri (app/config/logger.py)."""

import logging
from pathlib import Path

import pytest

from app.config.logger import get_logger


def test_get_logger_returns_logger_instance() -> None:
    """get_logger bir Logger nesnesi döndürmeli."""
    log = get_logger("test.module")
    assert isinstance(log, logging.Logger)


def test_get_logger_uses_provided_name() -> None:
    """Döndürülen logger adı verilen isimle eşleşmeli."""
    log = get_logger("app.services.test")
    assert log.name == "app.services.test"


def test_get_logger_idempotent() -> None:
    """Aynı isimle çağrıldığında aynı logger örneğini döndürmeli."""
    log1 = get_logger("same.name")
    log2 = get_logger("same.name")
    assert log1 is log2


def test_root_logger_has_handlers_after_configure() -> None:
    """Root logger yapılandırma sonrasında en az bir handler'a sahip olmalı."""
    get_logger("configure.trigger")
    root = logging.getLogger()
    assert len(root.handlers) >= 1


def test_root_logger_level_is_debug() -> None:
    """Root logger seviyesi DEBUG olarak ayarlanmış olmalı."""
    get_logger("level.check")
    root = logging.getLogger()
    assert root.level == logging.DEBUG


def test_log_file_is_created(tmp_path: Path, monkeypatch) -> None:
    """Loglama etkinleştirildiğinde data/jarvis.log oluşturulmalı."""
    import app.config.logger as logger_module

    # Yeni bir dosya yolu ayarlıyoruz, modülü yeniden yapılandırmaya zorluyoruz
    monkeypatch.setattr(logger_module, "_LOG_FILE", tmp_path / "test_jarvis.log")
    monkeypatch.setattr(logger_module, "_LOG_DIR", tmp_path)
    monkeypatch.setattr(logger_module, "_configured", False)

    log = logger_module.get_logger("file.creation.test")
    log.info("Log dosyası oluşturma testi")

    assert (tmp_path / "test_jarvis.log").exists()
