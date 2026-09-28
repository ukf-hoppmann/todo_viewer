# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `EPIC-001` **Backlog-Pflege per API statt direkter Dateizugriffe**
  - Type: Epic.
  - Status: Open.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Agenten (Ablösung der Schreibzugriffe des todo-Skills) und
    die UI lesen und pflegen Backlogs vollständig über `/api/v2`. Der
    Vertrag adressiert Items nur über `source_id` und ID und kennt
    weder Dateien, Zeilen noch Locations, sodass `TODO.md` später durch
    eine Datenbank ersetzt werden kann, ohne die API zu ändern.
  - Completion criteria: Alle Pflichtkinder sind abgeschlossen; ein
    Agent kann Items lesen, anlegen, bearbeiten, löschen und Notes/Specs
    schreiben, ohne Backlog-Dateien direkt anzufassen; kein Endpunkt
    enthält Dateipfade, Zeilen oder Locations.
  - Summary: Statt dass der Agent die Backlog-Dateien selbst bearbeitet,
    geht alles über die API des ToDo-Viewers. Die API wird so gebaut,
    dass die Markdown-Dateien später durch eine Datenbank ersetzt werden
    können.
  - Notes: `items/EPIC-001/EPIC-001_notes.md`.
  - Spec: `items/EPIC-001/EPIC-001_spec_harness.md`.

- `STORY-004` **Lean Index**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: `GET /api/v2/index` liefert für aktive und archivierte Items
    nur `source_id`, `id`, `type`, `status`, `title` und `parent`,
    optional gefiltert auf eine Quelle.
  - Completion criteria: Der Endpunkt hat ein festes Schema im
    OpenAPI-Vertrag, liefert genau diese Felder und ist durch API-Tests
    abgedeckt.
  - Notes: `items/STORY-004/STORY-004_notes.md`.
  - Summary: Die Übersichtsliste aller Einträge soll schlank bleiben. Sie
    zeigt nur das Nötigste, jetzt zusätzlich den Bereich, damit man
    schneller sieht, welche Einträge man sich genauer ansehen muss.

- `TASK-001` **Area im Lean Index**
  - Type: Task.
  - Parent: `STORY-004`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: `GET /api/v2/index` liefert je Item zusätzlich `area`
    (`IndexItemOut` in `backend/todo_viewer/api/v2/schemas.py`), damit sich
    aus der flachen Liste besser einschätzen lässt, welche Items relevant
    sind, bevor einzelne mit `show` geladen werden.
  - Completion criteria: Das OpenAPI-Schema des Index enthält `area`;
    API-Tests prüfen `area` für aktive und archivierte Items;
    `docs/techdocs/interfaces.md` beschreibt das Feld; `backlog_api.py
    index` im Claude_Harness zeigt die Area ohne weitere Änderung an.
