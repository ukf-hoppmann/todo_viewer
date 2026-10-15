"""Comparing two copies of a project's data (database and markdown folder) before they are synced."""
from __future__ import annotations

import dataclasses
import hashlib
from collections.abc import Collection, Mapping, Sequence
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


class Side(StrEnum):
    """The two places a project's data lives in a sync, whichever of them is the primary source."""

    DATABASE = "database"
    MARKDOWN = "markdown"


class Choice(StrEnum):
    """The decision for one conflict: whose state counts, or leave it for later."""

    DATABASE = "database"
    MARKDOWN = "markdown"
    DEFER = "defer"


class Change(StrEnum):
    """What happened to one entry since the last sync, seen from the two sides."""

    UNCHANGED = "unchanged"
    DATABASE_CHANGED = "database_changed"
    MARKDOWN_CHANGED = "markdown_changed"
    BOTH_CHANGED = "both_changed"
    DATABASE_NEW = "database_new"
    MARKDOWN_NEW = "markdown_new"
    BOTH_NEW = "both_new"  # on both sides with different content
    DATABASE_DELETED = "database_deleted"  # gone from the database, still in the markdown folder
    MARKDOWN_DELETED = "markdown_deleted"
    BOTH_DELETED = "both_deleted"  # gone everywhere: only the stored state is left over

    @property
    def is_conflict(self) -> bool:
        return self in _CONFLICTS


_CONFLICTS = frozenset({Change.BOTH_CHANGED, Change.BOTH_NEW, Change.DATABASE_DELETED, Change.MARKDOWN_DELETED})


@dataclass(frozen=True, order=True)
class EntryKey:
    """What a sync compares: an item (`name` empty) or one document of an item."""

    kind: str  # "item" | "document"
    label: str
    name: str = ""


@dataclass(frozen=True)
class EntryState:
    """The versions of an entry on both sides right after the last sync that left them equal."""

    database: str
    markdown: str


@dataclass(frozen=True)
class Resolution:
    """The owner's decision for one conflict; `name` is set for documents."""

    kind: str
    label: str
    name: str | None
    choice: Choice

    @property
    def key(self) -> EntryKey:
        return EntryKey(self.kind, self.label, self.name or "")


@dataclass(frozen=True)
class SyncEntry:
    """One item or document a sync creates or changes, or that is in conflict."""

    kind: str  # "item" | "document"
    label: str
    title: str
    name: str | None = None  # documents only
    origin: Side | None = None  # the side whose version is carried over; None for a conflict

    @property
    def key(self) -> EntryKey:
        return EntryKey(self.kind, self.label, self.name or "")


@dataclass(frozen=True)
class SideView:
    """One side's version of a conflicting entry: an item as named values, a document as text."""

    fields: tuple[tuple[str, str], ...] | None = None
    text: str | None = None


@dataclass(frozen=True)
class SyncConflict:
    entry: SyncEntry
    reason: Change
    database: SideView | None  # None: the entry is missing on this side
    markdown: SideView | None


@dataclass(frozen=True)
class SyncPreview:
    created: tuple[SyncEntry, ...]  # new on one side, carried to the other
    changed: tuple[SyncEntry, ...]  # changed on one side only, carried to the other
    unchanged: int
    created_documents: tuple[SyncEntry, ...]
    changed_documents: tuple[SyncEntry, ...]
    unchanged_documents: int
    conflicts: tuple[SyncConflict, ...]  # items first, then documents; nothing of them is touched without a decision
    skipped: tuple[SyncEntry, ...]
    # Identifies the state of both sides and of the stored sync state the preview was made from.
    token: str


@dataclass(frozen=True)
class PlannedEntry:
    key: EntryKey
    title: str
    change: Change


@dataclass(frozen=True)
class SyncPlan:
    preview: SyncPreview
    entries: tuple[PlannedEntry, ...]  # every entry that exists on at least one side, items before documents


@dataclass(frozen=True)
class Transfer:
    """One step of a run: the entry is copied from the other side to `to`, or deleted from `to`."""

    key: EntryKey
    title: str
    to: Side
    delete: bool = False


@dataclass(frozen=True)
class Decisions:
    transfers: tuple[Transfer, ...]
    deferred: tuple[PlannedEntry, ...]  # conflicts that stay as they are


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


def classify_entry(database: str | None, markdown: str | None, stored: EntryState | None) -> Change:
    """What happened to one entry, from its versions on both sides (None: missing) and the state after the last sync.

    Without a stored state an entry on one side only is new there, and different versions on both sides are a
    conflict. With one, a deletion on one side is a conflict even if the other side did not change.
    """
    if database is None and markdown is None:
        return Change.BOTH_DELETED
    if stored is None:
        if markdown is None:
            return Change.DATABASE_NEW
        if database is None:
            return Change.MARKDOWN_NEW
        return Change.UNCHANGED if database == markdown else Change.BOTH_NEW
    if database is None:
        return Change.DATABASE_DELETED
    if markdown is None:
        return Change.MARKDOWN_DELETED
    if database == markdown:
        return Change.UNCHANGED
    database_moved, markdown_moved = database != stored.database, markdown != stored.markdown
    if database_moved and not markdown_moved:
        return Change.DATABASE_CHANGED
    if markdown_moved and not database_moved:
        return Change.MARKDOWN_CHANGED
    return Change.BOTH_CHANGED


def plan_sync(database_items: Sequence[Item], markdown_items: Sequence[Item], database_docs: Documents,
              markdown_docs: Documents, states: Mapping[EntryKey, EntryState],
              skipped: Sequence[SyncEntry] = ()) -> SyncPlan:
    """What a sync finds: every entry classified by the versions on both sides and the state after the last sync.

    Items are equal if their versions are; documents if their contents are. The documents of an item that exists on
    one side only travel with it if it is new; those of a deleted item are not listed on their own, they follow the
    decision about the item.
    """
    database = {i.id: i for i in database_items}
    markdown = {i.id: i for i in markdown_items}
    labels = [*database, *(label for label in markdown if label not in database)]
    entries: list[PlannedEntry] = []
    titles: dict[str, str] = {}
    changes: dict[str, Change] = {}
    for label in labels:
        key = EntryKey("item", label)
        d, m = database.get(label), markdown.get(label)
        change = classify_entry(d.version if d else None, m.version if m else None, states.get(key))
        titles[label] = (d or m).title  # type: ignore[union-attr]
        changes[label] = change
        entries.append(PlannedEntry(key, titles[label], change))
    for label in labels:
        for name in _document_names(label, database_docs, markdown_docs):
            both = label in database and label in markdown
            d_text, m_text = database_docs.get((label, name)), markdown_docs.get((label, name))
            if both:
                stored = states.get(EntryKey("document", label, name))
                change = classify_entry(None if d_text is None else content_version(d_text),
                                        None if m_text is None else content_version(m_text), stored)
            elif changes[label] in (Change.DATABASE_NEW, Change.MARKDOWN_NEW):
                change = changes[label]
            else:
                continue
            entries.append(PlannedEntry(EntryKey("document", label, name), titles[label], change))
    texts = {EntryKey("document", label, name): (database_docs.get((label, name)), markdown_docs.get((label, name)))
             for label in labels for name in _document_names(label, database_docs, markdown_docs)}
    preview = _preview(entries, database, markdown, texts, skipped, _token(database_items, markdown_items,
                                                                          database_docs, markdown_docs, states))
    return SyncPlan(preview, tuple(entries))


def _document_names(label: str, *documents: Documents) -> list[str]:
    return sorted({name for docs in documents for (owner, name) in docs if owner == label})


_ORIGIN = {Change.DATABASE_NEW: Side.DATABASE, Change.DATABASE_CHANGED: Side.DATABASE,
           Change.MARKDOWN_NEW: Side.MARKDOWN, Change.MARKDOWN_CHANGED: Side.MARKDOWN}


def _preview(entries: Sequence[PlannedEntry], database: Mapping[str, Item], markdown: Mapping[str, Item],
             texts: Mapping[EntryKey, tuple[str | None, str | None]], skipped: Sequence[SyncEntry],
             token: str) -> SyncPreview:
    created: dict[str, list[SyncEntry]] = {"item": [], "document": []}
    changed: dict[str, list[SyncEntry]] = {"item": [], "document": []}
    unchanged = {"item": 0, "document": 0}
    conflicts: list[SyncConflict] = []
    for planned in entries:
        key, change = planned.key, planned.change
        entry = SyncEntry(key.kind, key.label, planned.title, key.name or None, _ORIGIN.get(change))
        if change is Change.UNCHANGED:
            unchanged[key.kind] += 1
        elif change in (Change.DATABASE_NEW, Change.MARKDOWN_NEW):
            created[key.kind].append(entry)
        elif change in (Change.DATABASE_CHANGED, Change.MARKDOWN_CHANGED):
            changed[key.kind].append(entry)
        elif change.is_conflict:
            if key.kind == "item":
                views = (database.get(key.label), markdown.get(key.label))
                sides = tuple(None if item is None else SideView(fields=item_fields(item)) for item in views)
            else:
                sides = tuple(None if text is None else SideView(text=text) for text in texts[key])
            conflicts.append(SyncConflict(entry, change, sides[0], sides[1]))
    conflicts.sort(key=lambda c: c.entry.kind != "item")  # stable: items first
    return SyncPreview(tuple(created["item"]), tuple(changed["item"]), unchanged["item"],
                       tuple(created["document"]), tuple(changed["document"]), unchanged["document"],
                       tuple(conflicts), tuple(skipped), token)


def item_fields(item: Item) -> tuple[tuple[str, str], ...]:
    """All stored fields of an item as name and text, so two versions can be compared field by field."""
    fields = []
    for name, value in dataclasses.asdict(item).items():
        if name == "project":
            continue
        if value is None:
            text = ""
        elif isinstance(value, list):
            text = "\n".join(str(v) for v in value)
        elif isinstance(value, dict):
            text = "\n".join(f"{k}: {v}" for k, v in value.items())
        else:
            text = str(value)
        fields.append((name, text))
    return tuple(fields)


def decide(plan: SyncPlan, resolutions: Sequence[Resolution], direction: SyncDirection | None) -> Decisions:
    """The steps of a run: conflict-free entries are carried over, a conflict only with a decision for it.

    A conflict without a decision, or whose decision would write a side the `direction` excludes, is deferred.
    The direction restricts only which side may be written; it does not change what counts as a conflict.
    """
    chosen = {r.key: r.choice for r in resolutions}
    allowed = {None: set(Side), SyncDirection.TO_MD: {Side.MARKDOWN}, SyncDirection.FROM_MD: {Side.DATABASE}}[direction]
    transfers: list[Transfer] = []
    deferred: list[PlannedEntry] = []
    for planned in plan.entries:
        change = planned.change
        if change in (Change.UNCHANGED, Change.BOTH_DELETED):
            continue
        step = _step(planned, chosen.get(planned.key, Choice.DEFER))
        if step is not None and step.to in allowed:
            transfers.append(step)
        elif change.is_conflict:
            deferred.append(planned)
    return Decisions(tuple(transfers), tuple(deferred))


def _step(planned: PlannedEntry, choice: Choice) -> Transfer | None:
    """The step for an entry; None for a conflict that is not decided."""
    change = planned.change
    if not change.is_conflict:
        target = Side.MARKDOWN if _ORIGIN[change] is Side.DATABASE else Side.DATABASE
        return Transfer(planned.key, planned.title, target)
    if choice is Choice.DEFER:
        return None
    winner = Side(choice.value)
    loser = Side.MARKDOWN if winner is Side.DATABASE else Side.DATABASE
    missing = {Change.DATABASE_DELETED: Side.DATABASE, Change.MARKDOWN_DELETED: Side.MARKDOWN}.get(change)
    return Transfer(planned.key, planned.title, loser, delete=missing is winner)


def merged_items(own: Sequence[Item], other: Sequence[Item], take: Collection[str],
                 drop: Collection[str]) -> list[Item]:
    """The items one side holds after a sync: its own, those in `take` replaced by (or added from) the other
    side's version, those in `drop` removed. An added item goes after the one before it on the other side."""
    result = [i for i in own if i.id not in drop]
    taken = {i.id: i for i in other if i.id in take}
    result = [taken.get(i.id, i) for i in result]
    present = {i.id for i in result}
    previous: str | None = None
    for item in other:
        if item.id in taken and item.id not in present:
            at = 0 if previous is None else next(n for n, i in enumerate(result) if i.id == previous) + 1
            result.insert(at, item)
            present.add(item.id)
        if item.id in present:
            previous = item.id
    return result


def check_token(expected: str | None, current: str) -> None:
    """Raises SyncStaleError unless `expected` (from the preview) is the token of the current state."""
    if expected != current:
        raise SyncStaleError()


def _token(database_items: Sequence[Item], markdown_items: Sequence[Item], database_docs: Documents,
           markdown_docs: Documents, states: Mapping[EntryKey, EntryState]) -> str:
    digest = hashlib.sha256()
    for side, items, docs in (("database", database_items, database_docs), ("markdown", markdown_items, markdown_docs)):
        digest.update(side.encode())
        for item in items:  # the order counts: it is what gets written
            digest.update(f"\0i{item.id}\0{item.version}".encode())
        for (label, name), content in sorted(docs.items()):
            digest.update(f"\0d{label}\0{name}\0{content_version(content)}".encode())
    digest.update(b"state")
    for key, state in sorted(states.items()):
        digest.update(f"\0{key.kind}\0{key.label}\0{key.name}\0{state.database}\0{state.markdown}".encode())
    return digest.hexdigest()[:16]
