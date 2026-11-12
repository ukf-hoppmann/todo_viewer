"""Anwendungsfälle für Topics: anlegen, ändern, verschieben, archivieren, reaktivieren und löschen."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.events import Event
from viewer.plugins.memos.application.common import (
    ELEMENT_TOPIC,
    TOPIC_TOPIC,
    Resolver,
    moment_field,
    text_field,
    unknown_fields,
)
from viewer.plugins.memos.application.ports import MemoRepository, SettingsRepository, TopicRepository
from viewer.plugins.memos.domain.model import ARCHIVE_TOPIC_NAME, MemosViolation, Topic
from viewer.plugins.memos.domain.topics import (
    ARCHIVE_TARGET,
    Choice,
    Content,
    TopicPlan,
    check_parent,
    content,
    plan_archive,
    plan_delete,
    plan_reactivate,
)

TOPIC_FIELDS = {"name", "due_at"}


class TopicService:
    def __init__(
        self,
        memos: MemoRepository,
        topics: TopicRepository,
        settings: SettingsRepository,
        resolver: Resolver,
        registry: Any,
        database: Database,
        clock: Clock,
        events: EventBus,
    ) -> None:
        self._memos = memos
        self._topics = topics
        self._settings = settings
        self._resolver = resolver
        self._registry = registry
        self._database = database
        self._clock = clock
        self._events = events

    def create(self, project_uid: str, name: str, parent_uid: str | None, due_at: object) -> str:
        clean = text_field("name", name)
        assert clean is not None
        due = moment_field("due_at", due_at)
        with self._database.transaction() as tx:
            check_parent(
                self._topics.list_in(tx, [project_uid]),
                project_uid,
                parent_uid,
                None,
                self._settings.load(tx).max_topic_depth,
            )
            element = self._registry.register(tx, project_uid, "topic", clean)
            topic = Topic(
                element.uid, project_uid, element.label, clean, parent_uid, due, None, False, element.revision
            )
            self._topics.insert(tx, topic)
        self._changed(topic.uid, "created")
        return topic.uid

    def get(self, ref: str, project_uid: str | None) -> Topic:
        with self._database.transaction() as tx:
            return self._resolver.topic(tx, ref, project_uid)

    def content_of(self, ref: str, project_uid: str | None) -> Content:
        with self._database.transaction() as tx:
            topic = self._resolver.topic(tx, ref, project_uid)
            return content(
                self._topics.list_in(tx, [topic.project_uid]), self._memos.list_in(tx, [topic.project_uid]), topic.uid
            )

    def update(self, ref: str, project_uid: str | None, version: int, fields: Mapping[str, Any]) -> str:
        unknown_fields(dict(fields), TOPIC_FIELDS)
        with self._database.transaction() as tx:
            topic = self._live(tx, ref, project_uid)
            updated = topic
            if "name" in fields:
                if topic.system:
                    raise MemosViolation("topic_system", f"Das Topic {topic.name} lässt sich nicht umbenennen")
                name = text_field("name", fields["name"])
                assert name is not None
                updated = replace(updated, name=name)
            if "due_at" in fields:
                updated = replace(updated, due_at=moment_field("due_at", fields["due_at"]))
            self._save(tx, topic, updated, version)
        self._changed(topic.uid, "updated")
        return topic.uid

    def move(self, ref: str, project_uid: str | None, version: int, parent_uid: str | None) -> str:
        with self._database.transaction() as tx:
            topic = self._live(tx, ref, project_uid)
            if topic.system:
                raise MemosViolation("topic_system", f"Das Topic {topic.name} lässt sich nicht verschieben")
            check_parent(
                self._topics.list_in(tx, [topic.project_uid]),
                topic.project_uid,
                parent_uid,
                topic.uid,
                self._settings.load(tx).max_topic_depth,
            )
            self._save(tx, topic, replace(topic, parent_uid=parent_uid), version)
        self._changed(topic.uid, "moved")
        return topic.uid

    def archive(self, ref: str, project_uid: str | None, version: int, choice: Choice | None) -> str:
        now = self._clock.now()
        with self._database.transaction() as tx:
            topic = self._live(tx, ref, project_uid)
            topics, memos = self._everything(tx, topic)
            plan = plan_archive(topics, memos, topic.uid, choice)
            self._apply_moves(tx, topic, plan)
            by_uid = {t.uid: t for t in topics}
            for uid in plan.topics:
                self._save(
                    tx, by_uid[uid], replace(by_uid[uid], archived_at=now), version if uid == topic.uid else None
                )
            for memo in (n for n in memos if n.uid in plan.memos):
                self._touch_memo(tx, replace(memo, archived=True))
        self._changed(topic.uid, "archived")
        return topic.uid

    def reactivate(self, ref: str, project_uid: str | None, version: int) -> str:
        with self._database.transaction() as tx:
            topic = self._resolver.topic(tx, ref, project_uid)
            topics, memos = self._everything(tx, topic)
            plan = plan_reactivate(topics, memos, topic.uid)
            by_uid = {t.uid: t for t in topics}
            for uid in plan.topics:
                self._save(
                    tx, by_uid[uid], replace(by_uid[uid], archived_at=None), version if uid == topic.uid else None
                )
            for memo in (n for n in memos if n.uid in plan.memos):
                self._touch_memo(tx, replace(memo, archived=False))
        self._changed(topic.uid, "reactivated")
        return topic.uid

    def delete(self, ref: str, project_uid: str | None, version: int, choice: Choice | None) -> int:
        """Legt das Topic mit den nicht umgehängten Memos und seinen Unter-Topics in den Papierkorb. Gibt die
        Zahl der gelöschten Elemente zurück."""
        at = self._clock.now()
        with self._database.transaction() as tx:
            topic = self._live(tx, ref, project_uid)
            topics, memos = self._everything(tx, topic)
            plan = plan_delete(topics, memos, topic.uid, choice)
            self._registry.bump_revision(tx, topic.uid, version)
            self._apply_moves(tx, topic, plan)
            uids = [*plan.topics, *plan.memos]
            for uid in uids:
                self._registry.mark_deleted(tx, uid, at)
        self._changed(topic.uid, "deleted")
        self._events.publish(Event(ELEMENT_TOPIC, {"change": "deleted", "uids": uids}, public=True))
        return len(uids)

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _live(self, tx: Transaction, ref: str, project_uid: str | None) -> Topic:
        topic = self._resolver.topic(tx, ref, project_uid)
        if topic.deleted_at is not None:
            raise MemosViolation("topic_deleted", f"{topic.label} liegt im Papierkorb; erst wiederherstellen")
        return topic

    def _everything(self, tx: Transaction, topic: Topic) -> tuple[list[Topic], list[Any]]:
        return self._topics.list_in(tx, [topic.project_uid]), self._memos.list_in(tx, [topic.project_uid])

    def _save(self, tx: Transaction, before: Topic, after: Topic, version: int | None) -> None:
        revision = self._registry.bump_revision(tx, before.uid, before.revision if version is None else version)
        self._topics.update(tx, replace(after, revision=revision))
        if after.name != before.name:
            self._registry.set_title(tx, before.uid, after.name)

    def _touch_memo(self, tx: Transaction, memo: Any) -> None:
        revision = self._registry.bump_revision(tx, memo.uid, memo.revision)
        self._memos.update(tx, replace(memo, revision=revision))

    def _apply_moves(self, tx: Transaction, topic: Topic, plan: TopicPlan) -> None:
        if not plan.moves:
            return
        archive_uid = self._archive_topic(tx, topic.project_uid) if ARCHIVE_TARGET in plan.moves.values() else None
        for uid, target in plan.moves.items():
            memo = self._memos.get(tx, uid)
            assert memo is not None
            self._touch_memo(tx, replace(memo, topic_uid=archive_uid if target == ARCHIVE_TARGET else target))

    def _archive_topic(self, tx: Transaction, project_uid: str) -> str:
        """Das neutrale Topic „Archiviert“; beim ersten Bedarf wird es angelegt."""
        found = self._topics.archive_topic_of(tx, project_uid)
        if found is not None:
            return found.uid
        element = self._registry.register(tx, project_uid, "topic", ARCHIVE_TOPIC_NAME)
        self._topics.insert(
            tx,
            Topic(
                element.uid, project_uid, element.label, ARCHIVE_TOPIC_NAME, None, None, None, True, element.revision
            ),
        )
        return str(element.uid)

    def _changed(self, uid: str, change: str) -> None:
        self._events.publish(Event(TOPIC_TOPIC, {"uid": uid, "change": change}, public=True))
