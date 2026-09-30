"""The routing adapters pick the storage adapter by the source's backend."""
from __future__ import annotations

from typing import Any

import pytest

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.errors import InvalidSourceError
from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.routing import RoutingBacklogRepository, RoutingDocumentStore


class RecordingBacklogs:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[str] = []

    def load(self, source: Source) -> Backlog:
        self.calls.append("load")
        return Backlog(items=[Item(id=self.name, title="t", project=source.project)])

    def initialize(self, source: Source, language: str) -> None:
        self.calls.append("initialize")


class RecordingDocuments:
    def __init__(self, name: str) -> None:
        self.name = name

    def read(self, source: Source, item_id: str, name: str) -> str:
        return f"{self.name}:{item_id}/{name}"


def _adapters(**named: Any) -> dict[str, Any]:
    return dict(named)


def test_backlog_calls_go_to_the_adapter_of_the_sources_backend():
    files, database = RecordingBacklogs("files"), RecordingBacklogs("db")
    routing = RoutingBacklogRepository(_adapters(markdown=files, database=database))

    loaded = routing.load(Source(project="P", path="docs", backend="database"))
    routing.initialize(Source(project="P", path="docs"), "de")

    assert [i.id for i in loaded.items] == ["db"]
    assert database.calls == ["load"]
    assert files.calls == ["initialize"]


def test_document_calls_go_to_the_adapter_of_the_sources_backend():
    routing = RoutingDocumentStore(_adapters(markdown=RecordingDocuments("files"), database=RecordingDocuments("db")))

    assert routing.read(Source(project="P", path="docs"), "T-1", "a.md") == "files:T-1/a.md"
    assert routing.read(Source(project="P", path="", backend="database"), "T-1", "a.md") == "db:T-1/a.md"


def test_unknown_backend_is_reported_with_a_stable_code():
    routing = RoutingBacklogRepository(_adapters(markdown=RecordingBacklogs("files")))

    with pytest.raises(InvalidSourceError) as caught:
        routing.load(Source(project="P", path="docs", backend="ftp"))

    assert caught.value.code == "unknown_backend"
