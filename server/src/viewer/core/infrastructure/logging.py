"""Strukturiertes Log nach `<log_dir>/viewer.log`; die Request-ID hängt per contextvars an jedem Eintrag."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import structlog


def configure_logging(log_dir: Path | str, *, level: int = logging.INFO, to_stderr: bool = False) -> Path:
    """Richtet stdlib-Logging und structlog ein und gibt den Pfad der Logdatei zurück."""
    directory = Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)
    log_file = directory / "viewer.log"

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
    ]
    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
    )
    handlers: list[logging.Handler] = [logging.FileHandler(log_file, encoding="utf-8")]
    if to_stderr:
        handlers.append(logging.StreamHandler(sys.stderr))
    root = logging.getLogger()
    for old in [h for h in root.handlers if getattr(h, "_viewer", False)]:
        root.removeHandler(old)
        old.close()
    for handler in handlers:
        handler.setFormatter(formatter)
        handler._viewer = True  # type: ignore[attr-defined]
        root.addHandler(handler)
    root.setLevel(level)
    return log_file
