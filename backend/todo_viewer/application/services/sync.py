from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import structlog

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import (
    DocumentForbiddenError,
    DocumentNotFoundError,
    SyncSameBackendError,
    SyncSourceInvalidError,
)
from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import (
    Decisions,
    EntryKey,
    EntryState,
    PlannedEntry,
    Resolution,
    Side,
    SyncDirection,
    SyncEntry,
    SyncPlan,
    SyncPreview,
    Transfer,
    check_token,
    decide,
    fingerprint,
    merged_items,
    plan_sync,
    primary_and_mirror,
    sync_pair,
)

from ..ports import (
    BacklogRepository,
    DatabaseBackup,
    DocumentStore,
    ItemStatusListener,
    MergeMarkerCheck,
    SyncStateStore,
)

log = structlog.get_logger(__name__)

# A markdown folder that does not exist yet or has no TODO.md is a target that is still empty.
_EMPTY_TARGET = frozenset({"not_found", "no_todo"})


@dataclass(frozen=True)
class SideFingerprints:
    """The content of the primary source and of its mirror, each as a fingerprint, and the open conflicts."""

    primary: str
    mirror: str
    conflicts: int = 0


@dataclass(frozen=True)
class SyncResult:
    preview: SyncPreview  # what was found before anything was written
    resolved: tuple[SyncEntry, ...]  # entries carried over; `origin` is the side they came from
    deleted: tuple[SyncEntry, ...]  # entries removed by a decision
    deferred: tuple[SyncEntry, ...]  # conflicts left as they were (no decision, or the direction excluded it)
    kept: tuple[SyncEntry, ...]  # the deferred ones that are deletions: the entry stays where it is
    # Both sides right after the sync, read while it still held the project; None if the project has no mirror.
    fingerprints: SideFingerprints | None = None


@dataclass(frozen=True)
class _Side:
    source: Source
    items: list[Item]
    documents: dict[tuple[str, str], str]
    skipped: list[SyncEntry]
    exists: bool = True


@dataclass(frozen=True)
class _Compared:
    database: _Side
    markdown: _Side
    states: dict[EntryKey, EntryState]
    plan: SyncPlan


class SyncService:
    """Compares a project's database side with its markdown folder entry by entry and carries over what only one
    side changed. Conflicts are carried over only with a decision; nothing happens by itself."""

    def __init__(self, backlogs: BacklogRepository, documents: DocumentStore,
                 listener: ItemStatusListener | None = None, db_backup: DatabaseBackup | None = None,
                 states: SyncStateStore | None = None, markers: MergeMarkerCheck | None = None):
        self._backlogs = backlogs
        self._documents = documents
        self._listener = listener
        self._db_backup = db_backup
        self._states = states
        self._markers = markers
        self._locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)
        self._guard = threading.Lock()

    def preview(self, source: Source, direction: SyncDirection | None = None, auto: bool = False) -> SyncPreview:
        """What a sync would do; changes nothing. `direction` only decides whether a missing folder is an error.

        `auto` is the strict reading of an automatic run: a missing folder and files with Git merge markers are
        errors (SyncSourceInvalidError), never something to work around.
        """
        with self._lock(source):
            return self._compare(source, direction, auto).plan.preview

    def in_sync(self, source: Source, direction: SyncDirection | None = None) -> bool:
        """True if a sync would find nothing to carry over and no conflict."""
        p = self.preview(source, direction)
        return not (p.created or p.changed or p.created_documents or p.changed_documents or p.conflicts)

    def fingerprints(self, source: Source) -> SideFingerprints | None:
        """The content of both sides as they are now, or None if the project has no mirror; changes nothing.

        Raises SyncSourceInvalidError if the primary source or an existing mirror cannot be read. A mirror that does
        not exist yet counts as empty.
        """
        with self._lock(source):
            return self._fingerprints(source)

    def run(self, source: Source, token: str | None, resolutions: Sequence[Resolution] = (),
            direction: SyncDirection | None = None, language: str = "en", remember: bool = True,
            auto: bool = False) -> SyncResult:
        """Carries over every entry only one side changed, and the conflicts `resolutions` decide; the rest stays.

        `token` is the one of the preview the caller confirmed (SyncStaleError if either side changed since).
        `direction` restricts which side is written. With `remember` the state of the entries both sides now agree on
        is stored for the next sync. `auto` marks a run of the automatic sync (read strictly like `preview(auto=True)`);
        it is the caller's task to pass no decisions, so nothing is deleted.
        """
        with self._lock(source):
            direction = self._direction(source, direction)
            found = self._compare(source, direction, auto)
            check_token(token, found.plan.preview.token)
            decisions = decide(found.plan, resolutions, direction)
            if any(t.to is Side.DATABASE for t in decisions.transfers) and self._db_backup:
                self._db_backup.create("auto" if auto else "sync")  # raises before anything is written if it fails
            primary_before = (found.database if source.backend == "database" else found.markdown).items
            done = self._apply(found, decisions, language)
            after = self._read_sides(source, direction)
            if remember:
                self._remember(source, after, found.states)
            # the primary source may have taken over changes of the other side
            self._announce_status_changes(source.project, primary_before,
                                          (after[0] if source.backend == "database" else after[1]).items)
            deferred = tuple(_entry(p) for p in decisions.deferred)
            return SyncResult(found.plan.preview,
                              resolved=tuple(_entry(t, origin=_other(t.to)) for t in done if not t.delete),
                              deleted=tuple(_entry(t) for t in done if t.delete), deferred=deferred,
                              kept=tuple(_entry(p) for p in decisions.deferred if p.change.name.endswith("_DELETED")),
                              fingerprints=self._overview(source, after[0], after[1],
                                                          self._states_of(source, after[1])))

    # --- applying ---

    def _apply(self, found: _Compared, decisions: Decisions, language: str) -> list[Transfer]:
        """Writes the database side first (one transaction), then the folder; returns what was really carried over."""
        done: list[Transfer] = []
        for target in (Side.DATABASE, Side.MARKDOWN):
            steps = [t for t in decisions.transfers if t.to is target]
            if steps:
                own, other = (found.database, found.markdown) if target is Side.DATABASE else (found.markdown,
                                                                                               found.database)
                done += self._write_side(target, own, other, steps, language)
        return done

    def _write_side(self, target: Side, own: _Side, other: _Side, steps: Sequence[Transfer],
                    language: str) -> list[Transfer]:
        take = {t.key.label for t in steps if t.key.kind == "item" and not t.delete}
        drop = {t.key.label for t in steps if t.key.kind == "item" and t.delete}
        items = merged_items(own.items, other.items, take, drop) if take or drop else None
        listed = {i.id: {*i.notes, *i.spec} for i in (items if items is not None else own.items)}
        copies = {(t.key.label, t.key.name): t for t in steps if t.key.kind == "document" and not t.delete}
        arriving = take - {i.id for i in own.items}  # items that are new on this side bring all their documents
        for (label, name), content in other.documents.items():
            if label in arriving and own.documents.get((label, name)) != content and (label, name) not in copies:
                copies[(label, name)] = Transfer(EntryKey("document", label, name), "", target)
        # A document is written only where its item lists it; otherwise it would be unreachable.
        writable = {k: t for k, t in copies.items() if k[1] in listed.get(k[0], ())}
        writes = [(label, name, other.documents[(label, name)]) for (label, name) in writable]
        removals = [t for t in steps if t.key.kind == "document" and t.delete]
        if not own.exists and (items is not None or writes):
            self._backlogs.initialize(own.source, language)
        if target is Side.DATABASE:  # documents belong to items, which must exist first
            if items is not None:
                self._backlogs.write_backlog(own.source, items, language)
            self._write_documents(own.source, writes)
        else:  # the backlog file goes last: it marks the export as complete
            self._write_documents(own.source, writes)
            if items is not None:
                self._backlogs.write_backlog(own.source, items, language)
        for step in removals:
            self._documents.delete_document(own.source, step.key.label, step.key.name)
        if target is Side.MARKDOWN:  # a database item takes its documents along when it is deleted
            for label in sorted(drop):
                self._documents.delete_documents(own.source, label)
        return [t for t in steps if t.key.kind == "item" or t.delete
                or (t.key.label, t.key.name) in writable]

    def _write_documents(self, target: Source, writes: Sequence[tuple[str, str, str]]) -> None:
        for label, name, content in writes:
            try:  # a file the target's item does not list yet is replaced, not refused
                current: str | None = self._documents.read(target, label, name)
            except DocumentNotFoundError:
                current = None
            self._documents.write(target, label, name, content,
                                  expected_version=None if current is None else content_version(current))

    # --- remembering ---

    def _states_of(self, source: Source, markdown: _Side) -> dict[EntryKey, EntryState]:
        return self._states.load(source.id, markdown.source.path) if self._states else {}

    def _remember(self, source: Source, after: tuple[_Side, _Side], before: dict[EntryKey, EntryState]) -> None:
        """Stores the version of every entry both sides now agree on and forgets the ones that are gone."""
        if self._states is None:
            return
        database, markdown = after
        d, m = _versions(database), _versions(markdown)
        put = {key: EntryState(v, v) for key, v in d.items() if m.get(key) == v and before.get(key) != EntryState(v, v)}
        remove = [key for key in before if key not in d and key not in m]
        self._states.save(source.id, markdown.source.path, put, remove)

    def _announce_status_changes(self, project: str, before: Sequence[Item], after: Sequence[Item]) -> None:
        """Tells the listener about every item whose status the sync changed, so event triggers can arrive. A
        failure is logged and never fails the sync, which is written already."""
        if self._listener is None:
            return
        was = {item.id: item.status for item in before}
        for item in after:
            if item.id in was and was[item.id] != item.status:
                try:
                    self._listener.item_status_changed(project, item.id, item.status)
                except Exception:
                    log.exception("sync_status_announce_failed", project=project, item=item.id)

    # --- reading ---

    def _fingerprints(self, source: Source) -> SideFingerprints | None:
        if primary_and_mirror(source) is None:
            return None
        database, markdown = self._read_sides(source, None, mirror_may_be_empty=True)
        return self._overview(source, database, markdown, self._states_of(source, markdown))

    @staticmethod
    def _overview(source: Source, database: _Side, markdown: _Side,
                  states: dict[EntryKey, EntryState]) -> SideFingerprints | None:
        if source.mirror == "none":
            return None
        plan = plan_sync(database.items, markdown.items, database.documents, markdown.documents, states)
        d, m = fingerprint(database.items, database.documents), fingerprint(markdown.items, markdown.documents)
        primary, mirror = (d, m) if source.backend == "database" else (m, d)
        return SideFingerprints(primary, mirror, len(plan.preview.conflicts))

    def _lock(self, source: Source) -> threading.Lock:
        with self._guard:
            return self._locks[source.id]

    @staticmethod
    def _direction(source: Source, direction: SyncDirection | None) -> SyncDirection | None:
        """A markdown project without a database mirror can only be read into the database."""
        if source.backend == "markdown" and not source.mirror_database:
            if direction is SyncDirection.TO_MD:
                raise SyncSameBackendError()
            return SyncDirection.FROM_MD
        return direction

    def _compare(self, source: Source, direction: SyncDirection | None, auto: bool = False) -> _Compared:
        direction = self._direction(source, direction)
        if auto:
            self._refuse_merge_markers(source)
        database, markdown = self._read_sides(source, direction, strict=auto)
        states = self._states_of(source, markdown)
        plan = plan_sync(database.items, markdown.items, database.documents, markdown.documents, states,
                         [*database.skipped, *markdown.skipped])
        return _Compared(database, markdown, states, plan)

    def _refuse_merge_markers(self, source: Source) -> None:
        """An unfinished Git merge leaves half-merged text in the files; an automatic run must not read it."""
        if self._markers is None:
            return
        _, markdown_source = sync_pair(source, SyncDirection.FROM_MD)
        files = self._markers.files_with_markers(markdown_source)
        if files:
            raise SyncSourceInvalidError("merge_markers", f"Git merge markers in {', '.join(files)}.")

    def _read_sides(self, source: Source, direction: SyncDirection | None, mirror_may_be_empty: bool = False,
                    strict: bool = False) -> tuple[_Side, _Side]:
        """Both sides; an unusable backlog stops the sync before anything is written. A folder that does not exist
        yet is an empty side only where nothing is lost by it: when the folder is the target or the mirror."""
        database_source, markdown_source = sync_pair(source, direction or SyncDirection.FROM_MD)
        markdown_may_be_empty = not strict and (direction is SyncDirection.TO_MD or
                                 (direction is None and source.backend == "database") or
                                 (mirror_may_be_empty and source.backend == "database"))
        database_may_be_empty = mirror_may_be_empty and source.backend == "markdown"
        return (self._read(database_source, empty_ok=database_may_be_empty),
                self._read(markdown_source, empty_ok=markdown_may_be_empty))

    def _read(self, source: Source, empty_ok: bool) -> _Side:
        """The items and documents of one side."""
        backlog = self._backlogs.load(source)
        if backlog.problem:
            if empty_ok and backlog.problem.code in _EMPTY_TARGET:
                return _Side(source, [], {}, [], exists=False)
            raise SyncSourceInvalidError(backlog.problem.code, backlog.problem.message)
        documents: dict[tuple[str, str], str] = {}
        skipped: list[SyncEntry] = []
        for item in backlog.items:
            for name in [*item.notes, *item.spec]:
                content = self._read_document(source, item, name)
                if content is None:
                    skipped.append(SyncEntry("document", item.id, item.title, name))
                else:
                    documents[(item.id, name)] = content
        return _Side(source, backlog.items, documents, skipped)

    def _read_document(self, source: Source, item: Item, name: str) -> str | None:
        """None for documents the sync cannot carry: written as a path, forbidden, or listed but missing."""
        if "/" in name:
            return None
        try:
            return self._documents.read(source, item.id, name)
        except (DocumentNotFoundError, DocumentForbiddenError):
            return None


def _versions(side: _Side) -> dict[EntryKey, str]:
    versions = {EntryKey("item", i.id): i.version for i in side.items}
    versions.update({EntryKey("document", label, name): content_version(text)
                     for (label, name), text in side.documents.items()})
    return versions


def _other(side: Side) -> Side:
    return Side.MARKDOWN if side is Side.DATABASE else Side.DATABASE


def _entry(step: Transfer | PlannedEntry, origin: Side | None = None) -> SyncEntry:
    key = step.key
    return SyncEntry(key.kind, key.label, step.title, key.name or None, origin)


__all__ = ["SideFingerprints", "SyncResult", "SyncService"]
