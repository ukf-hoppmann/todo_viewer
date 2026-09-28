from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest
import structlog

from todo_viewer.infrastructure.log_setup import configure_logging

LINE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ (DEBUG|INFO|WARNING|ERROR|CRITICAL) \S+")


@pytest.fixture(autouse=True)
def reset_logging() -> Iterator[None]:
    yield
    logging.getLogger().handlers.clear()
    structlog.reset_defaults()


def lines(path: Path) -> list[str]:
    for handler in logging.getLogger().handlers:
        handler.flush()
    return path.read_text(encoding="utf-8").splitlines()


def test_structlog_event_is_one_key_value_line(tmp_path: Path) -> None:
    log_file = tmp_path / "logs" / "app.log"
    configure_logging("INFO", log_file)

    structlog.get_logger("todo_viewer.api.test").info(
        "request", method="POST", path="/api/v2/items", status=409,
        details={"item": "STORY-1", "parent": "EPIC-2"}, message="parent is closed")

    [line] = lines(log_file)
    assert LINE.match(line)
    assert " INFO request " in line
    assert "logger=api.test" in line
    assert "method=POST path=/api/v2/items status=409" in line
    assert "details.item=STORY-1 details.parent=EPIC-2" in line
    assert 'message="parent is closed"' in line


def test_exception_follows_the_line_indented(tmp_path: Path) -> None:
    log_file = tmp_path / "app.log"
    configure_logging("INFO", log_file)

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        structlog.get_logger("x").error("request", status=500, exc_info=True)

    first, *trace = lines(log_file)
    assert " ERROR request " in first and "status=500" in first
    assert trace and all(t.startswith("    ") for t in trace)
    assert "RuntimeError: boom" in trace[-1]


def test_stdlib_records_use_the_same_format(tmp_path: Path) -> None:
    log_file = tmp_path / "app.log"
    configure_logging("INFO", log_file)

    logging.getLogger("uvicorn.error").info("Started server process [%d]", 42)

    [line] = lines(log_file)
    assert LINE.match(line)
    assert 'INFO "Started server process [42]" logger=uvicorn.error' in line


def test_level_filters_lower_events(tmp_path: Path) -> None:
    log_file = tmp_path / "app.log"
    configure_logging("WARNING", log_file)

    structlog.get_logger("x").info("hidden")
    structlog.get_logger("x").warning("shown")

    assert [line.split()[2] for line in lines(log_file)] == ["shown"]


def test_file_rotates_by_size(tmp_path: Path) -> None:
    configure_logging("INFO", tmp_path / "app.log")

    [handler] = logging.getLogger().handlers
    assert isinstance(handler, RotatingFileHandler)
    assert (handler.maxBytes, handler.backupCount) == (5 * 1024 * 1024, 5)


def test_without_file_logs_to_console() -> None:
    configure_logging("INFO", None)

    [handler] = logging.getLogger().handlers
    assert type(handler) is logging.StreamHandler


def test_unknown_level_is_refused() -> None:
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        configure_logging("LOUD", None)
