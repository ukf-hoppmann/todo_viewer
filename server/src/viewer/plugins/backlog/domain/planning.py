"""Geplante neue Items vor dem Anlegen prüfen, ohne Speicher (`TASK-074`).

Dieselben Regeln wie beim Anlegen (`build_new_item`, `LifecycleRules`); hier werden nur alle Verletzungen gesammelt
und den Einträgen des Plans zugeordnet. Die geplanten Items bekommen Platzhalter-Uids; Beziehungen untereinander
laufen über den `key` der Einträge, Verweise auf vorhandene Items stehen als `uid` in `fields`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from viewer.core.domain.errors import DomainError
from viewer.plugins.backlog.domain.editing import build_new_item
from viewer.plugins.backlog.domain.lifecycle import LifecycleRules
from viewer.plugins.backlog.domain.model import Item

#: Regeln, bei denen ein Plan-Eintrag über Beziehungen beteiligt ist, nicht nur als Verursacher.
CYCLE_CODES = frozenset({"dependency_cycle", "parent_cycle"})


@dataclass(frozen=True)
class PlannedItem:
    """Ein geplantes Item. `key` ist im Plan eindeutig; `fields` wie bei `create_item` (ein vorhandener Parent und
    vorhandene Abhängigkeiten als `uid` unter `parent` und `dependencies`); `parent_key` und `depends_keys` nennen
    andere Einträge des Plans."""

    key: str
    type: str
    fields: Mapping[str, Any]
    parent_key: str | None = None
    depends_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanProblem:
    """Ein Problem eines Eintrags (`key`) oder des ganzen Plans (`key` ist `None`); `code` ist stabil."""

    key: str | None
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


def placeholder_uid(key: str) -> str:
    return f"planned:{key}"


def check_planned(
    before: Sequence[Item], project_uid: str, planned: Sequence[PlannedItem], today: date
) -> list[PlanProblem]:
    """Die Probleme des Plans gegen die vorhandenen Items `before` des Projekts; leer, wenn er sich anlegen ließe."""
    problems: list[PlanProblem] = []
    built: list[Item] = []
    failed: set[str] = set()
    by_uid: dict[str, str] = {}
    for entry in planned:
        uid = placeholder_uid(entry.key)
        by_uid[uid] = entry.key
        values = dict(entry.fields)
        if entry.parent_key is not None:
            values["parent"] = placeholder_uid(entry.parent_key)
        depends = [*(values.get("dependencies") or ()), *(placeholder_uid(k) for k in entry.depends_keys)]
        if depends:
            values["dependencies"] = depends
        try:
            built.append(
                build_new_item(uid, str(values.get("title") or entry.key), project_uid, entry.type, values, today, 0, 1)
            )
        except DomainError as error:
            failed.add(uid)
            problems.append(PlanProblem(entry.key, error.code, error.message, dict(error.details)))
    for found in LifecycleRules().introduced(before, [*before, *built]):
        involved = [uid for uid in (found.uid, *found.related) if uid in by_uid]
        if found.error.code == "unknown_reference" and all(r in failed or r in by_uid for r in found.related):
            continue  # Folge eines Eintrags, der selbst schon ein Problem meldet
        details = dict(found.error.details)
        for uid in involved:
            problems.append(PlanProblem(by_uid[uid], found.error.code, found.error.message, details))
        if found.error.code in CYCLE_CODES or not involved:
            problems.append(PlanProblem(None, found.error.code, found.error.message, details))
    return problems
