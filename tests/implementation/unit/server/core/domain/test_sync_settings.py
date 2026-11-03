from __future__ import annotations

import math

import pytest
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.sync_settings import MAX_AUTO_SYNC_INTERVAL_SECONDS, check_auto_sync_interval


@pytest.mark.parametrize("seconds", [0, 1, 30, 2.5, MAX_AUTO_SYNC_INTERVAL_SECONDS])
def test_zero_and_every_value_from_one_second_up_to_the_maximum_are_valid(seconds: float) -> None:
    assert check_auto_sync_interval(seconds) == float(seconds)


@pytest.mark.parametrize("seconds", [-1, 0.5, MAX_AUTO_SYNC_INTERVAL_SECONDS + 1, math.inf, math.nan])
def test_other_values_are_rejected_with_the_allowed_range(seconds: float) -> None:
    with pytest.raises(InvalidInput) as raised:
        check_auto_sync_interval(seconds)
    assert raised.value.details["max"] == MAX_AUTO_SYNC_INTERVAL_SECONDS
