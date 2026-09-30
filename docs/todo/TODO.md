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

- `STORY-021` **SQLite-Adapter für Items, Archiv, Papierkorb und Dokumente**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-020`, `STORY-027`.
  - Goal: Ein Datenbank-Adapter (SQLAlchemy Core, SQLite) implementiert
    BacklogRepository und DocumentStore, inklusive Archiv, Papierkorb,
    Notizen und Specs. Die Daten werden normalisiert in Tabellen gespeichert
    (Items mit UUID und Label, Beziehungen, Zusatzfelder, Dokumente) mit
    versioniertem Schema (Migrationen) und einer Spalte position für die
    Reihenfolge. apply_all läuft in einer Transaktion, Versionskonflikte
    über Item.version.
  - Completion criteria: Die Contract-Suite ist für SQLite grün; ein Projekt
    mit backend=database funktioniert über die API Ende zu Ende (lesen,
    anlegen, ändern, archivieren, löschen, Dokumente).
  - Summary: Neuer DB-Adapter, der dieselbe Contract-Suite besteht wie
    Markdown.
  - Spec: `items/STORY-021/STORY-021_spec.md`.
  - Notes: `items/STORY-021/STORY-021_notes.md`.

- `STORY-022` **Projekte und UI-State in der zentralen Datenbank**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-021`.
  - Goal: Die Projektliste (bisher Source) und der UI-State liegen in der
    zentralen DB. Ein Projekt hat eine stabile Id statt Pfad-Hash, ein
    backend und optional einen Sync-Pfad zu seinen .md-Dateien. config.json
    behält nur storage_url (mit Zugangsdaten, lokal in Ordnung) und
    Markdown-Projekte. Bestehende Installationen werden ohne Datenverlust
    migriert.
  - Completion criteria: Projekte lassen sich in der DB anlegen, ändern und
    löschen; bestehende config.json-Quellen laufen unverändert weiter oder
    werden migriert; ui_state kommt aus der DB.
  - Summary: Ein zentraler Ort für Projekte, Einstellungen und Inhalte;
    Sync-Pfad je Projekt konfigurierbar.
  - Spec: `items/STORY-022/STORY-022_spec.md`.

- `STORY-023` **Sync zwischen Datenbank und Markdown (to_md / from_md)**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-022`.
  - Goal: Ein Sync-Service überträgt auf Knopfdruck oder API-Aufruf (POST
    /api/v2/sources/{id}/sync mit direction=to_md|from_md) alle Daten eines
    Projekts: TODO.md, archive.md und alle Items samt Notizen und Specs.
    Vorher gibt es eine Vorschau (neu, geändert, fehlend), Überschreiben nur
    mit Bestätigung; Konflikte werden über den Versionshash je Item erkannt.
    Löschungen (Einträge, die auf der Zielseite existieren, auf der
    Quellseite aber fehlen) werden als Warnung angezeigt und nur nach
    Rückfrage ausgeführt.
  - Completion criteria: Sync in beide Richtungen funktioniert per API mit
    Vorschau und Bestätigung. Der Export ist stabil (export -> import ->
    export ergibt identische Dateien) und der Import gibt dieselben Items
    zurück (gleiche Item.version); die .md müssen nicht byte-gleich zum
    Ausgangstext sein. Fehlende Einträge werden in der Vorschau als Warnung
    gemeldet und nur nach ausdrücklicher Nachfrage gelöscht. Ohne Sync-Pfad
    wird mit klarem Fehlercode abgelehnt.
  - Summary: Zweiseitiger Sync auf Knopfdruck, keine automatische
    Spiegelung.
  - Spec: `items/STORY-023/STORY-023_spec.md`.

- `STORY-024` **Speicher-Backend und Sync in der UI bedienen**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Open.
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

- `STORY-027` **Dokument-Port itembasiert statt pfadbasiert**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: In progress.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-020`.
  - Goal: Domain und Application adressieren Notizen und Specs nur noch über
    Item-ID und Dokumentname. Wo und wie ein Dokument liegt (Ordner
    items/<ID>/, Dateinamen, Umbenennen beim Typwechsel), weiß nur der
    Speicher-Adapter. Damit muss ein Datenbank-Adapter keine Ordnerstruktur
    nachbauen.
  - Completion criteria: Der DocumentStore-Port nimmt Item-ID und
    Dokumentname statt Pfaden; domain/documents.py und RetypePlanner kennen
    keine Pfade mehr; die HTTP-API und die Markdown-Dateien verhalten sich
    unverändert (Markdown-Goldens byte-gleich; in JSON-Goldens ändern sich
    nur die version-Werte von Items mit Dokumenten); die Contract-Suite
    prüft den neuen Port für Markdown und den Fake.
  - Summary: Umbau vor dem Datenbank-Adapter: Dokumente werden über Item und
    Namen angesprochen, die Ablage entscheidet der Adapter.
  - Notes: `items/STORY-027/STORY-027_notes.md`.
