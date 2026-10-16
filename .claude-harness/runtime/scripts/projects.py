"""Harness projects of a session: the root project plus registered subprojects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from harness_config import (
    CONFIG_RELATIVE_PATH,
    ROOT_PROJECT,
    ConfigError,
    HarnessConfig,
    load_config,
    project_relative,
)


@dataclass(frozen=True)
class Project:
    name: str
    # Folder relative to the session root; "." for the root project.
    path: PurePosixPath
    root: Path
    config: HarnessConfig

    def relative(self, file_path: str) -> PurePosixPath | None:
        """file_path relative to this project's root, or None when it lies outside."""
        return project_relative(self.root, file_path)


@dataclass(frozen=True)
class ProjectSet:
    session_root: Path
    # Usable projects, root first.
    projects: tuple[Project, ...]
    # Every registered subproject, including unusable ones.
    registry: tuple[tuple[str, PurePosixPath], ...]
    # (project name, message) for subprojects whose config is missing or invalid.
    errors: tuple[tuple[str, str], ...]

    def has_subprojects(self) -> bool:
        return bool(self.registry)

    def get(self, name: str) -> Project | None:
        return next((p for p in self.projects if p.name == name), None)

    def for_file(self, file_path: str) -> Project | None:
        """The project a file belongs to; None outside the session root or in an unusable subproject."""
        rel = project_relative(self.session_root, file_path)
        if rel is None:
            return None
        for name, path in self.registry:
            if rel.is_relative_to(path):
                return self.get(name)
        return self.get(ROOT_PROJECT)


def load_projects(session_root: Path) -> ProjectSet | None:
    """Load the root project and its subprojects.

    Returns None without a root config and raises ConfigError for an invalid
    one, because then the registry is unknown. A broken subproject only
    disables itself.
    """
    config = load_config(session_root)
    if config is None:
        return None
    projects = [Project(ROOT_PROJECT, PurePosixPath("."), session_root, config)]
    errors: list[tuple[str, str]] = []
    for name, path in config.projects:
        root = session_root / path
        try:
            sub_config = load_config(root, subproject=True)
        except ConfigError as exc:
            errors.append((name, str(exc)))
            continue
        if sub_config is None:
            errors.append((name, f"{path / CONFIG_RELATIVE_PATH} does not exist"))
            continue
        projects.append(Project(name, path, root, sub_config))
    return ProjectSet(session_root, tuple(projects), config.projects, tuple(errors))
