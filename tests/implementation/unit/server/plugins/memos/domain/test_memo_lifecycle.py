from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta

import pytest
from memos_fixtures import NOW, memo, topic
from viewer.core.domain.errors import InvalidInput
from viewer.plugins.memos.domain.due import effective_status, is_due
from viewer.plugins.memos.domain.lifecycle import finish, keep, restore, snooze
from viewer.plugins.memos.domain.model import (
    Memo,
    MemosSettings,
    MemosViolation,
    changed_settings,
    default_review_at,
)

PAST = NOW - timedelta(days=1)
FUTURE = NOW + timedelta(days=1)


def test_a_waiting_memo_is_due_once_its_review_date_is_reached() -> None:
    assert is_due(memo("a", review_at=PAST), NOW)
    assert is_due(memo("a", review_at=NOW), NOW)
    assert not is_due(memo("a", review_at=FUTURE), NOW)
    assert not is_due(memo("a"), NOW)


def test_a_snoozed_memo_is_due_again_when_its_new_date_comes() -> None:
    assert effective_status(memo("a", status="snoozed", review_at=PAST), NOW) == "due"
    assert effective_status(memo("a", status="snoozed", review_at=FUTURE), NOW) == "snoozed"


@pytest.mark.parametrize("status", ["done", "dropped", "promoted"])
def test_finished_memos_are_never_due(status: str) -> None:
    assert effective_status(memo("a", status=status, archived=True, review_at=PAST), NOW) == status


def test_archived_and_deleted_memos_do_not_trigger_a_review() -> None:
    assert not is_due(memo("a", archived=True, review_at=PAST), NOW)
    assert not is_due(memo("a", review_at=PAST, deleted_at=PAST), NOW)


def test_a_review_date_without_time_zone_counts_as_utc() -> None:
    assert is_due(memo("a", review_at=PAST.replace(tzinfo=None)), NOW)


def test_the_default_review_date_is_today_plus_the_interval() -> None:
    assert default_review_at(NOW, 30) == NOW + timedelta(days=30)


def test_keep_only_moves_the_review_date() -> None:
    kept = keep(memo("a", review_at=PAST), NOW, 10)
    assert kept == replace(memo("a", review_at=PAST), review_at=NOW + timedelta(days=10))


def test_snooze_sets_the_status_and_takes_a_given_date_over_the_default() -> None:
    assert snooze(memo("a"), NOW, 10).review_at == NOW + timedelta(days=10)
    chosen = snooze(memo("a"), NOW, 10, FUTURE)
    assert (chosen.status, chosen.review_at) == ("snoozed", FUTURE)


@pytest.mark.parametrize("target", ["done", "dropped", "promoted"])
def test_finishing_moves_the_memo_to_the_archive(target: str) -> None:
    done = finish(memo("a"), target)
    assert (done.status, done.archived) == (target, True)


def test_finishing_needs_a_closing_status() -> None:
    with pytest.raises(MemosViolation) as error:
        finish(memo("a"), "waiting")
    assert error.value.code == "memo_target_invalid"


@pytest.mark.parametrize(
    "bad,code",
    [
        (memo("a", archived=True, status="done"), "memo_archived"),
        (memo("a", deleted_at=PAST), "memo_deleted"),
    ],
)
def test_a_memo_that_is_not_in_use_rejects_changes(bad: Memo, code: str) -> None:
    changes: list[Callable[[Memo], Memo]] = [
        lambda n: keep(n, NOW, 5),
        lambda n: snooze(n, NOW, 5),
        lambda n: finish(n, "done"),
    ]
    for change in changes:
        with pytest.raises(MemosViolation) as error:
            change(bad)
        assert error.value.code == code


def test_restore_brings_an_archived_memo_back_to_waiting_with_a_new_date() -> None:
    back = restore(memo("a", status="done", archived=True), None, NOW, 5)
    assert (back.status, back.archived, back.review_at) == ("waiting", False, NOW + timedelta(days=5))


def test_restore_refuses_a_memo_that_is_not_archived_or_whose_topic_is_archived() -> None:
    with pytest.raises(MemosViolation) as error:
        restore(memo("a"), None, NOW, 5)
    assert error.value.code == "memo_not_archived"
    with pytest.raises(MemosViolation) as error:
        restore(memo("a", status="done", archived=True, topic="t"), topic("t", archived_at=PAST), NOW, 5)
    assert error.value.code == "topic_archived"


def test_settings_accept_whole_numbers_within_their_limits() -> None:
    assert changed_settings(MemosSettings(), 5, 60) == MemosSettings(5, 60)
    assert changed_settings(MemosSettings(4, 7)) == MemosSettings(4, 7)


@pytest.mark.parametrize("depth,days", [(0, None), (11, None), (None, 0), (None, 4000)])
def test_settings_outside_their_limits_are_rejected(depth: int | None, days: int | None) -> None:
    with pytest.raises(InvalidInput):
        changed_settings(MemosSettings(), depth, days)
