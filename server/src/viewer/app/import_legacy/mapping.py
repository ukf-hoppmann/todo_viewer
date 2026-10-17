"""Reine Regeln der Übernahme: Prioritäten, Labels, Zusatzfelder, stabile `uid`s."""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping, Sequence

#: Fester Namensraum für erzeugte `uid`s: aus denselben alten Schlüsseln entsteht immer dieselbe `uid`.
NAMESPACE = uuid.UUID("5b0f6a3e-0a46-4c33-9d0b-6e1c9d3f7a21")

#: Neue Werte, die alten englischen (High → Urgent, Medium → Important, Low → Normal) und die alten deutschen
#: (wie `LEGACY_PRIORITIES` des alten Viewers); verglichen wird ohne Rücksicht auf Groß- und Kleinschreibung.
PRIORITY_MAP: Mapping[str, str] = {
    "urgent": "Urgent",
    "important": "Important",
    "normal": "Normal",
    "prospective": "Prospective",
    "high": "Urgent",
    "medium": "Important",
    "low": "Normal",
    "dringend": "Urgent",
    "wichtig": "Important",
    "perspektivisch": "Prospective",
}

_LABEL = re.compile(r"^([A-Z]+)-(\d+)$")

#: Elementtyp der Items nach `item_type` des alten Viewers.
ITEM_KINDS: Mapping[str, str] = {"Epic": "epic", "Story": "story", "Task": "task"}


def stable_uid(*parts: object) -> str:
    return str(uuid.uuid5(NAMESPACE, "|".join(str(part) for part in parts)))


def map_priority(value: str | None) -> str | None:
    """Die neue Priorität; leer heißt `Normal`; `None` heißt „unbekannter Wert“."""
    text = (value or "").strip()
    if not text:
        return "Normal"
    return PRIORITY_MAP.get(text.lower())


def split_label(label: str) -> tuple[str, int] | None:
    match = _LABEL.match(label)
    return (match.group(1), int(match.group(2))) if match else None


def counters(labels: Sequence[str]) -> dict[str, int]:
    """Das höchste vergebene Label je Präfix."""
    highest: dict[str, int] = {}
    for label in labels:
        parsed = split_label(label)
        if parsed is not None:
            highest[parsed[0]] = max(highest.get(parsed[0], 0), parsed[1])
    return highest


def extra_fields_lines(fields: Sequence[tuple[str, str]]) -> list[str]:
    """Die Zeilen des Eintrags „Übernommene Zusatzfelder“: ein Feld je Zeile, Folgezeilen eingerückt."""
    lines = []
    for key, value in fields:
        first, *rest = value.strip().splitlines() or [""]
        lines.append("\n  ".join([f"{key}: {first}".rstrip(), *rest]))
    return lines


def document_kind(label: str, name: str, listed: str | None) -> str:
    """`notes` oder `spec`: nach der Liste der Namen des Items, sonst nach dem Namen (`<LABEL>_notes.md`)."""
    if listed in ("notes", "spec"):
        return listed
    return "notes" if name == f"{label}_notes.md" else "spec"
