"""Memos und Topics für Tests der Domäne des Plugins `memos`."""

from __future__ import annotations

from datetime import UTC, datetime

from viewer.plugins.memos.domain.due import Trigger
from viewer.plugins.memos.domain.model import Memo, Topic

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


def memo(
    uid: str,
    topic: str | None = None,
    status: str = "waiting",
    archived: bool = False,
    review_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> Memo:
    return Memo(
        uid=uid,
        project_uid="p",
        label=uid.upper(),
        summary=uid,
        body=None,
        status=status,
        topic_uid=topic,
        review_at=review_at,
        trigger_mode="any",
        archived=archived,
        revision=1,
        deleted_at=deleted_at,
    )


def topic(
    uid: str,
    parent: str | None = None,
    archived_at: datetime | None = None,
    deleted_at: datetime | None = None,
    system: bool = False,
    project: str = "p",
) -> Topic:
    return Topic(
        uid=uid,
        project_uid=project,
        label=uid.upper(),
        name=uid,
        parent_uid=parent,
        due_at=None,
        archived_at=archived_at,
        system=system,
        revision=1,
        deleted_at=deleted_at,
    )


def trigger(
    uid: str,
    kind: str = "event",
    target: str | None = "item",
    status: str | None = "Completed",
    fired_at: datetime | None = None,
    already_met: bool = False,
    memo_uid: str = "n",
) -> Trigger:
    return Trigger(uid, memo_uid, kind, target, status, fired_at, already_met)
