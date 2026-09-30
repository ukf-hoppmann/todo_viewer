# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `EPIC-003` **Wählbares Speicher-Backend: Markdown oder zentrale Datenbank**
  - Type: Epic.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Jedes Projekt kann wahlweise in Markdown-Dateien (wie bisher) oder
    in einer zentralen lokalen Datenbank gespeichert werden. Die Datenbank
    nimmt die komplette Struktur auf (Items, Archiv, Papierkorb, Notizen,
    Specs). Per Knopfdruck oder API-Aufruf lässt sich ein Projekt zwischen
    Datenbank und Markdown synchronisieren (to_md / from_md).
  - Completion criteria: Ein Projekt lässt sich je nach Wahl mit Markdown
    oder SQLite betreiben. Sync in beide Richtungen ist per API und UI
    möglich und ergibt beim Roundtrip md -> db -> md byte-gleiche Dateien.
    Die Architekturregeln erlauben beide Backends, Doku und Release sind
    aktualisiert.
  - Summary: Neben den Markdown-Dateien wird eine zentrale SQLite-Datenbank
    als Speicher wählbar, mit Sync in beide Richtungen auf Knopfdruck.
  - Spec: `items/EPIC-003/EPIC-003_spec.md`.

- `STORY-024` **Speicher-Backend und Sync in der UI bedienen**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: In progress.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-023`.
  - Goal: Im UI lässt sich je Projekt das Backend wählen, der Sync-Pfad
    einstellen und der Sync (to_md / from_md) mit Vorschau-Dialog und
    Bestätigung auslösen. Fehlercodes werden übersetzt, TypeScript-Typen aus
    OpenAPI neu generiert.
  - Completion criteria: Alle Backend- und Sync-Funktionen sind ohne Konsole
    über die UI nutzbar; UI-Tests decken Backend-Wahl, Vorschau und
    Bestätigung ab.
  - Summary: Backend-Wahl und Sync-Knöpfe im Projekt-Dialog.
  - Spec: `items/STORY-024/STORY-024_spec.md`.

- `STORY-025` **Doku und Release für das wählbare Speicher-Backend**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-024`.
  - Goal: README und Techdocs beschreiben Backend-Wahl, storage_url,
    DB-Sicherung, Sync-Ablauf und Migration; Tagesbericht und Release
    (voraussichtlich 0.3.0).
  - Completion criteria: Doku entspricht dem Ist-Zustand, Release ist
    getaggt, das eigene Backlog wurde probeweise in die DB übernommen.
  - Summary: Dokumentation und Release des Epics.
  - Spec: `items/STORY-025/STORY-025_spec.md`.

- `STORY-026` **Postgres als zweiter Datenbank-Typ (optional)**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-021`.
  - Goal: Der DB-Adapter läuft zusätzlich gegen Postgres (Treiber,
    URL-Konfiguration, Dialekt-Unterschiede in den Migrationen); dieselbe
    Contract-Suite. Nur nötig, wenn Postgres tatsächlich gebraucht wird.
  - Completion criteria: Die Contract-Suite ist für SQLite und Postgres
    grün; Postgres-Tests werden übersprungen, wenn kein Server erreichbar
    ist.
  - Summary: Optionaler zweiter Datenbank-Typ.
  - Spec: `items/STORY-026/STORY-026_spec.md`.
