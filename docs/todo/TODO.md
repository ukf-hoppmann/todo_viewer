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
    oder ein Memo anlegen. Der Knoten bleibt stehen und das Ergebnis hängt
    daran; mit einem Item wechselt der Knoten seinen Zustand von Idee zu
    geplant, ein Memo ändert den Zustand nicht.
  - Completion criteria: 1. Im Detail eines Knotens legt eine Aktion ein Item
    (Epic, Story oder Task) oder ein Memo an, mit Titel und Text des Knotens
    als Vorschlag, und hängt das Ergebnis an den Knoten. Den Typ legt der
    Mensch oder die KI je Knoten fest.
    2. Ein ganzer Ast lässt sich mit Vorschau überführen; Typ und Beziehung
    (Parent-Child oder Abhängigkeit) wählt der Mensch oder die KI für jeden
    Knoten einzeln, ohne Vorgabe aus Ebene oder Tiefe; Titel sind vor dem
    Anlegen änderbar.
    3. Was die Struktur des Backlogs nicht erlaubt, zeigt die Vorschau, bevor
    etwas angelegt wird.
    4. Domain-, API- und UI-Tests sind grün.
  - Summary: Aus einer gesammelten Idee einen Backlog-Eintrag oder ein Memo
    machen, einzeln je Knoten oder für einen ganzen Ast mit Vorschau. Die Idee
    bleibt in der Map stehen; mit einem Item zeigt sie, dass sie eingeplant
    ist.

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
    3. Die Regel für die KI steht in den MCP-Tool-Beschreibungen des Viewers,
    und der Owner hat einen fertigen Prompt, mit dem er sie an Claude_Harness
    übergibt.
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
    Maps), Knoten, Platzierungen (auch mehrere je Knoten und entfernte) und
    Zuordnungen ist beschrieben und mit Golden-Files abgedeckt; eine
    Cloud-Sitzung kann freie Maps füllen und Äste umhängen oder übertragen.
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
  - Goal: Die Einordnung eines Items nach Themen läuft nur noch über die
    Knoten der Mindmap; das Feld Area entfällt ganz, ohne abgeleiteten
    Ersatzwert. Die Themenbäume der Projekte entstehen einmalig durch eine KI
    aus den vorhandenen Items und werden nicht von Hand aufgebaut.
  - Completion criteria: 1. Das Feld Area entfällt ganz, auch als abgeleiteter
    Wert; die Schichten Web-UI und Backend-API sind keine eigene Einordnung
    mehr. Wo Area stand, zeigt die Oberfläche den Namen des Themas (bei Bedarf
    mit Pfad), und ein Filter nach einem Thema schließt seine Unterthemen ein.
    2. Der Owner hat einen fertigen Prompt, mit dem er in jedem Projekt eine
    KI den Themenbaum aus den vorhandenen Items erzeugen und die Items
    zuordnen lässt; die KI arbeitet aus Titel, Ziel und Text der Items, kein
    Item geht verloren.
    3. Das Feld wird direkt entfernt; Anzeige, Filter, API, MCP und
    Markdown-Spiegel kommen ohne Area aus. Eine Markdown-Datei, die das Feld
    noch enthält, lässt sich weiter importieren: das Feld wird ignoriert und
    führt nicht zu einem Fehler.
    4. Die Dokumentation und die Harness-Regeln sind angepasst.
    5. Domain-, API- und UI-Tests sind grün.
  - Summary: Das Etikett „Area“ an den Items verschwindet. Die Mindmap
    übernimmt die Einordnung nach Themen. Den ersten Themenbaum baut eine KI
    aus den vorhandenen Items, du bekommst dafür einen fertigen Prompt.
