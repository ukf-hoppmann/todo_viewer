"""HTTP contract of API v2. Items are addressed by ItemRef, sources by their stable id."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from todo_viewer.application.ports import FolderListing
from todo_viewer.domain.item import Item, ItemRef, Location
from todo_viewer.domain.source import Source, SourceProblem

LocationName = Literal["active", "archive"]
FormatName = Literal["backlog_v2", "checkbox"]
EditableFieldName = Literal["status", "priority", "required_for_parent"]


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


class ItemRefModel(BaseModel):
    source_id: str
    location: LocationName
    id: str
    line: int

    @classmethod
    def of(cls, source: Source, ref: ItemRef) -> ItemRefModel:
        return cls(source_id=source.id, location=ref.location.value, id=ref.id, line=ref.line)

    def to_domain(self) -> ItemRef:
        return ItemRef(self.id, Location(self.location), self.line)


class ItemOut(BaseModel):
    key: str = Field(description="Unique within the whole response: source/location/id")
    ref: ItemRefModel
    project: str
    format: FormatName
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
            key=f"{source.id}/{item.location.value}/{item.id}",
            ref=ItemRefModel.of(source, item.ref),
            project=source.project,
            format=item.format.value,
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


class ItemEditIn(BaseModel):
    ref: ItemRefModel
    field: EditableFieldName
    value: str
    resolution: str | None = None


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
