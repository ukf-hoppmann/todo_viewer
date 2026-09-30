"""Comparing two copies of a project's data (database and markdown folder) before they are synced."""
from __future__ import annotations

import dataclasses
import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from .documents import content_version
from .errors import SyncPathMissingError, SyncSameBackendError, SyncStaleError
from .item import Item
from .source import Source, SyncBaseline

# (item id, document name) -> content
Documents = Mapping[tuple[str, str], str]


class SyncDirection(StrEnum):
    TO_MD = "to_md"
    FROM_MD = "from_md"


class SyncState(StrEnum):
    """How a project's mirror relates to its primary source since the last sync."""

    NONE = "none"  # no mirror
    IN_SYNC = "in_sync"
    MIRROR_CHANGED = "mirror_changed"
    PRIMARY_CHANGED = "primary_changed"
    BOTH_CHANGED = "both_changed"
    UNKNOWN = "unknown"  # never synced, and the sides differ
    UNREADABLE = "unreadable"  # a side cannot be read


@dataclass(frozen=True)
class SyncEntry:
    """One item or document a sync creates, changes, would delete, or leaves alone."""

    kind: str  # "item" | "document"
    label: str
    title: str
    name: str | None = None  # documents only


@dataclass(frozen=True)
class SyncPreview:
    created: tuple[SyncEntry, ...]
    changed: tuple[SyncEntry, ...]
    unchanged: int
    missing: tuple[SyncEntry, ...]
    created_documents: tuple[SyncEntry, ...]
    changed_documents: tuple[SyncEntry, ...]
    unchanged_documents: int
    missing_documents: tuple[SyncEntry, ...]
    skipped: tuple[SyncEntry, ...]
    # Identifies the state of both sides the preview was made from.
    token: str


def default_direction(source: Source) -> SyncDirection:
    """From the primary source to the mirror: a database project writes its folder, a markdown project its mirror."""
    return SyncDirection.TO_MD if source.backend == "database" else SyncDirection.FROM_MD


def primary_and_mirror(source: Source) -> tuple[Source, Source] | None:
    """The primary source and its mirror as two sources with the project's id; None if it has no mirror."""
    if source.mirror == "none":
        return None
    database, markdown = sync_pair(source, default_direction(source))
    return (database, markdown) if source.backend == "database" else (markdown, database)


def fingerprint(items: Sequence[Item], documents: Documents) -> str:
    """Identifies the content of one side: its items (by version) and documents (by content), in any order."""
    digest = hashlib.sha256()
    for item in sorted(items, key=lambda i: i.id):
        digest.update(f"\0i{item.id}\0{item.version}".encode())
    for (label, name), content in sorted(documents.items()):
        digest.update(f"\0d{label}\0{name}\0{content_version(content)}".encode())
    return digest.hexdigest()[:16]


def classify(primary: str, mirror: str, baseline: SyncBaseline | None) -> SyncState:
    """Which side moved since the last sync, from the fingerprints of both sides now and right after it.

    Without a last sync only the sides themselves can be compared. Sides that are equal are in sync, however they
    got there; what a sync left different on purpose (kept entries) is part of the baseline, not a change.
    """
    if primary == mirror:
        return SyncState.IN_SYNC
    if baseline is None:
        return SyncState.UNKNOWN
    primary_moved, mirror_moved = primary != baseline.primary, mirror != baseline.mirror
    if primary_moved and mirror_moved:
        return SyncState.BOTH_CHANGED
    if primary_moved:
        return SyncState.PRIMARY_CHANGED
    return SyncState.MIRROR_CHANGED if mirror_moved else SyncState.IN_SYNC


def sync_pair(source: Source, direction: SyncDirection) -> tuple[Source, Source]:
    """The database side and the markdown side of a project, as two sources with the project's id.

    A database project is synced with its `sync_path` folder in both directions, and so is a markdown project
    that keeps a database mirror. A markdown project without one can only be read into the database (`from_md`),
    which is how it is moved.
    """
    if source.backend == "markdown":
        if direction is SyncDirection.TO_MD and not source.mirror_database:
            raise SyncSameBackendError()
        return dataclasses.replace(source, backend="database", path="", sync_path=None), source
    if not source.sync_path:
        raise SyncPathMissingError()
    return source, dataclasses.replace(source, backend="markdown", path=source.sync_path, sync_path=None)


def plan_sync(source_items: Sequence[Item], target_items: Sequence[Item], source_docs: Documents,
              target_docs: Documents, skipped: Sequence[SyncEntry] = ()) -> SyncPreview:
    """What a sync from source to target creates, changes, and finds missing on the source side.

    Items are equal if their versions are; documents if their contents are. The documents of items that are
    missing on the source side are not listed on their own; those of new items count as new.
    """
    target = {i.id: i for i in target_items}
    source = {i.id: i for i in source_items}
    created: list[SyncEntry] = []
    changed: list[SyncEntry] = []
    unchanged = 0
    for item in source_items:
        found = target.get(item.id)
        if found is None:
            created.append(SyncEntry("item", item.id, item.title))
        elif found.version != item.version:
            changed.append(SyncEntry("item", item.id, item.title))
        else:
            unchanged += 1
    missing = [SyncEntry("item", i.id, i.title) for i in target_items if i.id not in source]

    created_docs: list[SyncEntry] = []
    changed_docs: list[SyncEntry] = []
    missing_docs: list[SyncEntry] = []
    unchanged_docs = 0
    for (label, name), content in source_docs.items():
        current = target_docs.get((label, name))
        entry = SyncEntry("document", label, source[label].title, name)
        if current is None:
            created_docs.append(entry)
        elif current != content:
            changed_docs.append(entry)
        else:
            unchanged_docs += 1
    for (label, name) in target_docs:
        if label in source and (label, name) not in source_docs:
            missing_docs.append(SyncEntry("document", label, source[label].title, name))

    return SyncPreview(tuple(created), tuple(changed), unchanged, tuple(missing), tuple(created_docs),
                       tuple(changed_docs), unchanged_docs, tuple(missing_docs), tuple(skipped),
                       _token(source_items, target_items, source_docs, target_docs))


def merged_items(source_items: Sequence[Item], target_items: Sequence[Item], delete_missing: bool) -> list[Item]:
    """The items the target holds after a sync: those of the source, then the missing ones unless deleted."""
    kept = [] if delete_missing else [i for i in target_items if i.id not in {s.id for s in source_items}]
    return [*source_items, *kept]


def check_token(expected: str | None, current: str) -> None:
    """Raises SyncStaleError unless `expected` (from the preview) is the token of the current state."""
    if expected != current:
        raise SyncStaleError()


def _token(source_items: Sequence[Item], target_items: Sequence[Item], source_docs: Documents,
           target_docs: Documents) -> str:
    digest = hashlib.sha256()
    for side, items, docs in (("source", source_items, source_docs), ("target", target_items, target_docs)):
        digest.update(side.encode())
        for item in items:  # the order counts: it is what gets written
            digest.update(f"\0i{item.id}\0{item.version}".encode())
        for (label, name), content in sorted(docs.items()):
            digest.update(f"\0d{label}\0{name}\0{content_version(content)}".encode())
    return digest.hexdigest()[:16]
