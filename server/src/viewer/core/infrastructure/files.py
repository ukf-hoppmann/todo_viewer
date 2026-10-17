"""`FileStore` auf dem lokalen Dateisystem: atomar, Zeilenenden erhalten, Konflikte erkennen.

Angepasst kopiert aus dem Altcode (`text_file.py`, `merge_markers.py`); kein Import von dort.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from pathlib import Path

import structlog

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
    has_merge_markers,
    is_temp_name,
)

log = structlog.get_logger(__name__)

_MESSAGES = {
    "missing": "Der Spiegel-Ordner fehlt",
    "git_operation": "Im Spiegel-Ordner läuft eine Git-Operation",
    "unreadable": "Der Spiegel-Ordner enthält unlesbare Dateien",
    "merge_markers": "Der Spiegel-Ordner enthält Git-Merge-Marker",
}


class LocalFileStore:
    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[str, threading.RLock] = {}

    # --- lesen -------------------------------------------------------------------------------------------

    def list_folders(self, start: Path) -> FolderListing:
        target = Path(start)
        while not target.is_dir() and target != target.parent:  # nächster vorhandener Elternordner
            target = target.parent
        target = target.resolve()
        folders: list[FolderEntry] = []
        error: str | None = None
        try:
            for entry in sorted(target.iterdir(), key=lambda e: e.name.lower()):
                if entry.name.startswith("."):
                    continue
                try:
                    if entry.is_dir():
                        folders.append(FolderEntry(entry.name, (entry / "TODO.md").is_file()))
                except OSError:
                    continue
        except OSError as exc:
            error = str(exc)
            log.warning("folder_unreadable", path=str(target), error=error)
        return FolderListing(
            path=str(target),
            parent=str(target.parent) if target != target.parent else None,
            folders=tuple(folders),
            has_mirror=(target / "TODO.md").is_file(),
            error=error,
        )

    def inspect(self, folder: Path, patterns: Sequence[str] = ("**/*.md",)) -> FolderState:
        return self._scan(Path(folder), patterns)[1]

    def read(self, folder: Path, patterns: Sequence[str]) -> FileSet:
        entries, state = self._scan(Path(folder), patterns)
        if not state.ok:
            raise _blocked(state)
        return FileSet(entries)

    def _scan(self, folder: Path, patterns: Sequence[str]) -> tuple[dict[str, FileEntry], FolderState]:
        if not folder.exists():
            return {}, FolderState("missing")
        if not folder.is_dir():
            return {}, FolderState("unreadable", (".",))
        locks = _git_locks(folder)
        if locks:
            return {}, FolderState("git_operation", locks)
        entries: dict[str, FileEntry] = {}
        unreadable: list[str] = []
        marked: list[str] = []
        for relative in _matching_files(folder, patterns):
            try:
                data = (folder / relative).read_bytes()
                text, newline = decode_text(data)
            except (OSError, UnicodeDecodeError):
                unreadable.append(relative)
                continue
            if has_merge_markers(text):
                marked.append(relative)
            entries[relative] = FileEntry(relative, text, file_version(data), newline)
        if unreadable:
            return {}, FolderState("unreadable", tuple(unreadable))
        if marked:
            return {}, FolderState("merge_markers", tuple(marked))
        return entries, FolderState("ok")

    # --- schreiben ---------------------------------------------------------------------------------------

    def write(
        self,
        folder: Path,
        changes: Sequence[Change],
        expected: Mapping[str, str | None],
        *,
        create_folder: bool = False,
    ) -> dict[str, str | None]:
        folder = Path(folder)
        touched = _touched_paths(changes)
        for path in {*touched, *expected}:
            check_relative_path(path)
        undeclared = sorted(set(touched) - set(expected))
        if undeclared:
            raise ValueError(f"Pfade ohne erwartete Version: {undeclared}")
        with self._hold(folder):
            if not folder.is_dir():
                if folder.exists() or not create_folder:
                    raise _blocked(FolderState("missing" if not folder.exists() else "unreadable"))
                folder.mkdir(parents=True)
            locks = _git_locks(folder)
            if locks:
                raise _blocked(FolderState("git_operation", locks))
            stale = sorted(path for path, version in expected.items() if _version(folder / path) != version)
            if stale:
                raise MirrorConflict(
                    "Dateien haben sich seit dem Lesen geändert: " + ", ".join(stale), details={"paths": stale}
                )
            originals = {path: _read_bytes(folder / path) for path in touched}
            marked = sorted(path for path, data in originals.items() if data is not None and _marked(data))
            if marked:
                raise _blocked(FolderState("merge_markers", tuple(marked)))
            created_dirs: list[Path] = []
            try:
                for change in changes:
                    _apply(folder, change, created_dirs)
            except BaseException:
                _undo(folder, originals, created_dirs)
                raise
            result = {path: _version(folder / path) for path in touched}
        log.info("files_written", folder=str(folder), paths=sorted(touched))
        return result

    @contextmanager
    def _hold(self, folder: Path) -> Iterator[None]:
        with self._guard:
            lock = self._locks.setdefault(str(folder.resolve()), threading.RLock())
        with lock:
            yield


# --- Hilfen -----------------------------------------------------------------------------------------------


def _blocked(state: FolderState) -> MirrorBlocked:
    return MirrorBlocked(
        f"{_MESSAGES[state.status]}: {', '.join(state.files)}" if state.files else _MESSAGES[state.status],
        details={"state": state.status, "files": list(state.files)},
    )


def _matching_files(folder: Path, patterns: Sequence[str]) -> list[str]:
    found: set[str] = set()
    for pattern in patterns:
        for path in folder.glob(pattern):
            relative = path.relative_to(folder)
            if ".git" in relative.parts or is_temp_name(path.name) or not path.is_file():
                continue
            found.add(relative.as_posix())
    return sorted(found)


def _git_dir(folder: Path) -> Path | None:
    for candidate in [folder.resolve(), *folder.resolve().parents]:
        git = candidate / ".git"
        if git.is_dir():
            return git
        if git.is_file():  # Worktree: `gitdir: <pfad>`
            text = git.read_text(encoding="utf-8", errors="replace").strip()
            if text.startswith("gitdir:"):
                target = Path(text.removeprefix("gitdir:").strip())
                return target if target.is_absolute() else (candidate / target).resolve()
            return None
    return None


def _git_locks(folder: Path) -> tuple[str, ...]:
    git = _git_dir(folder)
    if git is None or not git.is_dir():
        return ()
    return tuple(sorted(f".git/{p.name}" for p in git.glob("*.lock")))


def _touched_paths(changes: Sequence[Change]) -> list[str]:
    paths: list[str] = []
    for change in changes:
        for path in (change.path, getattr(change, "new_path", None)):
            if path is not None and path not in paths:
                paths.append(path)
    return paths


def _read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _version(path: Path) -> str | None:
    data = _read_bytes(path)
    return None if data is None else file_version(data)


def _marked(data: bytes) -> bool:
    try:
        return has_merge_markers(decode_text(data)[0])
    except UnicodeDecodeError:
        return False


def _ensure_parent(path: Path, created_dirs: list[Path]) -> None:
    missing: list[Path] = []
    parent = path.parent
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    path.parent.mkdir(parents=True, exist_ok=True)
    created_dirs.extend(reversed(missing))


def _apply(folder: Path, change: Change, created_dirs: list[Path]) -> None:
    target = folder / change.path
    if isinstance(change, WriteFile):
        _ensure_parent(target, created_dirs)
        _atomic_write(target, encode_text(change.text, _read_bytes(target)))
    elif isinstance(change, DeleteFile):
        target.unlink(missing_ok=True)
        _prune_empty(folder, target.parent)
    elif isinstance(change, RenameFile):
        destination = folder / change.new_path
        _ensure_parent(destination, created_dirs)
        os.replace(target, destination)
        _prune_empty(folder, target.parent)


def _prune_empty(folder: Path, directory: Path) -> None:
    """Entfernt einen Unterordner, der durch Löschen oder Umbenennen leer wurde (nie den Spiegel-Ordner selbst)."""
    while directory != folder and folder in directory.parents:
        try:
            directory.rmdir()
        except OSError:
            return
        directory = directory.parent


def _atomic_write(path: Path, data: bytes) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            shutil.copymode(path, tmp)
        else:
            tmp.chmod(0o644)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _undo(folder: Path, originals: Mapping[str, bytes | None], created_dirs: list[Path]) -> None:
    """Stellt alle berührten Dateien auf den Stand vor `write` zurück (best effort)."""
    for path, data in originals.items():
        target = folder / path
        try:
            if data is None:
                target.unlink(missing_ok=True)
            elif _read_bytes(target) != data:
                target.parent.mkdir(parents=True, exist_ok=True)
                _atomic_write(target, data)
        except OSError:
            log.exception("undo_failed", path=path)
    for directory in reversed(created_dirs):
        with suppress(OSError):
            directory.rmdir()
