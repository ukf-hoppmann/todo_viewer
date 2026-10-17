"""Fake des `FileStore`-Ports im Speicher, für Tests des Sync und der Plugins.

Verhält sich wie `LocalFileStore` (das beweist die Contract-Suite unter
`tests/implementation/integration/server/contract/`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from viewer.core.domain.files import (
    Change,
    DeleteFile,
    FileEntry,
    FileSet,
    FolderEntry,
    FolderListing,
    FolderState,
    MirrorBlocked,
    MirrorConflict,
    RenameFile,
    WriteFile,
    check_relative_path,
    decode_text,
    encode_text,
    file_version,
    glob_match,
    has_merge_markers,
    is_temp_name,
)

_MESSAGES = {
    "missing": "Der Spiegel-Ordner fehlt",
    "git_operation": "Im Spiegel-Ordner läuft eine Git-Operation",
    "unreadable": "Der Spiegel-Ordner enthält unlesbare Dateien",
    "merge_markers": "Der Spiegel-Ordner enthält Git-Merge-Marker",
}


class InMemoryFileStore:
    def __init__(self) -> None:
        self.folders: dict[str, dict[str, bytes]] = {}
        self.git_locks: dict[str, list[str]] = {}

    # --- Aufbau für Tests ----------------------------------------------------------------------------------

    def make_folder(self, folder: Path) -> None:
        self.folders.setdefault(str(folder), {})

    def put(self, folder: Path, path: str, data: bytes | str) -> None:
        self.make_folder(folder)
        self.folders[str(folder)][path] = data.encode() if isinstance(data, str) else data

    def add_git_lock(self, folder: Path, name: str = "index.lock") -> None:
        self.git_locks.setdefault(str(folder), []).append(f".git/{name}")

    # --- FileStore -------------------------------------------------------------------------------------------

    def list_folders(self, start: Path) -> FolderListing:
        target = Path(start)
        while str(target) not in self.folders and target != target.parent:  # nächster vorhandener Elternordner
            target = target.parent
        files = self.folders.get(str(target), {})
        names = {path.split("/")[0] for path in files if "/" in path}
        names |= {Path(key).name for key in self.folders if Path(key).parent == target}
        folders = tuple(
            FolderEntry(name, f"{name}/TODO.md" in files or "TODO.md" in self.folders.get(str(target / name), {}))
            for name in sorted(names, key=str.lower)
            if not name.startswith(".")
        )
        return FolderListing(
            path=str(target),
            parent=str(target.parent) if target != target.parent else None,
            folders=folders,
            has_mirror="TODO.md" in files,
        )

    def inspect(self, folder: Path, patterns: Sequence[str] = ("**/*.md",)) -> FolderState:
        return self._scan(folder, patterns)[1]

    def read(self, folder: Path, patterns: Sequence[str]) -> FileSet:
        entries, state = self._scan(folder, patterns)
        if not state.ok:
            raise _blocked(state)
        return FileSet(entries)

    def write(
        self,
        folder: Path,
        changes: Sequence[Change],
        expected: Mapping[str, str | None],
        *,
        create_folder: bool = False,
    ) -> dict[str, str | None]:
        touched: list[str] = []
        for change in changes:
            for path in (change.path, getattr(change, "new_path", None)):
                if path is not None and path not in touched:
                    touched.append(path)
        for path in {*touched, *expected}:
            check_relative_path(path)
        undeclared = sorted(set(touched) - set(expected))
        if undeclared:
            raise ValueError(f"Pfade ohne erwartete Version: {undeclared}")
        key = str(folder)
        if key not in self.folders:
            if not create_folder:
                raise _blocked(FolderState("missing"))
            self.folders[key] = {}
        if self.git_locks.get(key):
            raise _blocked(FolderState("git_operation", tuple(self.git_locks[key])))
        files = self.folders[key]
        stale = sorted(p for p, v in expected.items() if _version(files.get(p)) != v)
        if stale:
            raise MirrorConflict(
                "Dateien haben sich seit dem Lesen geändert: " + ", ".join(stale), details={"paths": stale}
            )
        marked = sorted(p for p in touched if p in files and _marked(files[p]))
        if marked:
            raise _blocked(FolderState("merge_markers", tuple(marked)))
        working = dict(files)
        for change in changes:
            _apply(working, change)
        self.folders[key] = working
        return {p: _version(working.get(p)) for p in touched}

    def _scan(self, folder: Path, patterns: Sequence[str]) -> tuple[dict[str, FileEntry], FolderState]:
        key = str(folder)
        if key not in self.folders:
            return {}, FolderState("missing")
        if self.git_locks.get(key):
            return {}, FolderState("git_operation", tuple(sorted(self.git_locks[key])))
        entries: dict[str, FileEntry] = {}
        unreadable: list[str] = []
        marked: list[str] = []
        for path in sorted(self.folders[key]):
            name = path.rsplit("/", 1)[-1]
            if is_temp_name(name) or not any(glob_match(p, path) for p in patterns):
                continue
            data = self.folders[key][path]
            try:
                text, newline = decode_text(data)
            except UnicodeDecodeError:
                unreadable.append(path)
                continue
            if has_merge_markers(text):
                marked.append(path)
            entries[path] = FileEntry(path, text, file_version(data), newline)
        if unreadable:
            return {}, FolderState("unreadable", tuple(unreadable))
        if marked:
            return {}, FolderState("merge_markers", tuple(marked))
        return entries, FolderState("ok")


def _blocked(state: FolderState) -> MirrorBlocked:
    return MirrorBlocked(
        f"{_MESSAGES[state.status]}: {', '.join(state.files)}" if state.files else _MESSAGES[state.status],
        details={"state": state.status, "files": list(state.files)},
    )


def _version(data: bytes | None) -> str | None:
    return None if data is None else file_version(data)


def _marked(data: bytes) -> bool:
    try:
        return has_merge_markers(decode_text(data)[0])
    except UnicodeDecodeError:
        return False


def _apply(files: dict[str, bytes], change: Change) -> None:
    if isinstance(change, WriteFile):
        _check_parents(files, change.path)
        files[change.path] = encode_text(change.text, files.get(change.path))
    elif isinstance(change, DeleteFile):
        files.pop(change.path, None)
    elif isinstance(change, RenameFile):
        _check_parents(files, change.new_path)
        files[change.new_path] = files.pop(change.path)


def _check_parents(files: dict[str, bytes], path: str) -> None:
    parts = path.split("/")
    for i in range(1, len(parts)):
        if "/".join(parts[:i]) in files:
            raise NotADirectoryError(f"{'/'.join(parts[:i])} ist eine Datei")
