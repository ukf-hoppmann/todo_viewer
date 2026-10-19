from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from viewer.core.infrastructure.timezone import resolve_zone


def test_a_known_name_gives_that_zone_with_daylight_saving() -> None:
    zone = resolve_zone("Europe/Berlin")

    assert zone == ZoneInfo("Europe/Berlin")
    assert datetime(2026, 7, 1, 12, tzinfo=UTC).astimezone(zone).hour == 14
    assert datetime(2026, 1, 1, 12, tzinfo=UTC).astimezone(zone).hour == 13


@pytest.mark.parametrize("name", [None, "", "  ", "Nowhere/Land", "../etc/passwd"])
def test_a_missing_or_unknown_name_gives_utc(name: str | None) -> None:
    assert resolve_zone(name) is UTC
