"""Copy the plugin into a project so that Claude Code cloud sessions can use it.

Usage: cloud_export.py <project folder> [--status | --remove] [--write]
  A cloud session loads the repository but not the plugin. The copy puts what the plugin provides into
  places the cloud does load: skills below .claude/skills (prefix harness-), scripts and templates below
  .claude-harness/runtime, hooks in .claude/settings.json (they run only when CLAUDE_CODE_REMOTE is true).
  Only plugin/ is ever copied. The manifest .claude-harness/runtime/manifest.json records what was written.
  (no option)  preview: what a write would change
  --write      write the changes
  --status     only report the state of the copy: missing, current, or outdated
  --remove     take the copy out again: delete what the manifest lists, restore .claude/settings.json (the
               original text while it is untouched, otherwise only the copy's hooks are removed), delete the
               manifest last. Files edited by hand stay and are listed as "kept".
Output: "plugin: <version>", "copy: <version or none>", one line per change ("create", "update", or
"delete" plus the path; "(edited)" marks a file that is not what the last export wrote), "kept <path>" lines
for a removal, "changes: <n>", the unified diff of every update, and "written: <n>" after --write. --status
prints "status: <state>" instead of the changes.
Exit codes: 0 ok, 1 error (an "error:" line; nothing has been written), 2 usage.
"""

from __future__ import annotations

import copy
import difflib
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

# Where the copy lives inside a project (relative to the project root). A copy is a build product of the
# plugin; the names are fixed so that update and removal find it again.
SKILLS_DIR = PurePosixPath(".claude/skills")
RUNTIME_DIR = PurePosixPath(".claude-harness/runtime")
SETTINGS_FILE = PurePosixPath(".claude/settings.json")
# The manifest lists what an export wrote, so that update and removal know exactly which files are theirs.
MANIFEST_FILE = RUNTIME_DIR / "manifest.json"
MANIFEST_FORMAT = 1
RUNTIME_GITIGNORE = b"__pycache__/\n*.pyc\n"
# Prefix of every exported skill: it avoids clashes with built-in skills such as init.
SKILL_PREFIX = "harness-"
# Skills that stay with the local plugin: init and update manage the copy, worktree has no cloud counterpart.
LOCAL_ONLY_SKILLS = ("init", "update", "worktree")

# A hook command that contains this belongs to the copy; update and removal recognize their own entries by it.
MANAGED_MARK = RUNTIME_DIR.as_posix() + "/scripts/"
# The copy's hooks run only in cloud sessions (CLAUDE_CODE_REMOTE=true); locally the plugin's own hooks apply.
# "||" instead of a trailing "|| true" keeps the exit code of the script, which blocking hooks depend on.
CLOUD_GUARD = '[ "$CLAUDE_CODE_REMOTE" != "true" ] || '

_PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"
_PROJECT_RUNTIME = "${CLAUDE_PROJECT_DIR:-.}/" + RUNTIME_DIR.as_posix()
_FRONT_NAME = re.compile(r"^(name:[ \t]*)(\S+)", re.MULTILINE)
_SKILL_REF = re.compile(r"claude-harness:([a-z][a-z-]*)")


class ExportError(Exception):
    """The copy cannot be made or changed; nothing has been written."""


def rewrite_skill_text(text: str, exported: frozenset[str]) -> str:
    """Turn the text of a plugin skill file into the text of its project copy."""
    text = _prefix_skill_name(text)
    text = _SKILL_REF.sub(lambda m: SKILL_PREFIX + m.group(1) if m.group(1) in exported else m.group(0), text)
    return text.replace(_PLUGIN_ROOT, RUNTIME_DIR.as_posix())


def _prefix_skill_name(text: str) -> str:
    """Prefix the name in the frontmatter, nothing else."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end < 0:
        return text
    front = _FRONT_NAME.sub(lambda m: m.group(1) + SKILL_PREFIX + m.group(2), text[:end], count=1)
    return front + text[end:]


def exported_skill_names(plugin_root: Path) -> list[str]:
    """Names of the plugin skills that are copied, sorted."""
    skills = plugin_root / "skills"
    return sorted(
        path.name
        for path in skills.iterdir()
        if (path / "SKILL.md").is_file() and path.name not in LOCAL_ONLY_SKILLS
    )


def skill_files(plugin_root: Path) -> dict[str, bytes]:
    """Project path (posix, relative to the project root) -> content, for every file of every exported skill."""
    names = exported_skill_names(plugin_root)
    exported = frozenset(names)
    files: dict[str, bytes] = {}
    for name in names:
        base = plugin_root / "skills" / name
        for path in sorted(p for p in base.rglob("*") if p.is_file() and not _is_noise(p.relative_to(base))):
            target = SKILLS_DIR / (SKILL_PREFIX + name) / path.relative_to(base).as_posix()
            data = path.read_bytes()
            if path.suffix == ".md":
                data = rewrite_skill_text(data.decode("utf-8"), exported).encode("utf-8")
            files[target.as_posix()] = data
    return files


def _is_noise(relative: Path) -> bool:
    """Files that are no part of a skill: caches and hidden files such as .DS_Store."""
    return any(part == "__pycache__" or part.startswith(".") for part in relative.parts)


def hook_entries(plugin_hooks: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """The plugin's hook groups (content of hooks.json) as groups for the project's .claude/settings.json."""
    entries: dict[str, list[dict[str, Any]]] = {}
    for event, groups in plugin_hooks["hooks"].items():
        entries[event] = [_project_group(group) for group in groups]
    return entries


def _project_group(group: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(group)
    for hook in result["hooks"]:
        command = hook["command"].replace(_PLUGIN_ROOT, _PROJECT_RUNTIME)
        hook["command"] = CLOUD_GUARD + command
    return result


def parse_settings(text: str) -> dict[str, Any]:
    """The content of .claude/settings.json; an empty file counts as no settings."""
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except ValueError as error:
        raise ExportError(f"{SETTINGS_FILE} is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ExportError(f"{SETTINGS_FILE} does not contain a JSON object")
    return data


def dump_settings(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def merge_hooks(settings: dict[str, Any], entries: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Settings with the copy's hooks in place of any earlier copy; foreign hooks and other keys stay."""
    result = copy.deepcopy(settings)
    hooks = _foreign_hooks(result.get("hooks", {}))
    for event, groups in entries.items():
        hooks.setdefault(event, []).extend(copy.deepcopy(groups))
    result["hooks"] = hooks
    return result


def remove_hooks(settings: dict[str, Any]) -> dict[str, Any]:
    """Settings without the copy's hooks; a hooks key that stays empty is dropped."""
    result = copy.deepcopy(settings)
    if "hooks" not in result:
        return result
    hooks = _foreign_hooks(result["hooks"])
    if hooks:
        result["hooks"] = hooks
    else:
        del result["hooks"]
    return result


def _foreign_hooks(hooks: Any) -> dict[str, list[Any]]:
    """The hooks that do not belong to the copy, in their original order."""
    if not isinstance(hooks, dict):
        raise ExportError(f"hooks in {SETTINGS_FILE} is not an object")
    kept: dict[str, list[Any]] = {}
    for event, groups in hooks.items():
        remaining = [group for group in (_without_managed(g) for g in groups) if group is not None]
        if remaining:
            kept[event] = remaining
    return kept


def _without_managed(group: Any) -> Any:
    """The group without the copy's hooks, or None when nothing else is left in it."""
    if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
        return group
    foreign = [h for h in group["hooks"] if not _is_managed(h)]
    if not foreign:
        return None
    return {**group, "hooks": foreign}


def _is_managed(hook: Any) -> bool:
    return isinstance(hook, dict) and MANAGED_MARK in str(hook.get("command", ""))


@dataclass(frozen=True)
class Change:
    """One file the export would write (create, update) or remove (delete)."""

    path: str  # posix, relative to the project root
    kind: str  # "create", "update", or "delete"
    old: bytes | None
    new: bytes | None
    edited: bool = False  # the file on disk is not what the last export wrote (edited by hand, or not ours)


def plugin_version(plugin_root: Path) -> str:
    return str(json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"])


def runtime_files(plugin_root: Path) -> dict[str, bytes]:
    """Project path -> content for the plugin's scripts and templates."""
    files: dict[str, bytes] = {}
    for folder in ("scripts", "templates"):
        base = plugin_root / folder
        for path in sorted(p for p in base.rglob("*") if p.is_file() and not _is_noise(p.relative_to(base))):
            files[(RUNTIME_DIR / folder / path.relative_to(base).as_posix()).as_posix()] = path.read_bytes()
    # Running the scripts in a cloud session writes bytecode caches; they must never reach a commit.
    files[(RUNTIME_DIR / ".gitignore").as_posix()] = RUNTIME_GITIGNORE
    return files


def read_manifest(project: Path) -> dict[str, Any] | None:
    """The manifest of the last export, or None when the project has no copy."""
    path = project / MANIFEST_FILE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise ExportError(f"{MANIFEST_FILE} is not valid JSON: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        raise ExportError(f"{MANIFEST_FILE} is not a manifest")
    return data


def plan_export(plugin_root: Path, project: Path) -> list[Change]:
    """What an export would change in the project; writes nothing. Raises ExportError on unusable settings."""
    desired = {**skill_files(plugin_root), **runtime_files(plugin_root)}
    previous = read_manifest(project)
    recorded: dict[str, str] = previous["files"] if previous else {}
    changes: list[Change] = []
    for path, content in sorted(desired.items()):
        current = _read(project, path)
        if current is None:
            changes.append(Change(path, "create", None, content))
        elif current != content:
            changes.append(Change(path, "update", current, content, edited=_digest(current) != recorded.get(path)))
    for path in sorted(set(recorded) - set(desired)):
        current = _read(project, path)
        if current is not None:
            changes.append(Change(path, "delete", current, None, edited=_digest(current) != recorded[path]))
    settings_change, settings_state = _settings_plan(plugin_root, project, previous)
    if settings_change:
        changes.append(settings_change)
    manifest = _manifest_bytes(plugin_version(plugin_root), desired, settings_state)
    current_manifest = _read(project, MANIFEST_FILE.as_posix())
    if current_manifest != manifest:
        kind = "create" if current_manifest is None else "update"
        changes.append(Change(MANIFEST_FILE.as_posix(), kind, current_manifest, manifest))
    return changes


def _settings_plan(
    plugin_root: Path, project: Path, previous: dict[str, Any] | None
) -> tuple[Change | None, dict[str, Any]]:
    """The change to .claude/settings.json (None when the hooks are in place) and what the manifest records about it.

    The manifest keeps whether the export created the file, the text it had before the first export, and the hash
    of the text the export left behind. A removal restores the original exactly as long as the file is untouched.
    """
    current_bytes = _read(project, SETTINGS_FILE.as_posix())
    current = parse_settings(current_bytes.decode("utf-8") if current_bytes is not None else "")
    plugin_hooks = json.loads((plugin_root / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    merged = merge_hooks(current, hook_entries(plugin_hooks))
    change = None
    written = current_bytes if current_bytes is not None else b""
    if current_bytes is None or merged != current:
        written = dump_settings(merged).encode("utf-8")
        kind = "create" if current_bytes is None else "update"
        change = Change(SETTINGS_FILE.as_posix(), kind, current_bytes, written)
    if previous:
        created, original = bool(previous["settings_created"]), previous.get("settings_original")
    else:
        created = current_bytes is None
        # An original that already holds the copy's hooks cannot be restored as it was; removal then strips them.
        original = None if current_bytes is None or remove_hooks(current) != current else current_bytes.decode("utf-8")
    # Without a write the recorded hash stays: a file the user merely reformatted is no reason to touch the manifest.
    digest = previous["settings_written"] if previous and change is None else _digest(written)
    return change, {"settings_created": created, "settings_original": original, "settings_written": digest}


def _manifest_bytes(version: str, files: dict[str, bytes], settings_state: dict[str, Any]) -> bytes:
    data = {
        "format": MANIFEST_FORMAT,
        "plugin_version": version,
        **settings_state,
        "files": {path: _digest(content) for path, content in sorted(files.items())},
    }
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _target(project: Path, relative: str) -> Path:
    """The file for a project-relative path; refuses anything that leaves the project."""
    pure = PurePosixPath(relative)
    root = project.resolve()
    if pure.is_absolute() or ".." in pure.parts or not (root / relative).resolve().is_relative_to(root):
        raise ExportError(f"{relative} is outside the project")
    return root / relative


def _read(project: Path, relative: str) -> bytes | None:
    target = _target(project, relative)
    return target.read_bytes() if target.is_file() else None


def apply_changes(project: Path, changes: list[Change]) -> None:
    """Write the changes. Every path is checked before the first file is touched."""
    targets = [(change, _target(project, change.path)) for change in changes]
    for change, target in targets:
        if change.kind == "delete":
            target.unlink(missing_ok=True)
            _prune_empty(project, target)
        elif change.new is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(change.new)


def _prune_empty(project: Path, deleted: Path) -> None:
    """Remove the folders a deleted file leaves empty, up to the folders the project owns anyway."""
    root = project.resolve()
    keep = {root, root / ".claude", root / ".claude-harness", root / SKILLS_DIR}
    parent = deleted.parent
    while parent not in keep and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent


def export_status(plugin_root: Path, project: Path) -> str:
    """"missing" (no copy), "current", or "outdated" (the copy differs from what the plugin would write)."""
    if read_manifest(project) is None:
        return "missing"
    return "outdated" if plan_export(plugin_root, project) else "current"


def copy_problem(project: Path, wanted: bool, plugin_root: Path) -> str | None:
    """A session-start line when the project's copy does not match cloud.export, else None.

    Code that runs from a copy has no plugin to compare with and says nothing.
    """
    if not (plugin_root / "skills").is_dir():
        return None
    try:
        manifest = read_manifest(project)
        if not wanted:
            if manifest is None:
                return None
            return "Cloud copy: present although cloud.export is off. Run /claude-harness:update to remove it, or set cloud.export = true."
        if manifest is None:
            return "Cloud copy: cloud.export is on but the project has no copy. Run /claude-harness:update to create it, then commit it."
        if export_status(plugin_root, project) == "current":
            return None
        return (
            f"Cloud copy: outdated (copy {manifest.get('plugin_version')}, plugin {plugin_version(plugin_root)}). "
            "Run /claude-harness:update, then commit it."
        )
    except ExportError as error:
        return f"Cloud copy: cannot be checked ({error})."


def plan_remove(project: Path) -> tuple[list[Change], list[str]]:
    """What a removal would delete or restore, and the copied files it leaves alone because they were edited.

    The manifest goes last, so an interrupted removal can simply be run again. Writes nothing.
    """
    manifest = read_manifest(project)
    if manifest is None:
        raise ExportError(f"no copy to remove: {MANIFEST_FILE} not found")
    changes: list[Change] = []
    kept: list[str] = []
    for path, recorded in sorted(manifest["files"].items()):
        current = _read(project, path)
        if current is None:
            continue
        if _digest(current) == recorded:
            changes.append(Change(path, "delete", current, None))
        else:
            kept.append(path)
    changes += _cache_removals(project)
    settings_change = _settings_removal(project, manifest)
    if settings_change:
        changes.append(settings_change)
    changes.append(Change(MANIFEST_FILE.as_posix(), "delete", _read(project, MANIFEST_FILE.as_posix()), None))
    return changes, kept


def _cache_removals(project: Path) -> list[Change]:
    """Bytecode caches that running the copied scripts left below the runtime folder; they are no copy and no edit."""
    root = project.resolve()
    runtime = root / RUNTIME_DIR
    if not runtime.is_dir():
        return []
    caches = sorted(p for p in runtime.rglob("*") if p.is_file() and "__pycache__" in p.relative_to(runtime).parts)
    return [Change(p.relative_to(root).as_posix(), "delete", p.read_bytes(), None) for p in caches]


def _settings_removal(project: Path, manifest: dict[str, Any]) -> Change | None:
    """Delete the settings file the export created, restore the original, or strip the copy's hooks from it."""
    path = SETTINGS_FILE.as_posix()
    current_bytes = _read(project, path)
    if current_bytes is None:
        return None
    created, original = bool(manifest.get("settings_created")), manifest.get("settings_original")
    untouched = manifest.get("settings_written") == _digest(current_bytes)
    if untouched and created:
        return Change(path, "delete", current_bytes, None)
    if untouched and original is not None:
        return Change(path, "update", current_bytes, original.encode("utf-8"))
    current = parse_settings(current_bytes.decode("utf-8"))
    stripped = remove_hooks(current)
    if stripped == current:
        return None
    if created and stripped == {}:
        return Change(path, "delete", current_bytes, None, edited=not untouched)
    return Change(path, "update", current_bytes, dump_settings(stripped).encode("utf-8"), edited=not untouched)


def main(argv: list[str]) -> int:
    options = {a for a in argv[1:] if a.startswith("--")}
    folders = [a for a in argv[1:] if not a.startswith("--")]
    if len(folders) != 1 or options - {"--status", "--write", "--remove"} or ("--status" in options and len(options) > 1) or (
        "--remove" in options and "--status" in options
    ):
        print("usage: cloud_export.py <project folder> [--status | --remove] [--write]", file=sys.stderr)
        return 2
    project = Path(folders[0])
    plugin_root = Path(__file__).resolve().parent.parent
    try:
        if not (project / ".claude-harness" / "config.toml").is_file():
            raise ExportError(f"no .claude-harness/config.toml in {project}; run /claude-harness:init first")
        manifest = read_manifest(project)
        print(f"plugin: {plugin_version(plugin_root)}")
        print(f"copy: {manifest['plugin_version'] if manifest else 'none'}")
        if "--status" in options:
            print(f"status: {export_status(plugin_root, project)}")
            return 0
        kept: list[str] = []
        if "--remove" in options:
            changes, kept = plan_remove(project)
        else:
            changes = plan_export(plugin_root, project)
        _print_changes(changes, kept)
        if "--write" in options:
            apply_changes(project, changes)
            print(f"written: {len(changes)}")
    except ExportError as error:
        print(f"error: {error}")
        return 1
    return 0


def _print_changes(changes: list[Change], kept: list[str]) -> None:
    for change in changes:
        print(f"{change.kind} {change.path}" + (" (edited)" if change.edited else ""))
    for path in kept:
        print(f"kept {path} (edited)")
    print(f"changes: {len(changes)}")
    for change in changes:
        if change.kind == "update" and change.old is not None and change.new is not None:
            _print_diff(change.path, change.old, change.new)


def _print_diff(path: str, old: bytes, new: bytes) -> None:
    try:
        before, after = old.decode("utf-8"), new.decode("utf-8")
    except UnicodeDecodeError:
        return
    diff = difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), path, path)
    for line in diff:
        sys.stdout.write(line if line.endswith("\n") else line + "\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
