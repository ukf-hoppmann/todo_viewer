from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any

CONFIG_RELATIVE_PATH = PurePosixPath(".claude-harness/config.toml")
README = PurePosixPath("README.md")
# Where Claude Code creates worktrees (EnterWorktree), relative to the project root.
WORKTREES_DIR = PurePosixPath(".claude/worktrees")
CONFIG_VERSION = 1
KNOWN_MODULES = ("todo", "daily", "techdocs", "development", "semver")
DEFAULT_DOCS_ROOT = PurePosixPath("docs")
DEFAULT_LANGUAGE = "en"
DEFAULT_TODO_PATH = PurePosixPath("todo")
# How the AI works on the backlog: through the ToDo-Viewer's HTTP API, or on the files directly.
TODO_BACKENDS = ("api", "files")
DEFAULT_TODO_BACKEND = "api"
# Environment variables that choose the backend per environment without touching the checked-in config.
TODO_BACKEND_ENV = "CLAUDE_HARNESS_TODO_BACKEND"
# Set to "true" by Claude Code in cloud sessions (claude.ai/code), where the ToDo-Viewer is not reachable.
CLOUD_ENV = "CLAUDE_CODE_REMOTE"
# Default address of the ToDo-Viewer container (bound to localhost only); todo.api_url overrides it.
DEFAULT_TODO_API_URL = "http://localhost:5411/api"
# The old viewer served /api/v2; the rebuilt one serves /api/<plugin>/... Old configs are read as the new address.
_OLD_API_SUFFIX = "/api/v2"
DEFAULT_DAILY_PATH = PurePosixPath("daily")
DEFAULT_TECHDOCS_PATH = PurePosixPath("techdocs")
DEFAULT_DEVELOPMENT_PATH = PurePosixPath("development")
DEFAULT_VERSION_FILE = PurePosixPath("VERSION")
# Test folder relative to the project root, next to the source folder.
DEFAULT_TESTS_PATH = PurePosixPath("tests")
# Parts of the development suite; each is on while the suite is on unless set to false.
DEVELOPMENT_PARTS = ("architecture", "decomposition", "worktree", "testing")
TECHDOC_KINDS = ("architecture", "interfaces", "configuration", "operations")
DEFAULT_TECHDOCS = ("architecture", "interfaces", "configuration")

# Allowed keys per table; [modules] allows KNOWN_MODULES.
TABLE_KEYS = {
    "docs": {"root", "language"},
    "todo": {"path", "backend", "api_url"},
    "daily": {"path"},
    "techdocs": {"path", "documents"},
    "development": {"path", "tests", *DEVELOPMENT_PARTS},
    "harness": {"repo"},
    "semver": {"file", "sync", "paths"},
    "cloud": {"export"},
}
_TOP_LEVEL_KEYS = {"version", "modules", "projects", *TABLE_KEYS}
# Tables only the root project may contain: the subproject registry, the harness repo, and the cloud copy
# (one copy per repository, at its root).
_ROOT_ONLY_TABLES = ("projects", "harness", "cloud")
_LANGUAGE_PATTERN = re.compile(r"[a-z]{2}")
_URL_PATTERN = re.compile(r"https?://\S+")
PROJECT_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
ROOT_PROJECT = "root"


class ConfigError(ValueError):
    """Raised when the project configuration violates the config schema."""


class ConfigOutdated(ConfigError):
    """Raised when a config's version is older than CONFIG_VERSION but a migration path to it exists."""

    def __init__(self, current_version: int, target_version: int, steps: tuple[str, ...]):
        self.current_version = current_version
        self.target_version = target_version
        self.steps = steps
        super().__init__(
            f"{CONFIG_RELATIVE_PATH} is version {current_version}, current is {target_version} "
            f"({len(steps)} pending change(s))"
        )


@dataclass(frozen=True)
class Migration:
    """One schema step: from_version -> to_version, with a description and a data transform."""

    from_version: int
    to_version: int
    description: str
    upgrade: Callable[[dict[str, Any]], dict[str, Any]]


# Schema migrations, applied in sequence by version; empty until the schema has a breaking change.
MIGRATIONS: tuple[Migration, ...] = ()


def _migration_chain(version: int) -> tuple[Migration, ...] | None:
    """Migrations from version to CONFIG_VERSION, in order; None when no such path exists."""
    if version >= CONFIG_VERSION:
        return ()
    by_from = {m.from_version: m for m in MIGRATIONS}
    chain: list[Migration] = []
    current = version
    while current < CONFIG_VERSION:
        migration = by_from.get(current)
        if migration is None:
            return None
        chain.append(migration)
        current = migration.to_version
    return tuple(chain)


def migrate_data(data: dict[str, Any]) -> dict[str, Any]:
    """Apply the pending migrations to a raw config dict and return the result at CONFIG_VERSION."""
    version = data.get("version")
    if not isinstance(version, int):
        raise ConfigError(f"version must be an integer, got {version!r}")
    chain = _migration_chain(version)
    if chain is None:
        raise ConfigError(f"no migration path from version {version} to {CONFIG_VERSION}")
    result = dict(data)
    for migration in chain:
        result = migration.upgrade(result)
    result["version"] = CONFIG_VERSION
    return result


@dataclass(frozen=True)
class HarnessConfig:
    modules: dict[str, bool]
    docs_root: PurePosixPath
    language: str
    # Module paths are resolved against docs_root, i.e. relative to the project root.
    todo_path: PurePosixPath
    daily_path: PurePosixPath
    techdocs_path: PurePosixPath
    techdocs: tuple[str, ...]
    development_path: PurePosixPath
    development_parts: dict[str, bool]
    # Test folder, relative to the project root (not to docs_root).
    tests_path: PurePosixPath = DEFAULT_TESTS_PATH
    # Candidate paths of the Claude_Harness repository, one per machine; absolute or starting with '~'.
    harness_repos: tuple[str, ...] = ()
    # Subprojects registered in the root project: (name, path relative to the project root).
    projects: tuple[tuple[str, PurePosixPath], ...] = ()
    # Version file (relative to the project root), mirrored files, and product paths (both relative to the project).
    semver_file: PurePosixPath = DEFAULT_DOCS_ROOT / DEFAULT_VERSION_FILE
    semver_sync: tuple[PurePosixPath, ...] = ()
    semver_paths: tuple[PurePosixPath, ...] = (PurePosixPath("."),)
    todo_backend: str = DEFAULT_TODO_BACKEND
    todo_api_url: str = DEFAULT_TODO_API_URL
    # Why todo_backend differs from the config file ("cloud session; config.toml says api"); empty when it does not.
    todo_backend_note: str = ""
    # The project keeps a copy of the plugin for cloud sessions (see cloud_export.py).
    cloud_export: bool = False

    def enabled(self, module: str) -> bool:
        return self.modules.get(module, False)

    def notes_enabled(self) -> bool:
        """Notes are part of the todo module: in the ToDo-Viewer (api) or as files below the backlog folder (files)."""
        return self.enabled("todo")

    def viewer_notes_enabled(self) -> bool:
        """The ToDo-Viewer's notes and alarms (notes_api.py, alarms_api.py) need the API backend."""
        return self.notes_enabled() and self.todo_backend == "api"

    def part_enabled(self, part: str) -> bool:
        return self.enabled("development") and self.development_parts.get(part, True)

    def is_harness_file(self, rel: PurePosixPath) -> bool:
        """True for README.md, Git and harness files, and every harness document folder."""
        if rel == README or (rel.parts and rel.parts[0] in (".git", CONFIG_RELATIVE_PATH.parts[0])):
            return True
        if rel == self.semver_file:
            return True
        folders = (self.todo_path, self.daily_path, self.techdocs_path, self.development_path)
        return any(rel.is_relative_to(folder) for folder in folders)


def project_root(hook_input: dict[str, Any] | None = None) -> Path:
    """The session root: CLAUDE_PROJECT_DIR, else cwd; inside a Claude Code worktree that worktree.

    CLAUDE_PROJECT_DIR stays the main checkout while a session works in
    <root>/.claude/worktrees/<name>, so the worktree is taken from the hook's cwd
    or from the file the tool works on.
    """
    hook_input = hook_input or {}
    env_root = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_root:
        base = Path(env_root)
    else:
        cwd = Path(hook_input.get("cwd") or Path.cwd())
        base = _enclosing_worktree(cwd) or cwd
    tool_input = hook_input.get("tool_input") or {}
    candidates = [hook_input.get("cwd"), tool_input.get("file_path"), tool_input.get("notebook_path")]
    for candidate in filter(None, candidates):
        worktree = _worktree_of(base, Path(candidate))
        if worktree is not None:
            return worktree
    return base


def _enclosing_worktree(path: Path) -> Path | None:
    """The <root>/.claude/worktrees/<name> folder containing path, if any."""
    parts = path.parts
    marker = WORKTREES_DIR.parts
    for i in range(len(parts) - len(marker)):
        if parts[i:i + len(marker)] == marker:
            return Path(*parts[:i + len(marker) + 1])
    return None


def _worktree_of(base: Path, path: Path) -> Path | None:
    worktrees = base / WORKTREES_DIR
    for root, target in ((worktrees, path), (worktrees.resolve(), path.resolve())):
        try:
            rel = target.relative_to(root)
        except ValueError:
            continue
        if rel.parts:
            return root / rel.parts[0]
    return None


def project_relative(root: Path, file_path: str) -> PurePosixPath | None:
    """Return file_path relative to the project root, or None when it lies outside."""
    target = Path(file_path)
    if not target.is_absolute():
        target = root / target
    try:
        return PurePosixPath(target.resolve().relative_to(root.resolve()).as_posix())
    except ValueError:
        return None


def load_config(root: Path, *, subproject: bool = False) -> HarnessConfig | None:
    """Return the parsed config, or None when the project has no config file."""
    path = root / CONFIG_RELATIVE_PATH
    if not path.is_file():
        return None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{CONFIG_RELATIVE_PATH}: invalid TOML: {exc}") from exc
    config = parse_config(data, subproject=subproject)
    override = _backend_override(os.environ)
    if override is None or override[0] == config.todo_backend:
        return config
    backend, source = override
    return replace(config, todo_backend=backend, todo_backend_note=f"{source}; config.toml says {config.todo_backend}")


def _backend_override(env: Mapping[str, str]) -> tuple[str, str] | None:
    """The backend the environment forces and why, or None when the config decides."""
    value = env.get(TODO_BACKEND_ENV, "")
    if value:
        if value not in TODO_BACKENDS:
            raise ConfigError(f"{TODO_BACKEND_ENV} must be one of {', '.join(TODO_BACKENDS)}, got {value!r}")
        return value, TODO_BACKEND_ENV
    if env.get(CLOUD_ENV) == "true":
        return "files", "cloud session"
    return None


def _api_base(url: str) -> str:
    url = url.rstrip("/")
    return url[: -len("/v2")] if url.endswith(_OLD_API_SUFFIX) else url


def parse_config(data: dict[str, Any], *, subproject: bool = False) -> HarnessConfig:
    errors: list[str] = []

    if subproject:
        errors += [f"[{name}] is only allowed in the root project" for name in _ROOT_ONLY_TABLES if name in data]

    unknown = sorted(set(data) - _TOP_LEVEL_KEYS)
    if unknown:
        errors.append(f"unknown top-level keys: {', '.join(unknown)}")

    version = data.get("version")
    if version != CONFIG_VERSION:
        if isinstance(version, int) and version < CONFIG_VERSION:
            chain = _migration_chain(version)
            if chain is not None:
                raise ConfigOutdated(version, CONFIG_VERSION, tuple(m.description for m in chain))
        errors.append(f"version must be {CONFIG_VERSION}, got {version!r}")

    modules: dict[str, bool] = {}
    raw_modules = data.get("modules", {})
    if not isinstance(raw_modules, dict):
        errors.append("[modules] must be a table")
    else:
        for name, value in raw_modules.items():
            if name == "notes":
                errors.append(
                    "unknown module 'notes': notes are part of todo now (active with todo and "
                    "todo.backend = \"api\"); remove modules.notes"
                )
            elif name not in KNOWN_MODULES:
                errors.append(
                    f"unknown module '{name}' (known: {', '.join(KNOWN_MODULES)})"
                )
            elif not isinstance(value, bool):
                errors.append(f"modules.{name} must be true or false")
            else:
                modules[name] = value

    raw_docs = _table(data, "docs", errors)
    docs_root = _path_value(raw_docs, "root", "docs", DEFAULT_DOCS_ROOT, errors)
    language = raw_docs.get("language", DEFAULT_LANGUAGE)
    if not isinstance(language, str) or not _LANGUAGE_PATTERN.fullmatch(language):
        errors.append(f"docs.language must be a two-letter ISO 639-1 code, got {language!r}")

    raw_todo = _table(data, "todo", errors)
    todo_path = _path_value(raw_todo, "path", "todo", DEFAULT_TODO_PATH, errors)
    todo_backend = raw_todo.get("backend", DEFAULT_TODO_BACKEND)
    if todo_backend not in TODO_BACKENDS:
        errors.append(f"todo.backend must be one of {', '.join(TODO_BACKENDS)}, got {todo_backend!r}")
    todo_api_url = raw_todo.get("api_url", DEFAULT_TODO_API_URL)
    if not isinstance(todo_api_url, str) or not _URL_PATTERN.fullmatch(todo_api_url):
        errors.append(f"todo.api_url must be an http(s) URL, got {todo_api_url!r}")
        todo_api_url = DEFAULT_TODO_API_URL
    daily_path = _path_value(_table(data, "daily", errors), "path", "daily", DEFAULT_DAILY_PATH, errors)
    raw_techdocs = _table(data, "techdocs", errors)
    techdocs_path = _path_value(raw_techdocs, "path", "techdocs", DEFAULT_TECHDOCS_PATH, errors)
    techdocs = _techdoc_kinds(raw_techdocs.get("documents", list(DEFAULT_TECHDOCS)), errors)
    raw_development = _table(data, "development", errors)
    development_path = _path_value(raw_development, "path", "development", DEFAULT_DEVELOPMENT_PATH, errors)
    tests_path = _path_value(raw_development, "tests", "development", DEFAULT_TESTS_PATH, errors)
    development_parts: dict[str, bool] = {}
    for part in DEVELOPMENT_PARTS:
        if part not in raw_development:
            continue
        if isinstance(raw_development[part], bool):
            development_parts[part] = raw_development[part]
        else:
            errors.append(f"development.{part} must be true or false")

    harness_repos = _harness_repos(_table(data, "harness", errors).get("repo", []), errors)
    cloud_export = _table(data, "cloud", errors).get("export", False)
    if not isinstance(cloud_export, bool):
        errors.append("cloud.export must be true or false")
        cloud_export = False
    projects = _projects(data.get("projects", {}), errors)
    raw_semver = _table(data, "semver", errors)
    semver_file = _path_value(raw_semver, "file", "semver", DEFAULT_VERSION_FILE, errors)
    semver_sync = _path_list(raw_semver, "sync", "semver", (), errors)
    semver_paths = _path_list(raw_semver, "paths", "semver", (PurePosixPath("."),), errors)
    if not semver_paths:
        errors.append("semver.paths must not be empty")

    if errors:
        raise ConfigError(
            f"{CONFIG_RELATIVE_PATH}: " + "; ".join(errors)
        )
    return HarnessConfig(
        modules=modules,
        docs_root=docs_root,
        language=language,
        todo_path=docs_root / todo_path,
        daily_path=docs_root / daily_path,
        techdocs_path=docs_root / techdocs_path,
        techdocs=techdocs,
        development_path=docs_root / development_path,
        development_parts=development_parts,
        tests_path=tests_path,
        harness_repos=harness_repos,
        projects=projects,
        semver_file=docs_root / semver_file,
        semver_sync=semver_sync,
        semver_paths=semver_paths,
        todo_backend=todo_backend,
        todo_api_url=_api_base(todo_api_url),
        cloud_export=cloud_export,
    )


def _projects(value: Any, errors: list[str]) -> tuple[tuple[str, PurePosixPath], ...]:
    if not isinstance(value, dict):
        errors.append("[projects] must be a table")
        return ()
    projects: list[tuple[str, PurePosixPath]] = []
    for name, raw_path in value.items():
        if name == ROOT_PROJECT or not PROJECT_NAME.fullmatch(name):
            errors.append(
                f"invalid project name {name!r} (a letter, then letters, digits, '_', '-'; "
                f"'{ROOT_PROJECT}' is reserved)"
            )
            continue
        try:
            path = _relative_path(raw_path)
        except ConfigError as exc:
            errors.append(f"projects.{name} {exc}")
            continue
        if path == PurePosixPath("."):
            errors.append(f"projects.{name} must not be the project root itself")
            continue
        projects.append((name, path))
    for i, (name, path) in enumerate(projects):
        for other, other_path in projects[i + 1:]:
            if path.is_relative_to(other_path) or other_path.is_relative_to(path):
                errors.append(f"projects.{name} and projects.{other} overlap; nested projects are not supported")
    return tuple(projects)


def _harness_repos(value: Any, errors: list[str]) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        errors.append("harness.repo must be a list of non-empty strings")
        return ()
    relative = [v for v in value if not (v.startswith("~") or Path(v).is_absolute())]
    if relative:
        errors.append(f"harness.repo paths must be absolute or start with '~': {', '.join(relative)}")
    return tuple(value)


def _techdoc_kinds(value: Any, errors: list[str]) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        errors.append("techdocs.documents must be a list of strings")
        return DEFAULT_TECHDOCS
    unknown = [v for v in value if v not in TECHDOC_KINDS]
    if unknown:
        errors.append(
            f"unknown techdocs.documents: {', '.join(unknown)} (known: {', '.join(TECHDOC_KINDS)})"
        )
    if len(set(value)) != len(value):
        errors.append("techdocs.documents must not contain duplicates")
    return tuple(value)


def _table(data: dict[str, Any], name: str, errors: list[str]) -> dict[str, Any]:
    raw = data.get(name, {})
    if not isinstance(raw, dict):
        errors.append(f"[{name}] must be a table")
        return {}
    unknown = sorted(set(raw) - TABLE_KEYS[name])
    if unknown:
        errors.append(f"unknown keys in [{name}]: {', '.join(unknown)}")
    return raw


def _path_value(
    table: dict[str, Any], key: str, table_name: str, default: PurePosixPath, errors: list[str]
) -> PurePosixPath:
    if key not in table:
        return default
    try:
        return _relative_path(table[key])
    except ConfigError as exc:
        errors.append(f"{table_name}.{key} {exc}")
        return default


def _path_list(
    table: dict[str, Any], key: str, table_name: str, default: tuple[PurePosixPath, ...], errors: list[str]
) -> tuple[PurePosixPath, ...]:
    if key not in table:
        return default
    value = table[key]
    if not isinstance(value, list):
        errors.append(f"{table_name}.{key} must be a list of paths")
        return default
    paths = []
    for entry in value:
        try:
            paths.append(_relative_path(entry))
        except ConfigError as exc:
            errors.append(f"{table_name}.{key} entry {entry!r} {exc}")
    return tuple(paths)


def _relative_path(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("must be a non-empty string")
    path = PurePosixPath(value.strip())
    if path.is_absolute():
        raise ConfigError("must be a relative path")
    if ".." in path.parts:
        raise ConfigError("must not contain '..'")
    return path
