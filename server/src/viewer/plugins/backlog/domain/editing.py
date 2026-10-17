"""Felder eines Items prüfen und anwenden (Anlegen und Ändern), ohne Speicher."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import date

from viewer.core.domain.errors import DomainError, InvalidInput
from viewer.plugins.backlog.domain.model import FINAL_STATUSES, PRIORITIES, STATUSES, TYPES, Item

#: Felder, die `update_item` ändern darf.
EDITABLE = frozenset(
    {
        "title",
        "status",
        "priority",
        "required_for_parent",
        "goal",
        "completion_criteria",
        "summary",
        "area",
        "parent",
        "dependencies",
    }
)
#: Texte, die nicht leer werden dürfen.
REQUIRED_TEXT = frozenset({"title", "goal", "completion_criteria", "area"})
#: Felder, die ein neues Item setzen darf (Status ist immer `Open`, das Label vergibt der Server).
CREATABLE = EDITABLE - {"status"} | {"created"}
DEFAULT_PRIORITY = "Normal"
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class NotEditable(DomainError):
    code = "not_editable"


class ValueRequired(DomainError):
    code = "value_required"


class ResolutionRequired(DomainError):
    code = "resolution_required"


def _line(value: object) -> str:
    """Getrimmt und zu einer logischen Zeile zusammengefasst (so speichert das Dateiformat Texte)."""
    return " ".join(str(value).split()) if value is not None else ""


def _text(field: str, raw: object, *, required: bool) -> str | None:
    value = _line(raw)
    if value:
        return value
    if required:
        raise ValueRequired(f"Das Feld '{field}' darf nicht leer sein", details={"field": field})
    return None


def _uid(field: str, raw: object) -> str:
    value = str(raw).strip()
    if not value:
        raise InvalidInput(f"Ungültiger Wert für '{field}'", details={"field": field})
    return value


def normalize(field: str, raw: object) -> object:
    """Prüft einen Wert und bringt ihn in die gespeicherte Form (`None`: kein Wert)."""
    if field == "parent":
        return None if raw is None or raw == "" else _uid(field, raw)
    if field == "dependencies":
        if not isinstance(raw, list | tuple):
            raise InvalidInput("Abhängigkeiten sind eine Liste", details={"field": field})
        return tuple(dict.fromkeys(_uid(field, value) for value in raw))
    if field == "required_for_parent":
        if raw is not None and not isinstance(raw, bool):
            raise InvalidInput("'Pflicht für Parent' ist ja oder nein", details={"field": field})
        return raw
    if field == "priority":
        value = _text(field, raw, required=True)
        if value not in PRIORITIES:
            raise InvalidInput(f"Unbekannte Priorität '{value}'", details={"field": field, "allowed": list(PRIORITIES)})
        return value
    if field == "status":
        value = _text(field, raw, required=True)
        if value not in STATUSES:
            raise InvalidInput(f"Unbekannter Status '{value}'", details={"field": field, "allowed": list(STATUSES)})
        return value
    value = _text(field, raw, required=field in REQUIRED_TEXT)
    if field == "title" and value is not None and "**" in value:
        raise InvalidInput("Der Titel darf kein '**' enthalten", details={"field": field})
    return value


def apply_update(item: Item, changes: Mapping[str, object], resolution: str | None) -> Item:
    """Das Item nach der Änderung. Wirft bei unbekannten Feldern, leeren Pflichttexten und fehlender Entscheidung."""
    if not changes:
        raise NotEditable("Keine Änderung angegeben", details={"field": "(none)"})
    for field in changes:
        if field not in EDITABLE:
            raise NotEditable(f"Das Feld '{field}' lässt sich nicht ändern", details={"field": field})
    values: dict[str, object] = {}
    for field, raw in changes.items():
        if field == "status":
            continue  # zuletzt: es hängt an der Entscheidung
        value = normalize(field, raw)
        if field == "parent":
            values["parent_uid"] = value
            if value is None:
                values["required_for_parent"] = None
        elif field == "area":
            values["area"] = value
        else:
            values[field] = value
    if "status" in changes:
        status = str(normalize("status", changes["status"]))
        values["status"] = status
        if status in FINAL_STATUSES:
            if not (resolution or "").strip():
                raise ResolutionRequired(
                    "Für Completed und Rejected braucht es eine Entscheidung", details={"field": "resolution"}
                )
            values["resolution"] = _line(resolution)
        else:
            values["resolution"] = None
    return replace(item, **values)  # type: ignore[arg-type]


def build_new_item(
    uid: str,
    label: str,
    project_uid: str,
    type_: str,
    fields: Mapping[str, object],
    today: date,
    position: int,
    revision: int,
) -> Item:
    """Ein neues Item (Status `Open`) aus den Angaben; Titel, Bereich, Ziel und Kriterien sind Pflicht."""
    if type_ not in TYPES:
        raise InvalidInput(f"Unbekannter Typ '{type_}'", details={"field": "type", "allowed": list(TYPES)})
    for field in fields:
        if field not in CREATABLE:
            raise NotEditable(f"Das Feld '{field}' lässt sich beim Anlegen nicht setzen", details={"field": field})
    values = {field: normalize(field, raw) for field, raw in fields.items() if field != "created"}
    for field in ("title", "area", "goal", "completion_criteria"):
        values[field] = normalize(field, fields.get(field))
    created_text = str(fields.get("created") or today.isoformat()).strip()
    if not _DATE.match(created_text):
        raise InvalidInput("Das Datum muss JJJJ-MM-TT sein", details={"field": "created"})
    required = values.get("required_for_parent")
    return Item(
        uid=uid,
        project_uid=project_uid,
        label=label,
        type=type_,
        title=str(values["title"]),
        status="Open",
        priority=str(values.get("priority") or DEFAULT_PRIORITY),
        area=str(values["area"]),
        parent_uid=values.get("parent"),  # type: ignore[arg-type]
        required_for_parent=required if isinstance(required, bool) else None,
        goal=str(values["goal"]),
        completion_criteria=str(values["completion_criteria"]),
        summary=values.get("summary"),  # type: ignore[arg-type]
        resolution=None,
        created=date.fromisoformat(created_text),
        position=position,
        revision=revision,
        dependencies=tuple(values.get("dependencies") or ()),  # type: ignore[arg-type]
    )


_TEXT_FIELDS = ("title", "summary", "goal", "completion_criteria", "resolution")


def rewrite_labels(text: str, old: str, new: str) -> str:
    """Ersetzt `old`, wo es als eigene ID steht. Längere IDs, die nur damit beginnen (STORY-0081), bleiben."""
    pattern = rf"(?<![A-Za-z0-9_-]){re.escape(old)}(?![A-Za-z0-9-])(?!\.[A-Za-z0-9])(?!_(?!notes|spec))"
    return re.sub(pattern, new, text)


def rewrite_references(items: Sequence[Item], old: str, new: str) -> dict[str, dict[str, str]]:
    """Je Item `uid` → geänderte Textfelder, in denen `old` vorkommt (für einen Typwechsel)."""
    changed: dict[str, dict[str, str]] = {}
    for item in items:
        for field in _TEXT_FIELDS:
            text = getattr(item, field)
            if text and (rewritten := rewrite_labels(text, old, new)) != text:
                changed.setdefault(item.uid, {})[field] = rewritten
    return changed
