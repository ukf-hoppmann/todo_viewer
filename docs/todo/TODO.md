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

- `STORY-095` **Sync-Konflikte erklären: Herkunft, Umbenennung, Empfehlung**
  - Uid: 02d22676-5584-4eff-a2cc-7f3fe65e9d5c.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-11-03.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Im Sync-Dialog ist bei jedem Konflikt erkennbar, woher er kommt
    (welche Seite sich seit dem letzten Abgleich geändert hat, ob eine Datei
    wahrscheinlich umbenannt wurde) und welche Entscheidung naheliegt, ohne
    dass der Viewer selbst entscheidet.
  - Completion criteria: 1. Jeder Konflikt nennt je Seite, ob sie seit dem
    letzten Abgleich geändert ist, und den Zeitpunkt dieses Abgleichs.
    2. Bei einem Löschkonflikt wird ein wahrscheinlicher Umbenennungspartner
    (gleiche Art, gleiches Element, ähnlicher Inhalt) mit Ähnlichkeit
    angezeigt, falls es ihn gibt.
    3. Jeder Konflikt trägt eine Empfehlung mit Begründung in einem Satz;
    vorausgewählt wird nichts.
    4. Der Dialog zeigt eine Klartext-Überschrift, die Empfehlung und bei
    beidseitig vorhandenen Einträgen einen Diff statt zweier Volltexte;
    interne Feldnamen wie `kind`/`item` stehen als Kontext in der Kopfzeile.
    5. Die Ableitungen sind reine Funktionen im Core-Domain des Sync, ohne
    Wissen über Plugin-Inhalte, und durch Unit-Tests abgedeckt.
  - Summary: Konflikte im Sync-Dialog sind oft unverständlich (z. B. eine
    umbenannte Spec erscheint als 'in den Dateien gelöscht'). Die Story
    ergänzt jeden Konflikt um Herkunft, Umbenennungsverdacht und eine
    Empfehlung.

- `TASK-046` **Server: Konflikte um Herkunft, Umbenennungspartner und Empfehlung ergänzen**
  - Uid: cf20df9d-07c9-45ef-95a2-3e3d6b46b4ef.
  - Type: Task.
  - Parent: `STORY-095`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-03.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Sync-Vorschau liefert zu jedem Konflikt die abgeleiteten
    Erklärungen aus STORY-095_spec.md, berechnet in core/domain/sync.py.
  - Completion criteria: 1. `ConflictOut` enthält je Seite
    `changed_since_sync`, den Zeitpunkt des letzten Abgleichs des Eintrags,
    einen optionalen Umbenennungspartner (Schlüssel, Label, Ähnlichkeit) und
    eine Empfehlung (`database`/`files`/`none`) mit Begründungscode.
    2. Die Ableitungen sind reine Funktionen in `core/domain/sync.py` mit
    Unit-Tests, u. a. für den Fall umbenannte Spec (Löschung in den Dateien,
    neuer ähnlicher Eintrag am selben Element).
    3. OpenAPI und generierte TypeScript-Typen sind aktualisiert; bestehende
    Sync-Tests laufen grün.

- `TASK-047` **Sync-Dialog: Konflikte erklärt darstellen (Klartext, Empfehlung, Diff)**
  - Uid: e4a3ddbf-f7b3-4500-aa7c-82c16f59d924.
  - Type: Task.
  - Parent: `STORY-095`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-11-03.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-046`.
  - Goal: Der Sync-Dialog zeigt die Erklärungen aus dem Server verständlich
    an, wie in STORY-095_spec.md beschrieben.
  - Completion criteria: 1. Jede Konfliktkarte hat eine Klartext-Überschrift
    aus Konfliktart und Herkunft, mit Kontext (Art und Element) statt der
    Zeilen `kind`/`item`.
    2. Die empfohlene Option ist als „Empfohlen“ mit Begründung markiert,
    aber nicht vorausgewählt.
    3. Ein Umbenennungspartner wird mit Ähnlichkeit genannt; bei beidseitig
    vorhandenen Texten erscheint ein zeilenweiser Diff statt zweier
    Volltexte.
    4. Texte in de/en, Test-IDs nach Client-Regeln, Unit-Tests für die
    reinen Darstellungsfunktionen.
