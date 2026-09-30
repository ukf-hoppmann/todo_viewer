# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `EPIC-004` **Primärquelle und Spiegel pro Projekt, Einstellungsmenü**
  - Type: Epic.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Jedes Projekt hat eine primäre Quelle (Datenbank oder Markdown)
    und darf die andere Seite als Spiegel halten. Ein eigenes
    Einstellungsmenü bündelt alles Speicher-Bezogene: Primärquelle je
    Projekt, Pfade der Markdown-Seite, Sync mit wählbarer Richtung und den
    Sync-Status. Ziel im Alltag: auf der Datenbank arbeiten, Markdown als
    aktueller Spiegel. Das Menü ist in Abschnitten aufgebaut, damit weitere
    Einstellungen ohne Umbau dazukommen.
  - Completion criteria: - Pro Projekt lässt sich die primäre Quelle im Menü
    wählen; beim Wechsel läuft vorher ein Sync, und vorher wird ein Backup
    angelegt. - Beide Seiten dürfen als Spiegel gehalten werden; der Sync
    läuft standardmäßig von der primären zur anderen Seite, die Richtung ist
    pro Lauf wählbar. - Ein Projekt, dessen Spiegel seit dem letzten Sync
    extern geändert wurde, trägt in der Sidebar ein Badge, das das Menü bei
    diesem Projekt öffnet. - Der Sync umfasst alles (Backlog, Archiv, Notes,
    Specs, Papierkorb). - Es gibt nie einen automatischen Sync; die
    Architekturregeln sind entsprechend angepasst und vom Projekteigner
    freigegeben. - Das Menü ist über eine Abschnittsliste erweiterbar; die
    Doku ist aktuell.

- `STORY-035` **Doku und Release für Primärquelle, Spiegel und Einstellungsmenü**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-034`.
  - Goal: Technische Dokumentation und Release für die neuen Funktionen.
  - Completion criteria: - README und docs/techdocs (Konfiguration,
    Schnittstellen, Betrieb) beschreiben Primärquelle, Spiegel,
    Sync-Richtung, Status und Backup. - Ein Tagesbericht und ein Release
    (SemVer) sind erledigt.
  - Notes: `items/STORY-035/STORY-035_notes.md`.
  - Summary: README und Techdocs beschreiben Primärquelle, Spiegel,
    Sync-Richtung, Status und Backup durchgehend; Releases und Tagesberichte
    sind erledigt.
