"""HTTP contract of API v2. Items are addressed by source id + item id, sources by their stable id."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from todo_viewer.application.ports import FolderListing
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source, SourceProblem


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
    notes: list[str]
    spec: list[str]
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
            notes=item.notes,
            spec=item.spec,
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

    @classmethod
    def of(cls, source: Source, item: Item) -> IndexItemOut:
        return cls(source_id=source.id, id=item.id, type=item.item_type, status=item.status, title=item.title,
                   parent=item.parent)


class IndexOut(BaseModel):
    items: list[IndexItemOut]


class SourceOut(BaseModel):
    id: str
    project: str
    path: str

    @classmethod
    def of(cls, source: Source) -> SourceOut:
        return cls(id=source.id, project=source.project, path=source.path)


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


class ItemEditIn(BaseModel):
    version: str = Field(description="The item's version as last read; a changed item answers 409")
    fields: ItemFieldsIn
    resolution: str | None = Field(default=None, description="Required when status becomes Completed/Rejected")


class SourceIn(BaseModel):
    path: str
    project: str | None = None


class DocumentOut(BaseModel):
    path: str
    content: str


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
