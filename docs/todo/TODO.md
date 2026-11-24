# Project Backlog

Active project work: open, in progress, or awaiting a project-owner decision.
Completed and rejected items are moved to `archive.md`; per-item notes and
specs live in `items/<ID>/`.

Format: Claude_Harness backlog format version 2. The rules are defined in
`docs/techdocs/interfaces.md` of the ToDo Viewer.

## Work items

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
