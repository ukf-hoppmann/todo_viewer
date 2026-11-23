"""Der `MirrorCodec` des Plugins `mindmap`: Dateien `mindmap/**/*.md`."""

from __future__ import annotations

from collections.abc import Sequence

from viewer.core.domain.files import Change, FileSet
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.mindmap.infrastructure.mirror.decode import decode
from viewer.plugins.mindmap.infrastructure.mirror.encode import encode


class MindmapCodec:
    """Der Codec kennt den Namen des Projekts für die Verweise (`for_project`); ohne ihn heißt es `""`."""

    patterns = ("mindmap/**/*.md",)

    def __init__(self, project: str = "") -> None:
        self._project = project

    def for_project(self, name: str) -> MindmapCodec:
        return MindmapCodec(name)

    def decode(self, files: FileSet) -> list[MirrorEntry]:
        return decode(files, self._project)

    def encode(
        self, upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet
    ) -> Sequence[Change]:
        return encode(upserts, removed, current, self._project)
