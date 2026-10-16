"""Release versions (SemVer) of a harness project.

Usage: semver.py status [--project <name>]

`status` prints the version file and version, the last release tag, the
allowed next versions, findings, and the commits under semver.paths since the
last release. With subprojects, --project selects the project (default: root).
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from harness_config import ROOT_PROJECT, ConfigError, project_root
from projects import Project, ProjectSet, load_projects

Version = tuple[int, int, int]

_VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
STEPS = ("unchanged", "patch", "minor", "major")


@dataclass(frozen=True)
class Commit:
    short: str
    when: str
    subject: str


@dataclass(frozen=True)
class Status:
    version_file: PurePosixPath
    version_text: str | None
    version: Version | None
    tag_prefix: str
    last_tag: str | None
    last_version: Version | None
    findings: list[str]
    # None when there is no release tag or no Git repository.
    unreleased: list[Commit] | None


def parse_version(text: str) -> Version | None:
    match = _VERSION.fullmatch(text.strip())
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def format_version(version: Version) -> str:
    return ".".join(str(part) for part in version)


def allowed_next(version: Version) -> list[Version]:
    """The current version and its patch, minor, and major successors, in STEPS order."""
    major, minor, patch = version
    return [version, (major, minor, patch + 1), (major, minor + 1, 0), (major + 1, 0, 0)]


def tag_prefix(project: Project) -> str:
    return "v" if project.name == ROOT_PROJECT else f"{project.name}-v"


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def is_git_repo(root: Path) -> bool:
    return _git(root, "rev-parse", "--is-inside-work-tree") == "true"


def last_release(root: Path, prefix: str) -> tuple[str, Version] | None:
    """The tag with the highest version among tags '<prefix><MAJOR.MINOR.PATCH>'."""
    listing = _git(root, "tag", "--list", f"{prefix}*")
    releases = []
    for tag in (listing or "").splitlines():
        version = parse_version(tag[len(prefix):])
        if version is not None:
            releases.append((version, tag))
    if not releases:
        return None
    version, tag = max(releases)
    return tag, version


def _pathspecs(projects: ProjectSet, project: Project) -> list[str]:
    specs = [str(path) for path in project.config.semver_paths]
    if project.name == ROOT_PROJECT:
        # The root project does not release what belongs to a subproject.
        specs += [f":(exclude){path}" for _, path in projects.registry]
    return specs


def unreleased_commits(projects: ProjectSet, project: Project, tag: str) -> list[Commit]:
    log = _git(
        project.root, "log", "--reverse", "--date=format:%Y-%m-%d", "--format=%h%x1f%ad%x1f%s",
        f"{tag}..HEAD", "--", *_pathspecs(projects, project),
    )
    return [Commit(*line.split("\x1f", 2)) for line in (log or "").splitlines()]


def status(projects: ProjectSet, project: Project) -> Status:
    config, root = project.config, project.root
    findings: list[str] = []
    version_file = config.semver_file
    try:
        version_text: str | None = (root / version_file).read_text(encoding="utf-8").strip()
    except OSError:
        version_text = None
        findings.append(f"{version_file} does not exist")
    version = parse_version(version_text) if version_text is not None else None
    if version_text is not None and version is None:
        findings.append(f"{version_file} does not hold a version MAJOR.MINOR.PATCH (found {version_text!r})")

    prefix = tag_prefix(project)
    release = last_release(root, prefix) if is_git_repo(root) else None
    last_tag, last_version = release if release else (None, None)
    if version is not None and last_version is not None and version not in allowed_next(last_version):
        relation = "lower than" if version < last_version else "more than one step above"
        allowed = ", ".join(format_version(v) for v in allowed_next(last_version))
        findings.append(
            f"version {format_version(version)} is {relation} the last release {last_tag}; allowed: {allowed}"
        )

    if version is not None:
        wanted = format_version(version)
        for path in config.semver_sync:
            try:
                text = (root / path).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                findings.append(f"sync file {path} does not exist or is unreadable")
                continue
            if wanted not in text:
                findings.append(f"sync file {path} does not contain {wanted}")

    unreleased = unreleased_commits(projects, project, last_tag) if last_tag else None
    return Status(version_file, version_text, version, prefix, last_tag, last_version, findings, unreleased)


def render(project: Project, result: Status) -> str:
    shown = project.path / result.version_file
    lines = [f"Project: {project.name} ({project.path})"]
    lines.append(f"Version file: {shown} ({result.version_text if result.version_text is not None else 'missing'})")
    if result.last_tag:
        lines.append(f"Last release: {result.last_tag}")
        base = result.last_version
    else:
        lines.append("Last release: none (no release tag yet; any valid version is allowed)")
        base = result.version
    if base is not None:
        options = ", ".join(f"{format_version(v)} ({step})" for v, step in zip(allowed_next(base), STEPS))
        lines.append(f"Allowed versions: {options}")
    lines.append(f"Tag format: {result.tag_prefix}<version>")
    if project.config.semver_sync:
        lines.append(f"Sync files: {', '.join(str(p) for p in project.config.semver_sync)}")
    lines.append("Findings: none" if not result.findings else "Findings:")
    lines += [f"- {finding}" for finding in result.findings]
    if result.unreleased is not None:
        paths = ", ".join(str(p) for p in project.config.semver_paths)
        if result.unreleased:
            lines.append(f"Unreleased commits under {paths} (oldest first):")
            lines += [f"- {c.short} {c.when} {c.subject}" for c in result.unreleased]
        else:
            lines.append(f"No unreleased commits under {paths}.")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    name = None
    if len(argv) == 3 and argv[1] == "--project":
        argv, name = argv[:1], argv[2]
    if argv != ["status"]:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        projects = load_projects(project_root())
    except ConfigError as exc:
        print(f"Invalid configuration: {exc}", file=sys.stderr)
        return 1
    with_semver = [p.name for p in projects.projects if p.config.enabled("semver")] if projects else []
    project = projects.get(name or ROOT_PROJECT) if projects else None
    if project is None or not project.config.enabled("semver"):
        print(
            f"Module 'semver' is not enabled for project {name or ROOT_PROJECT!r} "
            f"(projects with semver: {', '.join(with_semver) or 'none'}).",
            file=sys.stderr,
        )
        return 1
    print(render(project, status(projects, project)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
