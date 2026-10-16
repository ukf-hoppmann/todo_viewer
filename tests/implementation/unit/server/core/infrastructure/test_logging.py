import json
import logging
from pathlib import Path

import structlog
from viewer.core.infrastructure.logging import configure_logging


def test_log_lines_are_json_with_context(tmp_path: Path) -> None:
    log_file = configure_logging(tmp_path / "logs")
    structlog.contextvars.bind_contextvars(request_id="r-1")
    try:
        structlog.get_logger("viewer.test").info("hallo", answer=42)
        logging.getLogger("fremd").warning("von stdlib")
    finally:
        structlog.contextvars.clear_contextvars()
    for h in logging.getLogger().handlers:
        h.flush()
    lines = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    mine = next(entry for entry in lines if entry.get("event") == "hallo")
    assert mine["answer"] == 42 and mine["request_id"] == "r-1" and mine["level"] == "info"
    assert any(entry.get("event") == "von stdlib" for entry in lines)
    assert log_file.name == "viewer.log"
