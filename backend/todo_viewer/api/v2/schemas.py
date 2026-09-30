"""HTTP contract of API v2. Items are addressed by source id + item id, sources by their stable id."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from todo_viewer.application.ports import FolderListing
from todo_viewer.application.services import DocumentResult, RetypeResult
from todo_viewer.domain.documents import DocumentRef, item_documents
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source, SourceProblem


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


class SourceOut(BaseModel):
    id: str
    project: str
    path: str = Field(description="Markdown projects: backlog folder; database projects: empty")
    backend: Literal["markdown", "database"]
    sync_path: str | None = Field(description="Database projects: folder to sync markdown files with")

    @classmethod
    def of(cls, source: Source) -> SourceOut:
        return cls(id=source.id, project=source.project, path=source.path,
                   backend=source.backend,  # type: ignore[arg-type]
                   sync_path=source.sync_path)


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
        None, description="Where the project is stored; on create default markdown, on update it must not change")
    sync_path: str | None = Field(None, description="Database projects: folder to sync markdown files with")


class BacklogCreateIn(BaseModel):
    path: str
    project: str | None = None
    language: Literal["en", "de"] = Field("en", description="Language of the headings and prose in the new files")


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
