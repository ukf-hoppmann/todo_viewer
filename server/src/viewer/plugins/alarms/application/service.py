"""Anwendungsfälle für Wecker: anlegen, ändern, zurückstellen, erledigen, auslösen und den Termin setzen."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from viewer.core.application.ports import Clock, Database, EventBus, Scheduler, Transaction
from viewer.core.domain.errors import InvalidInput, NotFound
from viewer.core.domain.events import Event
from viewer.plugins.alarms.application.ports import AlarmRepository
from viewer.plugins.alarms.domain import model
from viewer.plugins.alarms.domain.model import Alarm, AlarmViolation, utc

ALARM_TOPIC = "alarms.alarm.changed"
DUE_TOPIC = "alarms.due"
SCHEDULER_OWNER = "alarms"
FIELDS = {"text", "at", "target"}
_LABEL = re.compile(r"^[A-Z]+-\d+$")


@dataclass(frozen=True)
class AlarmView:
    alarm: Alarm
    #: Das Element, auf das sich der Wecker bezieht (uid, label, title, kind), falls es eins gibt.
    target: Any | None


def _text(value: object) -> str:
    if not isinstance(value, str) or not " ".join(value.split()):
        raise InvalidInput("text fehlt", details={"field": "text"})
    return " ".join(value.split())


def _moment(name: str, value: object) -> datetime:
    if isinstance(value, datetime):
        return utc(value)
    if isinstance(value, str):
        try:
            return utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            pass
    raise InvalidInput(f"{name} ist kein Zeitpunkt (JJJJ-MM-TT[THH:MM])", details={"field": name})


class AlarmService:
    def __init__(
        self,
        alarms: AlarmRepository,
        registry: Any,
        database: Database,
        clock: Clock,
        events: EventBus,
        scheduler: Scheduler,
    ) -> None:
        self._alarms = alarms
        self._registry = registry
        self._database = database
        self._clock = clock
        self._events = events
        self._scheduler = scheduler

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def list_alarms(self, project_uids: Sequence[str] | None, due_only: bool = False) -> list[AlarmView]:
        with self._database.transaction() as tx:
            alarms = self._alarms.list_in(tx, project_uids)
            if due_only:
                alarms = [a for a in alarms if a.status == "Due"]
            return [self._view(tx, a) for a in alarms]

    def get(self, ref: str, project_uid: str | None) -> AlarmView:
        with self._database.transaction() as tx:
            return self._view(tx, self._resolve(tx, ref, project_uid))

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def create(self, project_uid: str, fields: Mapping[str, Any]) -> str:
        self._check_fields(fields)
        text = _text(fields.get("text"))
        at = _moment("at", fields.get("at"))
        with self._database.transaction() as tx:
            target = self._target(tx, fields.get("target"), project_uid)
            element = self._registry.register(tx, project_uid, "alarm", text)
            alarm = Alarm(
                element.uid, project_uid, element.label, text, at, "Pending", target, None, None, element.revision
            )
            self._alarms.insert(tx, alarm)
        self._changed(alarm.uid, "created")
        self.reschedule()
        return alarm.uid

    def update(self, ref: str, project_uid: str | None, version: int, fields: Mapping[str, Any]) -> str:
        """Ändert Text, Zeitpunkt und Ziel; ein neuer Zeitpunkt lässt den Wecker wieder warten."""
        self._check_fields(fields)
        with self._database.transaction() as tx:
            alarm = self._resolve(tx, ref, project_uid)
            if alarm.deleted_at is not None:
                raise AlarmViolation("alarm_deleted", f"{alarm.label} liegt im Papierkorb", alarm=alarm.label)
            updated = alarm
            if "text" in fields:
                updated = replace(updated, text=_text(fields["text"]))
            if "target" in fields:
                updated = replace(
                    updated, target_uid=self._target(tx, fields["target"], alarm.project_uid), target_text=None
                )
            if "at" in fields:
                updated = model.reschedule(updated, _moment("at", fields["at"]))
            self._save(tx, alarm, updated, version)
        self._changed(alarm.uid, "updated")
        self.reschedule()
        return alarm.uid

    def snooze(self, ref: str, project_uid: str | None, version: int, until: object = None) -> str:
        target = _moment("until", until) if until not in (None, "") else None
        return self._transition(ref, project_uid, version, lambda a: model.snooze(a, self._clock.now(), target))

    def finish(self, ref: str, project_uid: str | None, version: int) -> str:
        return self._transition(ref, project_uid, version, model.finish)

    # --- Auslösen und Termin --------------------------------------------------------------------------------------

    def fire(self) -> list[str]:
        """Setzt die fälligen Wecker auf `Due` und meldet sie; setzt danach den nächsten Termin. Gibt die `uid`s der
        ausgelösten Wecker zurück."""
        fired: list[str] = []
        with self._database.transaction() as tx:
            for alarm in model.due_now(self._alarms.list_in(tx, None), self._clock.now()):
                revision = self._registry.bump_revision(tx, alarm.uid, alarm.revision)
                self._alarms.update(tx, replace(model.fire(alarm), revision=revision))
                fired.append(alarm.uid)
        if fired:
            self._events.publish(Event(DUE_TOPIC, {"uids": fired}, public=True))
            for uid in fired:
                self._changed(uid, "due")
        self.reschedule()
        return fired

    def _run(self) -> None:
        self.fire()

    def reschedule(self) -> None:
        """Genau ein Termin auf den nächsten wartenden Wecker (ein vergangener wird sofort nachgeholt)."""
        now = self._clock.now()
        with self._database.transaction() as tx:
            at = model.next_due(self._alarms.list_in(tx, None), now)
        self._scheduler.schedule(SCHEDULER_OWNER, at, self._run)

    def on_elements_changed(self, event: Event) -> None:
        """Papierkorb, Wiederherstellen, Sync: der nächste Termin kann sich geändert haben."""
        self.reschedule()
        self._events.publish(Event(ALARM_TOPIC, {"change": "reloaded"}, public=True))

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _transition(self, ref: str, project_uid: str | None, version: int, change: Any) -> str:
        with self._database.transaction() as tx:
            alarm = self._resolve(tx, ref, project_uid)
            self._save(tx, alarm, change(alarm), version)
        self._changed(alarm.uid, "updated")
        self.reschedule()
        return alarm.uid

    def _save(self, tx: Transaction, before: Alarm, after: Alarm, version: int) -> None:
        revision = self._registry.bump_revision(tx, before.uid, version)
        self._alarms.update(tx, replace(after, revision=revision))
        if after.text != before.text:
            self._registry.set_title(tx, before.uid, after.text)

    def _resolve(self, tx: Transaction, ref: str, project_uid: str | None) -> Alarm:
        alarm = self._alarms.get(tx, ref)
        if alarm is None and project_uid is not None and _LABEL.match(ref.strip()):
            element = self._registry.find_by_label(tx, project_uid, ref)
            alarm = self._alarms.get(tx, element.uid) if element else None
        if alarm is None:
            if project_uid is None and _LABEL.match(ref.strip()):
                raise InvalidInput(
                    f"'{ref}' ist keine uid; für ein Label braucht es das Projekt", details={"field": "project"}
                )
            raise NotFound(f"Wecker {ref} gibt es nicht", details={"ref": ref})
        return alarm

    def _target(self, tx: Transaction, value: object, project_uid: str) -> str | None:
        if value in (None, ""):
            return None
        element = self._registry.get(tx, str(value)) or self._registry.find_by_label(tx, project_uid, str(value))
        if element is None:
            raise NotFound(f"Ziel {value} gibt es nicht", details={"ref": str(value)})
        return str(element.uid)

    def _view(self, tx: Transaction, alarm: Alarm) -> AlarmView:
        return AlarmView(alarm, self._registry.get(tx, alarm.target_uid) if alarm.target_uid else None)

    @staticmethod
    def _check_fields(fields: Mapping[str, Any]) -> None:
        unknown = sorted(set(fields) - FIELDS)
        if unknown:
            raise InvalidInput(
                f"Unbekannte Felder: {', '.join(unknown)}", details={"field": unknown[0], "allowed": sorted(FIELDS)}
            )

    def _changed(self, uid: str, change: str) -> None:
        self._events.publish(Event(ALARM_TOPIC, {"uid": uid, "change": change}, public=True))
