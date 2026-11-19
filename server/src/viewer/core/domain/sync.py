"""Reine Logik des Sync: Einträge vergleichen, Plan berechnen, Konflikte auflösen (kein SQL, keine Dateien).

Begriffe: Die *Datenbank* ist die Wahrheit, die *Dateien* sind der Spiegel. Die *Basis* ist der Hash, den ein
Eintrag beim letzten erfolgreichen Sync auf beiden Seiten hatte (`core_sync_state`).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Literal

from viewer.core.domain.errors import DomainError

Side = Literal["database", "files"]
Direction = Literal["both", "to_database", "to_files"]
Choice = Literal["database", "files", "defer"]
ConflictKind = Literal["both_changed", "both_created", "deleted_in_files", "deleted_in_database"]
SyncState = Literal["in_sync", "primary_changed", "mirror_changed", "both_changed", "conflicts", "paused"]


class MirrorFormatError(DomainError):
    """Der Codec lehnt den Inhalt einer Datei ab; `code` ist der Formatfehler, `details` nennt Datei und Zeile."""

    def __init__(self, code: str, message: str, *, file: str, line: int | None = None) -> None:
        super().__init__(
            f"{file}{f':{line}' if line else ''}: {message}", code=code, details={"file": file, "line": line}
        )


class SyncPreviewStale(DomainError):
    code = "sync_preview_stale"


class DeletionNotConfirmed(DomainError):
    code = "deletion_not_confirmed"


class MirrorNotConfigured(DomainError):
    code = "mirror_not_configured"


@dataclass(frozen=True)
class MirrorEntry:
    """Ein Eintrag in der Form, die beide Seiten teilen.

    `refs` bildet Feldnamen auf Verweise ab (Labels, in den Dateien wie in der Datenbank); alles andere steht in
    `fields` (JSON-tauglich). `uid` fehlt bei neuen Einträgen aus den Dateien, die statt eines Labels einen
    `placeholder` tragen. Das Label gehört nicht zum Hash.
    """

    kind: str
    label: str | None
    fields: Mapping[str, Any]
    refs: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    uid: str | None = None
    placeholder: str | None = None
    #: Datei und Zeile, aus der der Codec den Eintrag gelesen hat (für Meldungen); nicht Teil des Vergleichs.
    source: tuple[str, int] | None = field(default=None, compare=False)
    #: Zeile je Feld oder Verweis (für Meldungen); nicht Teil des Vergleichs.
    source_lines: Mapping[str, int] = field(default_factory=dict, compare=False)
    #: Angaben, die der Codec mitführt, die aber nicht verglichen werden (z. B. Zeitstempel der Datei); nicht im Hash.
    extra: Mapping[str, Any] = field(default_factory=dict, compare=False)
    #: Die Datenbank hält den Eintrag im Papierkorb. Fehlt er dann in den Dateien, ist das kein Konflikt: die
    #: Löschung ist auf beiden Seiten angekommen (Entscheidung „Dateien“ bei „in den Dateien gelöscht“).
    trashed: bool = field(default=False, compare=False)

    @property
    def key(self) -> str:
        if self.uid is not None:
            return self.uid
        return f"new:{self.placeholder}"

    @property
    def hash(self) -> str:
        canonical = json.dumps(
            {"kind": self.kind, "fields": self.fields, "refs": {k: list(v) for k, v in self.refs.items()}},
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    def map_refs(self, mapping: Mapping[str, str]) -> MirrorEntry:
        """Ersetzt Verweise (Platzhalter → Label, altes → aktuelles Label)."""
        refs = {name: tuple(mapping.get(ref, ref) for ref in values) for name, values in self.refs.items()}
        return self if refs == dict(self.refs) else replace(self, refs=refs)

    def map_text(self, mapping: Mapping[str, str]) -> MirrorEntry:
        """Ersetzt Platzhalter im Fließtext der Felder (nur als ganze ID, siehe `replace_ids`)."""
        if not mapping:
            return self
        fields = _map_strings(self.fields, mapping)
        return self if fields == dict(self.fields) else replace(self, fields=fields)


@dataclass(frozen=True)
class Intent:
    """Eine Änderung an einer Seite. Bei `delete` ist `entry` der Eintrag, der dort gelöscht wird."""

    target: Side
    action: Literal["create", "update", "delete"]
    entry: MirrorEntry

    @property
    def is_deletion(self) -> bool:
        return self.action == "delete"


@dataclass(frozen=True)
class Conflict:
    kind: ConflictKind
    key: str
    label: str | None
    database: MirrorEntry | None
    files: MirrorEntry | None


@dataclass(frozen=True)
class Plan:
    intents: tuple[Intent, ...] = ()
    conflicts: tuple[Conflict, ...] = ()
    adopt: Mapping[str, str] = field(default_factory=dict)  # uid → Hash: beidseitig gleich, Basis nachziehen
    forget: tuple[str, ...] = ()  # uids in der Basis, die auf keiner Seite mehr vorkommen
    skipped: tuple[Intent, ...] = ()  # wegen der Richtung nicht ausgeführt
    not_imported: tuple[MirrorEntry, ...] = ()  # neue Dateieinträge, die die Richtung nicht übernimmt

    @property
    def changes(self) -> bool:
        return bool(self.intents or self.conflicts)


def compute_plan(
    database: Sequence[MirrorEntry],
    files: Sequence[MirrorEntry],
    base: Mapping[str, str],
    direction: Direction = "both",
    ephemeral: frozenset[str] = frozenset(),
    purged: frozenset[str] = frozenset(),
) -> Plan:
    """Vergleicht die Einträge beider Seiten je `uid` mit der Basis (Architektur §2, EPIC-007-Spec §7.3).

    - nur eine Seite geändert → übertragen; neu auf einer Seite → anlegen;
    - beide Seiten geändert oder beide neu mit verschiedenem Inhalt → Konflikt;
    - auf einer Seite gelöscht (Basis vorhanden) → Konflikt, nie automatisch gelöscht; Ausnahme: ein kurzlebiger
      Eintrag (`kind` in `ephemeral`), der in der Datenbank fehlt und in den Dateien seit der Basis unverändert ist,
      wird in den Dateien gelöscht;
    - ebenso ein Eintrag, den der Besitzer eben endgültig gelöscht hat (`uid` oder die `uid` seines Elements in
      `purged`), solange er in den Dateien seit der Basis unverändert ist (Architektur §2);
    - beidseitig gleich → nur die Basis wird nachgezogen.
    Einträge aus den Dateien ohne `uid` sind neu und kommen nur bei Richtung `both` in die Datenbank, weil dazu der
    Rückschrieb von `uid` und Label in die Dateien gehört.
    """
    db_by_uid = {e.uid: e for e in database if e.uid is not None}
    file_by_uid = {e.uid: e for e in files if e.uid is not None}
    intents: list[Intent] = []
    conflicts: list[Conflict] = []
    adopt: dict[str, str] = {}
    not_imported: list[MirrorEntry] = []

    for uid in sorted(set(db_by_uid) | set(file_by_uid)):
        db, fl, known = db_by_uid.get(uid), file_by_uid.get(uid), base.get(uid)
        if db and fl:
            if db.hash == fl.hash:
                if known != db.hash:
                    adopt[uid] = db.hash
                if fl.label is not None and db.label is not None and fl.label != db.label:
                    # nur die Anzeige weicht ab (z. B. Typwechsel in der Datenbank): die Datei zieht nach
                    intents.append(Intent("files", "update", db))
            elif known is None:
                conflicts.append(Conflict("both_created", uid, db.label, db, fl))
            elif known == db.hash:
                intents.append(Intent("database", "update", fl))
            elif known == fl.hash:
                intents.append(Intent("files", "update", db))
            else:
                conflicts.append(Conflict("both_changed", uid, db.label, db, fl))
        elif db:
            if known is None:
                intents.append(Intent("files", "create", db))
            elif not db.trashed:
                conflicts.append(Conflict("deleted_in_files", uid, db.label, db, None))
        elif fl:
            if known is None:
                intents.append(Intent("database", "create", fl))
            elif known == fl.hash and (fl.kind in ephemeral or is_purged(uid, purged)):
                intents.append(Intent("files", "delete", fl))
            else:
                conflicts.append(Conflict("deleted_in_database", uid, fl.label, None, fl))

    forget = tuple(sorted(uid for uid in base if uid not in db_by_uid and uid not in file_by_uid))

    for entry in files:
        if entry.uid is None:
            if direction == "both":
                intents.append(Intent("database", "create", entry))
            else:
                not_imported.append(entry)

    allowed = _allowed_targets(direction)
    kept = tuple(i for i in intents if i.target in allowed)
    skipped = tuple(i for i in intents if i.target not in allowed)
    return Plan(kept, tuple(conflicts), adopt, forget, skipped, tuple(not_imported))


def _allowed_targets(direction: Direction) -> tuple[Side, ...]:
    targets: dict[Direction, tuple[Side, ...]] = {
        "both": ("database", "files"),
        "to_database": ("database",),
        "to_files": ("files",),
    }
    return targets[direction]


def resolve_conflicts(
    conflicts: Sequence[Conflict],
    decisions: Mapping[str, Choice],
    direction: Direction = "both",
    delete_missing: bool = False,
) -> tuple[tuple[Intent, ...], tuple[Conflict, ...], tuple[Intent, ...]]:
    """Setzt die Entscheidungen des Besitzers um: `(Änderungen, offene Konflikte, wegen Richtung übersprungen)`.

    Eine Entscheidung, die einen Eintrag löscht, braucht `delete_missing=True`, sonst `DeletionNotConfirmed`.
    `defer`, fehlende Entscheidungen und Entscheidungen gegen die Richtung lassen den Konflikt offen.
    """
    allowed = _allowed_targets(direction)
    intents: list[Intent] = []
    open_conflicts: list[Conflict] = []
    skipped: list[Intent] = []
    for conflict in conflicts:
        choice = decisions.get(conflict.key, "defer")
        intent = _intent_for(conflict, choice)
        if intent is None:
            open_conflicts.append(conflict)
            continue
        if intent.is_deletion and not delete_missing:
            raise DeletionNotConfirmed(
                f"Die Entscheidung für {conflict.label or conflict.key} löscht und braucht delete_missing",
                details={"key": conflict.key, "choice": choice},
            )
        if intent.target in allowed:
            intents.append(intent)
        else:
            skipped.append(intent)
            open_conflicts.append(conflict)
    return tuple(intents), tuple(open_conflicts), tuple(skipped)


def _intent_for(conflict: Conflict, choice: Choice) -> Intent | None:
    if choice == "defer":
        return None
    db, fl = conflict.database, conflict.files
    if conflict.kind in ("both_changed", "both_created"):
        assert db is not None and fl is not None
        return Intent("files", "update", db) if choice == "database" else Intent("database", "update", fl)
    if conflict.kind == "deleted_in_files":
        assert db is not None
        return Intent("files", "create", db) if choice == "database" else Intent("database", "delete", db)
    assert fl is not None  # deleted_in_database
    return Intent("files", "delete", fl) if choice == "database" else Intent("database", "create", fl)


#: Ab dieser Ähnlichkeit gilt ein Eintrag als wahrscheinlich umbenannter Partner eines gelöschten.
RENAME_SIMILARITY = 0.6

Recommendation = Literal["database", "files", "none"]


@dataclass(frozen=True)
class RenamePartner:
    key: str
    label: str | None
    similarity: float


@dataclass(frozen=True)
class ConflictHint:
    """Erklärung eines Konflikts, aus vorhandenen Angaben abgeleitet (ändert nichts am Plan).

    `*_changed`: ob die Seite seit dem letzten Abgleich geändert ist; `None`, wenn es sie nicht gibt oder keine
    Basis. `recommendation` ist nur ein Vorschlag, `reason` sein Begründungscode.
    """

    database_changed: bool | None
    files_changed: bool | None
    synced_at: datetime | None
    renamed_to: RenamePartner | None
    recommendation: Recommendation
    reason: str


def explain_conflict(
    conflict: Conflict, base: Mapping[str, str], candidates: Sequence[MirrorEntry], synced_at: datetime | None
) -> ConflictHint:
    """Leitet zu einem Konflikt Herkunft, Umbenennungsverdacht und Empfehlung ab.

    `candidates` sind die Einträge der Seite, auf der `conflict` gelöscht wurde; `synced_at` ist der Zeitpunkt, zu
    dem der Eintrag zuletzt abgeglichen wurde. Bei einem Löschkonflikt gilt: ist die übrige Seite seit dem Abgleich
    unverändert, ist die Löschung die naheliegende Entscheidung, sonst ginge eine Änderung verloren.
    """
    known = base.get(conflict.key)

    def changed(entry: MirrorEntry | None) -> bool | None:
        return None if entry is None or known is None else entry.hash != known

    database_changed, files_changed = changed(conflict.database), changed(conflict.files)
    if conflict.kind in ("both_changed", "both_created"):
        return ConflictHint(database_changed, files_changed, synced_at, None, "none", conflict.kind)
    present = conflict.database or conflict.files
    assert present is not None
    renamed = _rename_partner(present, candidates)
    if conflict.kind == "deleted_in_files":
        keep, delete, other_changed = "database", "files", database_changed
    else:
        keep, delete, other_changed = "files", "database", files_changed
    if other_changed:
        recommendation, reason = keep, "deleted_other_changed"
    else:
        recommendation, reason = delete, "renamed" if renamed else "deleted_other_unchanged"
    return ConflictHint(database_changed, files_changed, synced_at, renamed, recommendation, reason)  # type: ignore[arg-type]


def _rename_partner(entry: MirrorEntry, candidates: Sequence[MirrorEntry]) -> RenamePartner | None:
    """Der ähnlichste andere Eintrag gleicher Art mit gleichen Verweisen (z. B. am selben Element), ab 0,6."""
    text = _comparable(entry)
    best: RenamePartner | None = None
    for other in candidates:
        if other.key == entry.key or other.kind != entry.kind or dict(other.refs) != dict(entry.refs):
            continue
        matcher = SequenceMatcher(None, text, _comparable(other), autojunk=False)
        if matcher.real_quick_ratio() < RENAME_SIMILARITY or matcher.quick_ratio() < RENAME_SIMILARITY:
            continue
        similarity = matcher.ratio()
        if similarity >= RENAME_SIMILARITY and (best is None or similarity > best.similarity):
            best = RenamePartner(other.key, other.label, round(similarity, 3))
    return best


def _comparable(entry: MirrorEntry) -> str:
    return json.dumps(entry.fields, sort_keys=True, ensure_ascii=False, default=str)


def is_purged(key: str, purged: frozenset[str]) -> bool:
    """Ist `key` ein endgültig gelöschtes Element oder gehört es dazu (Dokumente: `<uid>/<name>`)?"""
    return key in purged or any(key.startswith(f"{uid}/") for uid in purged)


def plan_token(project: str, direction: Direction, plan: Plan) -> str:
    """Zustandsloses Token der Vorschau: ändert sich der Plan, ändert sich das Token."""

    def side(entry: MirrorEntry | None) -> str | None:
        return entry.hash if entry else None

    body = {
        "project": project,
        "direction": direction,
        "intents": sorted([i.target, i.action, i.entry.key, i.entry.hash] for i in plan.intents),
        "conflicts": sorted([c.kind, c.key, side(c.database), side(c.files)] for c in plan.conflicts),
        "adopt": sorted(plan.adopt.items()),
        "forget": list(plan.forget),
        "skipped": sorted([i.target, i.action, i.entry.key, i.entry.hash] for i in plan.skipped),
        "not_imported": sorted([e.key, e.hash] for e in plan.not_imported),
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sync_state(plan: Plan) -> SyncState:
    """Zustand eines Projekts aus dem Plan (ohne `paused`, das kommt vom Ordnerzustand)."""
    if plan.conflicts:
        return "conflicts"
    to_files = any(i.target == "files" for i in plan.intents + plan.skipped)
    to_database = any(i.target == "database" for i in plan.intents + plan.skipped) or bool(plan.not_imported)
    if to_files and to_database:
        return "both_changed"
    if to_files:
        return "primary_changed"
    if to_database:
        return "mirror_changed"
    return "in_sync"


def text_labels(labels: Mapping[str, str]) -> dict[str, str]:
    """Aus `Platzhalter → Label` die Einträge, die im Fließtext vorkommen können (ohne Dokument-Platzhalter `…/…`)."""
    return {k: v for k, v in labels.items() if "/" not in k and k != v}


def replace_ids(text: str, mapping: Mapping[str, str]) -> str:
    """Ersetzt jede Schlüssel-ID aus `mapping`, wo sie als eigene ID steht. Längere IDs, die nur damit beginnen
    (`NEW-route-2` bei `NEW-route`), bleiben unverändert."""
    if not mapping or not any(key in text for key in mapping):
        return text
    keys = "|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True))
    pattern = rf"(?<![A-Za-z0-9_-])(?:{keys})(?![A-Za-z0-9-])(?!\.[A-Za-z0-9])(?!_(?!notes|spec))"
    return re.sub(pattern, lambda m: mapping[m.group(0)], text)


def _map_strings(value: Any, mapping: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return replace_ids(value, mapping)
    if isinstance(value, Mapping):
        return {k: _map_strings(v, mapping) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_map_strings(v, mapping) for v in value)
    return value


def substitute_placeholders(entries: Iterable[MirrorEntry], labels: Mapping[str, str]) -> list[MirrorEntry]:
    """Ersetzt in den Verweisen aller Einträge die Platzhalter durch die vergebenen Labels."""
    return [e.map_refs(labels) for e in entries]
