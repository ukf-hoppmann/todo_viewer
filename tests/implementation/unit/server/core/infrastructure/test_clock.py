from datetime import UTC

from viewer.core.infrastructure.clock import SystemClock


def test_system_clock_is_timezone_aware_utc() -> None:
    assert SystemClock().now().tzinfo is UTC
