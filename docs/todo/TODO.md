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
    3. Die Regeln für den Datei-Modus sind beschrieben, und der Owner hat einen
    fertigen Prompt, mit dem er sie an Claude_Harness übergibt.
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
    mehr. Das Thema eines Items zeigt die Oberfläche im Abschnitt „Knoten“ der
    Mindmap im Detail des Items; ein abgeleiteter Wert oder eine Spalte dafür
    entfällt.
    2. Der Owner hat einen fertigen Prompt, mit dem er in jedem Projekt eine
    KI den Themenbaum aus den vorhandenen Items erzeugen und die Items
    zuordnen lässt; die KI arbeitet aus Titel, Ziel und Text der Items, kein
    Item geht verloren.
    3. Das Feld wird direkt entfernt; Anzeige, API, MCP, Index-Zeilen und
    Markdown-Spiegel kommen ohne Area aus; der Spiegel schreibt das Format
    Version 3 und liest Version 2 und 3. Eine Markdown-Datei, die das Feld noch
    enthält, lässt sich weiter importieren: das Feld wird ignoriert und führt
    nicht zu einem Fehler.
    4. Die Dokumentation ist angepasst, und der Owner hat einen fertigen
    Prompt, mit dem er Claude_Harness anpasst.
    5. Domain-, API- und UI-Tests sind grün.
  - Summary: Das Etikett „Area“ an den Items verschwindet. Die Mindmap
    übernimmt die Einordnung nach Themen. Den ersten Themenbaum baut eine KI
    aus den vorhandenen Items, du bekommst dafür einen fertigen Prompt.

- `TASK-068` **Backlog-Spiegel: Format Version 3 ohne Area**
  - Uid: 5490cf98-8cec-4c5a-94a5-c0c5f95c120f.
  - Type: Task.
  - Parent: `STORY-106`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Spiegel des Backlogs (`TODO.md`, `archive.md`) schreibt das
    Format Version 3 ohne das Feld Area und liest die Versionen 2 und 3. Ein
    Feld Area in einer gelesenen Datei wird ignoriert und führt nie zu einem
    Fehler.
  - Completion criteria: 1. Der Codec schreibt die Kennung „backlog format
    version 3“ und kein Feld Area; die übrigen Felder behalten ihre
    Reihenfolge.
    2. Der Codec liest Version 2 und 3; ein Feld Area wird in beiden
    ignoriert, ohne Fehler; jede andere Versionsnummer ergibt weiter
    `format_version`.
    3. Der Teilnehmer lädt und schreibt Area nicht mehr; Items aus Dateien
    bekommen `area=None`.
    4. Golden-Files für Version 3 liegen unter `tests/fixtures/mirror-v3/`
    (gültige und ungültige Beispiele); `tests/fixtures/mirror-v2/` bleibt
    unverändert und prüft das Lesen von Version 2.
    5. Das Format ist in `docs/techdocs/interfaces.md` (Abschnitt
    „Backlog-Einträge“) als Version 3 beschrieben: Pflichtfelder ohne Area,
    Area wird gelesen und ignoriert, Unterschied zu Version 2.
    6. Alle Tests sind grün.
  - Summary: Die Backlog-Dateien kommen ohne das Feld Area aus und heißen
    Format Version 3. Alte Dateien mit Area lassen sich weiter einlesen.

- `TASK-069` **Area ist beim Anlegen nicht mehr Pflicht**
  - Uid: 945d33d7-a499-4bbf-a044-2bab0b29ba18.
  - Type: Task.
  - Parent: `STORY-106`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Items und Beförderungen von Memos lassen sich ohne Area anlegen.
    Area bleibt in dieser Task noch ein erlaubtes, optionales Feld, damit die
    Oberfläche in der nächsten Task ohne Bruch umgebaut werden kann.
  - Completion criteria: 1. `create_item` verlangt nur noch `title`, `goal`
    und `completion_criteria`; `area` darf fehlen und ist dann `None`.
    2. `promote_memo` verlangt nur noch `goal` und `completion_criteria`.
    3. Beschreibungen der HTTP-Routen und MCP-Tools nennen Area nicht mehr als
    Pflicht.
    4. Vorhandenes Verhalten mit Area (Anlegen, Ändern, Index, Spiegel) bleibt
    unverändert.
    5. Unit- und Integrationstests sind grün; ein Test legt ein Item ohne Area
    an, einer befördert ein Memo ohne Area.
  - Summary: Beim Anlegen eines Items muss kein Bereich mehr angegeben werden.
    Das Feld bleibt vorerst, damit die Oberfläche in einem eigenen Schritt
    umgebaut werden kann.

- `TASK-070` **Oberfläche ohne Area**
  - Uid: 84329ee9-90ad-4214-bb27-46cadae823b8.
  - Type: Task.
  - Parent: `STORY-106`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-11-23.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-069`.
  - Goal: Die Oberfläche zeigt, verlangt und ändert Area nirgends mehr: nicht
    im Item-Formular, nicht im Detail eines Items, nicht beim Befördern eines
    Memos.
  - Completion criteria: 1. Das Formular zum Anlegen und Ändern eines Items
    hat kein Feld Area; es sendet kein `area`.
    2. Das Detail eines Items zeigt und ändert Area nicht mehr; der Dialog
    „Neuer Bereich“ entfällt.
    3. Der Dialog zum Befördern eines Memos fragt Area nicht mehr ab und
    sendet kein `area`.
    4. Der API-Zugriff `listAreas` (`backlog/areas`) und alle Übersetzungen zu
    Area (de und en) sind entfernt.
    5. Der Abschnitt „Knoten“ des Mindmap-Plugins im Detail eines Items (Slot
    `backlog.item-detail`) steht weiter dort, wo Area stand, und zeigt das
    Thema des Items.
    6. Typprüfung, Lint und alle Client-Tests sind grün.
  - Summary: In der Oberfläche gibt es keinen Bereich mehr. Das Thema eines
    Items steht im Abschnitt „Knoten“ der Mindmap im Detail.

- `TASK-071` **Area aus Server und Datenbank entfernen**
  - Uid: 8a9a4732-2bd1-4fe4-baa2-db84d44c3bbd.
  - Type: Task.
  - Parent: `STORY-106`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-068`, `TASK-070`.
  - Goal: Das Feld Area gibt es in Domain, Anwendungsfällen, HTTP, MCP und
    Datenbank nicht mehr. Bestehende Daten bleiben bis auf die Area-Werte
    erhalten; ein Import alter Daten oder Dateien mit dem Feld läuft ohne
    Fehler.
  - Completion criteria: 1. `Item`, `ItemOut`, `IndexItem`, `CreateItem`,
    `UpdateItem` und die Operationen kennen kein `area` mehr; ein `area` in
    den Eingaben wird wie jedes unbekannte Feld abgewiesen.
    2. Die Index-Zeilen für Agenten (`backlog_index_lines`) lauten `ID | Type
    | Status | Title | Parent | Notes`; `list_areas` (HTTP und MCP
    `backlog_list_areas`) entfällt.
    3. Die Beförderung von Memos kennt kein `area` mehr.
    4. Eine Migration entfernt die Spalte `area_uid` und die Tabelle
    `backlog_areas` vorwärts mit Backup; alle anderen Felder der Items bleiben
    gleich; ein Test lädt eine Datenbank der Vorversion mit Daten und prüft
    das.
    5. Der Import aus dem alten Viewer ignoriert die Bereiche, ohne Fehler.
    6. Die generierten Client-Typen sind neu erzeugt und eingecheckt; `npx tsc
    -b` ist grün.
    7. Technische Doku (`docs/techdocs/interfaces.md`, `neubau-server.md`,
    `README.md`) nennt Area nicht mehr (außer als ignoriertes Feld im
    Dateiformat).
    8. Alle Tests und `scripts/check-next.sh` sind grün.
  - Summary: Das Feld Area verschwindet endgültig aus Server, Datenbank und
    Schnittstellen. Alles andere an den Items bleibt erhalten.

- `TASK-072` **Prompts: Themenbaum aus den Items erzeugen und Claude_Harness anpassen**
  - Uid: c79d3455-4859-4f8f-9b35-8a2804c99101.
  - Type: Task.
  - Parent: `STORY-106`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-071`.
  - Goal: Der Owner bekommt zwei fertige Prompts: einen, mit dem eine KI in
    jedem Projekt den Themenbaum aus den vorhandenen Items erzeugt und die
    Items zuordnet, und einen, mit dem Claude_Harness auf Format Version 3
    ohne Area angepasst wird.
  - Completion criteria: 1. Der Prompt für den Themenbaum steht als Datei in
    der Spec dieser Task (`…_spec_prompt-baum.md`) und im Abschluss der
    Session als Text beim Owner.
    2. Er arbeitet nur mit den Werkzeugen, die es nach der Entfernung gibt
    (MCP-Tools des Viewers), und ist gegen den echten Server mit einem
    Beispielprojekt ausprobiert: ein Projekt mit Items ohne Themen ergibt
    danach einen Baum, und kein Item geht verloren oder wird verändert.
    3. Der Prompt für Claude_Harness steht als Datei in der Spec dieser Task
    (`…_spec_prompt-harness.md`) und im Abschluss der Session als Text beim
    Owner; er nennt alle Änderungen am Format und an den Schnittstellen.
    4. Die KI übergibt nichts selbst an Claude_Harness.
  - Summary: Du bekommst zwei Prompts: einen, der in jedem Projekt den
    Themenbaum aus den Items erzeugt, und einen, mit dem du Claude_Harness auf
    das Format ohne Area bringst.

- `TASK-073` **Server: aus einem Knoten ein Item oder ein Memo anlegen**
  - Uid: 27f711f2-355e-4d1f-81a2-18569ebbdca6.
  - Type: Task.
  - Parent: `STORY-103`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-071`.
  - Goal: Über HTTP und MCP lässt sich aus einem Knoten ein Backlog-Item oder
    ein Memo anlegen; das Ergebnis hängt danach am Knoten. Typ des Items und
    seine Felder bestimmt der Aufrufer (Mensch oder KI).
  - Completion criteria: 1. Die Operation `create_item_at_node` legt ein Item
    (Epic, Story oder Task) mit den gegebenen Feldern an und hängt es an den
    Knoten; fehlt `title`, gilt der Titel des Knotens, fehlt `goal`, gilt der
    Text des Knotens; `completion_criteria` sind Pflicht.
    2. Die Operation `create_memo_at_node` legt ein Memo an (Pflicht
    `summary`, Standard der Titel des Knotens; `body` Standard der Text des
    Knotens) und verlinkt es mit dem Knoten.
    3. Ein Knoten im Papierkorb oder eines anderen Projekts wird abgewiesen;
    scheitert das Anhängen nach dem Anlegen, nennt der Fehler das angelegte
    Item, das dann unter „Nicht zugeordnet“ steht.
    4. Mit einem Item wechselt der Knoten seinen Zustand von Idee zu geplant;
    ein Memo ändert den Zustand nicht.
    5. Beide Operationen sind als HTTP-Route und als MCP-Tool vorhanden; die
    generierten Client-Typen sind neu erzeugt.
    6. Unit-Tests mit Fakes der neuen Ports und Integrationstests gegen die
    echten Plugins sind grün; die Import-Regeln (`server/pyproject.toml`)
    kennen die neue Abhängigkeit.
  - Summary: Aus einem Knoten der Mindmap lässt sich ein Item oder ein Memo
    anlegen, das gleich am Knoten hängt. Das ist die Grundlage für die
    Oberfläche und für die KI.

- `TASK-074` **Server: einen Ast mit Vorschau ins Backlog überführen**
  - Uid: d84f4d62-8979-4ce4-a2d9-b6b5fa3750b7.
  - Type: Task.
  - Parent: `STORY-103`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-073`.
  - Goal: Ein ganzer Ast lässt sich mit einer Vorschau ins Backlog überführen.
    Für jeden Knoten legt der Aufrufer Item (mit Typ) oder Memo fest und wie
    das Ergebnis zu den anderen Knoten steht (Parent-Child oder Abhängigkeit).
    Was die Struktur des Backlogs nicht erlaubt, nennt die Vorschau, bevor
    etwas angelegt wird.
  - Completion criteria: 1. `preview_branch_transfer` prüft einen Plan für
    einen Ast, ohne etwas zu schreiben, und nennt je Eintrag und für den
    ganzen Plan die Probleme mit stabilem Code.
    2. `transfer_branch` legt den Plan an, nur wenn die Vorschau ohne Probleme
    ist: Items und Memos in der Reihenfolge ihrer Beziehungen, jedes an seinem
    Knoten, mit Parent und Abhängigkeiten.
    3. Die Regeln des Backlogs (erlaubte Parent-Typen, keine Zyklen, kein
    Parent in geschlossenem Zustand, Pflichtfelder) werden mit demselben
    Regelsatz geprüft, der beim Anlegen gilt, nicht in der Mindmap noch einmal
    geschrieben.
    4. Es gibt keinen Automatismus: ohne Angabe für einen Knoten wird nichts
    angelegt; es gibt keine Vorgabe aus Ebene oder Tiefe.
    5. Scheitert das Anlegen mittendrin, nennt das Ergebnis, was angelegt
    wurde und was nicht (kein Rückbau).
    6. Beide Operationen sind HTTP und MCP; Unit-, Integrations- und der
    Harness-Systemtest sind grün.
  - Summary: Ein ganzer Ast der Mindmap wird mit Vorschau ins Backlog
    überführt. Du oder die KI legen je Knoten fest, was daraus wird; die
    Vorschau meldet, was nicht geht.

- `TASK-075` **Oberfläche: im Detail eines Knotens ein Item oder Memo anlegen**
  - Uid: 69e694e4-d8bc-4cd2-ba89-29d4efadc56a.
  - Type: Task.
  - Parent: `STORY-103`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-073`.
  - Goal: Im Detail eines Knotens legt eine Aktion ein Item oder ein Memo an,
    mit Titel und Text des Knotens als Vorschlag. Das Ergebnis hängt am
    Knoten.
  - Completion criteria: 1. Das Detail eines Knotens bietet „Item anlegen“ und
    „Memo anlegen“; beide nicht für Knoten im Papierkorb.
    2. Der Dialog für ein Item fragt Typ, Titel (vorbelegt mit dem
    Knotentitel), Ziel (vorbelegt mit dem Knotentext) und Abschlusskriterien
    (Pflicht, leer); der Dialog für ein Memo fragt Zusammenfassung
    (Knotentitel) und Text (Knotentext).
    3. Nach dem Anlegen erscheint das Ergebnis im Detail des Knotens, und der
    Zustand des Knotens ist neu berechnet (Item: geplant; Memo: unverändert).
    4. Serverfehler erscheinen im Dialog, der Dialog bleibt offen und behält
    die Eingaben.
    5. Typprüfung, Lint und Client-Tests sind grün; Texte in de und en.
  - Summary: Im Detail eines Knotens gibt es „Item anlegen“ und „Memo
    anlegen“. Titel und Text des Knotens sind der Vorschlag, das Ergebnis
    hängt gleich am Knoten.

- `TASK-076` **Oberfläche: einen Ast mit Vorschau ins Backlog überführen**
  - Uid: f415cc3d-9c46-4f3a-8f0c-cfdd5f472ec1.
  - Type: Task.
  - Parent: `STORY-103`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-074`, `TASK-075`.
  - Goal: Ein Ast lässt sich in einem Dialog überführen: je Knoten wählt der
    Mensch Item (Typ), Memo oder nichts und die Beziehung zu den anderen
    Knoten; die Vorschau zeigt Probleme, bevor etwas angelegt wird.
  - Completion criteria: 1. Im Menü eines Knotens öffnet „Ast überführen“
    einen Dialog mit dem Ast als Baum; jeder Knoten hat eine Wahl (nichts,
    Item mit Typ, Memo) und Felder für Titel, Ziel und Abschlusskriterien.
    2. Je Item-Knoten lässt sich die Beziehung wählen: „Kind von“ (ein Knoten
    des Plans oder ein vorhandenes Item), „hängt ab von“ (mehrere) oder keine;
    es gibt keine Vorbelegung aus Ebene oder Tiefe.
    3. Die Vorschau läuft live gegen den Server (`preview_branch_transfer`)
    und markiert Probleme am Knoten; „Überführen“ ist nur ohne Probleme
    möglich.
    4. Nach dem Überführen zeigt der Dialog das Ergebnis je Knoten (angelegt,
    Fehler, nicht versucht) und die Knoten tragen ihren neuen Zustand.
    5. Typprüfung, Lint und Client-Tests sind grün; Texte in de und en.
  - Summary: Ein ganzer Ast wird in einem Dialog überführt. Du wählst je
    Knoten, was daraus wird und wie die Teile zusammenhängen, und siehst
    vorher, was nicht geht.

- `TASK-077` **MCP-Tools nennen die Regel zum Zuordnen und Vorschlagen**
  - Uid: 33e20e2a-7ffb-444a-aea8-b79f27aa9361.
  - Type: Task.
  - Parent: `STORY-104`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-073`.
  - Goal: Die Beschreibungen der MCP-Tools des Viewers sagen einer KI, wie sie
    ein neues Item einem Knoten zuordnet: Baum lesen, passenden Knoten wählen,
    das Item an ihm anlegen; passt keiner, im Gespräch einen Knoten
    vorschlagen und ihn erst nach der Zustimmung des Owners anlegen; ohne
    Zustimmung bleibt das Item unter „Nicht zugeordnet“.
  - Completion criteria: 1. Die Beschreibungen von `backlog_create_item`,
    `mindmap_get_tree`, `mindmap_create_node`, `mindmap_assign_item` und
    `mindmap_create_item_at_node` nennen die Regel knapp und gleichlautend
    (ein gemeinsamer Text, an einer Stelle gepflegt).
    2. Ein Test hält fest, dass die Beschreibungen die Regel enthalten
    (Schlüsselaussagen: Baum lesen, Knoten wählen oder vorschlagen, nur nach
    Bestätigung anlegen, sonst „Nicht zugeordnet“).
    3. Über HTTP und MCP kann eine KI den Themenbaum lesen, ein Item zuordnen
    und einen Knoten anlegen; kein neues Werkzeug ist nötig (es gibt
    `get_tree`, `assign_item`, `create_node`, `create_item_at_node`).
    4. Das Verhalten ohne passenden Knoten (Item unter „Nicht zugeordnet“,
    kein erfundener Knoten) bleibt in `get_tree` sichtbar.
    5. Alle Tests sind grün.
  - Summary: Die KI erfährt über die Beschreibungen der Werkzeuge, dass sie
    neue Items einem Knoten zuordnen und Knoten nur nach deiner Zustimmung
    anlegen soll.

- `TASK-078` **Systemtest Zuordnen und Vorschlagen; Prompt für Claude_Harness**
  - Uid: ee66e6e2-4d92-4d00-9415-52cd63d7d378.
  - Type: Task.
  - Parent: `STORY-104`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-077`.
  - Goal: Der Systemtest über MCP deckt das Zuordnen und das Vorschlagen ab.
    Der Owner bekommt den fertigen Prompt, mit dem er die Regel in
    Claude_Harness übergibt.
  - Completion criteria: 1. Der Systemtest über MCP liest den Themenbaum, legt
    ein Item an einem vorhandenen Knoten an, legt nach einem simulierten „Ja“
    einen Knoten an und hängt ein Item daran, und lässt ein Item ohne
    passenden Knoten unter „Nicht zugeordnet“ stehen, ohne einen Knoten zu
    erfinden.
    2. Der Prompt für Claude_Harness steht als Datei in der Spec dieser Task
    (`…_spec_prompt-harness.md`) und im Abschluss der Session als Text beim
    Owner; er beschreibt die Regel und die Werkzeuge so, dass Claude_Harness
    sie in seinen Skill übernehmen kann.
    3. Die KI übergibt nichts selbst an Claude_Harness.
    4. Alle Tests sind grün.
  - Summary: Ein Test beweist den Ablauf Zuordnen und Vorschlagen über die
    Werkzeuge der KI. Du bekommst den Prompt für Claude_Harness.

- `TASK-079` **Mindmap-Spiegel: Dateiformat und Codec mit Golden-Files**
  - Uid: 9e6775f1-faa6-4e27-88c8-042f708bccae.
  - Type: Task.
  - Parent: `STORY-105`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Das Dateiformat der Mindmap (Knoten, Bäume, Platzierungen,
    Zuordnungen, Dokumente) ist beschrieben und als Codec umgesetzt: Dateien
    werden in Einträge gelesen und Einträge in Dateien geschrieben, byte-genau
    über Golden-Files abgesichert. Der Codec kennt keine Datenbank.
  - Completion criteria: 1. `docs/techdocs/interfaces.md` enthält einen
    Abschnitt „Mindmap-Dateien (Format Version 1)“ mit Dateien, Kopfzeilen,
    Verweisen, Platzhaltern, Dokumenten und den Fehlercodes.
    2. Der `MindmapCodec` (`patterns = ("mindmap/**/*.md",)`, `for_project`,
    `decode`, `encode`) liest und schreibt Knoten, Dokumente, den Projektbaum
    und freie Maps (auch mehrfache Platzierungen eines Knotens und entfernte
    Platzierungen).
    3. Ungültiger Inhalt ergibt `MirrorFormatError` mit Datei und Zeile
    (unbekanntes Feld, fehlendes Feld, ungültiger Wert, doppelte Uid,
    doppeltes Label, Dokument im Ordner eines anderen Labels, Merge-Marker,
    Knoten zweimal im selben Baum, Zyklus in der Ordnung).
    4. Schreiben ändert nur betroffene Einträge und Dateien, atomar über die
    Änderungen des Kerns; Zeilenenden bleiben erhalten; ein
    Platzhalter-Eintrag wird durch Label und Uid ersetzt, seine Dateien
    umbenannt.
    5. Golden-Files unter `tests/fixtures/mirror-mindmap/valid` und
    `…/invalid` decken jeden Fehlercode und jede Dateiart ab; Unit-Tests für
    `encode` und `decode` sind grün.
  - Summary: Das Dateiformat der Mindmap steht fest und lässt sich lesen und
    schreiben, mit Beispieldateien als Absicherung. Die Datenbank ist noch
    nicht beteiligt.

- `TASK-080` **Mindmap-Spiegel: Teilnehmer für Knoten und Bäume**
  - Uid: cea5e2b3-594c-4fca-80d1-33de8f27473c.
  - Type: Task.
  - Parent: `STORY-105`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-079`.
  - Goal: Knoten, Bäume und Platzierungen laufen über den Sync zwischen
    Datenbank und Dateien: laden, vergleichen, übernehmen, mit neuen Einträgen
    aus der Cloud (Platzhalter) und freien Maps. Der Teilnehmer ist beim Sync
    des Projekts registriert.
  - Completion criteria: 1. `MindmapParticipant` (`load`, `resolve_labels`,
    `assign_labels`, `apply`) liefert und schreibt Knoten (Titel, Text,
    Markierung, Papierkorb), den Projektbaum und freie Maps mit Platzierungen.
    2. Neue Knoten und neue freie Maps aus Dateien (Platzhalter) bekommen Uid
    und Label; Verweise der Bäume folgen dem neuen Label; ein umgehängter oder
    übertragener Ast in den Dateien ändert die Platzierungen in der Datenbank
    mit denselben Regeln wie die API (keine Kopie, Knoten mit gleicher Uid).
    3. Der Mindmap-Spiegel ist per `mirror=…` im Plugin `mindmap` registriert;
    ein Sync des Projekts nimmt ihn mit Vorschau und Konflikten auf (Konflikt:
    Knoten auf beiden Seiten geändert, Baum auf beiden Seiten geändert).
    4. Zuordnungen von Items und Memos, Dokumente der Knoten, entfernte
    Platzierungen und Papierkorb folgen in der nächsten Task; bis dahin
    bleiben sie unverändert (Dateien tragen sie nicht, der Sync lässt sie in
    der Datenbank stehen).
    5. Integrationstests (Contract-Suite wie für die anderen Plugins, Sync mit
    Konflikt) sind grün.
  - Summary: Knoten und Bäume der Mindmap gleichen sich zwischen Datenbank und
    Dateien ab, auch neue aus der Cloud. Zuordnungen und Dokumente folgen im
    nächsten Schritt.

- `TASK-081` **Mindmap-Spiegel: Zuordnungen, Dokumente, entfernte Platzierungen und Papierkorb**
  - Uid: 7cff08f1-f39d-4fe9-857d-bb9fadc0d970.
  - Type: Task.
  - Parent: `STORY-105`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-080`.
  - Goal: Der Mindmap-Spiegel trägt auch die Zuordnung von Items und Memos zu
    Knoten, die Dokumente der Knoten, die entfernten Platzierungen und den
    Papierkorb-Zustand von Knoten und freien Maps.
  - Completion criteria: 1. Zuordnungen (`Items:`, `Memos:`) laufen über den
    Sync: Datenbank → Dateien und zurück; ein Item bei zwei Knoten (Dateien)
    wird als `rule_violation` mit beiden Dateien abgewiesen.
    2. Verweise auf Items und Memos werden gegen die Datenbank geprüft
    (`unknown_reference` mit Zeile); Items und Memos aus anderen Projekten
    sind als `Projekt:LABEL` möglich, soweit sie die API zulässt.
    3. Dokumente der Knoten (`NODE-nnn_notes.md`, `_spec…`) laufen über den
    Sync wie die Dokumente von Memos, inklusive Löschen nach den Regeln der
    Architektur §2 (Löschung mit Absicht nur bei unveränderter Datei).
    4. Entfernte Platzierungen (`Removed:`) und der Papierkorb (Knoten
    `Deleted:`, freie Maps `Deleted:`) werden übertragen; ein im Papierkorb
    liegender Knoten in den Dateien führt zum Papierkorb in der Datenbank,
    nicht zum endgültigen Löschen.
    5. Ein kompletter Rundlauf (Datenbank → Dateien → neue Datenbank) ergibt
    dieselbe Mindmap; Integrationstests sind grün.
  - Summary: Der Mindmap-Spiegel enthält jetzt alles: welche Items und Memos
    an welchem Knoten hängen, die Notizen der Knoten, entfernte Platzierungen
    und den Papierkorb.

- `TASK-082` **Mindmap-Spiegel: Sync-Dialog, Cloud-Ablauf, Doku und Prompt für Claude_Harness**
  - Uid: f0241f7d-367f-44f1-8aec-51536800f5cd.
  - Type: Task.
  - Parent: `STORY-105`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-23.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-081`.
  - Goal: Der Sync-Dialog benennt die Einträge der Mindmap verständlich, ein
    Systemtest zeigt eine Cloud-Sitzung, die nur mit Dateien arbeitet, die
    Doku ist aktuell und der Owner hat den fertigen Prompt für Claude_Harness.
  - Completion criteria: 1. Der Sync-Dialog (Plugin `workspace`) zeigt Knoten,
    Bäume und Dokumente der Mindmap mit lesbaren Namen und im Konfliktfall mit
    Diff (de und en); Client-Tests sind grün.
    2. Ein Systemtest bildet eine Cloud-Sitzung nach: Dateien eines Projekts
    werden bearbeitet (freie Map füllen, einen Ast umhängen, einen Ast in eine
    andere Map übertragen, ein Item einem Knoten zuordnen, ein neuer Knoten
    mit Platzhalter), ein Sync übernimmt sie, die Datenbank zeigt dasselbe
    Ergebnis wie die gleichen Schritte über die API.
    3. `docs/techdocs/neubau-server.md`, `interfaces.md`, `operations.md`
    (falls berührt) und `README.md` beschreiben den Mindmap-Spiegel;
    `docs/todo/items/EPIC-008/EPIC-008_spec.md` nennt den Stand.
    4. Der Prompt für Claude_Harness steht als Datei in der Spec dieser Task
    (`…_spec_prompt-harness.md`) und im Abschluss der Session als Text beim
    Owner; er beschreibt die Regeln für den Datei-Modus.
    5. Die KI übergibt nichts selbst an Claude_Harness. Alle Tests sind grün.
  - Summary: Der Mindmap-Spiegel ist fertig: der Sync-Dialog zeigt ihn
    verständlich, ein Test spielt eine Cloud-Sitzung durch, und du bekommst
    den Prompt für Claude_Harness.
