from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from typing import Any

import pytest
from fakes import FixedClock
from viewer.core.application.client_log import (
    MAX_PART_BYTES,
    MAX_TEXT_CHARS,
    RATE_LIMIT,
    RATE_WINDOW,
    ClientLogIn,
    ClientLogService,
)
from viewer.core.domain.errors import InvalidInput


class RecordingWriter:
    def __init__(self) -> None:
        self.entries: list[tuple[str, str, Mapping[str, Any]]] = []

    def write(self, level: str, message: str, fields: Mapping[str, Any]) -> None:
        self.entries.append((level, message, fields))


def setup() -> tuple[ClientLogService, RecordingWriter, FixedClock]:
    writer, clock = RecordingWriter(), FixedClock()
    return ClientLogService(writer, clock), writer, clock


def test_entry_is_passed_on_without_empty_fields() -> None:
    service, writer, _ = setup()

    out = service.write(
        ClientLogIn(level="error", origin="backlog", id="a1b2c3d4", message="errors.unexpected", action="render")
    )

    assert out.accepted
    assert writer.entries == [
        ("error", "errors.unexpected", {"client_origin": "backlog", "client_id": "a1b2c3d4", "action": "render"})
    ]


def test_unknown_level_is_rejected() -> None:
    service, writer, _ = setup()

    with pytest.raises(InvalidInput):
        service.write(ClientLogIn(level="fatal"))

    assert writer.entries == []


def test_long_message_is_cut_and_large_parts_are_replaced_by_a_note() -> None:
    service, writer, _ = setup()

    service.write(ClientLogIn(level="warn", message="x" * (MAX_TEXT_CHARS + 50), data={"big": "y" * MAX_PART_BYTES}))

    _, message, fields = writer.entries[0]
    assert len(message) == MAX_TEXT_CHARS + 1
    assert fields["data"]["truncated"] is True


def test_entries_above_the_rate_limit_are_dropped_until_the_window_has_passed() -> None:
    service, writer, clock = setup()

    results = [service.write(ClientLogIn(level="info")).accepted for _ in range(RATE_LIMIT + 5)]

    assert results.count(True) == RATE_LIMIT
    assert len(writer.entries) == RATE_LIMIT
    clock.advance(RATE_WINDOW + timedelta(seconds=1))
    assert service.write(ClientLogIn(level="info")).accepted
