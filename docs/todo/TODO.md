# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `STORY-001` **Bessere Platzierung der Fortschritts-Pie-Charts**
  - Type: Story.
  - Parent: None.
  - Status: Awaiting confirmation.
  - Created: 2026-09-25.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Fortschritts-Pie-Charts sitzen sichtbar beim zugehörigen
    Namen (z. B. direkt dahinter oder am Namen ausgerichtet) statt
    abgesetzt davon. Die genaue Platzierung wird vorher besprochen.
  - Completion criteria: Die abgestimmte Platzierung ist in den
    betroffenen Ansichten umgesetzt und vom Projektverantwortlichen
    geprüft.
  - Summary: Die kleinen Fortschrittskreise sollen näher an den Namen
    der Einträge rücken. Wie genau, ist noch offen.
  - Notes: `items/STORY-001/STORY-001_notes.md`.
- `STORY-002` **Alle Tasks/Stories ein- und ausklappen**
  - Type: Story.
  - Parent: None.
  - Status: Awaiting confirmation.
  - Created: 2026-09-25.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Eine Bedienoption klappt mit einem Klick alle Tasks und
    Stories auf bzw. zu.
  - Completion criteria: Die Option ist in der UI vorhanden; ein Klick
    klappt alle Einträge auf, ein weiterer alle zu.
  - Summary: Zwei Buttons im Baum klappen alle Epics bzw. alle Stories
    auf oder zu – für markierte Projekte oder, ohne Markierung, für alle.
  - Notes: `items/STORY-002/STORY-002_notes.md`.
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
- `STORY-003` **Items nur über ID adressieren**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Items werden in API, Application-Ports und UI nur über
    `source_id` und ID angesprochen. `location` und `line` verschwinden
    aus dem Vertrag; „archiviert“ ist ein Attribut des Items. Externe
    Änderungen werden über ein undurchsichtiges Versions-Token erkannt.
    `GET /api/v2/items/{source_id}/{id}` liefert ein einzelnes Item,
    egal ob aktiv oder archiviert.
  - Completion criteria: Einzelabruf und Bearbeiten funktionieren nur
    mit ID und Versions-Token; ein veraltetes Token führt zu einem
    Konfliktfehler; eine unbekannte ID liefert 404 mit stabilem Code;
    die UI nutzt die neue Adressierung; Golden-File-Tests bleiben grün.
  - Summary: Einträge werden nur noch über ihre ID angesprochen, nicht mehr
    über Datei und Zeile. Einfache Checklisten ohne IDs werden nicht mehr
    unterstützt.
  - Notes: `items/STORY-003/STORY-003_notes.md`.
- `STORY-004` **Lean Index**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
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
- `STORY-005` **Parent-Lifecycle-Regeln im Domain erzwingen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Regeln des Backlog-Formats (Epic ohne Parent, Pflichtfeld
    `Required for parent`, Pflichtkind vor Verlassen von Open,
    Blockade durch offene oder abgelehnte Pflichtkinder, kein Abschluss
    mit aktiven Kindern, keine Zyklen in Parent und Dependencies)
    werden im Domain geprüft und bei jeder Änderung durchgesetzt.
  - Completion criteria: Verstöße liefern Fehler mit stabilen Codes;
    jede Regel ist durch Domain-Tests abgedeckt; die UI übersetzt die
    neuen Codes.
  - Summary: Der Server lehnt Änderungen ab, die gegen die Regeln für
    Epics, Stories und ihre Kinder verstoßen, statt das dem Agenten zu
    überlassen.
  - Notes: `items/STORY-005/STORY-005_notes.md`.
- `STORY-006` **Weitere Felder bearbeitbar**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`, `STORY-005`.
  - Goal: Über die API lassen sich zusätzlich Titel, Goal, Completion
    criteria, Summary, Area, Parent und Dependencies ändern;
    Dependencies werden als Liste übergeben.
  - Completion criteria: Jedes Feld ist per API änderbar, Änderungen
    betreffen nur das Feld (Golden Files), Lifecycle-Regeln greifen bei
    Parent- und Dependency-Änderungen.
  - Summary: Über die API lassen sich jetzt auch Titel, Texte, Area,
    Parent und Abhängigkeiten ändern, mehrere Felder in einem Schritt.
  - Notes: `items/STORY-006/STORY-006_notes.md`.
- `STORY-007` **Items anlegen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
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
- `STORY-008` **Items löschen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`.
  - Goal: `DELETE /api/v2/items/{source_id}/{id}` entfernt ein Item.
    Solange andere Items per Parent oder Dependencies darauf verweisen,
    wird das Löschen mit einem Konfliktfehler abgelehnt.
  - Completion criteria: Löschen ohne Verweise entfernt genau den
    Eintrag; Löschen mit Verweisen liefert einen Konfliktfehler, der
    die verweisenden IDs nennt.
  - Summary: Ein Item wird samt seiner Notes- und Spec-Dateien gelöscht,
    aber nicht, solange andere Items darauf verweisen.
  - Notes: `items/STORY-008/STORY-008_notes.md`.
- `STORY-009` **Notes und Specs über das Item schreiben**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`.
  - Goal: Notes und Specs werden über das Item adressiert statt über
    Dateipfade: Lesen und Ersetzen von Specs mit Versions-Token sowie
    ein strukturierter Endpunkt, der einen datierten Notes-Eintrag
    (Discussed/Decided/Open) anhängt. Der Server pflegt dabei die
    Felder `Notes`, `Spec` und die Pflicht zur `Summary`.
  - Completion criteria: Notes-Einträge und Specs lassen sich ohne
    Kenntnis von Dateipfaden lesen und schreiben; konkurrierende
    Änderungen liefern Konfliktfehler; das Format der Notes entspricht
    dem Backlog-Format.
- `STORY-010` **API-Zugang für Agenten**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`, `STORY-004`, `STORY-005`, `STORY-006`,
    `STORY-007`, `STORY-008`, `STORY-009`.
  - Goal: Ein Agent kann die API zuverlässig erreichen und nutzen; es
    ist geklärt und umgesetzt, wie der Server für Agenten verfügbar ist
    (dauerhaft laufend, bei Bedarf gestartet oder anderer Weg), und die
    Nutzung ist in den techdocs beschrieben.
  - Completion criteria: Die Zugangsvariante ist mit dem
    Projektverantwortlichen entschieden und umgesetzt; README bzw.
    techdocs beschreiben die Agent-Nutzung; ein Agent kann damit einen
    vollständigen Pflege-Durchlauf ohne Dateizugriff ausführen.
  - Summary: Agenten sprechen den dauerhaft laufenden Container per HTTP
    an; der Umgang mit einem nicht erreichbaren Server liegt im Harness.
  - Notes: `items/STORY-010/STORY-010_notes.md`.
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
