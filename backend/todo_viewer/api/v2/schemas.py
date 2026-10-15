"""HTTP contract of API v2. Items are addressed by source id + item id, sources by their stable id."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from todo_viewer.application.ports import FolderListing, StorageDescription
from todo_viewer.application.services import AutoSyncInfo, DocumentResult, RetypeResult, SyncResult, SyncStatus
from todo_viewer.domain.documents import DocumentRef, item_documents
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source, SourceProblem
from todo_viewer.domain.sync import SideView, SyncConflict, SyncEntry, SyncPreview, SyncSection


class HealthOut(BaseModel):
    status: Literal["ok"]
    api: Literal["2"] = Field(description="Major version of this API")


class ErrorOut(BaseModel):
    code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)


class ProblemOut(BaseModel):
    code: str
    message: str

    @classmethod
    def of(cls, problem: SourceProblem | None) -> ProblemOut | None:
        return cls(code=problem.code, message=problem.message) if problem else None


class DocumentRefOut(BaseModel):
    name: str = Field(description="Document name within the item, e.g. STORY-003_spec.md")
    kind: Literal["notes", "spec"]

    @classmethod
    def of(cls, ref: DocumentRef) -> DocumentRefOut:
        return cls(name=ref.name, kind=ref.kind.value)


class ItemOut(BaseModel):
    key: str = Field(description="Unique within the whole response: source_id/id")
    source_id: str
    id: str
    version: str = Field(description="Changes with every change of the item; required for edits")
    archived: bool
    project: str
    type: str
    title: str
    status: str
    parent: str | None
    required_for_parent: bool | None
    dependencies: list[str]
    created: str | None
    area: str | None
    priority: str | None
    goal: str | None
    completion_criteria: str | None
    summary: str | None
    resolution: str | None
    documents: list[DocumentRefOut] = Field(description="Notes and specs; read them via /documents/{name}")
    deleted: str | None = Field(description="Date the item was moved to the trash; null if in use")
    extra_fields: dict[str, str]
    archive_supported: bool

    @classmethod
    def of(cls, source: Source, item: Item, archive_supported: bool) -> ItemOut:
        return cls(
            key=f"{source.id}/{item.id}",
            source_id=source.id,
            id=item.id,
            version=item.version,
            archived=item.location is Location.ARCHIVE,
            project=source.project,
            type=item.item_type,
            title=item.title,
            status=item.status,
            parent=item.parent,
            required_for_parent=item.required_for_parent,
            dependencies=item.dependencies,
            created=item.created,
            area=item.area,
            priority=item.priority,
            goal=item.goal,
            completion_criteria=item.completion_criteria,
            summary=item.summary,
            resolution=item.resolution,
            documents=[DocumentRefOut.of(d) for d in item_documents(item)],
            deleted=item.deleted,
            extra_fields=item.extra_fields,
            archive_supported=archive_supported,
        )


class IndexItemOut(BaseModel):
    """The fields needed to place new work; see GET /backlog for the full item."""

    source_id: str
    id: str
    type: str
    status: str
    title: str
    parent: str | None
    area: str | None

    @classmethod
    def of(cls, source: Source, item: Item) -> IndexItemOut:
        return cls(source_id=source.id, id=item.id, type=item.item_type, status=item.status, title=item.title,
                   parent=item.parent, area=item.area)


class IndexOut(BaseModel):
    items: list[IndexItemOut]


class SyncStatusOut(BaseModel):
    source_id: str
    state: Literal[
        "none", "in_sync", "mirror_changed", "primary_changed", "both_changed", "unknown", "unreadable"
    ] = Field(
        description="none: no mirror; in_sync; mirror_changed / primary_changed / both_changed: which side changed "
                    "since the last sync (a sync through this API); unknown: never synced and the sides differ; "
                    "unreadable: a side cannot be read")
    last_sync_at: str | None = Field(description="When the project was last synced through this API; null if never")
    conflicts: int = Field(
        description="Entries that need a decision: changed on both sides, new on both with different content, or "
                    "deleted on one side. `state` can say in_sync while this is not 0: what a sync left undecided "
                    "does not count as a change")

    auto_sync: bool = Field(description="The automatic sync is on and acts for this project (the switch is on and "
                                        "there is a mirror)")
    auto_last_run_at: str | None = Field(
        description="When the automatic sync last carried something over (ISO 8601); null if it did not since the "
                    "viewer started")
    auto_paused: str | None = Field(
        description="Why the last check of the automatic sync could not run, e.g. merge_markers (a half-merged file "
                    "in the folder), not_found, unsupported_format; null if it ran or has not run")

    @classmethod
    def of(cls, source: Source, status: SyncStatus, auto: AutoSyncInfo | None = None) -> SyncStatusOut:
        auto = auto or AutoSyncInfo()
        return cls(source_id=source.id, state=status.state.value, last_sync_at=status.last_sync_at,
                   conflicts=status.conflicts, auto_sync=source.auto_sync_active, auto_last_run_at=auto.last_run_at,
                   auto_paused=auto.paused)


class StorageOut(BaseModel):
    kind: str = Field(description="Type of the central database, e.g. sqlite")
    location: str = Field(description="The database file (sqlite) or its URL without a password")
    schema_version: int = Field(description="Version of the database schema (number of applied migrations)")

    @classmethod
    def of(cls, storage: StorageDescription) -> StorageOut:
        return cls(kind=storage.kind, location=storage.location, schema_version=storage.schema_version)


class SourceOut(BaseModel):
    id: str
    project: str
    path: str = Field(description="Markdown projects: backlog folder; database projects: empty")
    backend: Literal["markdown", "database"]
    sync_path: str | None = Field(description="Database projects: folder to sync markdown files with")
    primary: Literal["markdown", "database"] = Field(description="The side that holds the truth (same as `backend`)")
    markdown_path: str | None = Field(
        description="The markdown folder on either side: the primary source of a markdown project, the mirror of a "
                    "database project; null if a database project has none")
    mirror: Literal["none", "markdown", "database"] = Field(
        description="The other side kept as a mirror; it is written by a sync only")
    auto_sync: bool = Field(
        description="The owner's switch for the automatic sync; it acts only while there is a mirror")

    @classmethod
    def of(cls, source: Source) -> SourceOut:
        return cls(id=source.id, project=source.project, path=source.path,
                   backend=source.backend,  # type: ignore[arg-type]
                   sync_path=source.sync_path,
                   primary=source.backend,  # type: ignore[arg-type]
                   markdown_path=source.markdown_path,
                   mirror=source.mirror, auto_sync=source.auto_sync)  # type: ignore[arg-type]


class SourceStatusOut(SourceOut):
    item_count: int
    problem: ProblemOut | None


class BacklogOut(BaseModel):
    sources: list[SourceStatusOut]
    items: list[ItemOut]


class ItemFieldsIn(BaseModel):
    """Fields to change; only the ones sent are changed. null clears optional fields (summary, parent)."""

    model_config = ConfigDict(extra="forbid")  # a misspelled field must not be ignored silently

    title: str | None = None
    status: str | None = None
    priority: str | None = None
    required_for_parent: str | None = Field(default=None, description="Yes or No")
    goal: str | None = None
    completion_criteria: str | None = None
    summary: str | None = None
    area: str | None = None
    parent: str | None = None
    dependencies: list[str] | None = None

    @model_validator(mode="after")
    def _not_empty(self) -> ItemFieldsIn:
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self

    def changes(self) -> dict[str, object]:
        """The fields sent, in declaration order so the file is written deterministically."""
        return {name: getattr(self, name) for name in type(self).model_fields if name in self.model_fields_set}


class ItemCreateIn(BaseModel):
    """A new item; the id is assigned by the server, the status is always Open."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    type: str = Field(description="Epic, Story or Task")
    title: str
    area: str
    goal: str
    completion_criteria: str
    priority: str | None = Field(default=None, description="Default: Normal")
    parent: str | None = None
    required_for_parent: str | None = Field(default=None, description="Yes or No; required with a parent")
    dependencies: list[str] = Field(default_factory=list)
    summary: str | None = None
    created: str | None = Field(default=None, description="YYYY-MM-DD; default: today")

    def fields(self) -> dict[str, object]:
        """The item fields sent, in declaration order."""
        return {name: getattr(self, name) for name in type(self).model_fields
                if name not in {"source_id", "type"} and name in self.model_fields_set}


class VersionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str


class ItemRetypeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(description="The item's version as last read; a changed item answers 409")
    type: str = Field(description="The new type: Epic, Story or Task; differs from the current one")


class NoticeOut(BaseModel):
    """Something to know after a successful change; `code` is stable (translate it), `message` is English."""

    code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)


class RetypeOut(BaseModel):
    item: ItemOut = Field(description="The item under its new id")
    old_id: str
    notices: list[NoticeOut] = Field(description="E.g. external_references_may_remain: check docs outside the backlog")

    @classmethod
    def of(cls, source: Source, result: RetypeResult) -> RetypeOut:
        return cls(item=ItemOut.of(source, result.item, result.archive_supported), old_id=result.old_id,
                   notices=[NoticeOut(code=n.code, message=n.message, details=n.details) for n in result.notices])


class ItemEditIn(BaseModel):
    version: str = Field(description="The item's version as last read; a changed item answers 409")
    fields: ItemFieldsIn
    resolution: str | None = Field(default=None, description="Required when status becomes Completed/Rejected")


class SourceIn(BaseModel):
    path: str = Field("", description="Markdown projects: backlog folder with TODO.md; unused for database ones")
    project: str | None = Field(None, description="Name; suggested from the folder if empty (markdown only)")
    backend: Literal["markdown", "database"] | None = Field(
        None, description="Where the project is stored; on create default markdown. On update another value moves "
                          "the project there (path and sync_path are then ignored): only when both sides are in "
                          "sync, else 409 sync_required")
    sync_path: str | None = Field(None, description="Database projects: folder to sync markdown files with")
    mirror: Literal["none", "markdown", "database"] | None = Field(
        None, description="The other side to keep as a mirror: database for a markdown project, markdown (needs "
                          "sync_path) for a database one, none to switch it off; unset leaves it as it is. Switching "
                          "the database mirror of a markdown project off deletes the copy in the database; switching "
                          "the markdown mirror of a database project off keeps its sync_path (send it again), so "
                          "switching it on needs no new folder. Not read when the backend changes")
    auto_sync: bool | None = Field(
        None, description="The owner's switch for the automatic sync of this project (default off): the viewer then "
                          "syncs it by itself, carrying only conflict-free changes and never deleting. Needs a mirror "
                          "(400 auto_sync_needs_mirror); unset leaves it as it is")


class BacklogCreateIn(BaseModel):
    path: str
    project: str | None = None
    language: Literal["en", "de"] = Field("en", description="Language of the headings and prose in the new files")


class ResolutionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["item", "document", "topic", "note", "note_document"]
    label: str = Field(description="The item's, topic's or note's label (for a document: that of its item or note)")
    name: str | None = Field(None, description="Documents and note documents: the document name; others: null")
    choice: Literal["database", "markdown", "defer"] = Field(
        description="database / markdown: the state of that side counts (a deletion on the other side is carried "
                    "out, a missing entry is restored there); defer: leave the conflict as it is")


class SyncIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["to_md", "from_md"] | None = Field(
        None, description="Restricts which side a run may write: to_md only the markdown folder, from_md only the "
                          "database side. Default: both sides, each entry travels from the side that changed it")
    confirm: bool = Field(False, description="false: only preview; true: carry out the sync")
    token: str | None = Field(None, description="The token of the preview being confirmed (required with confirm)")
    resolutions: list[ResolutionIn] = Field(
        default_factory=list, description="One decision per conflict; a conflict without one is deferred")
    language: Literal["en", "de"] = Field("en", description="Language of the headings in markdown files created")


class SyncEntryOut(BaseModel):
    label: str = Field(description="The item's id")
    title: str
    name: str | None = Field(description="Documents: the document name; items: null")
    origin: Literal["database", "markdown"] | None = Field(
        description="The side whose version is carried over to the other; null for conflicts and deferred entries")

    @classmethod
    def of(cls, entry: SyncEntry) -> SyncEntryOut:
        return cls(label=entry.label, title=entry.title, name=entry.name,
                   origin=entry.origin.value if entry.origin else None)


class SyncSectionOut(BaseModel):
    created: list[SyncEntryOut] = Field(description="New on one side (`origin`); carried to the other")
    changed: list[SyncEntryOut] = Field(description="Changed on one side only (`origin`); carried to the other")
    unchanged: int


class FieldOut(BaseModel):
    name: str
    value: str


class SideViewOut(BaseModel):
    fields: list[FieldOut] | None = Field(description="Items: every stored field as text; documents: null")
    text: str | None = Field(description="Documents: the whole text; items: null")

    @classmethod
    def of(cls, view: SideView | None) -> SideViewOut | None:
        if view is None:
            return None
        return cls(fields=None if view.fields is None else [FieldOut(name=n, value=v) for n, v in view.fields],
                   text=view.text)


class SyncConflictOut(BaseModel):
    kind: Literal["item", "document", "topic", "note", "note_document"]
    label: str
    title: str
    name: str | None = Field(description="Documents: the document name; items: null")
    reason: Literal["both_changed", "both_new", "database_deleted", "markdown_deleted"] = Field(
        description="both_changed: changed on both sides since the last sync; both_new: on both sides with "
                    "different content and never synced; database_deleted / markdown_deleted: gone from that side "
                    "since the last sync")
    database: SideViewOut | None = Field(description="The database version; null if the entry is missing there")
    markdown: SideViewOut | None = Field(description="The markdown version; null if the entry is missing there")

    @classmethod
    def of(cls, conflict: SyncConflict) -> SyncConflictOut:
        entry = conflict.entry
        return cls(kind=entry.kind, label=entry.label, title=entry.title, name=entry.name,  # type: ignore[arg-type]
                   reason=conflict.reason.value,  # type: ignore[arg-type]
                   database=SideViewOut.of(conflict.database), markdown=SideViewOut.of(conflict.markdown))


class SyncOut(BaseModel):
    executed: bool = Field(description="false for a preview")
    token: str = Field(description="Identifies the state of both sides; send it back to confirm this preview")
    items: SyncSectionOut
    documents: SyncSectionOut
    topics: SyncSectionOut = Field(description="Topics of the notes (STORY-047), compared like items")
    notes: SyncSectionOut = Field(description="Notes: the files of the notes folder; a note written there without a "
                                              "label (`new-<name>.md`) is `created` and gets its label on import")
    note_documents: SyncSectionOut = Field(description="Notes and specs of notes")
    conflicts: list[SyncConflictOut] = Field(
        description="Entries that need a decision (`resolutions`); until then nothing of them is touched")
    skipped: list[SyncEntryOut] = Field(description="Documents the sync cannot carry (a path, not readable, missing)")
    resolved: list[SyncEntryOut] = Field(description="Carried over by this run (`origin`: from which side)")
    deleted: list[SyncEntryOut] = Field(description="Removed by a decision")
    deferred: list[SyncEntryOut] = Field(description="Conflicts left as they were")
    kept: list[SyncEntryOut] = Field(description="Deferred deletions: the entry stays where it is")

    @classmethod
    def of(cls, preview: SyncPreview, result: SyncResult | None = None) -> SyncOut:
        def out(entries: tuple[SyncEntry, ...]) -> list[SyncEntryOut]:
            return [SyncEntryOut.of(e) for e in entries]

        def section(found: SyncSection) -> SyncSectionOut:
            return SyncSectionOut(created=out(found.created), changed=out(found.changed), unchanged=found.unchanged)

        return cls(
            executed=result is not None, token=preview.token,
            items=SyncSectionOut(created=out(preview.created), changed=out(preview.changed),
                                 unchanged=preview.unchanged),
            documents=SyncSectionOut(created=out(preview.created_documents), changed=out(preview.changed_documents),
                                     unchanged=preview.unchanged_documents),
            topics=section(preview.topics), notes=section(preview.notes),
            note_documents=section(preview.note_documents),
            conflicts=[SyncConflictOut.of(c) for c in preview.conflicts], skipped=out(preview.skipped),
            resolved=out(result.resolved) if result else [], deleted=out(result.deleted) if result else [],
            deferred=out(result.deferred) if result else [], kept=out(result.kept) if result else [])


class DocumentOut(DocumentRefOut):
    content: str
    version: str = Field(description="Changes with the content; required to replace a spec")

    @classmethod
    def of_result(cls, result: DocumentResult) -> DocumentOut:
        return cls(name=result.ref.name, kind=result.ref.kind.value, content=result.content, version=result.version)


class DocumentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(description="The whole new text of the document")
    version: str | None = Field(description="Version last read; null to create a new document")
    summary: str | None = Field(default=None, description="Sets the item summary; needed for the first notes")


class NotesEntryIn(BaseModel):
    """One dated notes entry; the date is set by the server."""

    model_config = ConfigDict(extra="forbid")

    topic: str
    discussed: list[str] = Field(default_factory=list)
    decided: list[str] = Field(default_factory=list)
    open: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None, description="Sets the item summary; required if it has none yet")


class FolderEntryOut(BaseModel):
    name: str
    has_todo: bool


class FolderListingOut(BaseModel):
    path: str
    parent: str | None
    has_todo: bool
    dirs: list[FolderEntryOut]
    error: str | None

    @classmethod
    def of(cls, listing: FolderListing) -> FolderListingOut:
        return cls(path=listing.path, parent=listing.parent, has_todo=listing.has_todo,
                   dirs=[FolderEntryOut(name=d.name, has_todo=d.has_todo) for d in listing.dirs],
                   error=listing.error)
