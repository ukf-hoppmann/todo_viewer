"""Generischer Sync-Dienst zwischen Datenbank (Wahrheit) und Markdown-Spiegel (EPIC-007-Spec §7.3).

Der Dienst kennt weder SQL noch Dateiformate noch die Fachlichkeit der Plugins. Jedes spiegelnde Plugin liefert einen
`MirrorCodec` (Dateien ⇄ Einträge) und einen `SyncParticipant` (Datenbank ⇄ Einträge); der Dienst gleicht je Projekt
alle Spiegel zusammen ab.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Protocol

import structlog

from viewer.core.application.ports import BackupMaker, Clock, Database, EventBus, FileStore, Scheduler, Transaction
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.events import Event
from viewer.core.domain.files import Change, FileSet, MirrorBlocked, matches_any
from viewer.core.domain.sync import (
    Choice,
    Conflict,
    ConflictHint,
    Direction,
    Intent,
    MirrorEntry,
    MirrorFormatError,
    MirrorNotConfigured,
    Plan,
    SyncPreviewStale,
    SyncState,
    compute_plan,
    explain_conflict,
    is_purged,
    plan_token,
    resolve_conflicts,
    sync_state,
)

log = structlog.get_logger(__name__)

AUTO_SYNC_OWNER = "core.sync"
STATE_TOPIC = "core.sync.state"


# --- Ports -----------------------------------------------------------------------------------------------------------


class MirrorCodec(Protocol):
    """Dateien ⇄ Einträge für ein Plugin. Kennt das Format, nicht die Datenbank."""

    @property
    def patterns(self) -> Sequence[str]:
        """Muster der Dateien dieses Plugins im Spiegel-Ordner (relativ, `**` erlaubt)."""
        ...

    def decode(self, files: FileSet) -> list[MirrorEntry]:
        """Liest die Einträge; wirft `MirrorFormatError(code, message, file=…, line=…)` bei ungültigem Inhalt."""
        ...

    def encode(
        self, upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet
    ) -> Sequence[Change]:
        """Änderungen an den Dateien: schreibt `upserts` (mit `uid` und Label), entfernt `removed`; verändert nur
        die betroffenen Einträge und Dateien. Trägt ein Eintrag in `upserts` einen `placeholder`, ersetzt er den
        gleichnamigen neuen Eintrag in den Dateien (Zeile, Ordner, Dokumente). `current` ist der gelesene Stand
        dieses Plugins."""
        ...


@dataclass(frozen=True)
class SyncChanges:
    """Was ein Teilnehmer in die Datenbank schreibt. `created` hat `uid` und Label (vom Sync vergeben), alle
    Verweise sind Labels ohne Platzhalter."""

    created: tuple[MirrorEntry, ...] = ()
    updated: tuple[MirrorEntry, ...] = ()
    deleted: tuple[MirrorEntry, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.created or self.updated or self.deleted)


class SyncParticipant(Protocol):
    """Datenbank ⇄ Einträge für ein Plugin. Kennt die Tabellen, nicht das Dateiformat."""

    def load(self, project: str) -> list[MirrorEntry]:
        """Alle Einträge des Projekts (mit `uid` und aktuellem Label, Verweise als aktuelle Labels)."""
        ...

    def resolve_labels(self, project: str, labels: Collection[str]) -> Mapping[str, str]:
        """Bildet bekannte Labels (auch frühere) auf das aktuelle Label ab; unbekannte fehlen im Ergebnis."""
        ...

    def assign_labels(
        self, project: str, entries: Sequence[MirrorEntry], tx: Transaction, taken: Collection[str] = ()
    ) -> Mapping[str, str]:
        """Vergibt für neue Einträge (mit `placeholder`) das nächste freie Label: Platzhalter → Label.

        `taken` sind Labels, die dieselbe Synchronisierung mit ihrer `uid` aus den Dateien anlegt; sie sind noch nicht
        in der Datenbank, dürfen aber nicht vergeben werden."""
        ...

    def apply(self, project: str, changes: SyncChanges, tx: Transaction) -> None:
        """Schreibt die Änderungen in der Transaktion `tx`."""
        ...


@dataclass(frozen=True)
class MirrorBinding:
    owner: str
    codec: MirrorCodec
    participant: SyncParticipant
    #: Kurzlebige Einträge (Architektur §2): eine Löschung in der Datenbank geht ohne Konflikt in die Dateien, auch
    #: beim Auto-Sync, solange der Eintrag dort seit dem letzten Sync unverändert ist.
    ephemeral: bool = False


@dataclass(frozen=True)
class MirrorConfig:
    folder: Path
    auto_sync: bool = False
    #: Der Name des Projekts: Codecs, die ihn für Verweise brauchen, werden mit `for_project` daran gebunden.
    name: str = ""


def bound_codec(codec: MirrorCodec, name: str) -> MirrorCodec:
    """Der Codec für das Projekt `name`: bietet er `for_project(name)` an, wird er daran gebunden."""
    binder = getattr(codec, "for_project", None)
    return binder(name) if callable(binder) else codec


class MirrorProjects(Protocol):
    """Projekte mit Spiegel-Einstellungen; erfüllt später das Plugin `workspace`."""

    def config(self, project: str) -> MirrorConfig | None: ...

    def auto_sync_projects(self) -> list[str]: ...

    def mirror_projects(self) -> list[str]:
        """Alle Projekte mit eingeschaltetem Spiegel, mit und ohne Auto-Sync."""
        ...


class SyncStateStore(Protocol):
    """Hash jedes Eintrags beim letzten Sync (`core_sync_state`)."""

    def load(self, project: str) -> dict[str, str]: ...

    def save(self, project: str, hashes: Mapping[str, str], at: datetime) -> None: ...

    def forget(self, project: str, uids: Collection[str]) -> None: ...

    def last_synced(self, project: str) -> datetime | None:
        """Der Zeitpunkt, zu dem zuletzt ein Eintrag des Projekts abgeglichen wurde."""
        ...

    def synced_times(self, project: str) -> dict[str, datetime]:
        """Der Zeitpunkt des letzten Abgleichs je Eintrag (`uid`)."""
        ...


class Ids(Protocol):
    def new_uid(self) -> str: ...


# --- Ergebnisse (auch Ein- und Ausgaben der Operationen) ------------------------------------------------------------


@dataclass(frozen=True)
class SyncStatus:
    project: str
    state: SyncState
    to_database: int = 0
    to_files: int = 0
    conflicts: int = 0
    reason: str | None = None
    files: list[str] = field(default_factory=list)
    #: Zeitpunkt des letzten Abgleichs (UTC); `None`, wenn das Projekt noch nie abgeglichen wurde.
    last_sync: datetime | None = None


@dataclass(frozen=True)
class TransferOut:
    key: str
    kind: str
    label: str | None
    target: Literal["database", "files"]
    action: Literal["create", "update", "delete"]


@dataclass(frozen=True)
class RenameOut:
    key: str
    label: str | None
    similarity: float


@dataclass(frozen=True)
class ConflictOut:
    key: str
    kind: str
    label: str | None
    conflict: str
    database: dict[str, Any] | None
    files: dict[str, Any] | None
    #: Seit dem letzten Abgleich geändert? `None`: Seite fehlt oder keine Basis.
    database_changed: bool | None = None
    files_changed: bool | None = None
    #: Zeitpunkt, zu dem der Eintrag zuletzt abgeglichen wurde (UTC).
    synced_at: datetime | None = None
    renamed_to: RenameOut | None = None
    #: Vorschlag (`database`, `files`, `none`) und Begründungscode; nie vorausgewählt.
    recommendation: Literal["database", "files", "none"] = "none"
    reason: str = ""


@dataclass(frozen=True)
class Preview:
    project: str
    direction: Direction
    token: str
    state: SyncState
    transfers: list[TransferOut]
    conflicts: list[ConflictOut]
    skipped: list[TransferOut]
    not_imported: list[TransferOut]


@dataclass(frozen=True)
class Decision:
    uid: str
    choice: Choice


@dataclass(frozen=True)
class SyncResult:
    project: str
    state: SyncState
    to_database: int
    to_files: int
    created: list[str]
    conflicts_left: list[ConflictOut]


# --- Dienst ----------------------------------------------------------------------------------------------------------


@dataclass
class _Snapshot:
    config: MirrorConfig
    fileset: FileSet
    raw_files: list[list[MirrorEntry]]  # je Spiegel, so wie geschrieben (Verweise unnormalisiert)
    files: list[list[MirrorEntry]]  # je Spiegel, Verweise auf aktuelle Labels abgebildet
    database: list[list[MirrorEntry]]
    base: dict[str, str]
    plan: Plan
    owner_of: dict[str, int]


class SyncService:
    def __init__(
        self,
        mirrors: Callable[[], Sequence[MirrorBinding]],
        *,
        projects: MirrorProjects,
        files: FileStore,
        state: SyncStateStore,
        database: Database,
        backups: BackupMaker,
        events: EventBus,
        scheduler: Scheduler,
        clock: Clock,
        ids: Ids,
        auto_interval_seconds: float = 30.0,
    ) -> None:
        self._mirror_provider = mirrors
        self._projects = projects
        self._files = files
        self._state = state
        self._database = database
        self._backups = backups
        self._events = events
        self._scheduler = scheduler
        self._clock = clock
        self._ids = ids
        self._interval = auto_interval_seconds
        self._guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._last_state: dict[str, tuple[SyncState, str | None]] = {}

    @property
    def _mirrors(self) -> list[MirrorBinding]:
        return list(self._mirror_provider())

    # --- Abfragen ohne Datenänderung ---------------------------------------------------------------------------

    def status(self, project: str) -> SyncStatus:
        """Zustand des Projekts, ohne etwas zu ändern. Ordner- und Formatprobleme ergeben `paused`, keinen Fehler."""
        return replace(self._status(project), last_sync=self._state.last_synced(project))

    def _status(self, project: str) -> SyncStatus:
        try:
            snapshot = self._load(project, "both")
        except MirrorNotConfigured:
            return SyncStatus(project, "paused", reason="not_configured")
        except MirrorBlocked as exc:
            return SyncStatus(project, "paused", reason=str(exc.details["state"]), files=list(exc.details["files"]))
        except MirrorFormatError as exc:
            return SyncStatus(project, "paused", reason=exc.code, files=[str(exc.details.get("file"))])
        return self._status_of(project, snapshot.plan)

    def preview(self, project: str, direction: Direction = "both") -> Preview:
        """Plan mit Token. Fehlt der Ordner oder ist er gesperrt oder ungültig, folgt der Fehler."""
        snapshot = self._load(project, direction)
        plan = snapshot.plan
        return Preview(
            project=project,
            direction=direction,
            token=plan_token(project, direction, plan),
            state=sync_state(plan),
            transfers=[_transfer(i) for i in plan.intents],
            conflicts=self._conflicts_out(project, snapshot, plan.conflicts),
            skipped=[_transfer(i) for i in plan.skipped],
            not_imported=[TransferOut(e.key, e.kind, e.label, "database", "create") for e in plan.not_imported],
        )

    # --- Ausführen -------------------------------------------------------------------------------------------------

    def execute(
        self,
        project: str,
        token: str,
        direction: Direction = "both",
        decisions: Sequence[Decision] = (),
        delete_missing: bool = False,
    ) -> SyncResult:
        with self._locks[project]:
            snapshot = self._load(project, direction)
            if plan_token(project, direction, snapshot.plan) != token:
                raise SyncPreviewStale(
                    "Seit der Vorschau hat sich etwas geändert; bitte neu in der Vorschau ansehen",
                    details={"project": project},
                )
            known = {c.key for c in snapshot.plan.conflicts}
            unknown = sorted(d.uid for d in decisions if d.uid not in known)
            if unknown:
                raise InvalidInput(f"Keine Konflikte für: {', '.join(unknown)}", details={"uids": unknown})
            chosen = {d.uid: d.choice for d in decisions}
            resolved, open_conflicts, _ = resolve_conflicts(snapshot.plan.conflicts, chosen, direction, delete_missing)
            result = self._run(project, snapshot, [*snapshot.plan.intents, *resolved], open_conflicts)
        self._publish(project, result.state, None, force=True)
        return result

    def auto(self, project: str) -> SyncStatus:
        """Ein Lauf des Auto-Sync: nur konfliktfreie Änderungen, löscht nur kurzlebige Einträge, pausiert bei
        Problemen."""
        with self._locks[project]:
            try:
                snapshot = self._load(project, "both")
            except (MirrorNotConfigured, MirrorBlocked, MirrorFormatError) as exc:
                status = self._paused(project, exc)
                self._publish(project, status.state, status.reason)
                return status
            intents = [i for i in snapshot.plan.intents if not i.is_deletion or self._ephemeral(snapshot, i)]
            changed = bool(intents)
            if changed:
                self._run(project, snapshot, intents, snapshot.plan.conflicts)
            elif snapshot.plan.adopt or snapshot.plan.forget:
                self._remember(project)
            status = self.status(project)
        self._publish(project, status.state, status.reason, force=changed)
        return status

    def carry_purged(self, uids: Collection[str]) -> None:
        """Trägt gewollte Löschungen (endgültig gelöschte Elemente, ein Dokument im Papierkorb) in die Dateien aller
        Spiegel-Projekte (Architektur §2): nur diese Einträge und ihre Dokumente (`uid` oder `uid/<teil>`), nur wo
        die Datei seit dem letzten Sync unverändert ist; alles andere bleibt offen.
        Wirft nicht: die Datenbank ist schon geändert, ein Hindernis (Git-Operation, geänderte Datei) lässt den
        Eintrag als Konflikt stehen."""
        purged = frozenset(uids)
        for project in self._projects.mirror_projects():
            try:
                self._carry_purged(project, purged)
            except Exception:
                log.exception("purge_sync_failed", project=project)

    def _carry_purged(self, project: str, purged: frozenset[str]) -> None:
        with self._locks[project]:
            try:
                snapshot = self._load(project, "both", purged)
            except (MirrorNotConfigured, MirrorBlocked, MirrorFormatError):
                log.warning("purge_sync_paused", project=project)
                return
            intents = [i for i in snapshot.plan.intents if i.is_deletion and is_purged(i.entry.key, purged)]
            if not intents:
                return
            self._write_files(project, snapshot, [], intents, {}, {})
            status = self._status_of_remembered(project)
        self._publish(project, status.state, None, force=True)

    def _status_of_remembered(self, project: str) -> SyncStatus:
        plan = self._remember(project)
        return self._status_of(project, plan) if plan else SyncStatus(project, "paused")

    # --- Auto-Sync-Takt ----------------------------------------------------------------------------------------

    def refresh_auto(self) -> None:
        """Setzt den Termin neu: läuft nur, solange mindestens ein Projekt Auto-Sync an hat."""
        if self._projects.auto_sync_projects():
            self._scheduler.schedule(AUTO_SYNC_OWNER, self._clock.now() + timedelta(seconds=self._interval), self._tick)
        else:
            self._scheduler.schedule(AUTO_SYNC_OWNER, None, self._tick)

    def _tick(self) -> None:
        for project in self._projects.auto_sync_projects():
            try:
                self.auto(project)
            except Exception:
                log.exception("auto_sync_failed", project=project)
        self.refresh_auto()

    # --- Innenleben ------------------------------------------------------------------------------------------------

    def _load(self, project: str, direction: Direction, purged: frozenset[str] = frozenset()) -> _Snapshot:
        config = self._projects.config(project)
        if config is None:
            raise MirrorNotConfigured(f"Projekt {project} hat keinen Spiegel-Ordner", details={"project": project})
        patterns = sorted({p for m in self._mirrors for p in m.codec.patterns})
        fileset = self._files.read(config.folder, patterns)
        raw_files: list[list[MirrorEntry]] = []
        database: list[list[MirrorEntry]] = []
        for mirror in self._mirrors:
            own = FileSet({p: e for p, e in fileset.files.items() if matches_any(mirror.codec.patterns, p)})
            raw_files.append(bound_codec(mirror.codec, config.name).decode(own))
            database.append(mirror.participant.load(project))
        _check_unique_placeholders(raw_files)
        aliases = self._aliases(project, raw_files)
        files = [[e.map_refs(aliases) for e in entries] for entries in raw_files]
        base = self._state.load(project)
        owner_of: dict[str, int] = {}
        for index, entries in enumerate(database):
            owner_of.update({e.key: index for e in entries})
        for index, entries in enumerate(files):
            owner_of.update({e.key: index for e in entries})
        ephemeral = frozenset(
            e.kind
            for index, mirror in enumerate(self._mirrors)
            if mirror.ephemeral
            for e in (*database[index], *files[index])
        )
        plan = compute_plan(
            [e for es in database for e in es], [e for es in files for e in es], base, direction, ephemeral, purged
        )
        return _Snapshot(config, fileset, raw_files, files, database, base, plan, owner_of)

    def _conflicts_out(self, project: str, snapshot: _Snapshot, conflicts: Sequence[Conflict]) -> list[ConflictOut]:
        if not conflicts:
            return []
        times = self._state.synced_times(project)
        database = [e for entries in snapshot.database for e in entries]
        files = [e for entries in snapshot.files for e in entries]
        out: list[ConflictOut] = []
        for conflict in conflicts:
            candidates = {"deleted_in_files": files, "deleted_in_database": database}.get(conflict.kind, [])
            hint = explain_conflict(conflict, snapshot.base, candidates, times.get(conflict.key))
            out.append(_conflict(conflict, hint))
        return out

    def _ephemeral(self, snapshot: _Snapshot, intent: Intent) -> bool:
        index = snapshot.owner_of.get(intent.entry.key)
        return index is not None and self._mirrors[index].ephemeral

    def _aliases(self, project: str, raw_files: list[list[MirrorEntry]]) -> dict[str, str]:
        labels = {ref for entries in raw_files for e in entries for refs in e.refs.values() for ref in refs}
        aliases: dict[str, str] = {}
        if labels:
            for mirror in self._mirrors:
                aliases.update({k: v for k, v in mirror.participant.resolve_labels(project, labels).items() if k != v})
        return aliases

    def _run(
        self, project: str, snapshot: _Snapshot, intents: Sequence[Intent], open_conflicts: Sequence[Conflict]
    ) -> SyncResult:
        to_database = [i for i in intents if i.target == "database"]
        to_files = [i for i in intents if i.target == "files"]
        placeholder_labels: dict[str, str] = {}
        new_uids: dict[str, str] = {}
        if to_database:
            self._backups.create("sync")
            placeholder_labels, new_uids = self._write_database(project, snapshot, to_database)
        if to_database or to_files:
            self._write_files(project, snapshot, to_database, to_files, new_uids, placeholder_labels)
        after = self._remember(project)
        return SyncResult(
            project=project,
            state=sync_state(after) if after else "paused",
            to_database=len(to_database),
            to_files=len(to_files),
            created=sorted(placeholder_labels.values()),
            conflicts_left=self._conflicts_out(project, snapshot, open_conflicts),
        )

    def _write_database(
        self, project: str, snapshot: _Snapshot, intents: Sequence[Intent]
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Schreibt in einer Transaktion für alle Teilnehmer. Gibt `(Platzhalter → Label, Platzhalter → uid)` zurück."""
        prepared: list[tuple[int, Intent, MirrorEntry]] = []
        new_uids: dict[str, str] = {}
        for intent in intents:
            entry = intent.entry
            if entry.uid is None:
                assert entry.placeholder is not None
                entry = replace(entry, uid=self._ids.new_uid())
                new_uids[entry.placeholder] = str(entry.uid)  # type: ignore[index]
            prepared.append((snapshot.owner_of[intent.entry.key], intent, entry))
        placeholder_labels: dict[str, str] = {}
        with self._database.transaction() as tx:
            for index, mirror in enumerate(self._mirrors):
                fresh = [e for i, intent, e in prepared if i == index and intent.entry.uid is None]
                if not fresh:
                    continue
                taken = [
                    str(e.label)
                    for i, intent, e in prepared
                    if i == index and intent.action == "create" and e.label is not None and not intent.is_deletion
                ]
                labels = mirror.participant.assign_labels(project, fresh, tx, taken)
                missing = sorted(str(e.placeholder) for e in fresh if e.placeholder not in labels)
                if missing:
                    raise InvalidInput(f"Kein Label vergeben für: {', '.join(missing)}", details={"missing": missing})
                placeholder_labels.update({str(e.placeholder): labels[str(e.placeholder)] for e in fresh})
            for index, mirror in enumerate(self._mirrors):
                created: list[MirrorEntry] = []
                updated: list[MirrorEntry] = []
                deleted: list[MirrorEntry] = []
                for i, intent, entry in prepared:
                    if i != index:
                        continue
                    if intent.is_deletion:
                        deleted.append(entry)
                        continue
                    final = entry.map_refs(placeholder_labels)
                    if intent.entry.uid is None:
                        final = replace(final, label=placeholder_labels[str(entry.placeholder)], placeholder=None)
                    (created if intent.action == "create" else updated).append(final)
                changes = SyncChanges(tuple(created), tuple(updated), tuple(deleted))
                if changes:
                    mirror.participant.apply(project, changes, tx)
        return placeholder_labels, new_uids

    def _write_files(
        self,
        project: str,
        snapshot: _Snapshot,
        to_database: Sequence[Intent],
        to_files: Sequence[Intent],
        new_uids: Mapping[str, str],
        placeholder_labels: Mapping[str, str],
    ) -> None:
        """Schreibt die Dateien aus dem Stand der Datenbank nach dem Commit, mit den beim Lesen erfassten Versionen."""
        loaded = [e for entries in (m.participant.load(project) for m in self._mirrors) for e in entries]
        after = {e.uid: e for e in loaded}
        by_label = {(e.kind, e.label): e for e in loaded}
        raw = {e.key: e for entries in snapshot.raw_files for e in entries}
        upserts: dict[int, dict[str, MirrorEntry]] = defaultdict(dict)
        removed: dict[int, list[MirrorEntry]] = defaultdict(list)
        for intent in to_files:
            index = snapshot.owner_of[intent.entry.key]
            if intent.is_deletion:
                removed[index].append(intent.entry)
            elif intent.entry.uid in after:
                upserts[index][str(intent.entry.uid)] = after[intent.entry.uid]
        for intent in to_database:
            if intent.is_deletion:
                continue
            index = snapshot.owner_of[intent.entry.key]
            uid = intent.entry.uid or new_uids[str(intent.entry.placeholder)]
            fresh = after.get(uid)
            if fresh is None and intent.entry.placeholder is not None:
                # der Teilnehmer darf die `uid` neuer Einträge selbst bilden (z. B. Dokumente): dann gilt das Label
                fresh = by_label.get((intent.entry.kind, placeholder_labels.get(intent.entry.placeholder)))
            if fresh is None:
                continue
            uid = str(fresh.uid)
            written = raw.get(intent.entry.key)
            if intent.entry.uid is None or written is None or _differs_in_display(written, fresh):
                # neue Einträge und Einträge mit Platzhalter oder altem Label; `placeholder` nennt, was in den Dateien
                # ersetzt wird (z. B. Zeile oder Ordner `NEW-<kurzname>`)
                upserts[index][uid] = replace(fresh, placeholder=intent.entry.placeholder)
        changes: list[Change] = []
        for index, mirror in enumerate(self._mirrors):
            if not upserts[index] and not removed[index]:
                continue
            current = FileSet(
                {p: e for p, e in snapshot.fileset.files.items() if matches_any(mirror.codec.patterns, p)}
            )
            codec = bound_codec(mirror.codec, snapshot.config.name)
            changes.extend(codec.encode(list(upserts[index].values()), removed[index], current))
        if not changes:
            return
        expected: dict[str, str | None] = {}
        for change in changes:
            for path in (change.path, getattr(change, "new_path", None)):
                if path is not None:
                    known = snapshot.fileset.files.get(path)
                    expected[path] = known.version if known else None
        self._files.write(snapshot.config.folder, changes, expected)

    def _remember(self, project: str) -> Plan | None:
        """Liest beide Seiten neu und zieht die Basis für alle beidseitig gleichen Einträge nach."""
        try:
            fresh = self._load(project, "both")
        except (MirrorBlocked, MirrorFormatError, MirrorNotConfigured):
            log.warning("sync_state_not_updated", project=project)
            return None
        if fresh.plan.adopt:
            self._state.save(project, fresh.plan.adopt, self._clock.now())
        if fresh.plan.forget:
            self._state.forget(project, fresh.plan.forget)
        return fresh.plan

    # --- Zustand und Ereignisse ------------------------------------------------------------------------------------

    def _status_of(self, project: str, plan: Plan) -> SyncStatus:
        return SyncStatus(
            project=project,
            state=sync_state(plan),
            to_database=sum(1 for i in plan.intents if i.target == "database") + len(plan.not_imported),
            to_files=sum(1 for i in plan.intents if i.target == "files"),
            conflicts=len(plan.conflicts),
        )

    def _paused(self, project: str, exc: Exception) -> SyncStatus:
        if isinstance(exc, MirrorNotConfigured):
            return SyncStatus(project, "paused", reason="not_configured")
        if isinstance(exc, MirrorBlocked):
            return SyncStatus(project, "paused", reason=str(exc.details["state"]), files=list(exc.details["files"]))
        assert isinstance(exc, MirrorFormatError)
        return SyncStatus(project, "paused", reason=exc.code, files=[str(exc.details.get("file"))])

    def _publish(self, project: str, state: SyncState, reason: str | None, force: bool = False) -> None:
        with self._guard:
            changed = self._last_state.get(project) != (state, reason)
            self._last_state[project] = (state, reason)
        if changed or force:
            payload = {"project": project, "state": state, "reason": reason}
            self._events.publish(Event(STATE_TOPIC, payload, public=True))


def _differs_in_display(written: MirrorEntry, db: MirrorEntry) -> bool:
    """Steht in der Datei ein anderes Label oder stehen andere Verweise (Platzhalter, altes Label) als in der DB?"""
    return written.label != db.label or dict(written.refs) != dict(db.refs)


def _check_unique_placeholders(raw_files: list[list[MirrorEntry]]) -> None:
    seen: set[str] = set()
    for entries in raw_files:
        for entry in entries:
            if entry.placeholder is None:
                continue
            if entry.placeholder in seen:
                raise MirrorFormatError(
                    "duplicate_label", f"Platzhalter {entry.placeholder} kommt mehrfach vor", file="*"
                )
            seen.add(entry.placeholder)


def _transfer(intent: Intent) -> TransferOut:
    entry = intent.entry
    return TransferOut(entry.key, entry.kind, entry.label, intent.target, intent.action)


def _entry_dict(entry: MirrorEntry | None) -> dict[str, Any] | None:
    if entry is None:
        return None
    return {
        "label": entry.label,
        "kind": entry.kind,
        "fields": dict(entry.fields),
        "refs": {k: list(v) for k, v in entry.refs.items()},
    }


def _conflict(conflict: Conflict, hint: ConflictHint) -> ConflictOut:
    kind = conflict.database or conflict.files
    renamed = hint.renamed_to
    return ConflictOut(
        key=conflict.key,
        kind=kind.kind if kind else "",
        label=conflict.label,
        conflict=conflict.kind,
        database=_entry_dict(conflict.database),
        files=_entry_dict(conflict.files),
        database_changed=hint.database_changed,
        files_changed=hint.files_changed,
        synced_at=hint.synced_at,
        renamed_to=RenameOut(renamed.key, renamed.label, renamed.similarity) if renamed else None,
        recommendation=hint.recommendation,
        reason=hint.reason,
    )
