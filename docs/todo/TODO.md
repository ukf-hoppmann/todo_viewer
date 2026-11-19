# Project Backlog

Active project work: open, in progress, or awaiting a project-owner decision.
Completed and rejected items are moved to `archive.md`; per-item notes and
specs live in `items/<ID>/`.

Format: Claude_Harness backlog format version 2. The rules are defined in
`docs/techdocs/interfaces.md` of the ToDo Viewer.

## Work items

- `EPIC-008` **Mindmap: Themen-Gerippe zum Brainstormen und als Übersicht des Backlogs**
  - Uid: 039478f4-0b3b-4807-8fd3-36fec9a4d372.
  - Type: Epic.
  - Status: In progress.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Viewer bekommt eine Mindmap als eigenes Datenmodell: ein Gerippe
    aus Themenknoten, in dem man Ideen sammelt und ordnet und an das
    Backlog-Items und Memos verlinkt werden. Sie zeigt mit wenigen Schritten,
    was es gibt und was kommt, ohne dass die Menge der Tasks die Darstellung
    füllt.
  - Completion criteria: 1. Je Projekt gibt es einen Themenbaum, in dem Knoten
    angelegt, geordnet und mit Notizen versehen werden.
    2. Items und Memos lassen sich an Knoten hängen; Knoten zeigen Anzahl,
    Fortschritt und einen abgeleiteten Zustand, Items sind keine eigenen
    Knoten.
    3. Fokus auf einen Knoten, Einzel- und Gesamtansicht sowie runde und
    seitliche Anordnung sind umschaltbar.
    4. Freie Maps und das Umhängen und Übertragen von Ästen zwischen Bäumen
    funktionieren, ohne dass etwas kopiert wird.
    5. Aus einem Ideen-Knoten lässt sich ein Backlog-Item anlegen, und die KI
    kann über API und MCP zuordnen und Knoten vorschlagen.
    6. Die Umsetzung lief in einem eigenen Branch und ist nach Freigabe des
    Owners zusammengeführt.
  - Summary: Eine Mindmap im Viewer: Themen sammeln und ordnen,
    Backlog-Einträge und Memos daran hängen und so schnell sehen, was es gibt
    und was kommt. Sie ist nur ein Gerippe und verlinkt; kopiert wird nichts.

- `EPIC-009` **Nachbesserungen am Neubau**
  - Uid: b22089d8-7efd-4395-9c14-7643501c0fa8.
  - Type: Epic.
  - Status: Open.
  - Created: 2026-11-17.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Folgearbeiten am ToDo-Viewer, die beim Neubau (`EPIC-007`) bewusst
    zurückgestellt wurden und nach dem Umstieg und der Entfernung des Altcodes
    anstehen.
  - Completion criteria: 1. Die Stories des Epics sind abgeschlossen oder
    verworfen.
  - Summary: Sammelstelle für Verbesserungen, die nach dem Neubau folgen.

- `STORY-102` **Freie Maps und Äste zwischen Bäumen umhängen und übertragen**
  - Uid: 5e2233a4-bac0-482b-8890-66e0855fa8e0.
  - Type: Story.
  - Parent: `EPIC-008`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-099`, `STORY-100`.
  - Goal: Neben dem Projektbaum kann ein Projekt freie Maps haben, etwa zum
    Brainstormen vor der Umsetzung. Äste lassen
    sich zwischen Bäumen umhängen (aus A weg, in B drin) oder übertragen
    (derselbe Ast in A und B), ohne zu kopieren.
  - Completion criteria: 1. Freie Maps lassen sich in einem Projekt anlegen,
    auswählen, umbenennen und löschen; die Maps eines Projekts stehen als Liste
    in der Seitenleiste, die Gesamtansicht zeigt nur Projektbäume.
    2. Umhängen geht innerhalb eines Baums und zwischen Bäumen; Übertragen
    geht nur zwischen Bäumen, ein Knoten steht höchstens einmal je Baum; beides
    nur innerhalb eines Projekts. Umhängen und Übertragen gehen auch über API
    und MCP, damit die KI Äste verschieben kann.
    3. Ein übertragener Ast ist markiert; „hier entfernen“ nimmt ihn nur aus
    diesem Baum, „Knoten löschen“ überall.
    4. Summen zählen ein Item auch dann nur einmal, wenn sein Ast über zwei
    Wege unter derselben Wurzel liegt.
    5. Domain-, API- und UI-Tests sind grün.
  - Summary: Mehrere Maps je Projekt und die Möglichkeit, einen Ast in eine
    andere Map zu hängen oder ihn in beiden zu führen, damit die Planungs-Map
    nicht schrumpft, wenn die Umsetzungs-Map wächst.

- `TASK-062` **Mindmap: freie Maps je Projekt**
  - Uid: 57a6b175-25bd-4d1e-8f8b-7fc05a044760.
  - Type: Task.
  - Parent: `STORY-102`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Projekt kann neben seinem Projektbaum freie Maps haben; sie
    lassen sich anlegen, auswählen, umbenennen und löschen.
  - Completion criteria: 1. Server und Oberfläche führen mehrere Bäume je
    Projekt.
    2. Die Maps eines Projekts stehen als Liste in der Seitenleiste (Projektbaum
    zuerst); die Gesamtansicht zeigt nur Projektbäume.
    3. API- und UI-Tests sind grün.

- `TASK-063` **Mindmap: Äste zwischen Bäumen umhängen und übertragen**
  - Uid: fa9495d7-cad8-4d2e-8db0-98fdf2a6d88d.
  - Type: Task.
  - Parent: `STORY-102`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-062`.
  - Goal: Ein Ast lässt sich in einen anderen Baum umhängen oder dorthin
    übertragen, sodass er in beiden steht; übertragene Äste sind markiert und
    lassen sich nur hier entfernen oder ganz löschen.
  - Completion criteria: 1. Der Server legt eine zweite Platzierung an und
    weist einen Knoten zweimal im selben Baum, Kreise und Ziele in anderen
    Projekten ab. Umhängen und Übertragen stehen als API und als MCP-Werkzeug
    bereit, damit die KI Äste verschieben kann.
    2. Die Oberfläche bietet „umhängen“ und „übertragen“ mit Wahl des Ziels
    (Kontextmenü und Ziehen auf die Map-Liste),
    markiert übertragene Äste und trennt „hier entfernen“ von „Knoten
    löschen“.
    3. Summen zählen jedes Item einmal; Domain-, API- und UI-Tests sind grün.

- `STORY-103` **Ideen-Knoten ins Backlog überführen**
  - Uid: 688f456a-295f-453d-a6cd-39d7bb6c6aa8.
  - Type: Story.
  - Parent: `EPIC-008`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-100`.
  - Goal: Aus einem Knoten ohne Items lässt sich direkt ein Backlog-Item
    anlegen. Der Knoten bleibt stehen, das neue Item hängt daran, und der
    Knoten wechselt dadurch seinen Zustand von Idee zu geplant.
  - Completion criteria: 1. Im Detail eines Knotens legt eine Aktion ein Epic,
    eine Story oder einen Task an, mit Titel und Text des Knotens als
    Vorschlag, und hängt das Item an den Knoten.
    2. Ein ganzer Ast lässt sich mit Vorschau überführen; Typen und Titel sind
    vor dem Anlegen änderbar.
    3. Was die Struktur des Backlogs nicht erlaubt, zeigt die Vorschau, bevor
    etwas angelegt wird.
    4. Domain-, API- und UI-Tests sind grün.
  - Summary: Aus einer gesammelten Idee mit einem Klick einen Backlog-Eintrag
    machen. Die Idee bleibt in der Map stehen und zeigt dann, dass sie
    eingeplant ist.

- `STORY-104` **KI ordnet neue Items der Mindmap zu und schlägt Knoten vor**
  - Uid: 5b8e795e-adf2-49e3-9cb8-6a2de4a49101.
  - Type: Story.
  - Parent: `EPIC-008`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-100`.
  - Goal: Wenn die KI ein Item anlegt, überlegt sie, an welchen Knoten es
    gehört, und hängt es dorthin. Passt keiner, schlägt sie einen Knoten oder
    Unterknoten vor und legt ihn nach Bestätigung an. So wird die Map nebenbei
    gefüllt, ohne zu wuchern.
  - Completion criteria: 1. Über API und MCP kann die KI den Themenbaum lesen,
    ein Item zuordnen und einen Knoten anlegen.
    2. Ein von der KI vorgeschlagener Knoten entsteht erst nach Bestätigung
    des Owners; ohne passenden Knoten landet das Item unter „Nicht
    zugeordnet“.
    3. Die Regel für die KI ist beschrieben und an Claude_Harness übergeben.
    4. Der Systemtest deckt Zuordnen und Vorschlagen ab.
  - Summary: Die KI sortiert neue Backlog-Einträge selbst in die Map ein und
    darf neue Themen vorschlagen, legt sie aber erst an, wenn du zustimmst.

- `STORY-105` **Mindmap im Markdown-Spiegel: Dateiformat und Sync**
  - Uid: fad60a4f-0990-4d9f-8036-b123bb43a596.
  - Type: Story.
  - Parent: `EPIC-008`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-100`, `STORY-102`.
  - Goal: Die Mindmap geht wie Backlog und Memos als Markdown über den Sync
    mit, damit sie über Git zwischen Rechnern wandert und die KI auch in
    Cloud-Sitzungen, die nur auf den Dateien arbeiten, zuordnen kann.
  - Completion criteria: 1. Ein Dateiformat für Bäume (Projektbäume und freie
    Maps), Knoten, Platzierungen und Zuordnungen ist beschrieben und mit
    Golden-Files abgedeckt; eine Cloud-Sitzung kann freie Maps füllen.
    2. Der Sync nimmt die Mindmap mit Vorschau und Konflikten in denselben
    Dialog auf.
    3. Die Regeln für den Datei-Modus sind an Claude_Harness übergeben.
  - Summary: Die Map auch als Dateien speichern, damit sie über Git mitgeht
    und die KI in der Cloud damit arbeiten kann. Gewünscht, aber kein Muss.

- `STORY-086` **Baum: Umwandeln-Dialog beim Ziehen**
  - Uid: 9ccc4f8d-f897-4fdd-bc8d-a67da5569d3f.
  - Type: Story.
  - Parent: `EPIC-009`.
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

- `STORY-092` **MCP-Server fehlerarm für Agenten: Projektbindung, Labels, typisierte Felder**
  - Uid: 203401d1-c591-4737-9d56-60aea47a3fec.
  - Type: Story.
  - Parent: `EPIC-009`.
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

- `STORY-106` **Area durch die Mindmap ersetzen**
  - Uid: 2583a192-6eb8-481d-8637-86eb8408fa9a.
  - Type: Story.
  - Parent: `EPIC-008`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-11-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-100`.
  - Goal: Die Einordnung eines Items nach Themen läuft über die Knoten der
    Mindmap und nicht mehr über das Feld Area. Bestehende Areas gehen ohne
    Verlust in Knoten über.
  - Completion criteria: 1. Die Art des Ersatzes (Feld entfällt oder wird aus
    dem Knoten abgeleitet) ist mit dem Owner geklärt und in der Spec
    festgehalten.
    2. Bestehende Areas werden einmalig in Knoten umgewandelt und die Items
    zugeordnet, ohne dass etwas verloren geht.
    3. Anzeige, Filter, API, MCP und Markdown-Spiegel kommen ohne Area aus
    oder zeigen den abgeleiteten Wert.
    4. Die Dokumentation und die Harness-Regeln sind angepasst.
    5. Domain-, API- und UI-Tests sind grün.
