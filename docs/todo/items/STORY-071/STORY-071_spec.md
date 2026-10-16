# `STORY-071` — Backlog anzeigen

Grundlage: `EPIC-007_spec.md`, Abschnitt 9 (`backlog`).

## Datenmodell (fest)

- `backlog_types(code PK)`: `Epic`, `Story`, `Task`.
- `backlog_statuses(code PK, final BOOL)`: `Open`, `In progress`,
  `Awaiting confirmation`, `Completed`, `Rejected`.
- `backlog_priorities(code PK, rank)`: `Urgent`, `Important`, `Normal`,
  `Prospective`.
- `backlog_areas(uid PK, project_uid, name, UNIQUE(project_uid, name))`.
- `backlog_items(uid PK FK workspace_elements, type FK, title, status FK,
  priority FK, area_uid FK, parent_uid FK NULL, required_for_parent BOOL NULL,
  goal, completion_criteria, summary NULL, resolution NULL, created DATE,
  position INT)`.
- `backlog_dependencies(item_uid, depends_on_uid)`.

## Domäne (reine Funktionen, Vorlage `src_old/backend/todo_viewer/domain`)

Baum, Fortschritt (erledigt/gesamt über Nachkommen, optional und abgelehnt
zählen nicht), Filter.

## Operationen

`list_items(projects, filters)` (Index wie heute: Label, Typ, Status,
Bereich, Titel, Parent), `get_item(label|uid)` mit Version.

## Frontend

Hauptroute „Backlog“ mit Unterseite „Baum“; Filter-Abschnitte Status und
Priorität (Standard wie heute: offene Status); „Epics/Stories
zuklappen/aufklappen“ für markierte Projekte; Detailpanel aus `STORY-067`.
Prioritäten- und Statusnamen übersetzt (DE: Dringend, Wichtig, Normal,
Perspektivisch). Kein Kanban.

## Tests

Domänen-Funktionen zuerst; Repository gegen echte SQLite; UI-Tests Baum und
Filter.
