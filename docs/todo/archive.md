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
