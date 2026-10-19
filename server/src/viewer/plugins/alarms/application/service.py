"""Anwendungsfälle für Wecker: anlegen, ändern, zurückstellen, erledigen, rückgängig machen, auslösen, den Elementen
folgen, aufräumen und den Termin setzen."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, tzinfo
from typing import Any

from viewer.core.application.ports import Clock, Database, EventBus, Scheduler, Transaction
from viewer.core.domain.errors import InvalidInput, NotFound
from viewer.core.domain.events import Event
from viewer.plugins.alarms.application.ports import AlarmRepository
from viewer.plugins.alarms.domain import model
from viewer.plugins.alarms.domain.model import Alarm, AlarmViolation, utc
from viewer.plugins.alarms.domain.series import REPEATS

ALARM_TOPIC = "alarms.alarm.changed"
DUE_TOPIC = "alarms.due"
SCHEDULER_OWNER = "alarms"
FIELDS = {"text", "at", "targets", "target", "repeat"}
#: Ereignisse, nach denen sich der nächste Termin geändert haben kann (Papierkorb, Wiederherstellen, Sync).
RELOAD_TOPICS = frozenset({"workspace.element.changed", "core.sync.state"})
_LABEL = re.compile(r"^[A-Z]+-\d+$")


@dataclass(frozen=True)
class TargetView:
    #: Das Element (uid, label, title, kind, deleted_at) aus dem Register.
    element: Any
    open: bool


@dataclass(frozen=True)
class AlarmView:
    alarm: Alarm
    targets: list[TargetView]
    #: Verpasste Serientermine seit `at` (abgeleitet); 0 ohne Wiederholung.
    missed: int = 0


def _text(value: object, required: bool) -> str:
    cleaned = " ".join(value.split()) if isinstance(value, str) else ""
    if value is not None and not isinstance(value, str):
        raise InvalidInput("text ist kein Text", details={"field": "text"})
    if required and not cleaned:
        raise InvalidInput("text fehlt (ein Wecker ohne Elemente braucht einen Text)", details={"field": "text"})
    return cleaned


def _moment(name: str, value: object) -> datetime:
    if isinstance(value, datetime):
        return utc(value)
    if isinstance(value, str):
        try:
            return utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            pass
    raise InvalidInput(f"{name} ist kein Zeitpunkt (JJJJ-MM-TT[THH:MM])", details={"field": name})


def _repeat(value: object) -> str:
    if value not in REPEATS:
        raise InvalidInput(
            f"repeat ist keine Wiederholung ({', '.join(REPEATS)})",
            details={"field": "repeat", "allowed": list(REPEATS)},
        )
    return str(value)


def _refs(fields: Mapping[str, Any]) -> list[str] | None:
    """Die Elemente aus `targets` (Liste) oder dem früheren `target` (eins oder `null`); `None`, wenn keins genannt
    ist."""
    if "targets" in fields and "target" in fields:
        raise InvalidInput("Nur targets oder target angeben", details={"field": "target"})
    if "targets" in fields:
        value = fields["targets"]
        if value is None:
            return []
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise InvalidInput("targets ist eine Liste aus uid oder Label", details={"field": "targets"})
        return [v for v in value if v.strip()]
    if "target" in fields:
        value = fields["target"]
        return [str(value)] if value not in (None, "") else []
    return None


class AlarmService:
    def __init__(
        self,
        alarms: AlarmRepository,
        registry: Any,
        database: Database,
        clock: Clock,
        zone: tzinfo,
        events: EventBus,
        scheduler: Scheduler,
    ) -> None:
        self._alarms = alarms
        self._registry = registry
        self._database = database
        self._clock = clock
        self._zone = zone
        self._events = events
        self._scheduler = scheduler
        #: Was die Oberfläche zuletzt von den Elementen der Wecker wissen konnte (offen, Titel): ändert es sich, meldet
        #: der Dienst `reloaded`, damit Karten und Detail neu laden.
        self._seen: dict[str, tuple[tuple[bool, str], ...]] = {}

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
        refs = _refs(fields) or []
        at = _moment("at", fields.get("at"))
        repeat = _repeat(fields.get("repeat", "none"))
        with self._database.transaction() as tx:
            targets = self._targets(tx, refs, project_uid)
            text = _text(fields.get("text"), required=not targets)
            element = self._registry.register(tx, project_uid, "alarm", self._title(tx, text, targets))
            alarm = Alarm(
                element.uid, project_uid, element.label, text, at, "Pending", targets, None, None, element.revision
            )
            alarm = model.with_repeat(alarm, repeat)
            self._alarms.insert(tx, alarm)
        self._changed(alarm.uid, "created")
        self.follow()
        self.reschedule()
        return alarm.uid

    def update(self, ref: str, project_uid: str | None, version: int, fields: Mapping[str, Any]) -> str:
        """Ändert Text, Zeitpunkt, Wiederholung und Elemente; ein neuer Zeitpunkt lässt den Wecker wieder warten."""
        self._check_fields(fields)
        refs = _refs(fields)
        with self._database.transaction() as tx:
            alarm = self._resolve(tx, ref, project_uid)
            if alarm.deleted_at is not None:
                raise AlarmViolation("alarm_deleted", f"{alarm.label} liegt im Papierkorb", alarm=alarm.label)
            updated = alarm
            if refs is not None:
                updated = replace(updated, targets=self._targets(tx, refs, alarm.project_uid), target_text=None)
            if "text" in fields or refs is not None:
                text = fields.get("text", updated.text)
                updated = replace(updated, text=_text(text, required=not updated.targets))
            if "repeat" in fields:
                updated = model.with_repeat(updated, _repeat(fields["repeat"]))
            if "at" in fields:
                updated = model.reschedule(updated, _moment("at", fields["at"]))
            self._save(tx, alarm, updated, version)
        self._changed(alarm.uid, "updated")
        self.follow()
        self.reschedule()
        return alarm.uid

    def snooze(self, ref: str, project_uid: str | None, version: int, until: object = None) -> str:
        target = _moment("until", until) if until not in (None, "") else None
        return self._transition(ref, project_uid, version, lambda a: model.snooze(a, self._clock.now(), target))

    def finish(self, ref: str, project_uid: str | None, version: int) -> str:
        return self._transition(ref, project_uid, version, lambda a: model.finish(a, self._clock.now(), self._zone))

    def reopen(self, ref: str, project_uid: str | None, version: int) -> str:
        return self._transition(ref, project_uid, version, lambda a: model.undo(a, self._clock.now()))

    # --- Auslösen, Elementen folgen, Aufräumen und Termin -----------------------------------------------------

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

    def purge(self) -> list[str]:
        """Löscht die Wecker endgültig, die seit `PURGE_AFTER` erledigt oder erloschen sind (ohne Papierkorb)."""
        with self._database.transaction() as tx:
            gone = model.to_purge(self._alarms.list_in(tx, None), self._clock.now())
            for alarm in gone:
                self._alarms.delete(tx, alarm.uid)
                self._registry.purge(tx, alarm.uid)
        for alarm in gone:
            self._seen.pop(alarm.uid, None)
            self._changed(alarm.uid, "purged")
        return [a.uid for a in gone]

    def follow(self) -> list[str]:
        """Die Wecker folgen ihren Elementen: ist keins mehr offen, erlöschen sie; ist eins wieder offen, kehrt ein
        erloschener zurück. Gibt die `uid`s der geänderten Wecker zurück; meldet `reloaded`, wenn sich an den Elementen
        etwas geändert hat, das die Oberfläche zeigt (offen, Titel)."""
        now = self._clock.now()
        changed: list[str] = []
        seen: dict[str, tuple[tuple[bool, str], ...]] = {}
        with self._database.transaction() as tx:
            for alarm in self._alarms.list_in(tx, None):
                if not alarm.targets:
                    continue
                states = [self._registry.is_open(tx, uid) for uid in alarm.targets]
                titles = [getattr(self._registry.get(tx, uid), "title", "") for uid in alarm.targets]
                seen[alarm.uid] = tuple(zip(states, titles, strict=True))
                after = model.follow_targets(alarm, states, now)
                if after != alarm:
                    revision = self._registry.bump_revision(tx, alarm.uid, alarm.revision)
                    self._alarms.update(tx, replace(after, revision=revision))
                    changed.append(alarm.uid)
        for uid in changed:
            self._changed(uid, "updated")
        if not changed and seen != self._seen and self._seen:
            self._events.publish(Event(ALARM_TOPIC, {"change": "reloaded"}, public=True))
        self._seen = seen
        return changed

    def start(self) -> None:
        """Nach dem Start einmal sofort laufen: erst dann haben alle Plugins ihre Prüfung „offen“ angemeldet. Der Lauf
        folgt den Elementen, holt verpasste Wecker nach, räumt auf und setzt den nächsten Termin."""
        self._scheduler.schedule(SCHEDULER_OWNER, self._clock.now(), self._run)

    def _run(self) -> None:
        self.follow()
        self.fire()
        self.purge()
        self.reschedule()

    def reschedule(self) -> None:
        """Genau ein Termin: der nächste wartende Wecker (ein vergangener wird sofort nachgeholt) oder das nächste
        Aufräumen."""
        now = self._clock.now()
        with self._database.transaction() as tx:
            at = model.next_wakeup(self._alarms.list_in(tx, None), now)
        self._scheduler.schedule(SCHEDULER_OWNER, at, self._run)

    def on_event(self, event: Event) -> None:
        """Jedes fremde Ereignis kann den Zustand eines Elements geändert haben: die Wecker folgen ihren Elementen.
        Papierkorb, Wiederherstellen und Sync können zudem den nächsten Termin ändern."""
        if event.topic.startswith("alarms."):
            return
        changed = self.follow()
        if changed or event.topic in RELOAD_TOPICS:
            self.reschedule()
        if event.topic in RELOAD_TOPICS:
            self._events.publish(Event(ALARM_TOPIC, {"change": "reloaded"}, public=True))

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _transition(self, ref: str, project_uid: str | None, version: int, change: Any) -> str:
        with self._database.transaction() as tx:
            alarm = self._resolve(tx, ref, project_uid)
            self._save(tx, alarm, change(alarm), version)
        self._changed(alarm.uid, "updated")
        self.follow()
        self.reschedule()
        return alarm.uid

    def _save(self, tx: Transaction, before: Alarm, after: Alarm, version: int) -> None:
        revision = self._registry.bump_revision(tx, before.uid, version)
        self._alarms.update(tx, replace(after, revision=revision))
        title = self._title(tx, after.text, after.targets)
        if title != self._title(tx, before.text, before.targets):
            self._registry.set_title(tx, before.uid, title)

    def _title(self, tx: Transaction, text: str, targets: Sequence[str]) -> str:
        """Der Anzeigetitel im Register (Suche): der Text, sonst der Titel des ersten Elements."""
        if text or not targets:
            return text
        first = self._registry.get(tx, targets[0])
        return str(first.title) if first is not None else ""

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

    def _targets(self, tx: Transaction, refs: Sequence[str], project_uid: str) -> tuple[str, ...]:
        uids: list[str] = []
        for value in refs:
            element = self._registry.get(tx, value) or self._registry.find_by_label(tx, project_uid, value)
            if element is None:
                raise NotFound(f"Element {value} gibt es nicht", details={"ref": value, "field": "targets"})
            if str(element.uid) not in uids:
                uids.append(str(element.uid))
        return tuple(uids)

    def _view(self, tx: Transaction, alarm: Alarm) -> AlarmView:
        targets = [
            TargetView(element, self._registry.is_open(tx, uid))
            for uid in alarm.targets
            if (element := self._registry.get(tx, uid)) is not None
        ]
        return AlarmView(alarm, targets, model.alarm_missed(alarm, self._clock.now(), self._zone))

    @staticmethod
    def _check_fields(fields: Mapping[str, Any]) -> None:
        unknown = sorted(set(fields) - FIELDS)
        if unknown:
            raise InvalidInput(
                f"Unbekannte Felder: {', '.join(unknown)}", details={"field": unknown[0], "allowed": sorted(FIELDS)}
            )

    def _changed(self, uid: str, change: str) -> None:
        self._events.publish(Event(ALARM_TOPIC, {"uid": uid, "change": change}, public=True))
