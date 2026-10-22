# Project Backlog

Active project work: open, in progress, or awaiting a project-owner decision.
Completed and rejected items are moved to `archive.md`; per-item notes and
specs live in `items/<ID>/`.

Format: Claude_Harness backlog format version 2. The rules are defined in
`docs/techdocs/interfaces.md` of the ToDo Viewer.

## Work items

- `STORY-086` **Baum: Umwandeln-Dialog beim Ziehen**
  - Uid: 9ccc4f8d-f897-4fdd-bc8d-a67da5569d3f.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-17.
  - Area: Web-UI.
  - Priority: Prospective.
  - Dependencies: `STORY-072`.
  - Goal: Zieht man ein Item an eine Stelle, an der sein Typ nicht erlaubt
    ist, bietet der Baum an, es umzuwandeln und dann zu verschieben, statt
    abzulehnen.
  - Completion criteria: 1. Die Server-Domain erzwingt die Struktur für
    Anlegen, Ändern, Verschieben, Typwechsel, Wiederherstellen und Abgleich:
    Epic nur als Wurzel, Story als Wurzel oder unter einem Epic, Task als
    Wurzel, unter einem Epic oder einer Story, nichts unter einem Task;
    bestehende Verletzungen blockieren unbeteiligte Änderungen nicht. 2. Ein
    Typwechsel ist nur erlaubt, wenn danach der ganze Teilbaum passt (Epic
    -> Story wandelt Kind-Storys zu Tasks, nicht möglich bei Kind-Storys mit
    Kindern; Story/Epic -> Task nur ohne Kinder); Labels und Verweise
    folgen. 3. Verschieben und Typwechsel über API und MCP antworten mit
    retype_required und dem Plan, wenn ein Typwechsel nötig ist, und führen
    ihn mit allow_retype in einer Transaktion aus; eine Vorschau ohne
    Änderung liefert denselben Plan. 4. Im Baum wird ohne nötigen Typwechsel
    ohne Rückfrage verschoben; sonst zeigt ein Dialog die betroffenen Items
    mit altem und neuem Label und die möglichen Zieltypen samt Abbrechen;
    Typ ändern im Detailpanel nutzt dieselben Regeln. 5. Domain-, API/MCP-
    und UI-Tests für Zustimmung, Ablehnung, Abbrechen und Fehlerfälle sind
    grün.
  - Summary: Folge zu Frage 10 in STORY-060: Umwandlung beim Ziehen mit
    Bestätigung, nach dem Live-Gang. Ziehen zwischen Projekten gibt es
    nicht.

- `EPIC-007` **Neuentwicklung als eigenständiges Tool**
  - Uid: c3a3ff5a-e320-4b04-af05-30257804a721.
  - Type: Epic.
  - Status: Open.
  - Created: 2026-10-10.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Das ToDo-Viewer wird von Grund auf neu entwickelt, mit einer
    tragfähigen Architektur und einem relationalen Datenmodell in der
    Datenbank. Es wird ein eigenständiges Produkt, das der KI eine API
    bietet und nicht mehr als Teil des KI-Harness entsteht.
  - Completion criteria: 1. Die Architektur ist dokumentiert und vom
    Projektinhaber freigegeben. 2. Das relationale Datenmodell ist
    umgesetzt. 3. Die neue Version deckt den Funktionsumfang von v0.8.7 ab,
    die API für die KI eingeschlossen. 4. Bestehende Backlogs lassen sich in
    die neue Datenbank übernehmen. 5. Das Tool läuft und ist dokumentiert,
    ohne Harness-Bezug. 6. Der Cutover ist erfolgt und der Altcode entfernt.
  - Summary: Kompletter Neubau des ToDo-Viewers mit besserer Architektur und
    relationaler Datenstruktur, als eigenständiges Tool mit API für die KI.

- `STORY-092` **MCP-Server fehlerarm für Agenten: Projektbindung, Labels, typisierte Felder**
  - Uid: 203401d1-c591-4737-9d56-60aea47a3fec.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-19.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Agent kann über MCP schreiben, ohne uids abzuschreiben, und
    ein Griff ins falsche Projekt fällt auf. Projekte lassen sich per Name
    oder uid ansprechen, Verweise in Feldern per Label, die Felder sind im
    Tool-Schema beschrieben, und jede Schreibantwort nennt Projekt, Label
    und Titel. Anlass: Claude_Harness stellt seine Skills erst auf MCP um,
    wenn das erfüllt ist (dort STORY-050).
  - Completion criteria: project/projects nehmen Name oder uid, mit
    einheitlichem Parameternamen in allen Tools (heute auch project_uid,
    target_project); parent und dependencies nehmen Labels im selben
    Projekt; ein unbekanntes Projekt in Filtern (z. B. backlog_index_lines,
    notes_index_lines) ergibt not_found statt einer leeren Liste; fields ist
    typisiert (Aufzählungen für type, status, priority; required_for_parent
    als Wahrheitswert) und steht in tools/list; jede Schreibantwort nennt
    Projektname, Label und Titel; optional bindet ein Tool
    workspace_use_project(folder) ein Standardprojekt an die MCP-Sitzung
    (Fehler no_project_bound nach Verbindungsverlust); Versionsprüfung, kein
    Anlegen von Projekten und kein endgültiges Löschen per MCP bleiben; der
    Systemtest test_harness_flow.py deckt die neuen Wege ab.
  - Summary: Verbesserungen am MCP-Server nach einer Prüfung aus
    Claude_Harness heraus: Agenten sollen keine uids mehr abschreiben müssen
    und Fehler früher und lesbarer sehen. Ergänzt STORY-081.

- `STORY-093` **Item-Notes mit Kopf und Protokoll: getrennt gespeichert, Stempel und Zustand**
  - Uid: 70cb741a-f5be-4430-951f-080f2fa6aa63.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: In progress.
  - Created: 2026-10-20.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Notes eines Backlog-Items bestehen aus einem Kopf mit dem
    geltenden Stand und einem Protokoll mit datierten Einträgen. Beide
    werden in eigenen Tabellen gespeichert und lassen sich unabhängig lesen
    und bearbeiten. Ein Stempel mit der Prüfsumme des Protokolls zeigt, ob
    der Kopf noch zum Protokoll passt. So kann der Harness (STORY-051 im
    Claude_Harness) den Kopf ohne das Protokoll laden und nach jeder
    Änderung prüfen lassen.
  - Completion criteria: 1. Kopf (1:1 zum Item, mit Inhalt, Stempel und
    eigener Revision) und Protokolleinträge (1:n, mit Datum, Thema,
    unverändertem Markdown-Text und Reihenfolge) liegen in eigenen Tabellen;
    die Migration zerlegt bestehende Notes ohne Textverlust, ein vorhandener
    Abschnitt `## Stand` wird zum Kopf. 2. Die Prüfsumme wird nach der
    gemeinsamen Definition in `format.md` des Harness berechnet; ein Test
    mit gemeinsamen Beispielen zeigt dasselbe Ergebnis wie `backlog.py`. 3.
    Es gibt Endpunkte (API und MCP) zum Lesen des Kopfs ohne Protokoll, zum
    Ersetzen und zum Bestätigen des Kopfs (beide setzen den Stempel); `POST
    …/notes` nimmt optional einen neuen Kopf mit; `GET/PUT` auf
    `<ID>_notes.md` arbeiten weiter auf der zusammengesetzten Datei. 4.
    `show` und `index` melden den Zustand des Kopfs (`current`, `stale`,
    `missing`); schreibende Antworten auf Notes weisen auf einen veralteten
    Kopf hin. 5. Der Spiegel setzt die Datei aus Titelzeile (immer aus dem
    aktuellen Item), Kopf, Stempelzeile und Protokoll zusammen und zerlegt
    sie beim Einlesen wieder, den Stempel aus der Datei eingeschlossen. 6.
    Die Oberfläche zeigt den Kopf oben, markiert einen veralteten Kopf und
    lässt das Protokoll einklappen. 7. Vertragstests decken Endpunkte,
    Prüfsumme, Migration und Spiegel in beide Richtungen ab; die technische
    Dokumentation ist nachgezogen.
  - Summary: Die Notizen zu einem Item bekommen oben einen Kopf mit dem
    aktuellen Stand und darunter das Protokoll. Beide werden getrennt
    gespeichert, und der Viewer zeigt an, wenn der Kopf nach neuen Einträgen
    nicht mehr geprüft wurde.

- `TASK-045` **Kopf und Protokoll der Item-Notes in der Oberfläche**
  - Uid: 7e806f03-76ea-4c41-83e8-6e6d7f09acd6.
  - Type: Task.
  - Parent: `STORY-093`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-20.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-044`.
  - Goal: In der Detailansicht eines Items stehen bei den Notes oben der
    Kopf und darunter das einklappbare Protokoll; ein veralteter oder
    fehlender Kopf ist markiert.
  - Completion criteria: 1. Kopf oben, Protokoll standardmäßig eingeklappt.
    2. Markierung bei stale oder missing als Symbol mit Tooltip. 3. Daten
    über die RTK-Query-API, Neuladen nach backlog.document.changed, Typen
    aus OpenAPI erzeugt. 4. Client-Tests mit Test-IDs.
  - Summary: Die Oberfläche zeigt den aktuellen Stand der Notes oben und
    markiert, wenn er nicht mehr geprüft ist.

- `STORY-094` **Notiz- und Spec-Dokumente löschen: Lösch-Befehl in API und MCP**
  - Uid: 564c047d-2845-4699-a295-e8b7f1bf680d.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-20.
  - Area: Backend-API.
  - Priority: Urgent.
  - Dependencies: None.
  - Goal: Für Notiz- und Spec-Dokumente eines Items gibt es bisher keinen
    Lösch-Befehl; nur Ersetzen mit put-doc ist möglich. Man muss ein
    Dokument deshalb bis auf die Überschrift leeren und kann die Kurzfassung
    (Summary) nicht entfernen. Es soll ein Lösch-Befehl für Notiz- und
    Spec-Dokumente (inkl. Themen-Specs) über API, MCP und Harness-Helfer
    geben, der auch die zugehörige Kurzfassung entfernt, wenn kein Dokument
    mehr übrig ist.
  - Completion criteria: Ein Notiz- oder Spec-Dokument lässt sich über API
    und MCP löschen; die Kurzfassung des Items wird mit dem letzten
    Notizdokument entfernt; Spiegel und
    Papierkorb-/Wiederherstellungsverhalten sind geklärt; Tests und Doku
    (API-Beschreibung, Harness-Skill api.md) sind angepasst.
  - Summary: Dringend: Notiz- und Spec-Dokumente können bisher nicht
    gelöscht, nur geleert werden. Ein Lösch-Befehl fehlt.
