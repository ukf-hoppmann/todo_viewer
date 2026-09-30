# Projekt-Backlog-Archiv

Erledigte und abgelehnte Einträge, nach Entscheidung des Projektverantwortlichen
unverändert aus `TODO.md` hierher verschoben.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `STORY-001` **Bessere Platzierung der Fortschritts-Pie-Charts**
  - Type: Story.
  - Parent: None.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-002` **Alle Tasks/Stories ein- und ausklappen**
  - Type: Story.
  - Parent: None.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-003` **Items nur über ID adressieren**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-005` **Parent-Lifecycle-Regeln im Domain erzwingen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-006` **Weitere Felder bearbeitbar**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-008` **Items löschen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-009` **Notes und Specs über das Item schreiben**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Summary: Notizen und Specs lassen sich über das Item lesen und
    schreiben, ohne Dateipfade zu kennen.
  - Notes: `items/STORY-009/STORY-009_notes.md`.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-010` **API-Zugang für Agenten**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-011` **Papierkorb: Löschen markiert, Wiederherstellen und endgültig Löschen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-012` **Felder im Bearbeiten-Modus ändern**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-006`.
  - Goal: Im Detail-Panel öffnet ein Knopf „Bearbeiten“ ein Formular für
    Titel, Goal, Completion criteria, Summary, Area, Parent und
    Dependencies. Speichern schreibt alle Änderungen in einem Schritt,
    Abbrechen verwirft sie. Bei einem Versionskonflikt bleiben die Eingaben
    erhalten und der aktuelle Stand wird angezeigt.
  - Completion criteria: Alle genannten Felder sind über den
    Bearbeiten-Modus änderbar; ohne Bearbeiten-Modus ist nichts
    versehentlich änderbar; Regelverstöße und Versionskonflikte werden
    verständlich angezeigt; Komponententests decken Speichern, Abbrechen und
    Konflikt ab.
  - Summary: Einträge lassen sich über einen eigenen Bearbeiten-Modus
    ändern, nicht durch versehentliches Klicken.
  - Notes: `items/STORY-012/STORY-012_notes.md`.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-013` **Items in der UI anlegen**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-007`.
  - Goal: Ein Knopf „Neu“ oben legt ein Epic, eine Story oder einen Task
    ohne Parent an; „Kind anlegen“ im Detail-Panel belegt den Parent vor.
    Der Dialog fragt Typ und Pflichtfelder ab und wählt das neue Item danach
    aus.
  - Completion criteria: Anlegen funktioniert über beide Einstiege;
    Pflichtfelder und Regelverstöße werden im Dialog gemeldet;
    Komponententests vorhanden.
  - Summary: Neue Einträge lassen sich direkt in der Oberfläche anlegen.
  - Notes: `items/STORY-013/STORY-013_notes.md`.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-014` **Löschen und Papierkorb-Ansicht**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-011`.
  - Goal: Im Detail-Panel verschiebt „Löschen“ ein Item in den Papierkorb;
    hat es Kinder, zeigt die UI sie als Warnung und löscht sie erst nach
    Bestätigung mit. Eine eigene Ansicht „Papierkorb“ neben Baum,
    Abhängigkeiten und Kanban listet gelöschte Items und bietet
    Wiederherstellen und endgültiges Löschen.
  - Completion criteria: Löschen, Wiederherstellen und endgültiges Löschen
    sind in der UI bedienbar, jeweils samt Kindern; endgültiges Löschen
    verlangt eine Bestätigung; Komponententests vorhanden.
  - Summary: Gelöschte Einträge landen in einer eigenen Papierkorb-Ansicht
    und lassen sich zurückholen oder endgültig entfernen.
  - Notes: `items/STORY-014/STORY-014_notes.md`.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `STORY-015` **Notes und Specs in der UI schreiben und ändern**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-009`.
  - Goal: Im Dokument-Dialog lässt sich ein Notes-Eintrag (Thema, Discussed,
    Decided, Open) anhängen, und Notizen wie Specs lassen sich als ganzer
    Text mit Markdown-Vorschau ändern oder neu anlegen: GET holt den Text,
    PUT schreibt den neuen. Beim ersten Notes-Dokument fragt die UI nach
    einer Summary, falls keine vorhanden ist.
  - Completion criteria: Notes-Einträge anhängen sowie Notizen und Specs
    ändern und anlegen funktioniert in der UI und per API; Versionskonflikte
    werden gemeldet, ohne die Eingabe zu verlieren; Komponententests
    vorhanden.
  - Summary: Notizen und Specs lassen sich direkt in der Oberfläche
    schreiben und nachträglich ändern.
  - Notes: `items/STORY-015/STORY-015_notes.md`.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.

- `TASK-001` **Area im Lean Index**
  - Type: Task.
  - Parent: `STORY-004`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt: GET
    /api/v2/index liefert area (fb61bd5).

- `STORY-004` **Lean Index**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: `GET /api/v2/index` liefert für aktive und archivierte Items nur
    `source_id`, `id`, `type`, `status`, `title`, `parent` und `area`,
    optional gefiltert auf eine Quelle.
  - Completion criteria: Der Endpunkt hat ein festes Schema im
    OpenAPI-Vertrag, liefert genau diese Felder und ist durch API-Tests
    abgedeckt.
  - Notes: `items/STORY-004/STORY-004_notes.md`.
  - Summary: Die Übersichtsliste aller Einträge soll schlank bleiben. Sie
    zeigt nur das Nötigste, jetzt zusätzlich den Bereich, damit man
    schneller sieht, welche Einträge man sich genauer ansehen muss.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt: Lean
    Index mit festem Schema inkl. area, durch API-Tests abgedeckt (fb61bd5,
    TASK-001).

- `STORY-017` **Klare Antwort und Wiederöffnen-Angebot bei geschlossenem Parent**
  - Type: Story.
  - Parent: None.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Wer ein aktives Kind an ein abgeschlossenes Epic oder eine
    abgeschlossene Story hängt, erfährt eindeutig, dass der Parent
    geschlossen ist und wie man ihn wieder öffnet; KI-Agenten verstehen die
    Antwort ohne Rätselraten, die UI bietet das Wiederöffnen direkt an.
  - Completion criteria: Der Server antwortet in diesem Fall mit 409
    parent_closed statt children_still_active, nennt das Kind und die zu
    öffnenden geschlossenen Vorfahren in Öffnungsreihenfolge und beschreibt
    in der Meldung den Weg zum Wiederöffnen; children_still_active bleibt
    für das Schließen eines Parents mit aktiven Kindern; der Anlegen-Dialog
    der UI fragt bei parent_closed, ob die Vorfahren wieder geöffnet werden
    sollen, und legt das Item danach an; übrige UI-Stellen zeigen die klare
    Meldung (de/en); interfaces.md beschreibt den Fehlercode und das
    Wiederöffnen per PATCH; Tests decken Domain, API und UI ab.
  - Summary: Auslöser: Der Harness bekam beim Anlegen einer Story unter dem
    abgeschlossenen EPIC-004 nur die missverständliche Meldung
    children_still_active und legte die Story ohne Parent an.
  - Resolution: Vom Projektverantwortlichen bestätigt: 409 parent_closed mit
    Vorfahren in Öffnungsreihenfolge, Wiederöffnen-Nachfrage im
    Anlegen-Dialog, Doku in interfaces.md und README (Merge f6a69ab).

- `STORY-016` **Wichtige Schritte und Fehler systematisch protokollieren**
  - Type: Story.
  - Parent: None.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Fehler lassen sich allein anhand des Logs analysieren:
    Start-Konfiguration, alle schreibenden Aktionen, abgelehnte Requests
    (4xx), Serverfehler (5xx) und bisher still geschluckte Fehler sind mit
    Kontext protokolliert. Das Log liegt außerhalb des Containers und bleibt
    beim Entfernen des Containers erhalten. Bisher gibt es im Backend kein
    Logging; nur das uvicorn-Zugriffslog zeigt Statuscodes.
  - Completion criteria: Beim Start werden Version und aktive Pfade
    (CONFIG_DIR, FRONTEND_DIR, BROWSE_START) geloggt; jede schreibende
    Aktion erzeugt eine INFO-Zeile mit Quelle, Item-ID bzw. Ziel und
    Ergebnis; jede 4xx-Antwort erzeugt eine Zeile mit Methode, Pfad,
    Statuscode, Fehlercode und details, jede 5xx zusätzlich den Stacktrace;
    still behandelte Fehler (unlesbare Quelle, defekte ui_state.json,
    OSError im Ordner-Browser) erzeugen eine WARNING; jede Zeile trägt eine
    Request-ID; Format einzeilig key=value, per grep durchsuchbar; LOG_FILE
    und LOG_LEVEL per Umgebungsvariable, ohne LOG_FILE Konsole; Rotation
    nach Größe (5 MB, 5 Dateien); docker-compose bindet ./logs als Volume
    ein, logs/ steht in .gitignore; Tests decken u. a. einen
    409-Regelverstoß, einen 500-Fehler und eine Schreibaktion ab;
    Konfiguration, Betrieb und Suche im Log sind in den Techdocs
    beschrieben.
  - Summary: Das Backend soll alle wichtigen Schritte und Fehler so
    protokollieren, dass sich Fehler allein über das Log (per grep, ohne
    vollständiges Lesen) analysieren lassen. Die Logdatei liegt in ./logs
    außerhalb des Containers.
  - Notes: `items/STORY-016/STORY-016_notes.md`.
  - Resolution: Confirmed by the project owner on 2026-09-28.

- `TASK-002` **Typ eines Items ändern**
  - Type: Task.
  - Parent: `STORY-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-30 bestätigt.

- `STORY-007` **Items anlegen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-30 bestätigt.

- `EPIC-001` **Backlog-Pflege per API statt direkter Dateizugriffe**
  - Type: Epic.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-30 bestätigt.

- `STORY-018` **Typ eines Items in der UI ändern**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-30 bestätigt.

- `EPIC-002` **Backlog-Pflege in der UI**
  - Type: Epic.
  - Status: Completed.
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
  - Resolution: Vom Projektverantwortlichen am 2026-09-30 bestätigt.

- `STORY-019` **Architekturregeln für wählbares Speicher-Backend öffnen**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Architekturregeln erlauben je Projekt wahlweise Markdown oder
    eine zentrale Datenbank hinter dem BacklogRepository-Port. Regel 1
    (Markdown als einzige Wahrheit) wird entsprechend umformuliert; das
    Backend-Scope-Dokument bekommt Regeln für DB-Adapter und Migrationen.
  - Completion criteria: architecture.md und
    docs/development/architecture/backend.md sind angepasst und vom
    Projekteigner freigegeben; Verweise auf die bisherige Regel 1 (Tests,
    Doku) sind konsistent.
  - Summary: Regel 1 und der Backend-Scope werden so geändert, dass Markdown
    und Datenbank gleichrangige Backends sind.
  - Spec: `items/STORY-019/STORY-019_spec.md`.
  - Resolution: Architekturregeln (Regel 1, Backend-Scope Abschnitt 5,
    import-linter) am 2026-09-30 vom Projekteigner bestätigt; Commit
    f64b4cc.

- `STORY-020` **Port-Vertrag als Contract-Suite und Routing je Projekt**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-019`.
  - Goal: Die Charakterisierungstests laufen als parametrisierte
    Contract-Suite gegen jeden BacklogRepository-/DocumentStore-Adapter. Ein
    RoutingRepository wählt je Source.backend (markdown | database) den
    Adapter; Verdrahtung in bootstrap.py.
  - Completion criteria: Die Contract-Suite läuft gegen den Markdown-Adapter
    und einen In-Memory-Fake, alle bisherigen Tests sind grün, das Verhalten
    ist unverändert, Source hat das Feld backend (Standard markdown).
  - Summary: Bestehende Tests werden zu einem wiederverwendbaren Maßstab für
    neue Adapter; Routing je Projekt kommt dazu.
  - Spec: `items/STORY-020/STORY-020_spec.md`.
  - Resolution: Vom Projekteigner bestätigt am 2026-09-30; umgesetzt in
    Merge d44626d, Release v0.2.2.

- `STORY-027` **Dokument-Port itembasiert statt pfadbasiert**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projekteigner bestätigt am 2026-09-30; umgesetzt in
    Merge 909e4c8.

- `STORY-021` **SQLite-Adapter für Items, Archiv, Papierkorb und Dokumente**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projekteigner bestätigt am 2026-09-30; umgesetzt in
    Merge 95fcb7a, Release v0.3.0.

- `STORY-022` **Projekte und UI-State in der zentralen Datenbank**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Notes: `items/STORY-022/STORY-022_notes.md`.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.

- `STORY-023` **Sync zwischen Datenbank und Markdown (to_md / from_md)**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Notes: `items/STORY-023/STORY-023_notes.md`.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.

- `TASK-003` **Backend-Wechsel per PUT nach Sync**
  - Type: Task.
  - Parent: `STORY-024`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Projekt lässt sich an Ort und Stelle auf das andere
    Speicher-Backend umstellen, mit gleicher source_id und gleichen
    Item-IDs. Markdown → Datenbank: Sync from_md (Vorschau, Bestätigung)
    liest den Ordner in die Datenbank, danach schaltet PUT /sources/{id} mit
    backend=database um; der Ordner wandert von path nach sync_path.
    Datenbank → Markdown: Sync to_md, danach PUT mit backend=markdown;
    sync_path wandert nach path. Der Sync akzeptiert dafür auch ein
    Markdown-Projekt (nur from_md).
  - Completion criteria: Der Wechsel funktioniert in beide Richtungen über
    die API: PUT mit neuem backend wird nur akzeptiert, wenn die Daten zuvor
    synchronisiert wurden (sonst klarer Fehlercode, nichts ändert sich);
    source_id und Item-IDs bleiben gleich; path und sync_path wandern wie im
    EPIC-003-Spec beschrieben; der Markdown-path bleibt eindeutig.
    Contract-, Service- und API-Tests decken beide Richtungen und die
    Fehlerfälle ab; Techdocs und OpenAPI sind angepasst.
  - Summary: Backend-Wechsel ohne neue Projekt-Id: erst Sync, dann PUT mit
    neuem backend.
  - Notes: `items/TASK-003/TASK-003_notes.md`.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.

- `STORY-024` **Speicher-Backend und Sync in der UI bedienen**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Notes: `items/STORY-024/STORY-024_notes.md`.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.

- `STORY-025` **Doku und Release für das wählbare Speicher-Backend**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Notes: `items/STORY-025/STORY-025_notes.md`.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.

- `STORY-026` **Postgres als zweiter Datenbank-Typ (optional)**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: No.
  - Status: Rejected.
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
  - Resolution: Vom Projektinhaber am 2026-09-30 vorerst verworfen: SQLite
    genügt für den lokalen Einzelbetrieb; Postgres nur bei echtem Bedarf neu
    aufnehmen.
  - Notes: `items/STORY-026/STORY-026_notes.md`.

- `EPIC-003` **Wählbares Speicher-Backend: Markdown oder zentrale Datenbank**
  - Type: Epic.
  - Status: Completed.
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
    möglich und ergibt beim Roundtrip md -> db -> md dieselben Items
    (gleiche Versionen) und Dokumente; Export -> Import -> Export ergibt
    identische Dateien. Die Architekturregeln erlauben beide Backends, Doku
    und Release sind aktualisiert.
  - Summary: Neben den Markdown-Dateien wird eine zentrale SQLite-Datenbank
    als Speicher wählbar, mit Sync in beide Richtungen auf Knopfdruck.
  - Spec: `items/EPIC-003/EPIC-003_spec.md`.
  - Notes: `items/EPIC-003/EPIC-003_notes.md`.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.

- `STORY-029` **Primärquelle und Spiegel pro Projekt in Modell und API**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-028`.
  - Goal: Jedes Projekt hat in Datenbank und API eine primäre Quelle und je
    Seite einen optionalen Spiegel mit eigenem Speicherort (Markdown-Ordner
    bzw. Datenbank). Beide Richtungen sind möglich. Bestehende Projekte
    werden ohne Verlust übernommen.
  - Completion criteria: - GET /sources nennt je Projekt Primärquelle und
    Spiegel; POST/PUT setzen sie. - Ein Markdown-Projekt kann einen
    Datenbank-Spiegel halten und umgekehrt. - Bestehende Projekte kommen per
    versionierter Migration unverändert weiter: Backend bleibt primär,
    sync_path wird zum Spiegel-Ordner. - Die Contract-Suite deckt beide
    Kombinationen ab; OpenAPI und TypeScript-Typen sind neu erzeugt.
  - Notes: `items/STORY-029/STORY-029_notes.md`.
  - Summary: Projekte kennen jetzt Primärquelle und optionalen Spiegel; die
    API zeigt beides und lässt den Spiegel setzen.
  - Resolution: Vom Projekteigner bestätigt; umgesetzt mit v0.6.1.
