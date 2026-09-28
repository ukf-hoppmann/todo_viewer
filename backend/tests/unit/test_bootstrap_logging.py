from __future__ import annotations

import logging
from pathlib import Path

import pytest
import structlog

from todo_viewer.bootstrap import Settings, start_logging


@pytest.fixture(autouse=True)
def reset_logging():
    yield
    logging.getLogger().handlers.clear()
    structlog.reset_defaults()


def test_settings_read_log_file_and_level(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOG_FILE", str(tmp_path / "app.log"))
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = Settings.from_env()

    assert (settings.log_file, settings.log_level) == (tmp_path / "app.log", "debug")


def test_settings_without_log_file_use_console(monkeypatch) -> None:
    monkeypatch.delenv("LOG_FILE", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = Settings.from_env()

    assert (settings.log_file, settings.log_level) == (None, "INFO")


def test_startup_line_names_the_active_paths(tmp_path: Path) -> None:
    log_file = tmp_path / "app.log"
    settings = Settings(base_dir=tmp_path, config_dir=tmp_path / "configs", frontend_dir=tmp_path / "dist",
                        browse_start=None, log_file=log_file, log_level="INFO")

    start_logging(settings)
    logging.getLogger().handlers[0].flush()

    [line] = log_file.read_text(encoding="utf-8").splitlines()
    assert " INFO startup " in line
    assert f"config_dir={tmp_path / 'configs'}" in line
    assert f"frontend_dir={tmp_path / 'dist'}" in line
    assert "browse_start=None" in line
    assert f"log_file={log_file}" in line and "log_level=INFO" in line
    assert "api=2 python=" in line
