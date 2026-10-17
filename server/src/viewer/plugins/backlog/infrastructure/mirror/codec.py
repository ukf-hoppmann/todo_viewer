"""Der `MirrorCodec` des Plugins `backlog`: Dateien `TODO.md`, `archive.md` und `items/**`."""

from __future__ import annotations

from collections.abc import Sequence

from viewer.core.domain.files import Change, FileSet
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.backlog.infrastructure.mirror.decode import decode
from viewer.plugins.backlog.infrastructure.mirror.encode import encode


class BacklogCodec:
    patterns = ("TODO.md", "archive.md", "items/**/*.md")

    def decode(self, files: FileSet) -> list[MirrorEntry]:
        return decode(files)

    def encode(
        self, upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet
    ) -> Sequence[Change]:
        return encode(upserts, removed, current)
