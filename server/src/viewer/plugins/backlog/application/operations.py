"""Ein- und Ausgaben und Operationen des Plugins `backlog` (HTTP + MCP)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.backlog.application.items import IndexEntry, ItemDetail, ItemService
from viewer.plugins.backlog.domain.model import Item, Progress


@dataclass(frozen=True)
class ProgressOut:
    done: int
    total: int


def _progress(progress: Progress | None) -> ProgressOut | None:
    return ProgressOut(progress.done, progress.total) if progress else None


@dataclass(frozen=True)
class ListItems:
    #: Komma-getrennte Projekt-`uid`s; ohne Angabe alle Projekte.
    projects: str | None = None
    #: Komma-getrennte Status; ohne Angabe alle.
    statuses: str | None = None
    #: Komma-getrennte Prioritäten; ohne Angabe alle.
    priorities: str | None = None
    query: str = ""


@dataclass(frozen=True)
class IndexItem:
    uid: str
    project_uid: str
    label: str
    type: str
    title: str
    status: str
    priority: str
    area: str | None
    parent_uid: str | None
    required_for_parent: bool | None
    progress: ProgressOut | None
    version: int


@dataclass(frozen=True)
class GetItem:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class ItemSummary:
    uid: str
    label: str
    type: str
    title: str
    status: str
    required_for_parent: bool | None
    deleted: bool


@dataclass(frozen=True)
class ItemOut:
    uid: str
    project_uid: str
    label: str
    type: str
    title: str
    status: str
    priority: str
    area: str | None
    parent: ItemSummary | None
    required_for_parent: bool | None
    goal: str | None
    completion_criteria: str | None
    summary: str | None
    resolution: str | None
    created: date
    children: list[ItemSummary]
    dependencies: list[ItemSummary]
    progress: ProgressOut | None
    version: int
    deleted: bool


class BacklogServices:
    """Die Dienste des Plugins; `repository` ist auch für Tests und für andere Teile des Backlogs offen."""

    def __init__(self, items: ItemService, repository: Any) -> None:
        self.items = items
        self.repository = repository


def _split(value: str | None) -> list[str]:
    return [part for part in (value or "").split(",") if part]


def summary(item: Item) -> ItemSummary:
    return ItemSummary(
        item.uid, item.label, item.type, item.title, item.status, item.required_for_parent, item.deleted_at is not None
    )


def index_item(entry: IndexEntry) -> IndexItem:
    i = entry.item
    return IndexItem(
        i.uid,
        i.project_uid,
        i.label,
        i.type,
        i.title,
        i.status,
        i.priority,
        i.area,
        i.parent_uid,
        i.required_for_parent,
        _progress(entry.progress),
        i.revision,
    )


def item_out(detail: ItemDetail) -> ItemOut:
    i = detail.item
    return ItemOut(
        i.uid,
        i.project_uid,
        i.label,
        i.type,
        i.title,
        i.status,
        i.priority,
        i.area,
        summary(detail.parent) if detail.parent else None,
        i.required_for_parent,
        i.goal,
        i.completion_criteria,
        i.summary,
        i.resolution,
        i.created,
        [summary(child) for child in detail.children],
        [summary(dependency) for dependency in detail.dependencies],
        _progress(detail.progress),
        i.revision,
        i.deleted_at is not None,
    )


def _list(services: BacklogServices, data: ListItems) -> list[IndexItem]:
    projects = _split(data.projects) if data.projects is not None else None
    entries = services.items.list_items(projects, _split(data.statuses), _split(data.priorities), data.query)
    return [index_item(entry) for entry in entries]


OPERATIONS: tuple[Operation, ...] = (
    Operation(
        "list_items",
        "Items der Projekte als flache Liste mit Fortschritt; Filter nach Status, Priorität und Text "
        "(Projekte, Status und Prioritäten komma-getrennt)",
        "read",
        ListItems,
        list[IndexItem],
        _list,
        HttpBinding("GET", "/items"),
    ),
    Operation(
        "get_item",
        "Ein Item mit allen Feldern, Kindern (auch gelöschten) und Abhängigkeiten; `ref` ist die uid oder ein Label "
        "(mit `project`)",
        "read",
        GetItem,
        ItemOut,
        lambda s, d: item_out(s.items.get_item(d.ref, d.project)),
        HttpBinding("GET", "/items/{ref}"),
    ),
)
