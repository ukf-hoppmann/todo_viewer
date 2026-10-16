"""Gemeinsamer Zugriff auf die Ablage hinter einem `FileStore`, damit die Contract-Suite beide Adapter prüft."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from in_memory_files import InMemoryFileStore
from viewer.core.application.ports import FileStore
from viewer.core.infrastructure.files import LocalFileStore


class Harness(Protocol):
    store: FileStore
    folder: Path

    def put(self, path: str, data: bytes | str) -> None: ...
    def get(self, path: str) -> bytes | None: ...
    def names(self) -> set[str]: ...
    def add_git_lock(self) -> None: ...
    def remove_folder(self) -> None: ...


class LocalHarness:
    def __init__(self, root: Path) -> None:
        self.store: FileStore = LocalFileStore()
        self.folder = root / "mirror"
        self.folder.mkdir()

    def put(self, path: str, data: bytes | str) -> None:
        target = self.folder / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.encode() if isinstance(data, str) else data)

    def get(self, path: str) -> bytes | None:
        target = self.folder / path
        return target.read_bytes() if target.is_file() else None

    def names(self) -> set[str]:
        return {p.relative_to(self.folder).as_posix() for p in self.folder.rglob("*") if p.is_file()}

    def add_git_lock(self) -> None:
        (self.folder / ".git").mkdir(exist_ok=True)
        (self.folder / ".git" / "index.lock").write_text("")

    def remove_folder(self) -> None:
        import shutil

        shutil.rmtree(self.folder)


class MemoryHarness:
    def __init__(self, root: Path) -> None:
        self.memory = InMemoryFileStore()
        self.store: FileStore = self.memory
        self.folder = root / "mirror"
        self.memory.make_folder(self.folder)

    def put(self, path: str, data: bytes | str) -> None:
        self.memory.put(self.folder, path, data)

    def get(self, path: str) -> bytes | None:
        return self.memory.folders.get(str(self.folder), {}).get(path)

    def names(self) -> set[str]:
        return set(self.memory.folders.get(str(self.folder), {}))

    def add_git_lock(self) -> None:
        self.memory.add_git_lock(self.folder)

    def remove_folder(self) -> None:
        del self.memory.folders[str(self.folder)]


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
