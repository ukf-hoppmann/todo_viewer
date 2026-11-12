"""Anwendungsfälle für Memos: lesen, anlegen, ändern und durch den Lebenszyklus führen."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.events import Event
from viewer.plugins.memos.application.common import (
    MEMO_TOPIC,
    moment_field,
    text_field,
    unknown_fields,
    usable_topic,
)
from viewer.plugins.memos.application.deps import Deps
from viewer.plugins.memos.application.telling import tell_items
from viewer.plugins.memos.application.triggers import Announce, TriggerService
from viewer.plugins.memos.domain import lifecycle
from viewer.plugins.memos.domain.due import DueState, Trigger, due_state, reset, trigger_arrived
from viewer.plugins.memos.domain.hints import Hint
from viewer.plugins.memos.domain.model import (
    STATUSES,
    TRIGGER_MODES,
    Memo,
    Topic,
    default_review_at,
)

MEMO_FIELDS = {"summary", "body", "topic", "review_at", "trigger_mode"}


@dataclass(frozen=True)
class IndexedMemo:
    memo: Memo
    #: Der abgeleitete Status (`due`, wenn das Memo fällig ist).
    status: str


@dataclass(frozen=True)
class IndexedTopic:
    topic: Topic
    #: Offene (nicht archivierte) Memos direkt im Topic und in allen Unter-Topics.
    open_memos: int
    #: Davon fällige.
    due_memos: int


@dataclass(frozen=True)
class MemosIndex:
    topics: list[IndexedTopic]
    memos: list[IndexedMemo]


@dataclass(frozen=True)
class TriggerView:
    trigger: Trigger
    #: Das Item eines Ereignisses (uid, label, title), sonst leer.
    target: Any | None
    arrived: bool


@dataclass(frozen=True)
class MemoDetail:
    memo: Memo
    state: DueState
    #: Von der Wurzel bis zum Topic des Memos.
    path: list[Topic]
    triggers: list[TriggerView] = field(default_factory=list)
    #: Die offenen Hinweise an das Memo.
    hints: list[Hint] = field(default_factory=list)
    #: Der Elementtitel (Label, Titel) zu den `source_uid` der Hinweise.
    sources: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return self.state.status


@dataclass(frozen=True)
class DueEntry:
    memo: Memo
    state: DueState
    path: list[Topic]
    triggers: list[TriggerView]
    hints: list[Hint]


class MemoService:
    def __init__(self, deps: Deps, triggers: TriggerService) -> None:
        self._d = deps
        self._triggers = triggers

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def _states(self, tx: Transaction, memos: Sequence[Memo], topics: Mapping[str, Topic]) -> dict[str, DueState]:
        """Der abgeleitete Zustand jedes Memos: mit seinen Auslösern, seinem Topic und seinen offenen Hinweisen."""
        uids = [memo.uid for memo in memos]
        triggers = self._d.triggers.for_memos(tx, uids)
        hints = self._d.hints.open_for(tx, uids)
        now = self._d.clock.now()
        return {
            memo.uid: due_state(
                memo,
                triggers.get(memo.uid, []),
                topics.get(memo.topic_uid) if memo.topic_uid else None,
                len(hints.get(memo.uid, [])),
                now,
            )
            for memo in memos
        }

    def index(self, project_uids: Sequence[str] | None, statuses: Sequence[str] = (), query: str = "") -> MemosIndex:
        """Topics (alle, mit Zählern) und die Memos, die Status und Text durchlassen."""
        unknown = [status for status in statuses if status not in STATUSES]
        if unknown:
            raise InvalidInput(
                f"Unbekannte Status: {', '.join(unknown)}", details={"field": "status", "allowed": list(STATUSES)}
            )
        needle = query.strip().lower()
        with self._d.database.transaction() as tx:
            topics = self._d.topics.list_in(tx, project_uids)
            memos = self._d.memos.list_in(tx, project_uids)
            by_uid = {topic.uid: topic for topic in topics}
            states = self._states(tx, memos, by_uid)
        open_count: dict[str, int] = {}
        due_count: dict[str, int] = {}
        for memo in memos:
            if memo.archived:
                continue
            current = memo.topic_uid
            while current is not None and current in by_uid:
                open_count[current] = open_count.get(current, 0) + 1
                if states[memo.uid].status == "due":
                    due_count[current] = due_count.get(current, 0) + 1
                current = by_uid[current].parent_uid
        indexed = [
            IndexedMemo(memo, states[memo.uid].status)
            for memo in memos
            if (not statuses or states[memo.uid].status in statuses)
            and (not needle or needle in memo.summary.lower() or needle in memo.label.lower())
        ]
        return MemosIndex([IndexedTopic(t, open_count.get(t.uid, 0), due_count.get(t.uid, 0)) for t in topics], indexed)

    def get(self, ref: str, project_uid: str | None) -> MemoDetail:
        with self._d.database.transaction() as tx:
            memo = self._d.resolver.memo(tx, ref, project_uid)
            path = self._path(tx, memo)
            topic = path[-1] if path else None
            triggers = self._d.triggers.for_memos(tx, [memo.uid]).get(memo.uid, [])
            hints = self._d.hints.open_for(tx, [memo.uid]).get(memo.uid, [])
            state = due_state(memo, triggers, topic, len(hints), self._d.clock.now())
            views = self._trigger_views(tx, triggers, topic)
            sources = {}
            for hint in hints:
                element = self._d.registry.get(tx, hint.source_uid)
                if element is not None:
                    sources[hint.source_uid] = element
        return MemoDetail(memo, state, path, views, hints, sources)

    def due(self, project_uids: Sequence[str] | None) -> list[DueEntry]:
        """Die fälligen Memos mit Grund, eingetretenen Auslösern und offenen Hinweisen."""
        with self._d.database.transaction() as tx:
            topics = {t.uid: t for t in self._d.topics.list_in(tx, project_uids)}
            memos = self._d.memos.list_in(tx, project_uids)
            states = self._states(tx, memos, topics)
            entries = []
            for memo in memos:
                if states[memo.uid].status != "due":
                    continue
                path = self._path(tx, memo)
                triggers = self._d.triggers.for_memos(tx, [memo.uid]).get(memo.uid, [])
                views = self._trigger_views(tx, triggers, topics.get(memo.topic_uid) if memo.topic_uid else None)
                hints = self._d.hints.open_for(tx, [memo.uid]).get(memo.uid, [])
                entries.append(DueEntry(memo, states[memo.uid], path, views, hints))
        return entries

    def _path(self, tx: Transaction, memo: Memo) -> list[Topic]:
        path: list[Topic] = []
        current = self._d.topics.get(tx, memo.topic_uid) if memo.topic_uid else None
        while current is not None and len(path) < 50:
            path.insert(0, current)
            current = self._d.topics.get(tx, current.parent_uid) if current.parent_uid else None
        return path

    def _trigger_views(self, tx: Transaction, triggers: Sequence[Trigger], topic: Topic | None) -> list[TriggerView]:
        now = self._d.clock.now()
        return [
            TriggerView(
                trigger,
                self._d.registry.get(tx, trigger.target_uid) if trigger.target_uid else None,
                trigger_arrived(trigger, topic, now),
            )
            for trigger in triggers
        ]

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def create(self, project_uid: str, fields: Mapping[str, Any]) -> str:
        unknown_fields(dict(fields), MEMO_FIELDS)
        summary = text_field("summary", fields.get("summary"))
        assert summary is not None
        body = text_field("body", fields.get("body"), required=False)
        mode = self._mode(fields.get("trigger_mode", "any"))
        review_at = moment_field("review_at", fields.get("review_at"))
        with self._d.database.transaction() as tx:
            usable_topic(self._d.topics, tx, fields.get("topic"), project_uid)
            review_at = review_at or default_review_at(self._d.clock.now(), self._d.settings.load(tx).review_days)
            element = self._d.registry.register(tx, project_uid, "memo", summary)
            memo = Memo(
                element.uid,
                project_uid,
                element.label,
                summary,
                body,
                "waiting",
                fields.get("topic"),
                review_at,
                mode,
                False,
                element.revision,
            )
            self._d.memos.insert(tx, memo)
        self._changed(memo.uid, "created")
        return memo.uid

    def update(self, ref: str, project_uid: str | None, version: int, fields: Mapping[str, Any]) -> str:
        """Ändert die genannten Felder eines Memos in Gebrauch; ein geänderter Text setzt ein neues Prüfdatum, wenn
        keines mitkommt."""
        unknown_fields(dict(fields), MEMO_FIELDS)
        with self._d.database.transaction() as tx:
            memo = self._d.resolver.memo(tx, ref, project_uid)
            lifecycle.check_open(memo)
            updated = memo
            if "summary" in fields:
                summary = text_field("summary", fields["summary"])
                assert summary is not None
                updated = replace(updated, summary=summary)
            if "body" in fields:
                updated = replace(updated, body=text_field("body", fields["body"], required=False))
            if "topic" in fields:
                usable_topic(self._d.topics, tx, fields["topic"], memo.project_uid)
                updated = replace(updated, topic_uid=fields["topic"])
            if "trigger_mode" in fields:
                updated = replace(updated, trigger_mode=self._mode(fields["trigger_mode"]))
            if "review_at" in fields:
                updated = replace(updated, review_at=moment_field("review_at", fields["review_at"]))
            elif updated.summary != memo.summary or updated.body != memo.body:
                days = self._d.settings.load(tx).review_days
                updated = replace(updated, review_at=default_review_at(self._d.clock.now(), days))
            self._save(tx, memo, updated, version)
        self._changed(memo.uid, "updated")
        return memo.uid

    def keep(self, ref: str, project_uid: str | None, version: int) -> str:
        return self._transition(
            ref, project_uid, version, lambda tx, memo: lifecycle.keep(memo, self._d.clock.now(), self._days(tx))
        )

    def snooze(
        self,
        ref: str,
        project_uid: str | None,
        version: int,
        review_at: object = None,
        trigger: Mapping[str, Any] | None = None,
    ) -> str:
        """Zurückgestellt: gefeuerte Auslöser feuern wieder neu, ein vorbeigegangener Topic-Termin fällt weg; ein neuer
        Auslöser (`trigger`: `kind`, `target`, `status`) ersetzt alle alten."""
        until = moment_field("review_at", review_at)
        announce = Announce()

        def apply(tx: Transaction, memo: Memo) -> Memo:
            now = self._d.clock.now()
            changed = lifecycle.snooze(memo, now, self._days(tx), until)
            topic = self._d.topics.get(tx, memo.topic_uid) if memo.topic_uid else None
            old = self._d.triggers.for_memos(tx, [memo.uid]).get(memo.uid, [])
            if trigger is not None:
                for entry in old:
                    self._triggers.remove_in_tx(tx, entry, announce)
                self._triggers.create_in_tx(
                    tx, changed, str(trigger.get("kind", "")), trigger.get("target"), trigger.get("status"), announce
                )
                return changed
            kept, removed = reset(old, topic, now)
            for entry in kept:
                self._d.triggers.update(tx, entry)
            for uid in removed:
                self._d.triggers.delete(tx, uid)
            return changed

        uid = self._transition(ref, project_uid, version, apply)
        announce.publish(self._d)
        return uid

    def finish(self, ref: str, project_uid: str | None, version: int, target: str) -> str:
        """Erledigt, verworfen oder befördert: das Memo wandert ins Archiv; verworfen und befördert sagt es den Items,
        auf die sie verweist."""

        def apply(tx: Transaction, memo: Memo) -> Memo:
            done = lifecycle.finish(memo, target)
            cause = {"dropped": "memo_dropped", "promoted": "memo_promoted"}.get(target)
            if cause is not None:
                tell_items(self._d, tx, memo, cause)
            return done

        return self._transition(ref, project_uid, version, apply)

    def restore(self, ref: str, project_uid: str | None, version: int) -> str:
        def apply(tx: Transaction, memo: Memo) -> Memo:
            topic = self._d.topics.get(tx, memo.topic_uid) if memo.topic_uid else None
            return lifecycle.restore(memo, topic, self._d.clock.now(), self._days(tx))

        return self._transition(ref, project_uid, version, apply)

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _transition(self, ref: str, project_uid: str | None, version: int, change: Callable[..., Memo]) -> str:
        with self._d.database.transaction() as tx:
            memo = self._d.resolver.memo(tx, ref, project_uid)
            self._save(tx, memo, change(tx, memo), version)
        self._changed(memo.uid, "updated")
        return memo.uid

    def _save(self, tx: Transaction, before: Memo, after: Memo, version: int) -> None:
        revision = self._d.registry.bump_revision(tx, before.uid, version)
        self._d.memos.update(tx, replace(after, revision=revision))
        if after.summary != before.summary:
            self._d.registry.set_title(tx, before.uid, after.summary)

    def _days(self, tx: Transaction) -> int:
        return self._d.settings.load(tx).review_days

    @staticmethod
    def _mode(value: object) -> str:
        if value not in TRIGGER_MODES:
            raise InvalidInput("trigger_mode ist any oder all", details={"field": "trigger_mode"})
        return str(value)

    def _changed(self, uid: str, change: str) -> None:
        self._d.events.publish(Event(MEMO_TOPIC, {"uid": uid, "change": change}, public=True))
