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
  - Completion criteria: Alle Pflichtkinder sind abgeschlossen; ein Agent
    kann Items lesen, anlegen, bearbeiten, löschen und Notes/Specs
    schreiben, ohne Backlog-Dateien direkt anzufassen; kein Item-Endpunkt
    enthält Dateipfade, Zeilen oder Locations (der Ordnerpfad einer Quelle
    in `/sources` und `/folders` gehört zur Konfiguration und ist
    ausgenommen).
  - Summary: Statt dass der Agent die Backlog-Dateien selbst bearbeitet,
    geht alles über die API des ToDo-Viewers. Die API wird so gebaut,
    dass die Markdown-Dateien später durch eine Datenbank ersetzt werden
    können.
  - Notes: `items/EPIC-001/EPIC-001_notes.md`.
  - Spec: `items/EPIC-001/EPIC-001_spec_harness.md`.

- `STORY-007` **Items anlegen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: In progress.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`, `STORY-005`.
  - Goal: `POST /api/v2/items` legt ein Epic, eine Story oder einen
    Task an. Der Server vergibt die nächste freie ID des Typs über
    aktive und archivierte Items, setzt Status Open und das heutige
    Datum als Standard für Created.
  - Completion criteria: Neu angelegte Items sind formatgültig, haben
    eine eindeutige ID und werden als Item zurückgegeben; ungültige
    Eingaben liefern Fehler mit stabilen Codes.
  - Summary: Neue Epics, Stories und Tasks lassen sich über die API
    anlegen; der Server vergibt die ID und prüft die Regeln.
  - Notes: `items/STORY-007/STORY-007_notes.md`.

- `TASK-002` **Typ eines Items ändern**
  - Type: Task.
  - Parent: `STORY-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein eigener Endpunkt `POST /api/v2/items/{source}/{id}/retype`
    ändert den Typ eines Items (Epic, Story, Task). Das Item erhält die
    nächste freie ID des Zieltyps; Header, `parent` und `dependencies` aller
    Items (aktiv, Archiv, Papierkorb), der Ordner `items/<ID>/` sowie
    ID-Erwähnungen in Notes und Specs des Backlogs werden atomar mitgezogen.
    Die Antwort enthält einen Hinweis, dass Techdocs und andere Stellen
    außerhalb des Backlogs die alte ID noch nennen können; UI und Agenten
    können ihn anzeigen bzw. darauf aufbauen.
  - Completion criteria: Der Typwechsel liefert das Item mit neuer ID und
    Version und lässt keine Verweise auf die alte ID im Backlog zurück. Die
    Antwort nennt alte und neue ID und trägt einen Hinweis mit stabilem Code
    auf mögliche Verweise außerhalb des Backlogs. Die Lifecycle-Regeln (z.
    B. Epic ohne Parent, Epic mit Pflichtkind) werden geprüft und verletzen
    sie, bleibt alles unverändert. Tests decken aktive und archivierte
    Items, Kinder, Abhängigkeiten und Dokumente ab; OpenAPI und Techdocs
    sind aktualisiert.
  - Summary: Den Typ eines Items ändern, ohne dass Verweise im Backlog
    brechen.
  - Notes: `items/TASK-002/TASK-002_notes.md`.

- `EPIC-002` **Backlog-Pflege in der UI**
  - Type: Epic.
  - Status: In progress.
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

- `STORY-018` **Typ eines Items in der UI ändern**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-002`.
  - Goal: Im Detail-Panel lässt sich der Typ eines Items ändern. Die UI ruft
    den Typwechsel der API auf, wählt das Item danach unter seiner neuen ID
    aus und zeigt den Hinweis der API, dass Techdocs und andere Stellen
    außerhalb des Backlogs die alte ID noch nennen können.
  - Completion criteria: Ein Item lässt sich im Detail-Panel auf einen
    anderen Typ umstellen; danach ist es unter der neuen ID ausgewählt und
    die Ansichten zeigen es dort. Regelverstöße der API (z. B. Epic mit
    Parent) erscheinen als übersetzte Meldung ohne Änderung. Der Hinweis auf
    mögliche Verweise außerhalb des Backlogs ist sichtbar und enthält die
    alte und die neue ID. Texte sind in Deutsch und Englisch vorhanden;
    Typecheck, Lint und Web-Tests sind grün.
  - Summary: Den Typ eines Items direkt in der Oberfläche ändern, samt
    Hinweis auf Verweise außerhalb des Backlogs.
  - Notes: `items/STORY-018/STORY-018_notes.md`.
