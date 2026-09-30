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

- `STORY-032` **Sync-Status: Spiegel extern geändert erkennen**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: In progress.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-030`.
  - Goal: Der Dienst erkennt, ob sich eine Seite seit dem letzten Sync
    geändert hat (z. B. KI hat Markdown-Dateien bearbeitet) und liefert
    Status und Zeitpunkt des letzten Syncs je Projekt. Er synchronisiert
    dabei nie von selbst.
  - Completion criteria: - GET /sources nennt je Projekt den Sync-Status (in
    Sync, Spiegel geändert, primäre Quelle geändert, beide geändert) und den
    letzten Sync-Zeitpunkt. - Die Erkennung braucht keinen Sync und ändert
    keine Daten. - Tests decken alle vier Zustände ab.
  - Notes: `items/STORY-032/STORY-032_notes.md`.
  - Summary: Jedes Projekt mit Spiegel meldet, welche Seite sich seit dem
    letzten Sync geändert hat; das Lesen ändert nichts.

- `STORY-033` **Einstellungsmenü: erweiterbarer Rahmen und Abschnitt „Allgemein“**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-029`.
  - Goal: Ein Einstellungsmenü (Zahnrad in der Sidebar) besteht aus
    Abschnitten, die in einer Liste registriert werden; ein neuer Abschnitt
    ist ein neuer Eintrag. Der erste Abschnitt „Allgemein“ zeigt den
    Datenbank-Ort nur lesend (Bearbeiten bleibt in der config.json) und
    stellt das Standard-Backend für neue Projekte ein.
  - Completion criteria: - Das Menü öffnet sich über die Sidebar und zeigt
    die Abschnitte als Navigation. - Abschnitte werden aus einer Liste
    gerendert; ein Test zeigt, dass ein zusätzlicher Eintrag ohne weitere
    Änderung erscheint. - „Allgemein“ zeigt Datenbank-Typ und -Ort nur
    lesend und speichert das Standard-Backend im UI-Zustand. - Das
    Standard-Backend ist beim Hinzufügen eines Projekts vorausgewählt.

- `STORY-034` **Menüabschnitt „Projekte“: Primärquelle, Pfade und Sync je Projekt**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-033`, `STORY-030`, `STORY-031`, `STORY-032`.
  - Goal: Pro Projekt eine Karte: primäre Quelle umschalten, Pfade beider
    Seiten (Markdown-Ordner, Spiegel) einstellen, Sync mit Richtung
    auslösen, Sync-Status sehen. Der Bearbeiten-Dialog der Sidebar behält
    nur den Namen; Entfernen und Reihenfolge bleiben in der Sidebar. Das
    Sync-Badge in der Sidebar öffnet das Menü bei diesem Projekt.
  - Completion criteria: - Jede Karte zeigt Primärquelle, beide Pfade,
    Status und letzten Sync. - Wechsel der Primärquelle führt über Sync und
    Backup aus dem Menü. - Sync-Richtung ist wählbar; Standard ist von der
    primären Seite zur anderen. - Das Badge erscheint bei geändertem Spiegel
    und öffnet das Menü bei diesem Projekt. - Der Bearbeiten-Dialog enthält
    nur noch den Namen. - Web-Tests decken Karte, Richtung und Badge ab.

- `STORY-035` **Doku und Release für Primärquelle, Spiegel und Einstellungsmenü**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-034`.
  - Goal: Technische Dokumentation und Release für die neuen Funktionen.
  - Completion criteria: - README und docs/techdocs (Konfiguration,
    Schnittstellen, Betrieb) beschreiben Primärquelle, Spiegel,
    Sync-Richtung, Status und Backup. - Ein Tagesbericht und ein Release
    (SemVer) sind erledigt.
