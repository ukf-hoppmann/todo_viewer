from __future__ import annotations

import uuid


class UuidIds:
    def new_uid(self) -> str:
        return str(uuid.uuid4())
