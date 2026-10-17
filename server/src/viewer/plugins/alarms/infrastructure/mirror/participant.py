"""Datenbank ⇄ Einträge für den Spiegel: liest Wecker, vergibt Labels, schreibt Änderungen."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any

from viewer.core.application.ports import Clock, Database, Transaction
from viewer.core.application.sync import SyncChanges
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.alarms.application.ports import AlarmRepository
from viewer.plugins.alarms.domain.model import Alarm
from viewer.plugins.alarms.infrastructure.mirror.syntax import (
    ALARMS_FILE,
    KIND_ALARM,
    format_day,
    format_time,
    to_datetime,
)

_LABEL = re.compile(r"^[A-Z]+-\d+$")


def _time(value: str | None) -> datetime | None:
    return to_datetime(value) if value else None


class AlarmsParticipant:
    def __init__(
        self, alarms: AlarmRepository, registry: Any, project_store: Any, database: Database, clock: Clock
    ) -> None:
        self._alarms = alarms
        self._registry = registry
        self._projects = project_store
        self._database = database
        self._clock = clock

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def load(self, project: str) -> list[MirrorEntry]:
        with self._database.transaction() as tx:
            names = {p.uid: p.name for p in self._projects.list(tx, include_deleted=True)}
            return [
                self._entry(tx, project, alarm, names)
                for alarm in self._alarms.list_in(tx, [project], include_deleted=True)
            ]

    def _entry(self, tx: Transaction, project: str, alarm: Alarm, names: Mapping[str, str]) -> MirrorEntry:
        element = self._registry.get(tx, alarm.uid)
        fields = {
            "text": alarm.text,
            "at": format_time(alarm.at),
            "status": alarm.status,
            "snoozed_until": format_time(alarm.snoozed_until),
            "deleted": format_day(alarm.deleted_at),
        }
        refs: dict[str, tuple[str, ...]] = {}
        if alarm.target_uid:
            target = self._registry.get(tx, alarm.target_uid)
            if target is not None:
                same = target.project_uid == project
                refs["target"] = (
                    str(target.label)
                    if same
                    else f"{names.get(target.project_uid, target.project_uid)}:{target.label}",
                )
        elif alarm.target_text:
            refs["target"] = (alarm.target_text,)
        extra = {"created": format_day(element.created_at) if element else None}
        return MirrorEntry(KIND_ALARM, alarm.label, fields, refs, alarm.uid, extra=extra)

    def resolve_labels(self, project: str, labels: Collection[str]) -> Mapping[str, str]:
        found: dict[str, str] = {}
        with self._database.transaction() as tx:
            by_name = {p.name: p.uid for p in self._projects.list(tx)}
            for token in labels:
                qualifier, separator, bare = token.rpartition(":")
                if not separator:
                    qualifier, bare = "", token
                if not _LABEL.match(bare):
                    continue
                target = by_name.get(qualifier) if qualifier else project
                if target is None:
                    continue
                element = self._registry.find_by_label(tx, target, bare)
                if element is not None:
                    found[token] = f"{qualifier}:{element.label}" if qualifier else str(element.label)
        return found

    def assign_labels(
        self, project: str, entries: Sequence[MirrorEntry], tx: Transaction, taken: Collection[str] = ()
    ) -> Mapping[str, str]:
        self._registry.note_labels(tx, project, list(taken))
        return {str(e.placeholder): self._registry.reserve_label(tx, project, "alarm") for e in entries}

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def apply(self, project: str, changes: SyncChanges, tx: Transaction) -> None:
        created = {str(e.uid) for e in changes.created}
        new = {str(e.label): str(e.uid) for e in changes.created}
        for entry in changes.created:
            f = entry.fields
            self._registry.register_as(tx, project, "alarm", str(entry.uid), str(entry.label), f["text"])
            self._alarms.insert(
                tx,
                Alarm(
                    str(entry.uid), project, str(entry.label), f["text"], to_datetime(f["at"]), "Pending",
                    None, None, None, 1,
                ),
            )  # fmt: skip
        for entry in (*changes.created, *changes.updated):
            self._write(tx, project, entry, str(entry.uid) in created, new)
        for entry in changes.deleted:
            element = self._registry.get(tx, str(entry.uid))
            if element is not None and element.deleted_at is None:
                self._registry.mark_deleted(tx, element.uid)

    def _write(self, tx: Transaction, project: str, entry: MirrorEntry, is_new: bool, new: Mapping[str, str]) -> None:
        f = entry.fields
        stored = self._alarms.get(tx, str(entry.uid))
        assert stored is not None
        target_uid, target_text = self._target(tx, project, entry, new)
        alarm = replace(
            stored,
            text=f["text"],
            at=to_datetime(f["at"]),
            status=f["status"],
            snoozed_until=_time(f["snoozed_until"]),
            target_uid=target_uid,
            target_text=target_text,
        )
        if not is_new:
            alarm = replace(alarm, revision=self._registry.bump_revision(tx, alarm.uid, stored.revision))
            if alarm.text != stored.text:
                self._registry.set_title(tx, alarm.uid, alarm.text)
        self._alarms.update(tx, alarm)
        element = self._registry.get(tx, alarm.uid)
        day = f["deleted"]
        if day and element is not None and element.deleted_at is None:
            self._registry.mark_deleted(tx, alarm.uid, datetime.fromisoformat(f"{day}T00:00:00+00:00"))
        elif not day and element is not None and element.deleted_at is not None:
            self._registry.restore(tx, alarm.uid)

    def _target(
        self, tx: Transaction, project: str, entry: MirrorEntry, new: Mapping[str, str]
    ) -> tuple[str | None, str | None]:
        """Das Ziel als `uid` oder, wenn es in einem anderen Projekt liegt, das es hier nicht gibt, als Text. Ein
        unbekanntes Label im eigenen Projekt ist `unknown_reference`."""
        if not entry.refs.get("target"):
            return None, None
        token = entry.refs["target"][0]
        if token in new:
            return new[token], None
        qualifier, separator, bare = token.rpartition(":")
        if separator:
            match = next((p for p in self._projects.list(tx) if p.name == qualifier), None)
            element = self._registry.find_by_label(tx, match.uid, bare) if match is not None else None
            return (str(element.uid), None) if element is not None else (None, token)
        element = self._registry.find_by_label(tx, project, token)
        if element is None:
            line = entry.source_lines.get("target", (entry.source or (ALARMS_FILE, 1))[1])
            raise MirrorFormatError(
                "unknown_reference",
                f"`{token}` gab es im Projekt nie (verwendet von `{entry.label}`)",
                file=ALARMS_FILE,
                line=line,
            )
        return str(element.uid), None
