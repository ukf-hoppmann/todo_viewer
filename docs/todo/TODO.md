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

- `STORY-100` **Items und Memos an Knoten hängen: Anzahl, Fortschritt und Zustand am Thema**
  - Uid: 36fb7560-506d-49a0-9d0b-bcbc5b35015f.
  - Type: Story.
  - Parent: `EPIC-008`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-099`.
  - Goal: Backlog-Items und Memos lassen sich an Knoten hängen. Ein Knoten
    zeigt Anzahl und Fortschritt seiner Items samt Unterknoten und einen
    daraus abgeleiteten Zustand; die Items selbst stehen nur im Detail. Items
    ohne Knoten stehen in einer Seitenansicht und werden von dort in den Baum
    gezogen. So wird der Themenbaum zur Übersicht des Backlogs.
  - Completion criteria: 1. Ein Item hängt an höchstens einem Knoten; Kinder
    erben den Knoten ihres Parents, außer sie sind eigens angehängt, dann
    zählen sie und ihre Kinder zum neuen Knoten. Wird ein Knoten gelöscht,
    fallen seine Items an den Parent-Knoten zurück, sonst in „Nicht
    zugeordnet“.
    2. Ein Knoten zeigt Anzahl und Fortschrittsring über sich und seine
    Unterknoten; jedes Item zählt genau einmal, auch über leere Knoten hinweg; Items im
    Papierkorb zählen nie.
    3. Der Zustand Idee, geplant, in Arbeit oder erledigt ergibt sich aus den
    Items und ist filterbar.
    4. Das Detail eines Knotens listet seine Items und verlinkten Memos; Memos
    zählen nicht in der Zahl.
    5. Items ohne Knoten stehen in einer Seitenansicht „Nicht zugeordnet“. Sie
    lässt sich ausschalten. Von dort ordnet man Items per Drag-and-drop einem
    Knoten zu.
    6. Domain-, API- und UI-Tests sind grün.
  - Summary: Backlog-Einträge und Memos an Themen hängen. Das Thema zeigt nur
    eine Zahl und den Fortschritt, damit die Map übersichtlich bleibt.

- `TASK-056` **Mindmap-Server: Items und Memos zuordnen, Vererbung, Summen und Zustand**
  - Uid: b8dc196f-65c2-4f22-a846-46d853a2ec75.
  - Type: Task.
  - Parent: `STORY-100`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Server verknüpft Items und Memos mit Knoten, berechnet den
    wirksamen Knoten jedes Items nach der Vererbungsregel und liefert je
    Knoten Anzahl, Fortschritt und Zustand.
  - Completion criteria: 1. Zuordnen und Lösen gehen über API und MCP; ein
    zweiter Knoten für dasselbe Item wird abgewiesen oder ersetzt den ersten
    ausdrücklich.
    2. Die reine Funktion für wirksamen Knoten, Summen ohne Doppelzählung und
    Zustand ist mit Tests abgedeckt, auch für leere Knoten und eigens
    angehängte Kinder.
    3. Die Antwort des Baums enthält je Knoten Anzahl, Fortschritt und Zustand
    sowie die Items ohne Knoten.
    4. Zählende Items folgen dem Statusfilter des Backlogs; Items im Papierkorb
    zählen nie; der Zustand folgt der Regel der Story-Spec und ist vom Filter
    unabhängig.
    5. Wird ein Knoten gelöscht, fallen seine Items an den Parent-Knoten
    zurück, sonst nach „Nicht zugeordnet“; Memos lassen sich an mehrere Knoten
    verlinken, der Link ruht im Papierkorb.

- `TASK-057` **Mindmap: Zahl, Fortschrittsring, Zustand und Filter am Knoten, Items und Memos im Detail**
  - Uid: 0401cbeb-4e8c-42db-b37a-57b857f6772e.
  - Type: Task.
  - Parent: `STORY-100`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-056`.
  - Goal: Die Map zeigt an jedem Knoten Anzahl, Fortschrittsring und Zustand,
    bietet einen Filter über die Zustände und listet im Detail die Items und
    Memos des Knotens; Items lassen sich in der Oberfläche zuordnen und lösen.
  - Completion criteria: 1. Ideen-Knoten sind gestrichelt und hohl, Knoten mit
    Items zeigen Ring und Zahl, erledigte sind gedimmt.
    2. Der Filter blendet Knoten nach Zustand aus; die Seitenansicht „Nicht
    zugeordnet“ listet Items ohne Knoten, lässt sich ausschalten, und Items
    lassen sich von dort per Drag-and-drop einem Knoten zuordnen.
    3. Im Detail eines Knotens und eines Items lässt sich die Zuordnung setzen
    und lösen.
    4. Zahl, Ring und Detail folgen dem Statusfilter des Backlogs.
    5. UI-Tests sind grün und der Ablauf ist im Browser geprüft.

- `TASK-065` **Mindmap: Markierungen „verworfen“ und „später“ an Ideen-Knoten**
  - Uid: ea634e30-aae8-49b4-a5ab-8b77aa40bf03.
  - Type: Task.
  - Parent: `STORY-100`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-11-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-056`.
  - Goal: Ideen-Knoten lassen sich als „verworfen“ oder „später“ markieren,
    damit alte Ideen als Spur stehen bleiben, aber nicht mehr stören. Die
    Markierung gehört zum Knoten, nicht zu seinen Items.
  - Completion criteria: 1. Ein Knoten trägt höchstens eine Markierung
    (keine, verworfen, später); setzen und löschen gehen über API, MCP und
    Oberfläche.
    2. Markierte Knoten sind sichtbar abgesetzt, und der Zustandsfilter kann
    sie ausblenden.
    3. Die Markierung gilt nur für den Knoten selbst, nicht für Unterknoten,
    und ändert weder die Summen der Items noch den Zustand.
    4. Die offene Form (feste Werte oder frei) ist vor der Umsetzung mit dem
    Owner geklärt; Domain-, API- und UI-Tests sind grün.

- `STORY-101` **Mindmap-Ansichten: Fokus auf einen Knoten, Einzel- und Gesamtansicht, runde Anordnung, Abhängigkeiten**
  - Uid: 3366e17a-d7f3-4810-85c4-adf6817191fe.
  - Type: Story.
  - Parent: `EPIC-008`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-100`.
  - Goal: Man kann jeden Knoten als Wurzel öffnen und von dort weiterplanen,
    von einem Item aus zur Map springen, alle Projekte unter einer gemeinsamen
    Wurzel sehen, zwischen runder und seitlicher Anordnung wechseln und
    Abhängigkeiten zwischen Themen einblenden.
  - Completion criteria: 1. Fokus zeigt die Map ab einem Knoten mit einem Pfad
    zurück nach oben.
    2. Am Item gibt es „Gehe hin“ (Map an seiner Stelle öffnen), „Erstelle“
    (eigenen Knoten anlegen) und „Anker“ (als Wurzel öffnen); „Anker“ erst,
    wenn das Item einen eigenen Knoten hat.
    3. Die Gesamtansicht zeigt eine gemeinsame Wurzel mit den Projekten als
    ersten Knoten, gefiltert über die Projektauswahl; die Einzelansicht zeigt
    eine Map.
    4. Die Anordnung ist umschaltbar zwischen rund und Baum zur Seite.
    5. Abhängigkeiten zwischen Themen sind als zusammengefasste Linien an- und
    abschaltbar, standardmäßig aus.
    6. UI-Tests sind grün.
  - Summary: Verschiedene Blicke auf die Map: einen Ast als eigene Map öffnen,
    alle Projekte zusammen sehen, rund oder zur Seite anordnen und
    Abhängigkeiten zwischen Themen einblenden.

- `TASK-058` **Mindmap: Fokus auf einen Knoten und die Aktionen „Gehe hin“, „Erstelle“, „Anker“ am Item**
  - Uid: 44aae02d-c3c4-48b7-81d2-4ad27c9d5398.
  - Type: Task.
  - Parent: `STORY-101`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Jeder Knoten lässt sich als Wurzel öffnen, mit Pfad zurück. Im
    Detail eines Items führen „Gehe hin“, „Erstelle“ und „Anker“ zur Map.
  - Completion criteria: 1. Der Fokus steht in der Adresse und zeigt einen
    Pfad bis zur Wurzel.
    2. „Gehe hin“ öffnet die Map am wirksamen Knoten des Items; „Erstelle“
    legt unter ihm einen Knoten mit dem Namen des Items an und hängt es eigens
    dorthin; „Anker“ gibt es nur mit eigenem Knoten.
    3. UI-Tests sind grün.

- `TASK-059` **Mindmap: Gesamtansicht mit gemeinsamer Wurzel über die gewählten Projekte**
  - Uid: 9d65405e-bef7-4405-b7d3-693fbbfc7615.
  - Type: Task.
  - Parent: `STORY-101`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-058`.
  - Goal: Neben der Einzelansicht gibt es eine Gesamtansicht mit einer
    gemeinsamen Wurzel, unter der die in der Seitenleiste gewählten Projekte
    die ersten Knoten sind.
  - Completion criteria: 1. Die Ansicht ist umschaltbar; Projekte hinzu- und
    wegschalten wirkt sofort.
    2. Die Summen an der gemeinsamen Wurzel zählen jedes Item einmal.
    3. UI-Tests sind grün.

- `TASK-060` **Mindmap: runde Anordnung, umschaltbar zur Anordnung zur Seite**
  - Uid: a52f7b44-3538-457d-8e85-46d493bdd7d9.
  - Type: Task.
  - Parent: `STORY-101`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Map lässt sich rund anordnen, mit der Wurzel in der Mitte, und
    zurück zur Anordnung zur Seite schalten. Vorab zeigt ein Prototyp mit
    einer großen Map, ob ELK `radial` genügt oder eine eigene Anordnung nötig
    ist.
  - Completion criteria: 1. Das Ergebnis des Prototyps und die Wahl der
    Anordnung stehen in den Notizen der Story.
    2. Beide Anordnungen sind umschaltbar und die Wahl bleibt gespeichert.
    3. Eine Map mit vielen Knoten bleibt in der runden Anordnung ohne
    Überlappung lesbar.

- `TASK-061` **Mindmap: Abhängigkeiten zwischen Themen ein- und ausblenden**
  - Uid: c9b91950-7822-42e1-9b52-d0d3d0176a6f.
  - Type: Task.
  - Parent: `STORY-101`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Schalter blendet Linien zwischen Themen ein, sobald ein Item des
    einen Themas von einem Item des anderen abhängt.
  - Completion criteria: 1. Die Linien werden aus den Abhängigkeiten der Items
    und ihren wirksamen Knoten zusammengefasst; die reine Funktion ist
    getestet.
    2. Der Schalter ist standardmäßig aus und sein Zustand bleibt gespeichert.

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
    Brainstormen vor der Umsetzung, und ein Memo seine eigene Map. Äste lassen
    sich zwischen Bäumen umhängen (aus A weg, in B drin) oder übertragen
    (derselbe Ast in A und B), ohne zu kopieren.
  - Completion criteria: 1. Freie Maps lassen sich in einem Projekt anlegen,
    auswählen, umbenennen und löschen; die Map eines Memos öffnet man aus dem
    Memo.
    2. Umhängen geht innerhalb eines Baums und zwischen Bäumen; Übertragen
    geht nur zwischen Bäumen, ein Knoten steht höchstens einmal je Baum.
    3. Ein übertragener Ast ist markiert; „hier entfernen“ nimmt ihn nur aus
    diesem Baum, „Knoten löschen“ überall.
    4. Summen zählen ein Item auch dann nur einmal, wenn sein Ast über zwei
    Wege unter derselben Wurzel liegt.
    5. Domain-, API- und UI-Tests sind grün.
  - Summary: Mehrere Maps je Projekt und die Möglichkeit, einen Ast in eine
    andere Map zu hängen oder ihn in beiden zu führen, damit die Planungs-Map
    nicht schrumpft, wenn die Umsetzungs-Map wächst.

- `TASK-062` **Mindmap: freie Maps je Projekt und die Map eines Memos**
  - Uid: 57a6b175-25bd-4d1e-8f8b-7fc05a044760.
  - Type: Task.
  - Parent: `STORY-102`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Projekt kann neben seinem Projektbaum freie Maps haben, und ein
    Memo eine eigene Map; sie lassen sich anlegen, auswählen, umbenennen und
    löschen.
  - Completion criteria: 1. Server und Oberfläche führen mehrere Bäume je
    Projekt und höchstens einen je Memo.
    2. Die Auswahl der Map sitzt an der mit dem Owner abgestimmten Stelle der
    Mindmap-Seite; die Map eines Memos öffnet man aus dem Memo.
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
    weist einen Knoten zweimal im selben Baum sowie Kreise ab.
    2. Die Oberfläche bietet „umhängen“ und „übertragen“ mit Wahl des Ziels,
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
  - Completion criteria: 1. Ein Dateiformat für Bäume, Knoten, Platzierungen
    und Zuordnungen ist beschrieben und mit Golden-Files abgedeckt.
    2. Der Sync nimmt die Mindmap mit Vorschau und Konflikten in denselben
    Dialog auf.
    3. Die Regeln für den Datei-Modus sind an Claude_Harness übergeben.
  - Summary: Die Map auch als Dateien speichern, damit sie über Git mitgeht
    und die KI in der Cloud damit arbeiten kann. Gewünscht, aber kein Muss.

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
