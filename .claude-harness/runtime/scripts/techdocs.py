"""Classify edited files for the techdocs module."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from harness_config import README, HarnessConfig
from projects import Project

_TEST_NAME = re.compile(r"^test_|_test\.|\.test\.")


def _is_test(path: PurePosixPath) -> bool:
    return any(part in ("test", "tests") for part in path.parts[:-1]) or bool(
        _TEST_NAME.search(path.name)
    )


def _is_interface_doc(config: HarnessConfig, rel: PurePosixPath) -> bool:
    """Interface docs for the AI (index and tree) are documentation upkeep while the architecture part is on."""
    if not config.part_enabled("architecture"):
        return False
    base = config.development_path
    return rel == base / "interfaces.md" or rel.is_relative_to(base / "interfaces")


def classify(project: Project, file_path: str) -> str | None:
    """Return 'docs', 'project', or None for files of project that do not matter."""
    rel = project.relative(file_path)
    if rel is None:
        return None
    config = project.config
    if rel == README or rel.is_relative_to(config.techdocs_path) or _is_interface_doc(config, rel):
        return "docs"
    if config.is_harness_file(rel) or _is_test(rel):
        return None
    return "project"


def document_paths(config: HarnessConfig) -> list[PurePosixPath]:
    return [README] + [config.techdocs_path / f"{kind}.md" for kind in config.techdocs]
