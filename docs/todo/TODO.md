# Project Backlog

Active project work: open, in progress, or awaiting a project-owner decision.
Completed and rejected items are moved to `archive.md`; per-item notes and
specs live in `items/<ID>/`.

Format: Claude_Harness backlog format version 2. The rules are defined in
`docs/techdocs/interfaces.md` of the ToDo Viewer.

## Work items

- `STORY-077` **Notes und Topics (Plugin notes)**
  - Uid: 10590159-c19b-41e2-88a6-26b3ec076cc1.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-069`.
  - Goal: Notes mit Wiedervorlage und Topics stehen in einem eigenen Plugin:
    relational gespeichert, als Baum Projekt → Topic → Note gezeigt, mit
    Detail, Status-Aktionen, Archiv, Löschen und Drag & Drop.
  - Completion criteria: 1. Datenmodell mit festen Status, Topics mit
    Tiefenbegrenzung, Dokumenten je Note. 2. Baum mit Hervorhebung der
    Topic-Bereiche, Zählern, fällige zuerst, Hover-Aktionen. 3. Detail mit
    Aktionen (Bearbeiten, Erledigen, Verwerfen, Zurückstellen, Behalten,
    Löschen, Großansicht). 4. Topics archivieren und wieder aktivieren,
    Löschen eines Topics mit Notizen über Auswahldialog. 5. Notes und Topics
    per Drag & Drop verschieben. 6. Fällig-Zähler in der Kopfzeile. 7.
    Operationen über API und MCP. 8. Tests grün.
  - Summary: Notes und Topics im neuen Viewer, inklusive der offenen Wünsche
    zum Archivieren und Löschen von Topics.

- `TASK-036` **Seitengerüst: Flags sidebar und detail, leere Bereiche, usePageDetail**
  - Uid: 15f20c68-6b88-42df-943f-e59f8a5eea52.
  - Type: Task.
  - Parent: `STORY-088`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-18.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Gerüst an einem Ort: Header mit Tabs immer da, linke Sidebar
    und rechte Detailspalte per layout-Flag der Route, leer und von Plugins
    gefüllt.
  - Completion criteria: 1. Route-Flags `sidebar` und `detail`; die Sidebar
    erscheint per Flag statt über `when` der Abschnitte. 2. `usePageDetail`
    füllt die Detailspalte; sie ist nur sichtbar, wenn gefüllt, und hat
    einen Schließen-Knopf. 3. Header, Sidebar und Detail liegen an einem Ort
    (Layout-Plugin); die ezf-ui-Navigations-Sidebar mit Unterrouten
    entfällt, sofern ungenutzt. 4. Architekturbeschreibung (client.md) nach
    Freigabe angepasst. 5. UI-Tests für Flags an/aus und Füllen/Schließen
    sind grün.

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

- `STORY-065` **Generischer Sync-Dienst über Datenbank und Dateien**
  - Uid: 1f81c8d1-0f65-4cbc-b6d1-b6d695afa384.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-063`, `STORY-064`, `TASK-035`.
  - Goal: Ein Sync-Dienst im Core gleicht für jedes spiegelnde Plugin die DB
    und den Markdown-Ordner eines Projekts über UUIDs ab, mit Vorschau,
    Konflikten, Entscheidungen, Import neuer Einträge und Auto-Sync, ohne
    Fachwissen über die Plugins.
  - Completion criteria: 1. Mit einem Test-Plugin (Codec + Teilnehmer)
    laufen Vorschau, Ausführen mit Entscheidungen, Richtungsbeschränkung und
    Konflikterkennung wie in Abschnitt 7.3 beschrieben. 2. Einträge ohne
    `uid` aus den Dateien bekommen `uid` und Label, Platzhalter-Verweise
    werden umgeschrieben, die Dateien danach aktualisiert. 3. Auto-Sync
    überträgt nur konfliktfreie Änderungen, löscht nie, pausiert bei
    Merge-Markern und sichert vorher die DB. 4. Der Status je Projekt ist
    ohne Datenänderung abfragbar und wird per SSE gemeldet. 5. Formatfehler
    des Codecs stoppen den Sync mit Datei und Zeile.
  - Summary: Der Abgleich zwischen Datenbank und Markdown-Dateien, einmal
    gebaut für alle Plugins. Darüber kommen Einträge aus der Cloud in die
    Datenbank.

- `STORY-074` **Abhängigkeiten-Graph**
  - Uid: 2fd09b0c-6e9b-419f-a0df-7d1e35454830.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-071`.
  - Goal: Die Abhängigkeiten zwischen Items werden als gerichteter Graph
    gezeigt, mit Hervorheben und Mehrfachauswahl wie im heutigen Viewer.
  - Completion criteria: 1. Unterseite „Abhängigkeiten“ im Backlog zeigt nur
    Items mit Abhängigkeiten, Layout ELK von links nach rechts. 2. Auswahl,
    Hover und ⌘/Strg/⇧-Klick heben Knoten, Kanten und Nachbarn hervor; Esc
    setzt zurück. 3. Graph-Bibliotheken werden erst beim Öffnen geladen. 4.
    Tests der Graph-Domäne grün.
  - Summary: Der Abhängigkeiten-Graph aus dem alten Viewer im neuen Viewer.

- `TASK-038` **Slot workspace.element-detail mit ElementDetail**
  - Uid: 32938d29-5762-408f-8801-03b5ab7a9f89.
  - Type: Task.
  - Parent: `STORY-088`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-18.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-036`.
  - Goal: Ein Plugin kann die Detailansicht eines fremden Elements zeigen,
    ohne vom Eigentümer-Plugin abzuhängen.
  - Completion criteria: 1. `workspace` stellt den Slot
    `workspace.element-detail` und die Komponente `ElementDetail uid kind`
    bereit. 2. Backlog meldet seine Ansicht für epic/story/task an, Notes
    für Notizen und Themen. 3. Ohne Anmeldung zeigt `ElementDetail` eine
    Ersatzansicht (Label, Titel, Links). 4. UI-Tests für angemeldete Art,
    unbekannte Art und gelöschtes Element sind grün.

- `STORY-080` **Wecker (Plugin alarms)**
  - Uid: 359ff9f5-f044-4b38-93bd-d13c5fca22ab.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-065`, `STORY-069`.
  - Goal: Wecker erinnern zu einem Zeitpunkt an ein Element oder frei; das
    Backend löst sie aus, solange der Viewer läuft, und meldet sie per SSE
    an die UI; sie werden gespiegelt.
  - Completion criteria: 1. Wecker anlegen mit Zeitpunkt, Text und
    optionalem Ziel über UI, API und MCP. 2. Das Backend setzt genau einen
    Termin auf den nächsten fälligen Wecker; beim Start werden verpasste
    nachgeholt. 3. Fällige Wecker erscheinen als Banner und im Zähler, ggf.
    als Browser-Benachrichtigung; erledigen und zurückstellen. 4. Codec für
    `alarms.md` nach Format Version 2. 5. Tests mit fester Uhr grün.
  - Summary: Ein eigener Wecker statt der Krücke über Notes: erinnert zu
    einer Uhrzeit, an ein Element oder einfach so.

- `STORY-081` **KI-Schnittstelle vollständig: MCP und API für den Harness**
  - Uid: 36c33cae-a5d3-4751-8166-6a52e634ea3e.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-062`, `STORY-070`, `STORY-072`, `STORY-073`,
    `STORY-078`, `STORY-080`.
  - Goal: Alles, was der Harness heute über `backlog_api.py` und
    `notes_api.py` tut, geht im Neubau über MCP und HTTP, und die Liste der
    Tools ist für die Anpassung des Harness dokumentiert.
  - Completion criteria: 1. Eine Gegenüberstellung aller heutigen Befehle
    der beiden Helfer mit den neuen Tools ist vollständig, ohne Lücke. 2.
    Ein Systemtest arbeitet einen typischen Harness-Ablauf über MCP durch
    (Index, Anlegen, Ändern mit Version, Notiz anhängen, Note anlegen,
    Wecker stellen). 3. `docs/techdocs/interfaces.md` beschreibt die
    MCP-Tools. 4. Tests grün.
  - Summary: Sicherstellen, dass eine LLM über MCP alles kann, was der
    Harness heute über die API macht.

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

- `STORY-066` **Client-Grundgerüst: ezf-ui-Core ohne Login, Layout, SSE, UI-Zustand**
  - Uid: 4c0ed26f-22a2-47fb-b843-4fd28fbe4b95.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-061`.
  - Goal: Das neue Frontend startet mit dem aus ezf-ui kopierten Core ohne
    Login, dem Layout aus Kopfzeile und Seitenleiste, Sprachumschaltung,
    Einstellungsseite und Live-Aktualisierung über SSE.
  - Completion criteria: 1. `client/` baut und startet (Vite, Proxy auf Port
    5412) und zeigt Kopfzeile und Seitenleiste mit einem Beispiel-Plugin. 2.
    Kein Login-Code im Core. 3. Ein Ereignis vom Server löst im
    Beispiel-Plugin ein Neuladen aus. 4. Sprache DE/EN umschaltbar, im
    UI-Zustand des Servers gespeichert. 5. ESLint-Regel
    `architecture/boundaries`, tsc und Vitest sind grün.
  - Summary: Das leere Gerüst der neuen Oberfläche, übernommen aus ezf-ui:
    Kopfzeile, Seitenleiste, austauschbare Plugins und Live-Updates vom
    Server.

- `STORY-079` **Notes im Markdown-Spiegel**
  - Uid: 4ef07551-4f17-43b0-a998-df1c4b43b5d9.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-065`, `STORY-078`.
  - Goal: Das Plugin notes liefert Codec und Sync-Teilnehmer für Notes,
    Topics, Auslöser, Verknüpfungen und Dokumente nach Format Version 2.
  - Completion criteria: 1. Codec liest und schreibt `notes/` nach Format
    Version 2 gegen die Beispiele aus `tests/fixtures/mirror-v2/`. 2.
    `notes/new-<kurzname>.md` und Topic-Platzhalter bekommen beim Sync Label
    und Uid. 3. Verknüpfungen und Auslöser werden über Labels in den Dateien
    und `uid`s in der DB abgebildet. 4. Tests grün.
  - Summary: Notes und Topics als Markdown-Dateien für die Arbeit in der
    Cloud, abgeglichen mit der Datenbank.

- `STORY-076` **Sync in der Oberfläche: Spiegel-Einstellungen, Sync-Dialog, Status**
  - Uid: 5bd639b9-e1a4-4f6f-9fae-179d867a4b92.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-075`.
  - Goal: Spiegel und Sync eines Projekts lassen sich in der UI einrichten
    und ausführen, Konflikte werden mit Vergleich entschieden, und der Stand
    ist live in Seitenleiste und Projektkarte sichtbar.
  - Completion criteria: 1. Projektkarte in den Einstellungen: Spiegel aus /
    Sync von Hand / Sync automatisch, Ordner, Richtung, letzter Sync, eine
    Hauptaktion. 2. Sync-Dialog lädt die Vorschau, zeigt Konflikte zuerst
    mit Feldvergleich, Entscheidungen einzeln oder gesammelt, Löschungen nur
    einzeln. 3. Status (in Sync, braucht dich, nicht gespiegelt; ⚠ und ↻ in
    der Seitenleiste) aktualisiert sich über SSE. 4. Tests grün.
  - Summary: Die Oberfläche für den Abgleich: einrichten, Vorschau ansehen,
    Konflikte entscheiden, Stand live sehen.

- `STORY-070` **Papierkorb für alle Elementtypen**
  - Uid: 60317713-7ce3-4a3d-b2ed-83716a12a45b.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-068`.
  - Goal: Gelöschte Elemente aller Plugins landen in einem gemeinsamen
    Papierkorb, lassen sich samt Kindern wiederherstellen und nur vom
    Projektinhaber endgültig löschen.
  - Completion criteria: 1. Löschen eines Elements mit Kindern fragt nach
    und verschiebt alle in den Papierkorb. 2. Die Ansicht Papierkorb zeigt
    Elemente aller Plugins der gewählten Projekte mit Löschdatum, gefiltert
    nach Suche. 3. Wiederherstellen und endgültig Löschen einzeln und
    gesammelt; ist ein Element mit seinem Vorfahren gewählt, wird nur der
    Vorfahre angefragt. 4. Über MCP gibt es kein endgültiges Löschen. 5.
    Tests grün.
  - Summary: Ein Papierkorb für Items, Notes, Topics und Wecker gemeinsam,
    mit Wiederherstellen und endgültigem Löschen.

- `STORY-071` **Backlog anzeigen: Baum, Filter, Suche, Detail (Plugin backlog)**
  - Uid: 94d0bd73-f76f-4538-b09c-6ef8306da2db.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-068`.
  - Goal: Das Plugin backlog speichert Epics, Stories und Tasks relational
    und zeigt sie im Baum mit Fortschritt, gefiltert nach Status, Priorität,
    Projekt und Suche, mit Detailpanel.
  - Completion criteria: 1. Datenmodell mit festen Tabellen für Typen,
    Status, Prioritäten (`Urgent`, `Important`, `Normal`, `Prospective`) und
    Bereiche. 2. Baum Epic → Story → Task je Projekt mit Fortschrittsring,
    optionale Kinder gestrichelt, abgelehnte zählen nicht. 3. Filter Status
    und Priorität in der Seitenleiste, Suche und Projekte aus workspace. 4.
    Detailpanel mit allen Feldern und Kindern. 5. Lese-Operationen über API
    und MCP. 6. Tests grün.
  - Summary: Der Backlog im neuen Viewer: Baum mit Fortschritt, Filter und
    Detailansicht. Die Kanban-Ansicht entfällt.

- `STORY-061` **Server-Grundgerüst: Core mit Plugin-Host, HTTP, Ereignissen und SSE**
  - Uid: 96d662b7-90d3-44df-8682-a00e35b5fd90.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-034`.
  - Goal: Ein leerer Server-Core startet aus der Composition Root mit einer
    festen Plugin-Liste, veröffentlicht die Operationen der Plugins als
    HTTP-Routen und leitet Ereignisse per SSE an Clients weiter.
  - Completion criteria: 1. `server/` startet auf Port 5412 mit einem
    Beispiel-Plugin; `GET /api/core/health` antwortet. 2. Eine Operation des
    Beispiel-Plugins ist als Route erreichbar und steht im OpenAPI-Schema.
    3. Ein veröffentlichtes Ereignis kommt bei einem SSE-Client auf
    `/api/core/events` an. 4. Fehlerhafte Plugin-Definitionen (unbekanntes
    requires, Zyklus, doppelte Route) verhindern den Start mit klarer
    Meldung. 5. import-linter-Verträge laufen und sind grün.
  - Summary: Das leere Gerüst des neuen Servers: Plugins einstecken, ihre
    Funktionen als API anbieten und Neuigkeiten live an den Browser melden.

- `STORY-073` **Backlog-Dokumente: Notizen und Specs**
  - Uid: 97a30881-3e01-4981-bd5b-feec02b40d91.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-071`.
  - Goal: Jedes Item kann Notizen (datierte Einträge) und Specs haben, die
    in der DB gespeichert, in der UI mit Vorschau bearbeitet und über API
    und MCP gelesen und geschrieben werden.
  - Completion criteria: 1. Dokumente `<LABEL>_notes.md`, `<LABEL>_spec.md`,
    `<LABEL>_spec_<thema>.md` je Item in der DB. 2. Notiz-Eintrag anhängen
    (Thema, Besprochen, Entschieden, Offen; Datum vom Server). 3. Ganzes
    Dokument bearbeiten mit Vorschau und Konflikterkennung. 4. Erste Notiz
    verlangt eine Kurzfassung des Items. 5. Tests grün.
  - Summary: Notizen und Specs zu Items, wie heute, im neuen Viewer.

- `STORY-067` **Gemeinsame UI-Bausteine für alle Plugins**
  - Uid: 98d859b2-3756-458f-8fdf-50b07c37572d.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-066`.
  - Goal: Plugins bauen ihre Ansichten aus gemeinsamen Bausteinen (Baum,
    Detailpanel, Markdown-Editor, Filterabschnitt, Dialoge, Drag & Drop)
    statt sie jeweils neu zu schreiben.
  - Completion criteria: 1. Die Bausteine aus der Spec liegen in
    `client/src/shared` und sind über ihr `index.ts` nutzbar. 2. Jeder
    Baustein hat Unit-Tests und Test-IDs. 3. Eine Beispielseite im
    Test-Plugin nutzt Baum, Detailpanel und Editor zusammen. 4. Kein
    Baustein hält globalen Store-Zustand.
  - Summary: Wiederverwendbare Bausteine für die Oberfläche, damit Backlog,
    Notes und Wecker gleich aussehen und sich gleich bedienen lassen.

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

- `STORY-078` **Notes-Auslöser, Änderungshinweise, Befördern und Zurückstufen**
  - Uid: a4bb2496-ca9c-46bf-af39-c0a247644494.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-072`, `STORY-077`.
  - Goal: Notes melden sich über Ereignis-Auslöser (Item erreicht Status),
    Topic-Termine und Prüfdatum, zeigen Änderungshinweise zwischen Notes und
    Items und lassen sich zu Items befördern und zurückstufen.
  - Completion criteria: 1. Ereignis-Auslöser reagieren auf
    `backlog.item.status_changed`, ohne dass `backlog` notes kennt. 2.
    Fällig-Entscheidung ist eine reine Funktion mit der Uhr als Parameter.
    3. Änderungshinweise zwischen verknüpften Notes und Items mit
    Entscheidungen keep/detach/acknowledge/drop/promote. 4. Befördern legt
    ein Item mit `origin`-Verknüpfung an; Zurückstufen wandelt ein offenes
    Item in eine Note. 5. Fällig-Liste gruppiert nach Grund. 6. Tests grün.
  - Summary: Notes, die sich von selbst melden, wenn etwas Bestimmtes
    passiert, und der Weg zwischen Note und Backlog-Item in beide
    Richtungen.

- `STORY-063` **Infrastruktur Datenbank: Migrationen je Plugin, Transaktionen, Backups**
  - Uid: aae84a1a-1da0-4af4-b808-22d37fee89be.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-061`.
  - Goal: Core und Plugins speichern relational in SQLite mit eigenen,
    vorwärts gerichteten Migrationen, Transaktionen und optimistischer
    Sperre; vor Migrationen wird gesichert.
  - Completion criteria: 1. Beim Start werden die Migrationen von Core und
    Plugins in Abhängigkeitsreihenfolge ausgeführt, Stand in
    `core_migrations`. 2. Vor jeder Migration entsteht ein Backup unter
    `configs/backups/`, die letzten 10 bleiben. 3. Ein Test migriert eine
    leere DB auf den aktuellen Stand. 4. Fremdschlüssel sind eingeschaltet;
    ein Fremdschlüssel auf ein Plugin außerhalb von `requires` lässt die
    Prüfung scheitern. 5. Der UI-Zustand (`/api/core/ui-state/{owner}`) wird
    in der DB gespeichert.
  - Summary: Die Datenbank-Grundlage: jedes Plugin bringt seine Tabellen
    mit, Änderungen am Schema laufen kontrolliert und gesichert.

- `STORY-088` **Wiederverwendbares Seitengerüst mit Sidebar und Detailspalte; Wecker zeigt sein Ziel**
  - Uid: b65219ae-c972-4a08-a26b-9574b8d0dd41.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Awaiting confirmation.
  - Created: 2026-10-18.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Alle Seiten nutzen ein gemeinsames Gerüst: Header mit Tabs immer
    da, eine linke Sidebar und eine rechte Detailspalte, beide per Flag der
    Route an- und abschaltbar und leer, gefüllt durch die Plugins. Darüber
    zeigt der Wecker das verknüpfte Element rechts an, ohne von Backlog oder
    Notes abzuhängen.
  - Completion criteria: 1. Die Route schaltet per layout-Flag `sidebar` und
    `detail` die Bereiche; die Seite füllt die Detailspalte über
    `usePageDetail` (analog `usePageHeader`), das Gerüst übernimmt Breite,
    Scrollen und Schließen. Die ezf-ui-Navigations-Sidebar (Unterrouten)
    entfällt. 2. Backlog, Notes, Graph und Papierkorb nutzen das Gerüst;
    kein Plugin baut den Split selbst. 3. Slot `workspace.element-detail`
    mit `ElementDetail uid kind`: Backlog und Notes melden ihre
    Detailansicht an, ohne Anmeldung gibt es eine schlichte Ersatzansicht.
    4. Wecker: ein Klick auf die ganze Zeile öffnet das Ziel rechts (nur
    Detail, keine Navigation); Bearbeiten, Zurückstellen und Erledigt sind
    Icon-Buttons mit Tooltip, im Kopf der Detailspalte und in der Zeile;
    gelöschte Ziele öffnen nichts. 5. Architekturbeschreibung angepasst,
    UI-Tests je Schritt grün.
  - Summary: Aus der Prüfung am 2026-10-18: Im Wecker ist das Ziel nicht
    anklickbar, die Textbuttons überlappen, und das Split-Layout ist in
    Backlog und Notes kopiert. ezf-ui dient nur als Ideengeber. Umsetzung
    erst nach dem Umstieg (STORY-084).

- `STORY-068` **Projekte, Suche und Element-Register (Plugin workspace)**
  - Uid: b921c649-42fa-4bfd-b11b-904881297231.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-063`, `STORY-067`.
  - Goal: Projekte lassen sich anlegen, umbenennen, ordnen und entfernen;
    alle Elementtypen der Plugins haben ein gemeinsames Register mit UUID,
    Label und Revision; die Seitenleiste zeigt Suche und Projektliste; ein
    einheitlicher Neu-Dialog legt Elemente aller Plugins an.
  - Completion criteria: 1. Projekte über UI, API und MCP verwalten, inkl.
    Ordner-Browser für den Spiegel-Ordner. 2. Plugins melden Elementtypen
    an; Labels werden je Projekt und Präfix nie wiederverwendet. 3.
    Seitenleiste: Suche (für alle Tabs gemeinsam) und Projektliste mit
    Ein-/Ausblenden, Markieren, Reihenfolge. 4. Ein Neu-Dialog zeigt alle
    angemeldeten Typen. 5. Tests für Register, Labels und
    Projekt-Operationen sind grün.
  - Summary: Die gemeinsame Grundlage aller Inhalte: Projekte, eindeutige
    Kennungen für jedes Element, die Suche und ein einziger Weg zum
    Neuanlegen.

- `STORY-082` **Datenübernahme aus dem alten Viewer**
  - Uid: b94a9306-7f06-4126-9a9b-668fc60f8a44.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-070`, `STORY-075`, `STORY-079`, `STORY-080`.
  - Goal: Ein Übernahme-Befehl überträgt alle Projekte, Items, Dokumente,
    Notes, Topics, Verknüpfungen, Auslöser und den Papierkorb aus
    `configs/todo.db` (und Markdown-primären Projekten) in die neue DB,
    verlustfrei und wiederholbar.
  - Completion criteria: 1. `python -m viewer.app.import_legacy` liest die
    alte DB und Markdown-primäre Ordner und schreibt `configs/viewer.db`
    nach einem Backup. 2. `uid`s der alten DB werden übernommen; Labels
    bleiben gleich. 3. Prioritäten: Urgent/Important/Normal/Prospective
    unverändert, High → Urgent, Medium → Important, Low → Normal, alte
    deutsche Werte wie heute; jeder andere Wert bricht mit Liste ab. 4.
    Zusatzfelder und Zeit-Auslöser nach den Annahmen in `STORY-060`. 5. Ein
    Bericht nennt Zahlen je Typ und jede Abweichung. 6. Ein zweiter Lauf auf
    eine frische DB ergibt dasselbe Ergebnis.
  - Summary: Alle bestehenden Daten in den neuen Viewer übernehmen,
    inklusive der Umstellung der Prioritäten.

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

- `TASK-037` **Backlog, Notes, Graph und Papierkorb auf das Seitengerüst umstellen**
  - Uid: cef9ec92-6c32-4692-80ac-07591fda8f34.
  - Type: Task.
  - Parent: `STORY-088`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-18.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-036`.
  - Goal: Die Seiten bauen ihren Split nicht mehr selbst, sondern nutzen
    Sidebar und Detailspalte des Gerüsts.
  - Completion criteria: 1. Backlog, Notes und Graph nutzen `usePageDetail`
    statt eigener `flex: 1 1 50%`-Boxen. 2. Der Papierkorb schaltet `detail`
    ein und zeigt das gewählte Element rechts. 3. Verhalten wie vorher
    (Auswahl, Schließen, persistente Auswahl). 4. Bestehende UI-Tests sind
    grün, neue Tests für den Papierkorb.

- `TASK-039` **Wecker: Zeile klickbar, Ziel in der Detailspalte, Icon-Aktionen**
  - Uid: d5810abe-8c93-4fd4-8dbb-82b51202b2a5.
  - Type: Task.
  - Parent: `STORY-088`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-18.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-037`, `TASK-038`.
  - Goal: Im Wecker sieht man per Klick, worauf sich ein Alarm bezieht,
    bevor man ihn erledigt oder zurückstellt; die Aktionen überlappen nicht
    mehr.
  - Completion criteria: 1. Ein Klick auf die ganze Zeile öffnet das Ziel
    per `ElementDetail` in der Detailspalte, ohne zu navigieren; die Zeile
    ist markiert. 2. Alarme ohne Ziel oder mit gelöschtem Ziel öffnen
    nichts. 3. Bearbeiten, Zurückstellen und Erledigt sind Icon-Buttons mit
    Tooltip und aria-label, in der Zeile und im Kopf der Detailspalte;
    Klicks darauf öffnen das Detail nicht. 4. Test-IDs bleiben, UI-Tests für
    Öffnen und Aktionen sind grün.

- `STORY-075` **Backlog im Markdown-Spiegel**
  - Uid: d5ed7b91-c359-4820-b1aa-7406e85a2e21.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-065`, `STORY-071`, `STORY-073`.
  - Goal: Das Plugin backlog liefert Codec und Sync-Teilnehmer für Format
    Version 2, sodass Items und ihre Dokumente zwischen DB und
    Markdown-Ordner abgeglichen werden und in der Cloud angelegte Items in
    der DB ankommen.
  - Completion criteria: 1. Codec liest und schreibt `TODO.md`, `archive.md`
    und `items/` nach Format Version 2 bytegenau gegen die Beispiele aus
    `tests/fixtures/mirror-v2/`. 2. Nur geänderte Einträge werden in den
    Dateien geändert. 3. Neue Items mit Platzhalter bekommen beim Sync Label
    und Uid; Verweise und Ordner werden umgeschrieben. 4. Ungültige Werte
    (z. B. Priorität `High`) stoppen den Sync mit Datei und Zeile. 5. Tests
    grün.
  - Summary: Der Backlog als Markdown-Dateien für die Arbeit in der Cloud,
    abgeglichen mit der Datenbank.

- `STORY-062` **MCP-Host: Operationen als MCP-Tools für LLMs**
  - Uid: e4e63c0a-4210-42be-81c9-d3851026e148.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-061`.
  - Goal: Jede Operation eines Plugins mit `mcp=True` steht LLMs als
    MCP-Tool zur Verfügung, ohne dass das Plugin MCP-Code schreibt.
  - Completion criteria: 1. Der Server bietet unter `/mcp` einen MCP-Server
    (Streamable HTTP). 2. Ein MCP-Client listet die Tools des
    Beispiel-Plugins mit Beschreibung und JSON-Schema und ruft eines
    erfolgreich auf. 3. Ein `DomainError` kommt beim MCP-Client mit
    demselben `code` an wie über HTTP. 4. Tests für Tool-Liste, Aufruf und
    Fehler sind grün.
  - Summary: Neben der API bekommt der Server einen MCP-Zugang, über den
    eine LLM alle Funktionen direkt nutzen kann.

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

- `STORY-087` **Browser-Logs ins viewer.log schreiben**
  - Uid: e86b8042-b480-4a30-b7f8-9b3c562d14cc.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Awaiting confirmation.
  - Created: 2026-10-17.
  - Area: Backend-API.
  - Priority: Prospective.
  - Dependencies: `STORY-066`, `STORY-083`.
  - Goal: Meldungen und Fehler des Clients landen über eine Operation des
    Core im viewer.log des Servers, statt nur in der Browser-Konsole.
  - Completion criteria: 1. Der Core bietet eine Operation, die Log-Einträge
    des Browsers (Stufe, Meldung, Quelle) annimmt und ins viewer.log
    schreibt. 2. Der Client sendet Fehler und Warnungen dorthin, ohne bei
    Ausfall des Servers selbst Fehler zu erzeugen. 3. Menge und Größe der
    Einträge sind begrenzt. 4. Tests für Operation und Client sind grün.
  - Summary: Warnungen und Fehler des Browsers landen im viewer.log des
    Servers.

- `STORY-064` **Infrastruktur Dateien: atomares Schreiben, Konflikte, Merge-Marker**
  - Uid: ee9eb2da-3413-44b5-a2c9-370b833bdf54.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-061`.
  - Goal: Der Core liest und schreibt Spiegel-Ordner sicher: atomar, mit
    erhaltenen Zeilenenden, mit Konflikterkennung und mit Schutz vor
    Merge-Markern und laufenden Git-Operationen.
  - Completion criteria: 1. Ein Ordner wird als Menge von Dateien mit Inhalt
    und Version gelesen. 2. Schreiben ist atomar und behält LF/CRLF. 3. Eine
    seit dem Lesen geänderte Datei führt zu `mirror_conflict` statt
    Überschreiben. 4. Merge-Marker und `.git/*.lock` werden gemeldet, statt
    zu lesen. 5. Contract-Tests gegen echte temporäre Ordner sind grün.
  - Summary: Die Dateien-Grundlage für den Markdown-Spiegel: nichts geht
    beim Schreiben kaputt, und fremde Änderungen werden nicht überschrieben.

- `STORY-072` **Backlog bearbeiten: Felder, Formular, Anlegen, Typwechsel, Drag & Drop**
  - Uid: f14e59f7-2cec-44a6-90b4-73c45131ed6b.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-071`.
  - Goal: Items lassen sich über UI, API und MCP mit allen Regeln des
    Backlog-Formats anlegen, ändern, umhängen und im Typ wechseln, auch per
    Drag & Drop im Baum.
  - Completion criteria: 1. Inline-Felder (Status, Priorität, Bereich,
    Pflicht für Parent, Abhängigkeiten) und Bearbeiten-Formular speichern
    mit Versionsprüfung. 2. Anlegen über den Neu-Dialog und „Kind anlegen“;
    Label vergibt der Server. 3. Parent-Regeln und Lebenszyklus wie im
    Format, Resolution bei Completed/Rejected, Wiedereröffnen-Dialog für
    geschlossene Vorfahren. 4. Typwechsel ändert das Label, die `uid`
    bleibt. 5. Drag & Drop ändert Parent und Reihenfolge mit Regelprüfung.
    6. Statuswechsel erzeugen das Ereignis `backlog.item.status_changed`. 7.
    Tests grün.
  - Summary: Alles, was man heute am Backlog ändern kann, im neuen Viewer,
    dazu Umhängen per Drag & Drop.

- `STORY-083` **Betrieb: Container, Start-Skript, Logs und Backups des Neubaus**
  - Uid: f4ce031d-079d-4d7f-8a5a-460393c5f36c.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-066`.
  - Goal: Der Neubau läuft als eigener Container neben dem alten Viewer und
    lässt sich mit einem Skript bauen, starten, aktualisieren und
    überwachen.
  - Completion criteria: 1. Ein Dockerfile baut Server und Client in ein
    Image; der Server liefert das gebaute Frontend aus. 2. Ein
    Compose-Dienst `todo-viewer-next` läuft auf Port 5412 mit `configs/` und
    `logs/` als Volumes. 3. `todo.sh` hat Befehle für den Neubau (`next
    start|stop|update|logs|status`). 4. `docs/techdocs/operations.md`
    beschreibt den Betrieb des Neubaus.
  - Summary: Den neuen Viewer im Container betreiben, neben dem alten, bis
    zum Umstieg.

- `STORY-069` **Verknüpfungen zwischen Elementen**
  - Uid: f748deeb-1b0d-4706-a578-d85ccbb4c4ad.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-068`.
  - Goal: Beliebige Elemente (auch projektübergreifend) lassen sich mit
    Rollen verknüpfen, und jedes Detailpanel zeigt, was auf das Element
    verweist.
  - Completion criteria: 1. Verknüpfungen mit Rolle `reference`, `origin`
    oder `trigger` anlegen und entfernen über API, MCP und UI. 2. Verweise
    überleben Typwechsel und Umbenennen, weil sie an der `uid` hängen. 3.
    Detailpanels zeigen ausgehende und eingehende Verknüpfungen über einen
    Slot. 4. Tests grün.
  - Summary: Elemente untereinander verknüpfen, zum Beispiel eine Note mit
    einem Item, und sehen, was worauf verweist.

- `STORY-089` **Wecker als Erinnerung: mehrere Elemente, Erlöschen und Aufräumen nach 24 h**
  - Uid: f6066bb8-fe33-447b-859f-8ed7455742e9.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Awaiting confirmation.
  - Created: 2026-10-18.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Wecker ist eine Erinnerung, kein Planungselement. Er verweist
    auf beliebig viele Elemente (Note, Epic, Story, Task …) oder ist eine
    freie Erinnerung mit Text. Erledigt bleibt er 24 Stunden sichtbar und
    verschwindet dann endgültig. Sind alle seine Elemente nicht mehr offen
    (erledigt, archiviert, gelöscht …), erlischt er von selbst. Das Label
    bleibt als Transportschlüssel für Cloud und Markdown-Spiegel, die
    Oberfläche zeigt es nicht.
  - Completion criteria: 1. Ein erledigter Wecker bleibt 24 h ausgegraut mit
    Rückgängig sichtbar und wird danach endgültig gelöscht, ohne Papierkorb.
    2. Ein Wecker hat 0..n verknüpfte Elemente statt eines Ziels; der Text
    ist optional, ohne Elemente aber Pflicht; bestehende Wecker sind
    migriert (Backup vorher); API, MCP und Spiegel führen die Liste. 3. Die
    Liste ist nach Zeit gruppiert (Fällig, Heute, Später) und zeigt kein
    Label; Überschrift ist der Text, sonst der Titel des ersten Elements. 4.
    Das Detail zeigt oben eine Erinnerungsleiste mit Zeit, Überschrift und
    Icon-Aktionen; bei einem Element dieses direkt, bei mehreren Karten zum
    Wechseln (erste offen); nicht mehr offene Elemente ausgegraut. 5. Ist
    kein verknüpftes Element mehr offen, gilt der Wecker als erledigt
    (24-h-Übergang); wird eins in dieser Zeit wieder geöffnet, kehrt er
    zurück. 6. Techdoku angepasst, Tests je Schritt grün.
  - Summary: Wecker werden zu Erinnerungen: beliebig viele Elemente oder
    freier Text, Erlöschen, wenn nichts mehr offen ist, und Aufräumen 24 h
    nach Erledigt.

- `TASK-041` **Wecker-Server: mehrere Elemente, Erlöschen, Aufräumen nach 24 h, Spiegel**
  - Uid: 377708ff-c0fe-46c2-b138-0a59bbed6b9e.
  - Type: Task.
  - Parent: `STORY-089`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-18.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Wecker hat 0..n Elemente, erlischt, wenn keins mehr offen ist,
    kehrt zurück, wenn eins wieder offen ist, und wird 24 h nach Erledigt
    endgültig gelöscht; Spiegel und API führen die Liste.
  - Completion criteria: 1. Domain: Status Expired, done_at,
    expire/revive/undo, to_purge, next_wakeup mit fester Uhr getestet. 2.
    Migration v2 mit alarms_targets, done_at, Übernahme von target_uid;
    Migrationstest. 3. Operationen mit targets (Liste), text optional nur
    mit Elementen, reopen_alarm; Timer räumt auf. 4. alarms.md: Target als
    Liste, Done at, Expired; Bindung ephemeral; Golden Files und
    Contract-Suite grün. 5. OpenAPI-Typen neu erzeugt.

- `TASK-042` **Wecker-Client: Liste nach Zeit, Detail mit Erinnerungsleiste und Karten, Formular mit mehreren Elementen**
  - Uid: 644841f7-ff68-42f0-9d45-89a85882273e.
  - Type: Task.
  - Parent: `STORY-089`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-18.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Wecker-Seite zeigt Erinnerungen nach Zeit gruppiert ohne
    Label; das Detail zeigt eine Erinnerungsleiste und das Element oder
    Karten zum Wechseln; das Formular nimmt mehrere Elemente.
  - Completion criteria: 1. domain/grouping.ts (Fällig, Heute, Später,
    Erledigt) und Überschrift getestet. 2. Liste mit Karten, ausgegrauten
    geschlossenen Elementen und Rückgängig. 3. Detail: Leiste, ein Element
    direkt, mehrere als Karten (erstes offen), keins nur Leiste. 4. Formular
    mit Mehrfachauswahl; SetAlarm, AlarmCounter und Meldung auf targets. 5.
    Techdoku angepasst, Tests grün, im Browser angesehen.

- `TASK-040` **Grundlagen: kurzlebige Spiegel-Einträge und Zustand „offen“ im Register**
  - Uid: e9d19c3e-68bb-43e9-bb48-693e780fc796.
  - Type: Task.
  - Parent: `STORY-089`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-18.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Sync trägt Löschungen kurzlebiger Einträge aus der Datenbank
    ohne Konflikt in die Dateien; das Element-Register beantwortet, ob ein
    Element offen ist, über Prüfungen, die Backlog und Notes je Typ
    anmelden.
  - Completion criteria: 1. MirrorBinding.ephemeral; compute_plan löscht in
    den Dateien unveränderte kurzlebige Einträge, die in der Datenbank
    fehlen; der automatische Sync führt nur diese Löschungen aus. 2.
    registry.register_state und registry.is_open; gelöscht gilt als
    geschlossen, ohne Prüfung als offen. 3. Backlog (Completed/Rejected) und
    Notes (erledigt, verworfen, befördert, archiviert; Topic archiviert)
    melden ihre Prüfung an. 4. Tests grün.

- `STORY-091` **Fällig-Glocke in der Projektleiste: Wecker und fällige Notes in einer Liste, global und je Projekt**
  - Uid: 1145a9d5-6c90-48b2-9849-dd3ccf0d5ad6.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-19.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Alles, was jetzt Aufmerksamkeit will, meldet sich an einer Stelle:
    eine Glocke im Kopf „Projekte“ (global) und je Projektzeile. Beide
    öffnen dieselbe Liste aus fälligen Weckern und fälligen Notes, angeführt
    vom zuletzt fällig gewordenen Eintrag, damit ein ignorierter Eintrag
    einen neuen nicht verdeckt. Wecker und Notes bleiben in Daten und
    Plugins getrennt; nur die Anzeige ist gemeinsam.
  - Completion criteria: 1. Im Kopf „Projekte“ (neben Stift und Plus) steht
    eine Glocke mit der Anzahl aller fälligen Wecker und Notes als Badge,
    nur sichtbar, wenn es welche gibt; ⏰n und !n verschwinden aus der
    App-Leiste; die Zahl im Browser-Tab ist die Summe. 2. Jede Projektzeile
    mit Fälligem zeigt eine Glocke mit Anzahl als IconButton, immer
    sichtbar. 3. Ein Klick öffnet immer ein Popup mit einer Liste, auch bei
    einem Eintrag; je Projekt gefiltert auf dieses Projekt. 4. Die Liste
    mischt Wecker und Notes, sortiert nach „fällig seit“ absteigend; der
    oberste Eintrag ist aufgeklappt. 5. Jede Zeile zeigt ein Art-Symbol
    (Wecker/Note), bei Notes den Grund als Beschriftung, und die eigenen
    Aktionen der Art (Wecker: Erledigt, Schlummern; Note: Behalten,
    Schlummern, Erledigt, Verworfen bzw. Hinweis-Entscheidungen); ein Klick
    springt zum Wecker-Element bzw. zur Note und zeigt es im Detail. 6. Der
    Server liefert für fällige Notes „fällig seit“ (Auslöser: fired_at,
    Hinweis: created_at, Topic-Termin: due_at, Prüfdatum: review_at). 7. Die
    gemeinsame Liste ist eine Komponente mit einem Anknüpfungspunkt, an den
    Wecker- und Notes-Plugin ihre Einträge und Zeilen melden, ohne einander
    zu kennen (Architekturregeln vor der Planung geprüft). 8. Techdoku
    angepasst, Tests je Schritt grün.
  - Summary: Eine Glocke im Kopf der Projektliste und je Projekt öffnet
    alles Fällige – Wecker und Notes – als eine Liste, neuester oben und
    aufgeklappt, mit Sprung zum Element.

- `STORY-090` **Projektleiste schlanker: Bearbeiten oben, Sync-Symbole als Aktion bzw. beim Hovern**
  - Uid: e2855cf3-e6e6-44dd-8aa3-2af63212036f.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-19.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Projektliste in der Sidebar zeigt pro Zeile nur, was
    Aufmerksamkeit braucht. Bearbeitet wird das markierte Projekt über einen
    Stift im Kopf neben dem Plus oder per Doppelklick auf den Namen; das
    Sync-Warndreieck führt direkt zum Sync des Projekts, das
    Auto-Sync-Symbol erscheint nur beim Hovern.
  - Completion criteria: 1. Im Kopf „Projekte“ steht neben dem Plus ein
    Stift, der die Karte des markierten Projekts öffnet; ohne Markierung ist
    er ausgegraut mit dem Tooltip „Erst ein Projekt auswählen“. 2. Der Stift
    pro Zeile entfällt; ein Doppelklick auf den Projektnamen öffnet die
    Karte. 3. Das Warndreieck ist ein IconButton mit Tooltip, bleibt immer
    sichtbar und öffnet direkt die Sync- bzw. Konfliktansicht des Projekts.
    4. Das Auto-Sync-Symbol erscheint nur, solange die Zeile gehovert oder
    fokussiert ist. 5. Techdoku angepasst, Tests je Schritt grün.
  - Summary: Weniger Symbole pro Projektzeile: Bearbeiten zentral oben oder
    per Doppelklick, Sync-Warnung als direkter Link, Auto-Sync nur beim
    Hovern.
