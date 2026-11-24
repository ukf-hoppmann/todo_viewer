"""Der Adapter des Ports `MemoWriter` auf die Dienste des Plugins `memos` (ohne dessen Code zu importieren)."""

from __future__ import annotations

from typing import Any

from viewer.plugins.mindmap.application.ports import CreatedElement


class ServicesMemoWriter:
    """`services` ist das Ergebnis von `build` des Plugins `memos` (`MemosServices`)."""

    def __init__(self, services: Any) -> None:
        self._memos = services.memos

    def create_memo(self, project_uid: str, fields: dict[str, Any]) -> CreatedElement:
        uid = str(self._memos.create(project_uid, fields))
        memo = self._memos.get(uid, None).memo
        return CreatedElement(uid, memo.label, memo.summary)
