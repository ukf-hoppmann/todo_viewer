"""Composition root: the only place that knows which adapter implements which port."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from todo_viewer.application.container import Container
from todo_viewer.application.services import (
    BacklogOverviewService,
    DocumentService,
    FolderBrowseService,
    ItemService,
    SourceLookup,
    SourceService,
    UiStateService,
)
from todo_viewer.domain.editing import EditPlanner
from todo_viewer.infrastructure.config import JsonFile, JsonSourceRepository, JsonUiStateStore, LegacySourceMigrator
from todo_viewer.infrastructure.filesystem import GitProjectNameSuggester, LocalFolderBrowser, browse_start_from
from todo_viewer.infrastructure.markdown import build_markdown_repository
from todo_viewer.infrastructure.markdown.documents import MarkdownDocumentStore
from todo_viewer.infrastructure.markdown.layout import LayoutFactory, SourcePathResolver

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    config_dir: Path
    frontend_dir: Path
    browse_start: str | None

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            base_dir=PROJECT_ROOT,
            config_dir=Path(os.environ.get("CONFIG_DIR", PROJECT_ROOT / "configs")),
            frontend_dir=Path(os.environ.get("FRONTEND_DIR", PROJECT_ROOT / "web" / "dist")),
            browse_start=os.environ.get("BROWSE_START"),
        )


def build_container(settings: Settings) -> Container:
    resolver = SourcePathResolver(settings.base_dir)
    backlogs = build_markdown_repository(settings.base_dir)
    source_repo = JsonSourceRepository(JsonFile(settings.config_dir / "config.json"), LegacySourceMigrator())
    lookup = SourceLookup(source_repo)

    return Container(
        overview=BacklogOverviewService(source_repo, backlogs),
        items=ItemService(backlogs, EditPlanner()),
        sources=SourceService(source_repo, backlogs, GitProjectNameSuggester(resolver)),
        source_lookup=lookup,
        documents=DocumentService(lookup, MarkdownDocumentStore(LayoutFactory(resolver))),
        folders=FolderBrowseService(LocalFolderBrowser(browse_start_from(settings.browse_start), resolver)),
        ui_state=UiStateService(JsonUiStateStore(JsonFile(settings.config_dir / "ui_state.json"))),
    )
