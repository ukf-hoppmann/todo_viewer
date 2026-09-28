# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items
- `EPIC-001` **Backlog-Pflege per API statt direkter Dateizugriffe**
  - Type: Epic.
  - Status: In progress.
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
- `EPIC-002` **Backlog-Pflege in der UI**
  - Type: Epic.
  - Status: Open.
  - Created: 2026-09-27.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: In der UI lassen sich Items anlegen und löschen, ihre
    Freitext-Felder (Titel, Goal, Completion criteria, Summary, Area,
    Parent, Dependencies) bearbeiten sowie Notes-Einträge und Specs
    schreiben. Die UI nutzt dafür die Endpunkte aus `EPIC-001`.
  - Completion criteria: Alle Pflichtkinder sind abgeschlossen; jede
    genannte Funktion ist in der UI bedienbar, Fehlercodes der API
    werden übersetzt angezeigt, und der Projektverantwortliche hat die
    Bedienung geprüft.
  - Summary: Alles, was künftig ein Agent über die API am Backlog
    ändern kann, soll auch direkt in der Oberfläche möglich sein.
  - Notes: `items/EPIC-002/EPIC-002_notes.md`.

- `STORY-011` **Papierkorb: Löschen markiert, Wiederherstellen und endgültig Löschen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-008`.
  - Goal: Löschen markiert ein Item als gelöscht, statt es zu entfernen.
    Gelöschte Items liegen in einem Papierkorb mit eigener Route, aus dem
    sie wiederhergestellt oder endgültig gelöscht werden. Löschen und
    Wiederherstellen kaskadieren auf Kind-Items; vorher warnt die API und
    verlangt eine Bestätigung.
  - Completion criteria: Gelöschte Items verschwinden aus Übersicht und
    Index und erscheinen im Papierkorb; Wiederherstellen und endgültiges
    Löschen funktionieren samt Kindern; ohne Bestätigung liefert die API
    eine Warnung mit den betroffenen Kindern; Tests und Doku sind vorhanden.
  - Summary: Gelöschte Einträge landen erst im Papierkorb und können
    zurückgeholt werden.
  - Notes: `items/STORY-011/STORY-011_notes.md`.
