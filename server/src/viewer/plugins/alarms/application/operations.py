"""Ein- und Ausgaben und Operationen des Plugins `alarms` (HTTP + MCP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.alarms.application.service import AlarmService, AlarmView
from viewer.plugins.alarms.domain.model import purge_time


class AlarmServices:
    def __init__(self, alarms: AlarmService, participant: Any) -> None:
        self.alarms = alarms
        self.participant = participant


@dataclass(frozen=True)
class AlarmTargetRef:
    uid: str
    label: str
    title: str
    kind: str
    deleted: bool
    #: Offen nach seinem Besitzer (nicht erledigt, verworfen, archiviert, gelöscht …).
    open: bool


@dataclass(frozen=True)
class AlarmOut:
    uid: str
    project_uid: str
    label: str
    text: str
    at: datetime
    #: `Pending` (wartet), `Due` (hat sich gemeldet), `Snoozed` (zurückgestellt), `Done` (erledigt) oder `Expired`
    #: (erloschen: keins seiner Elemente ist mehr offen).
    status: str
    snoozed_until: datetime | None
    #: Die Elemente, an die er erinnert, in ihrer Reihenfolge; leer bei einer freien Erinnerung.
    targets: list[AlarmTargetRef]
    #: Verweise in andere Projekte, die hier nicht aufzulösen sind, als Text (`Projekt:LABEL`, komma-getrennt).
    target_text: str | None
    #: Wann er erledigt wurde oder erloschen ist; 24 h später wird er endgültig gelöscht.
    done_at: datetime | None
    #: Wann er endgültig gelöscht wird (nur erledigt oder erloschen).
    purge_at: datetime | None
    version: int
    deleted: bool
    #: `none`, `daily`, `weekly`, `monthly` oder `yearly`. Ein Serienwecker wird beim Erledigen nie `Done`, sondern
    #: wartet auf den nächsten Termin; die Termine rechnen in der Zeitzone des Servers.
    repeat: str
    #: Startpunkt der Serie (UTC); leer ohne Wiederholung.
    series_from: datetime | None
    #: Verpasste Serientermine seit `at` (abgeleitet, nicht gespeichert); 0 ohne Wiederholung.
    missed: int


@dataclass(frozen=True)
class ListAlarms:
    #: Komma-getrennte Projekt-`uid`s; ohne Angabe alle Projekte.
    projects: str | None = None
    #: Nur die Wecker, die sich gemeldet haben und auf Erledigen oder Zurückstellen warten.
    due_only: bool = False


@dataclass(frozen=True)
class GetAlarm:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class CreateAlarm:
    project: str
    #: `at` (ISO, UTC wenn ohne Zone) ist Pflicht; `targets` (Liste aus uid oder Label) optional; `repeat` (`none`,
    #: `daily`, `weekly`, `monthly`, `yearly`) optional; `text` ist Pflicht, wenn es keine `targets` gibt.
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UpdateAlarm:
    ref: str
    version: int
    #: Geändert werden nur die genannten Felder (`text`, `at`, `repeat`, `targets`; `[]` löst alle Elemente). Ein neuer
    #: Zeitpunkt lässt den Wecker wieder warten.
    fields: dict[str, Any]
    project: str | None = None


@dataclass(frozen=True)
class SnoozeAlarm:
    ref: str
    version: int
    #: Bis wann (ISO); ohne Angabe eine Stunde.
    until: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class FinishAlarm:
    ref: str
    version: int
    project: str | None = None


@dataclass(frozen=True)
class ReopenAlarm:
    ref: str
    version: int
    project: str | None = None


def alarm_out(view: AlarmView) -> AlarmOut:
    a = view.alarm
    targets = [
        AlarmTargetRef(e.uid, e.label, e.title, e.kind, e.deleted_at is not None, t.open)
        for t in view.targets
        if (e := t.element) is not None
    ]  # fmt: skip
    return AlarmOut(
        a.uid, a.project_uid, a.label, a.text, a.at, a.status, a.snoozed_until, targets, a.target_text, a.done_at,
        purge_time(a), a.revision, a.deleted_at is not None, a.repeat, a.series_from, view.missed,
    )  # fmt: skip


def _split(value: str | None) -> list[str]:
    return [part for part in (value or "").split(",") if part]


def _detail(services: AlarmServices, uid: str) -> AlarmOut:
    return alarm_out(services.alarms.get(uid, None))


def _list(services: AlarmServices, data: ListAlarms) -> list[AlarmOut]:
    projects = _split(data.projects) if data.projects is not None else None
    return [alarm_out(view) for view in services.alarms.list_alarms(projects, data.due_only)]


OPERATIONS: tuple[Operation, ...] = (
    Operation(
        "list_alarms",
        "Wecker als Liste (nach Zeitpunkt); `due_only` zeigt nur die, die sich gemeldet haben. Projekte komma-getrennt",
        "read",
        ListAlarms,
        list[AlarmOut],
        _list,
        HttpBinding("GET", "/alarms"),
    ),
    Operation(
        "get_alarm",
        "Ein Wecker mit seinen Elementen; `ref` ist die uid oder ein Label (mit `project`)",
        "read",
        GetAlarm,
        AlarmOut,
        lambda s, d: alarm_out(s.alarms.get(d.ref, d.project)),
        HttpBinding("GET", "/alarms/{ref}"),
    ),
    Operation(
        "create_alarm",
        "Stellt einen Wecker: er meldet sich zum Zeitpunkt `at`, solange der Viewer läuft. Er erinnert an Elemente "
        "(`targets`, dann erlischt er, wenn keins mehr offen ist) oder ist frei mit `text`. Mit `repeat` (`none`, "
        "`daily`, `weekly`, `monthly`, `yearly`) wiederholt er sich; die Termine rechnen in der Zeitzone des Servers. "
        "Für „Erinner mich“; „Merk dir“ ist ein Memo",
        "write",
        CreateAlarm,
        AlarmOut,
        lambda s, d: _detail(s, s.alarms.create(d.project, d.fields)),
        HttpBinding("POST", "/alarms"),
    ),
    Operation(
        "update_alarm",
        "Ändert Text, Zeitpunkt, Wiederholung (`repeat`) oder Elemente eines Weckers mit Versionsprüfung; ein neuer "
        "Zeitpunkt lässt ihn wieder warten und beginnt bei einem Serienwecker eine neue Serie",
        "write",
        UpdateAlarm,
        AlarmOut,
        lambda s, d: _detail(s, s.alarms.update(d.ref, d.project, d.version, d.fields)),
        HttpBinding("PUT", "/alarms/{ref}"),
    ),
    Operation(
        "snooze_alarm",
        "Stellt einen Wecker zurück (Standard: eine Stunde, sonst bis `until`)",
        "write",
        SnoozeAlarm,
        AlarmOut,
        lambda s, d: _detail(s, s.alarms.snooze(d.ref, d.project, d.version, d.until)),
        HttpBinding("POST", "/alarms/{ref}/snooze"),
    ),
    Operation(
        "finish_alarm",
        "Erledigt einen Wecker; 24 h später wird er endgültig gelöscht. Ein Serienwecker wird nie erledigt, sondern "
        "wartet auf den nächsten Termin nach jetzt",
        "write",
        FinishAlarm,
        AlarmOut,
        lambda s, d: _detail(s, s.alarms.finish(d.ref, d.project, d.version)),
        HttpBinding("POST", "/alarms/{ref}/finish"),
    ),
    Operation(
        "reopen_alarm",
        "Nimmt „Erledigt“ zurück, solange der Wecker noch nicht gelöscht ist; er wartet wieder (oder ist fällig). "
        "Nicht für Serienwecker",
        "write",
        ReopenAlarm,
        AlarmOut,
        lambda s, d: _detail(s, s.alarms.reopen(d.ref, d.project, d.version)),
        HttpBinding("POST", "/alarms/{ref}/reopen"),
    ),
)
