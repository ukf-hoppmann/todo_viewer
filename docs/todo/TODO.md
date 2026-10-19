# Project Backlog

Active project work: open, in progress, or awaiting a project-owner decision.
Completed and rejected items are moved to `archive.md`; per-item notes and
specs live in `items/<ID>/`.

Format: Claude_Harness backlog format version 2. The rules are defined in
`docs/techdocs/interfaces.md` of the ToDo Viewer.

## Work items

- `STORY-084` **Umstieg: der Neubau ersetzt den alten Viewer**
  - Uid: 1d71c607-6a99-4e28-ab92-cfad65a29d99.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-060`, `STORY-074`, `STORY-076`, `STORY-081`,
    `STORY-082`, `STORY-083`.
  - Goal: Der Neubau läuft als ToDo-Viewer auf Port 5411 mit allen
    übernommenen Daten, die Spiegel sind im Format Version 2 neu
    geschrieben, die Dokumentation beschreibt nur noch den Neubau, und der
    Altcode ist entfernt.
  - Completion criteria: 1. Backup der alten DB und aller Spiegel-Ordner
    liegt vor. 2. Übernahme ausgeführt, Bericht ohne ungeklärte Abweichung.
    3. Neubau auf 5411, alter Container entfernt. 4. Spiegel aller Projekte
    neu geschrieben und in den Repositories committet (vom Inhaber). 5. Nach
    ausdrücklicher Abnahme des Neubaus durch den Projektinhaber: `src_old/`,
    `reference/` und die Scopes `legacy`, `backend`, `web` entfernt; README
    und `docs/techdocs/` beschreiben den Neubau. 6. Formatbeschreibung und
    Tool-Liste an den Projektinhaber für den Harness übergeben. 7. Version
    1.0.0. 8. Offene Altitems nach Entscheidung des Inhabers geschlossen.
  - Summary: Der Tag des Umstiegs: Daten übernehmen, den neuen Viewer auf
    die gewohnte Adresse setzen, den alten entfernen.

- `STORY-085` **Serienwecker: Wiederholung am Wecker**
  - Uid: 409b1dce-0f22-4222-91b9-7fb867234356.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-17.
  - Area: Backend-API.
  - Priority: Prospective.
  - Dependencies: `STORY-080`.
  - Goal: Ein Wecker kann sich wiederholen (täglich, wöchentlich, monatlich,
    jährlich); nach langer Pause erscheint er einmal, mit der Zahl der
    verpassten Termine.
  - Completion criteria: 1. Der Wecker hat ein Feld Wiederholung (keine,
    täglich, wöchentlich, monatlich, jährlich) in Datenbank, API, MCP,
    Formular und Markdown-Spiegel. 2. Beim Erledigen oder Fälligwerden rückt
    er auf den ersten Termin nach jetzt, gerechnet ab dem Fälligkeitstermin.
    3. Verpasste Termine erscheinen als ein Wecker mit Zähler (Anzeige, wenn
    optisch gut umsetzbar). 4. Tests für Regeln, Migration und Oberfläche
    sind grün.
  - Summary: Folge zu Frage 5 in STORY-060: Serien kommen nach dem
    Live-Gang. Wecker hängen schon an jedem Element, die Wiederholung ist
    nur ein Feld am Wecker.

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
  - Completion criteria: 1. Story auf Story: Dialog 'Nur als Task möglich,
    umwandeln und verschieben?'; bei Ja Typwechsel, dann Verschieben; bei
    Nein bleibt alles. 2. Ein Epic ohne Kinder lässt sich ebenso als Story
    umwandeln. 3. Fälle, in denen die Umwandlung Kinder verwaisen ließe,
    werden mit Grund abgelehnt. 4. Das Label ändert sich wie beim Typwechsel
    im Detailpanel, Verweise folgen. 5. UI-Tests für Zustimmung, Ablehnung
    und Fehlerfälle sind grün.
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

- `STORY-060` **Noch zu klären: offene Fragen zum Neubau**
  - Uid: e82954be-70bf-4ad6-9b73-cca74503771c.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Alle Fragen zum Neubau, die beim Zerlegen offen geblieben sind,
    sind beantwortet, und die Antworten stehen in den betroffenen Specs und
    Notizen.
  - Completion criteria: 1. Jede Frage in der Spec dieser Story ist vom
    Projektinhaber beantwortet oder ihre Annahme bestätigt. 2. Die Antworten
    stehen in den Notizen dieser Story und in den Specs der betroffenen
    Items. 3. Neue Fragen, die während der Umsetzung auftauchen, werden hier
    ergänzt.
  - Summary: Sammelstelle für offene Fragen zum Neubau. Jede Frage hat eine
    Annahme, mit der die Umsetzung weiterlaufen kann, bis du anders
    entscheidest.

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
