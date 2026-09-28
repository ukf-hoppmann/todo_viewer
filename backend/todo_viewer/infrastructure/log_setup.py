"""Logging: one grep-able key=value line per event, a stack trace indented below it.

Line: `<UTC time> <LEVEL> <event> logger=<name> req=<id> key=value ...`. structlog events and
stdlib records (uvicorn) share the format and the handler: a size-rotated file or the console.
"""
from __future__ import annotations

import json
import logging
import sys
from collections.abc import Iterator, MutableMapping
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import structlog

MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5
PACKAGE_PREFIX = "todo_viewer."


def configure_logging(level: str, file: Path | None) -> None:
    """Routes all logging to `file` (rotated by size) or, without a file, to stderr."""
    numeric = logging.getLevelNamesMapping().get(level.upper())
    if numeric is None:
        raise ValueError(f"LOG_LEVEL {level!r} is not a logging level (DEBUG, INFO, WARNING, ERROR)")

    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%dT%H:%M:%SZ", utc=True),
    ]
    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    handler: logging.Handler
    if file is None:
        handler = logging.StreamHandler(sys.stderr)
    else:
        file.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(file, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
    handler.setFormatter(structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            render_line,
        ],
    ))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(numeric)
    # uvicorn installs its own handlers; its records should go through ours.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True


def render_line(_: Any, __: str, event_dict: MutableMapping[str, Any]) -> str:
    time = event_dict.pop("timestamp", "-")
    level = str(event_dict.pop("level", "-")).upper()
    event = _value(event_dict.pop("event", "-"))
    exception = event_dict.pop("exception", None)
    logger = str(event_dict.pop("logger", "-")).removeprefix(PACKAGE_PREFIX)

    fields = [f"logger={logger}"]
    req = event_dict.pop("req", None)
    if req is not None:
        fields.append(f"req={req}")
    fields.extend(f"{key}={_value(value)}" for key, value in _flatten(event_dict))

    line = " ".join([time, level, event, *fields])
    if exception:
        line += "\n" + "\n".join("    " + row for row in str(exception).rstrip().splitlines())
    return line


def _flatten(fields: MutableMapping[str, Any], prefix: str = "") -> Iterator[tuple[str, Any]]:
    for key, value in fields.items():
        if isinstance(value, dict) and value:
            yield from _flatten(value, f"{prefix}{key}.")
        else:
            yield f"{prefix}{key}", value


def _value(value: Any) -> str:
    text = str(value)
    if text == "" or any(c.isspace() or c in '="' for c in text):
        return json.dumps(text, ensure_ascii=False)
    return text
