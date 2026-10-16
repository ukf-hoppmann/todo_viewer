"""config.json: sources with their storage backend, and the location of the central database."""
from __future__ import annotations

import json
from pathlib import Path

from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.config import (
    JsonFile,
    JsonSourceRepository,
    LegacySourceMigrator,
    notes_settings,
    storage_url,
)


def _config(tmp_path: Path, data: dict) -> JsonFile:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return JsonFile(path)


def test_sources_keep_their_backend_and_the_config_its_other_keys(tmp_path: Path):
    file = _config(tmp_path, {"storage_url": "sqlite:///x.db", "sources": [
        {"project": "Files", "path": "docs"}, {"project": "Central", "path": "central", "backend": "database"}]})
    repo = JsonSourceRepository(file, LegacySourceMigrator())

    with repo.edit() as sources:
        sources.append(Source(project="New", path="new", backend="database"))

    assert [s.backend for s in repo.all()] == ["markdown", "database", "database"]
    assert file.read() == {"storage_url": "sqlite:///x.db", "sources": [
        {"project": "Files", "path": "docs"}, {"project": "Central", "path": "central", "backend": "database"},
        {"project": "New", "path": "new", "backend": "database"}]}


def test_storage_url_falls_back_to_the_default(tmp_path: Path):
    assert storage_url(JsonFile(tmp_path / "missing.json"), "sqlite:///d.db") == "sqlite:///d.db"
    assert storage_url(_config(tmp_path, {"sources": []}), "sqlite:///d.db") == "sqlite:///d.db"
    assert storage_url(_config(tmp_path, {"storage_url": "sqlite:///x.db"}), "sqlite:///d.db") == "sqlite:///x.db"


def test_notes_options_have_defaults_and_can_be_set(tmp_path: Path):
    assert notes_settings(JsonFile(tmp_path / "missing.json")).max_topic_depth == 3
    assert notes_settings(_config(tmp_path, {"sources": []})).review_days == 30
    custom = notes_settings(_config(tmp_path, {"notes": {"max_topic_depth": 4, "review_days": 14}}))
    assert (custom.max_topic_depth, custom.review_days) == (4, 14)
    broken = notes_settings(_config(tmp_path, {"notes": {"max_topic_depth": 0, "review_days": "x"}}))
    assert (broken.max_topic_depth, broken.review_days) == (3, 30)
