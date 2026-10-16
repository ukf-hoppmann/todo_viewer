"""Architecture rules of the development suite: scope table, inherited rules, path matching, read state."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from harness_config import PROJECT_NAME, HarnessConfig
from projects import Project, ProjectSet
from state import architecture_read_file

RULES_FILE = "architecture.md"
SCOPES_HEADING = "## Scopes"
INHERITED_HEADING = "## Inherited rules"
_SCOPE_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_SEPARATOR_ROW = re.compile(r"\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?")


@dataclass(frozen=True)
class Scope:
    name: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class Inherited:
    project: str
    # RULES_FILE for the main rules file, otherwise scope names of that project.
    rules: tuple[str, ...]


def rules_path(config: HarnessConfig) -> PurePosixPath:
    return config.development_path / RULES_FILE


def scopes_dir(config: HarnessConfig) -> PurePosixPath:
    return config.development_path / "architecture"


def scope_path(config: HarnessConfig, name: str) -> PurePosixPath:
    return scopes_dir(config) / f"{name}.md"


def parse_scopes(text: str) -> tuple[list[Scope], list[str]]:
    """Read the scope table below '## Scopes'. Returns scopes and error messages."""
    scopes: list[Scope] = []
    errors: list[str] = []
    rows = _table_rows(text, SCOPES_HEADING)
    for row in rows[1:]:  # rows[0] is the header
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 2:
            errors.append(f"scope row needs Scope and Paths: {row.strip()}")
            continue
        name, paths = cells[0], cells[1]
        if not _SCOPE_NAME.fullmatch(name):
            errors.append(f"invalid scope name {name!r} (lowercase letters, digits, '-')")
            continue
        patterns = tuple(p.strip() for p in re.findall(r"`([^`]+)`", paths) if p.strip())
        if not patterns:
            errors.append(f"scope {name!r} has no path patterns in backticks")
            continue
        invalid = [p for p in patterns if p.startswith("/") or ".." in PurePosixPath(p).parts]
        if invalid:
            errors.append(f"scope {name!r}: patterns must be relative without '..': {', '.join(invalid)}")
            continue
        if any(scope.name == name for scope in scopes):
            errors.append(f"scope {name!r} is listed twice")
            continue
        scopes.append(Scope(name, patterns))
    return scopes, errors


def parse_inherited(text: str) -> tuple[list[Inherited], list[str]]:
    """Read the table below '## Inherited rules'. Returns entries and error messages."""
    entries: list[Inherited] = []
    errors: list[str] = []
    for row in _table_rows(text, INHERITED_HEADING)[1:]:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 2:
            errors.append(f"inherited rules row needs Project and Rules: {row.strip()}")
            continue
        project, rules_cell = cells[0], cells[1]
        if not PROJECT_NAME.fullmatch(project):
            errors.append(f"invalid project name {project!r}")
            continue
        rules = tuple(r.strip() for r in re.findall(r"`([^`]+)`", rules_cell) if r.strip())
        if not rules:
            errors.append(f"project {project!r} has no rules in backticks")
            continue
        invalid = [r for r in rules if r != RULES_FILE and not _SCOPE_NAME.fullmatch(r)]
        if invalid:
            errors.append(f"project {project!r}: rules must be {RULES_FILE} or scope names: {', '.join(invalid)}")
            continue
        if any(entry.project == project for entry in entries):
            errors.append(f"project {project!r} is listed twice")
            continue
        entries.append(Inherited(project, rules))
    return entries, errors


def inherited_files(projects: ProjectSet, project: Project) -> tuple[list[PurePosixPath], list[str]]:
    """Rule files (relative to the session root) that project inherits, plus errors.

    Entries with errors are skipped; inherited files are not inherited further.
    """
    rules = project.root / rules_path(project.config)
    if not rules.is_file():
        return [], []
    entries, errors = parse_inherited(rules.read_text(encoding="utf-8"))
    files: list[PurePosixPath] = []
    for entry in entries:
        if entry.project == project.name:
            errors.append(f"project {entry.project!r} cannot inherit from itself")
            continue
        other = projects.get(entry.project)
        if other is None:
            errors.append(f"unknown or unusable project {entry.project!r}")
            continue
        other_rules = rules_path(other.config)
        if not other.config.part_enabled("architecture") or not (other.root / other_rules).is_file():
            errors.append(f"project {entry.project!r} has no active architecture rules")
            continue
        scopes = {scope.name for scope in load_scopes(other.root, other.config)[0]}
        for name in entry.rules:
            if name == RULES_FILE:
                files.append(other.path / other_rules)
            elif name not in scopes:
                errors.append(f"project {entry.project!r} has no scope {name!r}")
            elif (other.root / scope_path(other.config, name)).is_file():
                files.append(other.path / scope_path(other.config, name))
            else:
                errors.append(f"scope file {other.path / scope_path(other.config, name)} is missing")
    return files, errors


def _table_rows(text: str, heading: str) -> list[str]:
    rows: list[str] = []
    in_section = False
    for line in _COMMENT.sub("", text).splitlines():
        if line.startswith("## "):
            in_section = line.strip() == heading
            continue
        if in_section and line.lstrip().startswith("|") and not _SEPARATOR_ROW.fullmatch(line.strip()):
            rows.append(line)
    return rows


def match_path(pattern: str, path: PurePosixPath) -> bool:
    """Glob match: '*' and '?' stay within one path part, '**' spans any number of parts."""
    regex = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            regex += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            regex += ".*"
            i += 2
        elif pattern[i] == "*":
            regex += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            regex += "[^/]"
            i += 1
        else:
            regex += re.escape(pattern[i])
            i += 1
    return re.fullmatch(regex, path.as_posix()) is not None


def load_scopes(root: Path, config: HarnessConfig) -> tuple[list[Scope], list[str]]:
    """Scopes of an existing rules file plus errors, including missing scope files."""
    rules = root / rules_path(config)
    if not rules.is_file():
        return [], []
    scopes, errors = parse_scopes(rules.read_text(encoding="utf-8"))
    for scope in scopes:
        if not (root / scope_path(config, scope.name)).is_file():
            errors.append(f"scope file {scope_path(config, scope.name)} is missing")
    return scopes, errors


def required_files(root: Path, config: HarnessConfig, rel: PurePosixPath) -> list[PurePosixPath]:
    """Rule files that must have been read before changing the project file rel."""
    if not (root / rules_path(config)).is_file():
        return []
    scopes, _ = load_scopes(root, config)
    required = [rules_path(config)]
    for scope in scopes:
        path = scope_path(config, scope.name)
        if (root / path).is_file() and any(match_path(p, rel) for p in scope.patterns):
            required.append(path)
    return required


def read_files(session_id: str) -> set[str]:
    try:
        return set(json.loads(architecture_read_file(session_id).read_text()))
    except (OSError, ValueError):
        return set()


def mark_read(session_id: str, rel: PurePosixPath) -> None:
    done = read_files(session_id) | {rel.as_posix()}
    path = architecture_read_file(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(done)))


def reset_read(session_id: str) -> None:
    architecture_read_file(session_id).unlink(missing_ok=True)
