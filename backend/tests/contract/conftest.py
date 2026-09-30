"""Every storage adapter runs the same contract tests on the same starting data (fixtures/backlog)."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.fakes import InMemoryBacklogRepository, InMemoryDocumentStore
from todo_viewer.application.ports import BacklogRepository, DocumentStore
from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.repository import DatabaseBacklogRepository
from todo_viewer.infrastructure.markdown import KeyedLocks, build_markdown_documents, build_markdown_repository

FIXTURE = Path(__file__).parents[1] / "fixtures" / "backlog"


@dataclass
class Adapter:
    """A backlog repository and document store on one source that holds the fixture backlog."""

    repo: BacklogRepository
    docs: DocumentStore | None
    source: Source


def _markdown(tmp_path: Path) -> Adapter:
    shutil.copytree(FIXTURE, tmp_path / "b")
    locks = KeyedLocks()
    return Adapter(build_markdown_repository(Path("/"), locks), build_markdown_documents(Path("/"), locks),
                   Source(project="P", path=str(tmp_path / "b")))


def _fixture_items() -> list[Item]:
    return build_markdown_repository(Path("/")).load(Source(project="P", path=str(FIXTURE))).items


def _memory() -> Adapter:
    source = Source(project="P", path="memory")
    seed = _fixture_items()
    documents = {(p.parent.name, p.name): p.read_text(encoding="utf-8")
                 for p in sorted((FIXTURE / "items").glob("*/*.md"))}
    return Adapter(InMemoryBacklogRepository(seed), InMemoryDocumentStore(documents), source)


def _database(tmp_path: Path) -> Adapter:
    source = Source(project="P", path="db-project", backend="database")
    repo = DatabaseBacklogRepository(Database(f"sqlite:///{tmp_path / 'todo.db'}"))
    repo.store_all(source, _fixture_items())
    return Adapter(repo, None, source)


@pytest.fixture(params=["markdown", "memory", "database"])
def adapter(request: pytest.FixtureRequest, tmp_path: Path) -> Adapter:
    return {"markdown": lambda: _markdown(tmp_path), "memory": _memory,
            "database": lambda: _database(tmp_path)}[request.param]()


@pytest.fixture
def docs_adapter(adapter: Adapter) -> Adapter:
    if adapter.docs is None:
        pytest.skip("no document store for this adapter yet")
    return adapter
