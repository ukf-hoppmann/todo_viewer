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
# One or more segments separated by '/'; the file is architecture/<name>.md.
_SCOPE_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
READING_HEADER = "required reading"
USES_HEADING = "## Required on use"
# Characters of an identifier; at least one letter.
_IDENTIFIER = re.compile(r"[A-Za-z0-9_$.]*[A-Za-z][A-Za-z0-9_$.]*")
_SEPARATOR_ROW = re.compile(r"\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?")


@dataclass(frozen=True)
class Scope:
    name: str
    patterns: tuple[str, ...]
    # Files relative to the project root that must be read before changing a file of the scope.
    required_reading: tuple[str, ...] = ()


@dataclass(frozen=True)
class Usage:
    """Row of a 'Required on use' table: using one of the identifiers requires reading the files."""
    uses: tuple[str, ...]
    # Files relative to the project root (to the session root once returned by the inherited_* helpers).
    read: tuple[str, ...]


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
    reading_column = _reading_column(rows[0]) if rows else None
    for row in rows[1:]:  # rows[0] is the header
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 2:
            errors.append(f"scope row needs Scope and Paths: {row.strip()}")
            continue
        name, paths = cells[0], cells[1]
        if not _SCOPE_NAME.fullmatch(name):
            errors.append(f"invalid scope name {name!r} (segments of lowercase letters, digits, '-', separated by '/')")
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
        reading: tuple[str, ...] = ()
        if reading_column is not None and reading_column < len(cells):
            reading, reading_errors = _parse_reading(name, cells[reading_column])
            errors += reading_errors
        scopes.append(Scope(name, patterns, reading))
    return scopes, errors


def _reading_column(header: str) -> int | None:
    cells = [cell.strip().lower() for cell in header.strip().strip("|").split("|")]
    return cells.index(READING_HEADER) if READING_HEADER in cells else None


def _parse_reading(scope: str, cell: str) -> tuple[tuple[str, ...], list[str]]:
    """Paths in backticks of a Required reading cell; invalid ones are dropped and reported."""
    if not cell:
        return (), []
    entries = [e.strip() for e in re.findall(r"`([^`]+)`", cell) if e.strip()]
    if not entries:
        return (), [f"scope {scope!r}: required reading must be file paths in backticks: {cell}"]
    valid, invalid = _split_paths(entries)
    errors = [f"scope {scope!r}: required reading must be a file path relative to the project "
              f"root without '..' or patterns: {entry}" for entry in invalid]
    return valid, errors


def _split_paths(entries: list[str]) -> tuple[tuple[str, ...], list[str]]:
    """File paths relative to the project root without '..' or patterns, and the invalid entries."""
    valid: list[str] = []
    invalid: list[str] = []
    for entry in entries:
        parts = PurePosixPath(entry).parts
        if entry.startswith("/") or ".." in parts or re.search(r"[*?\[\]]", entry):
            invalid.append(entry)
        elif entry not in valid:
            valid.append(entry)
    return tuple(valid), invalid


def parse_uses(text: str) -> tuple[list[Usage], list[str]]:
    """Read the table below '## Required on use'. Returns usages and error messages."""
    usages: list[Usage] = []
    errors: list[str] = []
    for row in _table_rows(text, USES_HEADING)[1:]:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 2:
            errors.append(f"required on use row needs Uses and Read: {row.strip()}")
            continue
        names = [n.strip() for n in re.findall(r"`([^`]+)`", cells[0]) if n.strip()]
        files = [f.strip() for f in re.findall(r"`([^`]+)`", cells[1]) if f.strip()]
        if not names:
            errors.append(f"required on use: uses must be identifiers in backticks: {cells[0]}")
        if not files:
            errors.append(f"required on use: read must be file paths in backticks: {cells[1]}")
        uses = tuple(dict.fromkeys(n for n in names if _IDENTIFIER.fullmatch(n)))
        errors += [f"required on use: invalid identifier {n!r} (letters, digits, '_', '$', '.', at least one letter)"
                   for n in names if not _IDENTIFIER.fullmatch(n)]
        read, invalid = _split_paths(files)
        errors += [f"required on use {', '.join(names)}: read must be a file path relative to the project "
                   f"root without '..' or patterns: {entry}" for entry in invalid]
        if uses and read:
            usages.append(Usage(uses, read))
    return usages, errors


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


def _resolve_inherited(
    projects: ProjectSet, project: Project
) -> tuple[list[tuple[Project, str, Scope | None]], list[str]]:
    """Inherited rule files as (defining project, RULES_FILE or scope name, scope), plus errors.

    Entries with errors are skipped; inherited files are not inherited further.
    """
    rules = project.root / rules_path(project.config)
    if not rules.is_file():
        return [], []
    entries, errors = parse_inherited(rules.read_text(encoding="utf-8"))
    resolved: list[tuple[Project, str, Scope | None]] = []
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
        scopes = {scope.name: scope for scope in load_scopes(other.root, other.config)[0]}
        for name in entry.rules:
            if name == RULES_FILE:
                resolved.append((other, name, None))
            elif name not in scopes:
                errors.append(f"project {entry.project!r} has no scope {name!r}")
            elif (other.root / scope_path(other.config, name)).is_file():
                resolved.append((other, name, scopes[name]))
            else:
                errors.append(f"scope file {other.path / scope_path(other.config, name)} is missing")
    return resolved, errors


def inherited_files(projects: ProjectSet, project: Project) -> tuple[list[PurePosixPath], list[str]]:
    """Rule files (relative to the session root) that project inherits, plus errors."""
    resolved, errors = _resolve_inherited(projects, project)
    files: list[PurePosixPath] = []
    for other, name, scope in resolved:
        if scope is None:
            files.append(other.path / rules_path(other.config))
            continue
        files.append(other.path / scope_path(other.config, name))
        for reading in scope.required_reading:
            path = other.path / reading
            files.append(path)
            if not (other.root / reading).is_file():
                errors.append(f"required reading {path} of scope {name!r} is missing")
    return files, errors


def inherited_uses(projects: ProjectSet, project: Project) -> tuple[list[Usage], list[str]]:
    """'Required on use' rows of the inherited rule files, files relative to the session root, plus errors."""
    resolved, _ = _resolve_inherited(projects, project)
    usages: list[Usage] = []
    errors: list[str] = []
    for other, name, scope in resolved:
        path = rules_path(other.config) if scope is None else scope_path(other.config, name)
        found, found_errors = _file_uses(other.root, path, other.path / path)
        usages += [Usage(u.uses, tuple((other.path / r).as_posix() for r in u.read)) for u in found]
        errors += found_errors
    return usages, errors


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
        for reading in scope.required_reading:
            if not (root / reading).is_file():
                errors.append(f"required reading {reading} of scope {scope.name!r} is missing")
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
        # A missing reading file stays required, so the hook can name it.
        if any(match_path(p, rel) for p in scope.patterns):
            required += [PurePosixPath(r) for r in scope.required_reading if PurePosixPath(r) not in required]
    return required


def _file_uses(root: Path, path: PurePosixPath, shown: PurePosixPath) -> tuple[list[Usage], list[str]]:
    """'Required on use' rows of one rules file; errors name the file and include missing read files."""
    file = root / path
    if not file.is_file():
        return [], []
    usages, errors = parse_uses(file.read_text(encoding="utf-8"))
    errors = [f"{shown}: {error}" for error in errors]
    for usage in usages:
        errors += [f"{shown}: required on use {', '.join(usage.uses)}: {r} is missing"
                   for r in usage.read if not (root / r).is_file()]
    return usages, errors


def load_uses(root: Path, config: HarnessConfig, rel: PurePosixPath | None = None) -> tuple[list[Usage], list[str]]:
    """'Required on use' rows of the rules file and of the scopes that match rel, plus errors.

    Without rel, every scope counts (to validate all tables).
    """
    rules = root / rules_path(config)
    if not rules.is_file():
        return [], []
    usages, errors = _file_uses(root, rules_path(config), rules_path(config))
    for scope in parse_scopes(rules.read_text(encoding="utf-8"))[0]:
        if rel is None or any(match_path(p, rel) for p in scope.patterns):
            path = scope_path(config, scope.name)
            found, found_errors = _file_uses(root, path, path)
            usages += found
            errors += found_errors
    return usages, errors


def use_pattern(identifier: str) -> re.Pattern[str]:
    """Identifier as a literal ('.' included) that is not part of a longer name."""
    return re.compile(rf"(?<![A-Za-z0-9_$]){re.escape(identifier)}(?![A-Za-z0-9_$])")


def counted_reads(projects: ProjectSet) -> set[str]:
    """Files (relative to the session root) whose complete Read counts besides rules and scope files.

    Required reading of the scopes and the files of the 'Required on use' tables of every
    project (inherited rules belong to the projects defining them).
    """
    files: set[str] = set()
    for project in projects.projects:
        config = project.config
        if not config.part_enabled("architecture") or not (project.root / rules_path(config)).is_file():
            continue
        for scope in load_scopes(project.root, config)[0]:
            files.update((project.path / r).as_posix() for r in scope.required_reading)
        for usage in load_uses(project.root, config)[0]:
            files.update((project.path / r).as_posix() for r in usage.read)
        files.update(p.as_posix() for p in inherited_files(projects, project)[0])
    return files


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
