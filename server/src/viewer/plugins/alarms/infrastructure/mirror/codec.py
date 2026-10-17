"""Der `MirrorCodec` des Plugins `alarms`: die Datei `alarms.md`."""

from __future__ import annotations

from collections.abc import Sequence

from viewer.core.domain.files import Change, FileSet
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.alarms.infrastructure.mirror.decode import decode
from viewer.plugins.alarms.infrastructure.mirror.encode import encode


class AlarmsCodec:
    """Der Codec kennt den Namen des Projekts für das Ziel (`for_project`); ohne ihn heißt es `""`."""

    patterns = ("alarms.md",)

    def __init__(self, project: str = "") -> None:
        self._project = project

    def for_project(self, name: str) -> AlarmsCodec:
        return AlarmsCodec(name)

    def decode(self, files: FileSet) -> list[MirrorEntry]:
        return decode(files, self._project)

    def encode(
        self, upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet
    ) -> Sequence[Change]:
        return encode(upserts, removed, current, self._project)
