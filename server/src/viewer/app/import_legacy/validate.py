"""Prüft die alte Datenbank, bevor etwas geschrieben wird: ein Fehler bricht ab und nennt alle Fundstellen."""

from __future__ import annotations

from collections import Counter

from viewer.app.import_legacy.mapping import ITEM_KINDS, map_priority, split_label
from viewer.app.import_legacy.reader import Legacy, LegacyError
from viewer.plugins.backlog.domain.model import STATUSES as ITEM_STATUSES
from viewer.plugins.notes.domain.model import STATUSES as NOTE_STATUSES
from viewer.plugins.notes.domain.model import TRIGGER_MODES

TRIGGER_KINDS = ("time", "event", "topic_due")
LINK_ROLES = ("reference", "origin", "trigger")
LINK_TARGETS = ("item", "topic", "note")


def project_name(row: dict[str, object]) -> str:
    return str(row.get("name") or row["id"])


def validate(legacy: Legacy) -> None:
    problems: list[str] = []
    names = Counter(project_name(p).lower() for p in legacy.projects)
    for project in legacy.projects:
        if project.get("backend") == "markdown":
            problems.append(
                f"Das Projekt '{project_name(project)}' ist noch Markdown-primär: erst im alten Viewer in seine "
                "Datenbank spiegeln"
            )
        if names[project_name(project).lower()] > 1:
            problems.append(f"Der Projektname '{project_name(project)}' kommt mehrfach vor")
    known = {str(p["id"]) for p in legacy.projects}
    labels: Counter[tuple[str, str]] = Counter()
    bad_priority: list[str] = []
    for item in legacy.items:
        where = f"{item['label']}"
        if item["project_id"] not in known:
            problems.append(f"{where}: das Projekt '{item['project_id']}' gibt es nicht")
        if item["item_type"] not in ITEM_KINDS:
            problems.append(f"{where}: unbekannter Typ '{item['item_type']}'")
        if item["status"] not in ITEM_STATUSES:
            problems.append(f"{where}: unbekannter Status '{item['status']}'")
        if map_priority(item["priority"]) is None:
            bad_priority.append(f"{where} ('{item['priority']}')")
        labels[(str(item["project_id"]), str(item["label"]))] += 1
    if bad_priority:
        problems.append("Unbekannte Prioritäten: " + ", ".join(bad_priority))
    for topic in legacy.topics:
        labels[(str(topic["project_id"]), str(topic["label"]))] += 1
        if topic["project_id"] not in known:
            problems.append(f"{topic['label']}: das Projekt '{topic['project_id']}' gibt es nicht")
    for note in legacy.notes:
        labels[(str(note["project_id"]), str(note["label"]))] += 1
        if note["project_id"] not in known:
            problems.append(f"{note['label']}: das Projekt '{note['project_id']}' gibt es nicht")
        if note["status"] not in (*NOTE_STATUSES, "due"):
            problems.append(f"{note['label']}: unbekannter Status '{note['status']}'")
        if note["trigger_mode"] not in TRIGGER_MODES:
            problems.append(f"{note['label']}: unbekannter Auslöser-Modus '{note['trigger_mode']}'")
    for (project_id, label), number in labels.items():
        if number > 1:
            problems.append(f"Das Label {label} kommt im Projekt '{project_id}' mehrfach vor")
        if split_label(label) is None:
            problems.append(f"{label} ist kein Label (PRÄFIX-Nummer)")
    for trigger in legacy.triggers:
        if trigger["kind"] not in TRIGGER_KINDS:
            problems.append(f"Auslöser {trigger['id']}: unbekannte Art '{trigger['kind']}'")
    for link in legacy.links:
        if link["role"] not in LINK_ROLES or link["target_kind"] not in LINK_TARGETS:
            problems.append(f"Verknüpfung {link['id']}: unbekannte Rolle oder Art")
    if problems:
        raise LegacyError("Die Übernahme bricht ab:\n  - " + "\n  - ".join(problems))
