"""HTTP contract (Pydantic). Mapping from domain objects lives next to each schema."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from todo_viewer.application.ports import FolderListing
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source


class ItemOut(BaseModel):
    id: str
    title: str
    source_file: str
    project: str
    line: int
    format: str
    type: str
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

    @classmethod
    def of(cls, item: Item) -> ItemOut:
        return cls(
            id=item.id, title=item.title, source_file=item.source_file, project=item.project, line=item.line,
            format=item.format.value, type=item.item_type, status=item.status, parent=item.parent,
            required_for_parent=item.required_for_parent, dependencies=item.dependencies, created=item.created,
            area=item.area, priority=item.priority, goal=item.goal, completion_criteria=item.completion_criteria,
            summary=item.summary, resolution=item.resolution, notes=item.notes, spec=item.spec,
            extra_fields=item.extra_fields,
        )


class ListedItemOut(ItemOut):
    source_index: int
    in_archive: bool
    archive_supported: bool

    @classmethod
    def listed(cls, item: Item, source_index: int, archive_supported: bool) -> ListedItemOut:
        return cls(**ItemOut.of(item).model_dump(), source_index=source_index,
                   in_archive=item.location is Location.ARCHIVE, archive_supported=archive_supported)


class SourceStatusOut(BaseModel):
    index: int
    project: str
    path: str
    count: int
    error: str | None
    code: str | None


class DataOut(BaseModel):
    items: list[ListedItemOut]
    sources: list[SourceStatusOut]


class SourceOut(BaseModel):
    """A configured source; unknown config keys are passed through."""

    model_config = ConfigDict(extra="allow")

    project: str
    path: str

    @classmethod
    def of(cls, source: Source) -> SourceOut:
        return cls(project=source.project, path=source.path, **source.extra)


class ConfigOut(BaseModel):
    sources: list[SourceOut]


class SourceIn(BaseModel):
    path: str | None = None
    project: str | None = None


class SourceResult(BaseModel):
    source: SourceOut


class SourceRemoved(BaseModel):
    removed: SourceOut


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


class DocumentOut(BaseModel):
    path: str
    content: str


class Ok(BaseModel):
    ok: bool = True


class ItemUpdateIn(BaseModel):
    """Legacy edit request addressing the item by file path and line."""

    source_file: str = Field(min_length=1)
    line: StrictInt
    id: str = Field(min_length=1)
    project: str = Field(min_length=1)
    format: str = Field(min_length=1)
    field: str = Field(min_length=1)
    value: str
    resolution: str | None = None


class ItemResult(BaseModel):
    item: ItemOut


UiStateBody = dict[str, Any]
