"""Ein- und Ausgaben und Operationen des Plugins `alarms` (HTTP + MCP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.alarms.application.service import AlarmService, AlarmView


class AlarmServices:
    def __init__(self, alarms: AlarmService, participant: Any) -> None:
        self.alarms = alarms
        self.participant = participant


@dataclass(frozen=True)
class TargetRef:
    uid: str
    label: str
    title: str
    kind: str
    deleted: bool


@dataclass(frozen=True)
class AlarmOut:
    uid: str
    project_uid: str
    label: str
    text: str
    at: datetime
    #: `Pending` (wartet), `Due` (hat sich gemeldet), `Snoozed` (zurückgestellt), `Done`.
    status: str
    snoozed_until: datetime | None
    #: Das Element, auf das sich der Wecker bezieht; sonst leer.
    target: TargetRef | None
    #: Ein Ziel in einem anderen Projekt, das hier nicht aufzulösen ist, als Text (`Projekt:LABEL`).
    target_text: str | None
    version: int
    deleted: bool


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
    #: `text` und `at` (ISO, UTC wenn ohne Zone) sind Pflicht; `target` (uid oder Label) ist optional.
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UpdateAlarm:
    ref: str
    version: int
    #: Geändert werden nur die genannten Felder (`text`, `at`, `target`; `null` löst das Ziel). Ein neuer
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


def alarm_out(view: AlarmView) -> AlarmOut:
    a, t = view.alarm, view.target
    target = TargetRef(t.uid, t.label, t.title, t.kind, t.deleted_at is not None) if t is not None else None
    return AlarmOut(
        a.uid, a.project_uid, a.label, a.text, a.at, a.status, a.snoozed_until, target, a.target_text, a.revision,
        a.deleted_at is not None,
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
        "Ein Wecker mit Ziel; `ref` ist die uid oder ein Label (mit `project`)",
        "read",
        GetAlarm,
        AlarmOut,
        lambda s, d: alarm_out(s.alarms.get(d.ref, d.project)),
        HttpBinding("GET", "/alarms/{ref}"),
    ),
    Operation(
        "create_alarm",
        "Stellt einen Wecker: er meldet sich zum Zeitpunkt `at`, solange der Viewer läuft; optional an ein Element "
        "gebunden (`target`). Für „Erinner mich“; „Merk dir“ ist eine Note",
        "write",
        CreateAlarm,
        AlarmOut,
        lambda s, d: _detail(s, s.alarms.create(d.project, d.fields)),
        HttpBinding("POST", "/alarms"),
    ),
    Operation(
        "update_alarm",
        "Ändert Text, Zeitpunkt oder Ziel eines Weckers mit Versionsprüfung; ein neuer Zeitpunkt lässt ihn "
        "wieder warten",
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
        "Erledigt einen Wecker",
        "write",
        FinishAlarm,
        AlarmOut,
        lambda s, d: _detail(s, s.alarms.finish(d.ref, d.project, d.version)),
        HttpBinding("POST", "/alarms/{ref}/finish"),
    ),
)
