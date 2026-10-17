from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta

import pytest
from notes_fixtures import NOW, note, topic
from viewer.core.domain.errors import InvalidInput
from viewer.plugins.notes.domain.lifecycle import finish, keep, restore, snooze
from viewer.plugins.notes.domain.model import (
    Note,
    NotesSettings,
    NotesViolation,
    changed_settings,
    default_review_at,
    effective_status,
    is_due,
)

PAST = NOW - timedelta(days=1)
FUTURE = NOW + timedelta(days=1)


def test_a_waiting_note_is_due_once_its_review_date_is_reached() -> None:
    assert is_due(note("a", review_at=PAST), NOW)
    assert is_due(note("a", review_at=NOW), NOW)
    assert not is_due(note("a", review_at=FUTURE), NOW)
    assert not is_due(note("a"), NOW)


def test_a_snoozed_note_is_due_again_when_its_new_date_comes() -> None:
    assert effective_status(note("a", status="snoozed", review_at=PAST), NOW) == "due"
    assert effective_status(note("a", status="snoozed", review_at=FUTURE), NOW) == "snoozed"


@pytest.mark.parametrize("status", ["done", "dropped", "promoted"])
def test_finished_notes_are_never_due(status: str) -> None:
    assert effective_status(note("a", status=status, archived=True, review_at=PAST), NOW) == status


def test_archived_and_deleted_notes_do_not_trigger_a_review() -> None:
    assert not is_due(note("a", archived=True, review_at=PAST), NOW)
    assert not is_due(note("a", review_at=PAST, deleted_at=PAST), NOW)


def test_a_review_date_without_time_zone_counts_as_utc() -> None:
    assert is_due(note("a", review_at=PAST.replace(tzinfo=None)), NOW)


def test_the_default_review_date_is_today_plus_the_interval() -> None:
    assert default_review_at(NOW, 30) == NOW + timedelta(days=30)


def test_keep_only_moves_the_review_date() -> None:
    kept = keep(note("a", review_at=PAST), NOW, 10)
    assert kept == replace(note("a", review_at=PAST), review_at=NOW + timedelta(days=10))


def test_snooze_sets_the_status_and_takes_a_given_date_over_the_default() -> None:
    assert snooze(note("a"), NOW, 10).review_at == NOW + timedelta(days=10)
    chosen = snooze(note("a"), NOW, 10, FUTURE)
    assert (chosen.status, chosen.review_at) == ("snoozed", FUTURE)


@pytest.mark.parametrize("target", ["done", "dropped", "promoted"])
def test_finishing_moves_the_note_to_the_archive(target: str) -> None:
    done = finish(note("a"), target)
    assert (done.status, done.archived) == (target, True)


def test_finishing_needs_a_closing_status() -> None:
    with pytest.raises(NotesViolation) as error:
        finish(note("a"), "waiting")
    assert error.value.code == "note_target_invalid"


@pytest.mark.parametrize(
    "bad,code",
    [
        (note("a", archived=True, status="done"), "note_archived"),
        (note("a", deleted_at=PAST), "note_deleted"),
    ],
)
def test_a_note_that_is_not_in_use_rejects_changes(bad: Note, code: str) -> None:
    changes: list[Callable[[Note], Note]] = [
        lambda n: keep(n, NOW, 5),
        lambda n: snooze(n, NOW, 5),
        lambda n: finish(n, "done"),
    ]
    for change in changes:
        with pytest.raises(NotesViolation) as error:
            change(bad)
        assert error.value.code == code


def test_restore_brings_an_archived_note_back_to_waiting_with_a_new_date() -> None:
    back = restore(note("a", status="done", archived=True), None, NOW, 5)
    assert (back.status, back.archived, back.review_at) == ("waiting", False, NOW + timedelta(days=5))


def test_restore_refuses_a_note_that_is_not_archived_or_whose_topic_is_archived() -> None:
    with pytest.raises(NotesViolation) as error:
        restore(note("a"), None, NOW, 5)
    assert error.value.code == "note_not_archived"
    with pytest.raises(NotesViolation) as error:
        restore(note("a", status="done", archived=True, topic="t"), topic("t", archived_at=PAST), NOW, 5)
    assert error.value.code == "topic_archived"


def test_settings_accept_whole_numbers_within_their_limits() -> None:
    assert changed_settings(NotesSettings(), 5, 60) == NotesSettings(5, 60)
    assert changed_settings(NotesSettings(4, 7)) == NotesSettings(4, 7)


@pytest.mark.parametrize("depth,days", [(0, None), (11, None), (None, 0), (None, 4000)])
def test_settings_outside_their_limits_are_rejected(depth: int | None, days: int | None) -> None:
    with pytest.raises(InvalidInput):
        changed_settings(NotesSettings(), depth, days)
