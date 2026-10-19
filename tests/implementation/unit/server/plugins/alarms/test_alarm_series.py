from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from viewer.plugins.alarms.domain.series import first_after, missed, occurrence

BERLIN = ZoneInfo("Europe/Berlin")


def local(year: int, month: int, day: int, hour: int = 11, minute: int = 0) -> datetime:
    """Ein Zeitpunkt, wie er in Berlin an der Wand steht (UTC, wie ihn der Wecker speichert)."""
    return datetime(year, month, day, hour, minute, tzinfo=BERLIN).astimezone(UTC)


def utc(*parts: int) -> datetime:
    return datetime(*parts, tzinfo=UTC)


@pytest.mark.parametrize(
    ("repeat", "n", "expected"),
    [
        ("daily", 0, local(2026, 5, 1)),
        ("daily", 3, local(2026, 5, 4)),
        ("weekly", 2, local(2026, 5, 15)),
        ("monthly", 1, local(2026, 6, 1)),
        ("yearly", 1, local(2027, 5, 1)),
    ],
)
def test_the_nth_term_is_counted_from_the_start(repeat: str, n: int, expected: datetime) -> None:
    assert occurrence(local(2026, 5, 1), repeat, n, BERLIN) == expected


def test_a_monthly_series_is_cut_at_the_end_of_the_month_and_comes_back() -> None:
    start = local(2026, 1, 31)
    days = [occurrence(start, "monthly", n, BERLIN).astimezone(BERLIN).date() for n in range(4)]

    assert [d.isoformat() for d in days] == ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30"]


def test_a_monthly_series_ends_on_the_29th_of_february_in_a_leap_year() -> None:
    assert occurrence(local(2028, 1, 31), "monthly", 1, BERLIN) == local(2028, 2, 29)


def test_a_yearly_series_from_the_29th_of_february_is_cut_and_comes_back() -> None:
    start = local(2028, 2, 29)

    assert occurrence(start, "yearly", 1, BERLIN) == local(2029, 2, 28)
    assert occurrence(start, "yearly", 4, BERLIN) == local(2032, 2, 29)


def test_eleven_oclock_stays_eleven_oclock_over_the_switch_to_summer_time() -> None:
    start = local(2026, 3, 27)  # CET; am 29.03. beginnt die Sommerzeit

    assert occurrence(start, "daily", 2, BERLIN) == local(2026, 3, 29)
    assert occurrence(start, "daily", 2, BERLIN) == utc(2026, 3, 29, 9)  # eine Stunde früher in UTC


def test_eleven_oclock_stays_eleven_oclock_over_the_switch_to_winter_time() -> None:
    start = local(2026, 10, 24)  # CEST; am 25.10. endet die Sommerzeit

    assert occurrence(start, "daily", 1, BERLIN) == utc(2026, 10, 25, 10)


def test_a_local_time_that_does_not_exist_moves_on_by_the_length_of_the_gap() -> None:
    start = local(2026, 3, 28, 2, 30)

    assert occurrence(start, "daily", 1, BERLIN) == local(2026, 3, 29, 3, 30)


def test_a_local_time_that_exists_twice_takes_the_first() -> None:
    start = local(2026, 10, 24, 2, 30)

    assert occurrence(start, "daily", 1, BERLIN) == utc(2026, 10, 25, 0, 30)  # 02:30 MESZ, nicht 02:30 MEZ


def test_the_first_term_after_now_is_strictly_later() -> None:
    start = local(2026, 5, 1)

    assert first_after(start, "daily", local(2026, 5, 3, 10), BERLIN) == local(2026, 5, 3)
    assert first_after(start, "daily", local(2026, 5, 3), BERLIN) == local(2026, 5, 4)
    assert first_after(start, "daily", local(2026, 4, 1), BERLIN) == local(2026, 5, 1)


def test_the_first_term_after_a_long_pause_is_not_walked_day_by_day() -> None:
    start = local(2020, 1, 31)

    assert first_after(start, "monthly", local(2026, 5, 31, 12), BERLIN) == local(2026, 6, 30)
    assert first_after(start, "daily", local(2026, 5, 31, 12), BERLIN) == local(2026, 6, 1)


def test_missed_counts_the_terms_after_the_alarms_time_up_to_now() -> None:
    start = local(2026, 5, 1)

    assert missed(start, start, "daily", local(2026, 5, 1, 12), BERLIN) == 0
    assert missed(start, start, "daily", local(2026, 5, 4), BERLIN) == 3
    assert missed(start, start, "daily", local(2026, 5, 4, 10), BERLIN) == 2


def test_missed_after_a_long_pause_counts_every_term() -> None:
    start = local(2026, 1, 31)

    assert missed(start, start, "monthly", local(2026, 6, 30), BERLIN) == 5
    assert missed(start, start, "weekly", local(2026, 5, 1), BERLIN) == 12  # 90 Tage


def test_missed_starts_at_the_alarms_time_not_at_the_series_start() -> None:
    start = local(2026, 5, 1)

    assert missed(local(2026, 5, 3), start, "daily", local(2026, 5, 5, 12), BERLIN) == 2


def test_a_snoozed_time_between_two_terms_does_not_add_a_missed_term() -> None:
    start = local(2026, 5, 1)

    assert missed(local(2026, 5, 1, 12), start, "daily", local(2026, 5, 2, 10), BERLIN) == 0


def test_without_repetition_nothing_is_missed() -> None:
    start = local(2026, 5, 1)

    assert missed(start, None, "none", local(2026, 6, 1), BERLIN) == 0
