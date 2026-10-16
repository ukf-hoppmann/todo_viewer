# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `EPIC-005` **Notizen und Wiedervorlage: Topics, Notes, Auslöser**
  - Type: Epic.
  - Status: Open.
  - Created: 2026-10-06.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Gedanken, Fragen und Beobachtungen, die kein klarer Auftrag sind,
    lassen sich strukturiert festhalten und tauchen von selbst wieder auf.
    Notes liegen in Topics (Tiefe 2, bis 3), tragen eine Kurzfassung und
    optional einen Langtext, verweisen auf Backlog-Items (auch
    projektübergreifend) und werden vom Viewer zu einem Zeitpunkt, bei einem
    Ereignis oder zum Topic-Termin als fällig markiert. Eine Wiedervorlage
    (Standard 30 Tage) verhindert, dass Notes vermüllen. Die Pflege läuft
    über die UI und über die API für Claude oder andere LLMs; alle
    mechanischen Prüfungen übernimmt der Viewer, damit sie keine Tokens
    kosten. Die Regeln, was Claude damit tun darf, liegen im Harness, nicht
    hier.
  - Completion criteria: Alle Pflicht-Stories sind abgeschlossen. Der
    Besitzer kann in der UI und per API Topics und Notes anlegen, verlinken,
    als fällig erkennen, zurückstellen, erledigen, verwerfen und zu
    Backlog-Items befördern. Ein Beispiel wie 'Backend-Element nachziehen,
    sobald das UI-Element fertig ist' funktioniert ohne Handarbeit. Die Doku
    beschreibt Modell, API und Bedienung.
  - Summary: Ein eigener Bereich neben dem Backlog für Merker, die keine
    Arbeit sind: Notes in Topics, mit Zeit- und Ereignis-Auslösern,
    Wiedervorlage und Verweisen in beide Richtungen.
  - Notes: `items/EPIC-005/EPIC-005_notes.md`.

- `STORY-041` **Änderungshinweise zwischen Notes und Items**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ändert sich ein verlinktes Item (abgeschlossen, verworfen,
    gelöscht, umgebaut, Projekt nicht erreichbar), bekommt die Note einen
    Hinweis mit den Optionen behalten, abkoppeln, verwerfen, befördern.
    Umgekehrt zeigt das Item, wenn eine verlinkte Note verworfen oder
    befördert wurde. Ein Hinweis bleibt stehen, bis jemand entscheidet.
  - Completion criteria: Jede der genannten Änderungen erzeugt in beide
    Richtungen einen Hinweis; keine Note verschwindet still.
  - Summary: Ändert sich ein verlinktes Item (abgeschlossen, verworfen,
    gelöscht, umgebaut, Projekt nicht erreichbar), bekommt die Note einen
    Hinweis mit den Optionen behalten, abkoppeln, verwerfen, befördern
  - Notes: `items/STORY-041/STORY-041_notes.md`.
  - Spec: `items/STORY-041/STORY-041_spec.md`.

- `EPIC-006` **Markdown nicht mehr Normalbetrieb: Datenbank und API als Hauptanwendung**
  - Type: Epic.
  - Status: Open.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Datenbank mit der API ist die Hauptanwendung für das Backlog
    und für Notes. Markdown-Dateien (TODO.md, archive.md, items/) sind kein
    Normalbetrieb mehr, sondern eine Option zum Exportieren, Importieren und
    Abgleichen, zum Beispiel für die Cloud-Nutzung. Neue Projekte starten
    mit der Datenbank als Primärquelle. Die dafür nötigen Änderungen im
    Harness (Standard-Backend, Hooks, Skills) und in der Doku sind Teil
    dieses Epics.
  - Completion criteria: Ein neues Projekt läuft ohne Markdown-Dateien
    vollständig über die API. Export und Import des Backlogs nach und aus
    Markdown funktionieren ohne Verlust. Harness und Doku beschreiben die
    Datenbank als Normalfall und Markdown als Option. Der Besitzer hat den
    Umfang der Umstellung bestätigt.
  - Summary: Das Backlog wird im Normalfall nur noch über API und Datenbank
    geführt; Markdown bleibt als Export, Import und Sync-Option erhalten.
  - Notes: `items/EPIC-006/EPIC-006_notes.md`.

- `STORY-048` **Notes und Topics ohne Projekt anlegen**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-09.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Notes und Topics lassen sich anlegen und verwalten, ohne dass sie
    einem Projekt zugeordnet sein müssen (z. B. als allgemeine Inbox).
    Bisher gehören beide immer zu einem Projekt, Labels zählen je Projekt
    und die Anlage läuft nur unter /projects/{project}/…
  - Completion criteria: 1. Eine Note und ein Topic können ohne Projekt über
    API und UI angelegt werden. 2. Projektlose Notes und Topics erscheinen
    in Index, Fällig-Zähler und Fällig-Liste. 3. Eine projektlose Note lässt
    sich per move einem Projekt zuordnen und umgekehrt. 4. Das Label-Schema
    für projektlose Notes und Topics ist festgelegt und dokumentiert;
    Architekturregeln und Techdocs sind angepasst.
  - Summary: Bisher gehört jede Note und jedes Topic zu einem Projekt. Diese
    Story ermöglicht auch projektlose Notes und Topics, etwa als allgemeine
    Inbox.

- `STORY-054` **Topic mit Notizen löschen: Auswahldialog statt stilles Mitlöschen**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-09.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Beim Löschen eines Topics mit Notizen weist das System auf die
    betroffenen Notizen hin und lässt wählen, was damit geschieht.
    Abgeschlossene Notizen können erhalten bleiben, aktive Notizen lassen
    sich vorher umhängen.
  - Completion criteria: 1. Löschen eines Topics mit Notizen (aktiv oder
    archiviert) oder Unter-Topics liefert in der API einen Hinweis mit
    Anzahl aktiver und archivierter Notizen, statt still zu kaskadieren. 2.
    Die UI zeigt dazu einen Dialog mit zwei Checkboxen: 'Archivierte Notizen
    behalten' (werden dem neutralen Topic 'Archiviert' des Projekts
    zugeordnet) und 'Aktive Notizen verschieben' (mit Auswahl des
    Zieltopics). Nicht gewählte Gruppen werden mit dem Topic in den
    Papierkorb gelegt. 3. 'OK' führt die gewählten Optionen in einer
    Transaktion aus, 'Abbrechen' ändert nichts. 4. Das Topic 'Archiviert'
    wird pro Projekt beim ersten Bedarf automatisch angelegt und ist nicht
    löschbar. Die dorthin umgehängten Notizen behalten ihren Status und
    bleiben im Archiv sichtbar. 5. Das Wiederherstellen des gelöschten
    Topics bringt nur die mit gelöschten Notizen zurück. 6. Unit-Tests für
    die Planungsregel, API-Test und UI-Test für den Dialog.
  - Summary: Wer ein Topic löscht, das Notizen enthält, bekommt einen
    Dialog: archivierte Notizen behalten und aktive Notizen umhängen sind
    wählbar, der Rest wird mit gelöscht. So geht eine abgeschlossene Notiz
    nicht mehr unbemerkt mit dem Topic verloren.

- `STORY-055` **Topics ins Archiv verschieben und wieder aktivieren**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-09.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-054`.
  - Goal: Topics lassen sich archivieren, um den Baum übersichtlich zu
    halten, ohne Notizen zu verlieren. Archivierte Topics samt Unter-Topics
    und Notizen sind ausgeblendet und jederzeit wieder aktivierbar.
  - Completion criteria: 1. Ein Topic lässt sich archivieren und wieder
    aktivieren (API und UI). Archivierte Topics samt Unter-Topics sind im
    Baum ausgeblendet, ein Archiv-Filter zeigt sie. 2. Beim Archivieren
    werden offene Notizen im Topic und in den Unter-Topics mit dem Grund
    'parent archived' als archiviert markiert. Sie werden beim Reaktivieren
    des Topics wieder aktiviert. Notizen, die unabhängig davon archiviert
    waren (erledigt, verworfen, übernommen), bleiben auch danach archiviert.
    3. Archivierte Notizen lösen keine Wiedervorlage und keine Trigger aus,
    solange sie wegen des Topics archiviert sind. 4. Das Archivieren benutzt
    denselben Auswahldialog wie das Löschen aus der Story 'Topic mit Notizen
    löschen' (Notizen behalten oder umhängen), mit der zusätzlichen
    Möglichkeit, aktive Notizen einfach mit zu archivieren. 5. Unit-Tests
    für Archivieren und Reaktivieren inklusive der unabhängig archivierten
    Notizen, API-Test und UI-Test.
  - Summary: Ein Topic kann wie ein Backlog-Item ins Archiv wandern und ist
    dann ausgeblendet, ohne dass etwas gelöscht wird. Offene Notizen darin
    werden mit archiviert und beim Reaktivieren des Topics wieder aktiviert.

- `STORY-056` **Eigenständige Erinnerungen: an Note, Item oder frei, zu einem Zeitpunkt**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-09.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Erinnerungen werden ein eigenes, allgemeines Konzept und gelten
    nicht nur für Notes. Man kann an eine Note, an ein Backlog-Item (Task,
    Story, Epic) oder einfach so erinnern lassen, jeweils zu einem
    Zeitpunkt. Die bisherige Lösung, Notes mit zeitlichem Auslöser als
    Krücke zu nutzen, die sich irgendwann melden, wird dadurch abgelöst.
  - Completion criteria: Eine Erinnerung lässt sich anlegen mit Zeitpunkt
    und optionalem Bezug (Note, Backlog-Item oder keiner). Sie wird zum
    Zeitpunkt fällig und ist sichtbar (Fällig-Anzeige, Zähler). Sie lässt
    sich erledigen oder zurückstellen. Für bestehende Notes mit zeitlichem
    Auslöser ist der Übergang geklärt. Details (Datenmodell, UI,
    Harness-Skill, Verhältnis zu EPIC-005) werden vor der Umsetzung geklärt.
  - Summary: Eigenständiges Erinnerungskonzept: an Notes, Items oder frei zu
    einem Zeitpunkt, statt Notes mit Zeit-Auslöser als Behelf.

- `EPIC-007` **Neuentwicklung als eigenständiges Tool**
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
  - Notes: `items/EPIC-007/EPIC-007_notes.md`.
  - Spec: `items/EPIC-007/EPIC-007_spec.md`.

- `STORY-060` **Noch zu klären: offene Fragen zum Neubau**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Notes: `items/STORY-060/STORY-060_notes.md`.
  - Spec: `items/STORY-060/STORY-060_spec.md`.

- `STORY-061` **Server-Grundgerüst: Core mit Plugin-Host, HTTP, Ereignissen und SSE**
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
  - Notes: `items/STORY-061/STORY-061_notes.md`.
  - Spec: `items/STORY-061/STORY-061_spec.md`.

- `STORY-062` **MCP-Host: Operationen als MCP-Tools für LLMs**
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
  - Notes: `items/STORY-062/STORY-062_notes.md`.
  - Spec: `items/STORY-062/STORY-062_spec.md`.

- `STORY-063` **Infrastruktur Datenbank: Migrationen je Plugin, Transaktionen, Backups**
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
  - Notes: `items/STORY-063/STORY-063_notes.md`.
  - Spec: `items/STORY-063/STORY-063_spec.md`.

- `STORY-064` **Infrastruktur Dateien: atomares Schreiben, Konflikte, Merge-Marker**
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
  - Notes: `items/STORY-064/STORY-064_notes.md`.
  - Spec: `items/STORY-064/STORY-064_spec.md`.

- `STORY-065` **Generischer Sync-Dienst über Datenbank und Dateien**
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
  - Notes: `items/STORY-065/STORY-065_notes.md`.
  - Spec: `items/STORY-065/STORY-065_spec.md`.

- `STORY-066` **Client-Grundgerüst: ezf-ui-Core ohne Login, Layout, SSE, UI-Zustand**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Notes: `items/STORY-066/STORY-066_notes.md`.
  - Spec: `items/STORY-066/STORY-066_spec.md`.

- `STORY-067` **Gemeinsame UI-Bausteine für alle Plugins**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Notes: `items/STORY-067/STORY-067_notes.md`.
  - Spec: `items/STORY-067/STORY-067_spec.md`.

- `STORY-068` **Projekte, Suche und Element-Register (Plugin workspace)**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Notes: `items/STORY-068/STORY-068_notes.md`.
  - Spec: `items/STORY-068/STORY-068_spec.md`.

- `STORY-069` **Verknüpfungen zwischen Elementen**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-069/STORY-069_spec.md`.

- `STORY-070` **Papierkorb für alle Elementtypen**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-070/STORY-070_spec.md`.

- `STORY-071` **Backlog anzeigen: Baum, Filter, Suche, Detail (Plugin backlog)**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Notes: `items/STORY-071/STORY-071_notes.md`.
  - Spec: `items/STORY-071/STORY-071_spec.md`.

- `STORY-072` **Backlog bearbeiten: Felder, Formular, Anlegen, Typwechsel, Drag & Drop**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-072/STORY-072_spec.md`.

- `STORY-073` **Backlog-Dokumente: Notizen und Specs**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-073/STORY-073_spec.md`.

- `STORY-074` **Abhängigkeiten-Graph**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-074/STORY-074_spec.md`.

- `STORY-075` **Backlog im Markdown-Spiegel**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Notes: `items/STORY-075/STORY-075_notes.md`.
  - Spec: `items/STORY-075/STORY-075_spec.md`.

- `STORY-076` **Sync in der Oberfläche: Spiegel-Einstellungen, Sync-Dialog, Status**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-076/STORY-076_spec.md`.

- `STORY-077` **Notes und Topics (Plugin notes)**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-077/STORY-077_spec.md`.

- `STORY-078` **Notes-Auslöser, Änderungshinweise, Befördern und Zurückstufen**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-077`, `STORY-072`.
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
  - Spec: `items/STORY-078/STORY-078_spec.md`.

- `STORY-079` **Notes im Markdown-Spiegel**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-079/STORY-079_spec.md`.

- `STORY-080` **Wecker (Plugin alarms)**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-069`, `STORY-065`.
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
  - Notes: `items/STORY-080/STORY-080_notes.md`.
  - Spec: `items/STORY-080/STORY-080_spec.md`.

- `STORY-081` **KI-Schnittstelle vollständig: MCP und API für den Harness**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-081/STORY-081_spec.md`.

- `STORY-082` **Datenübernahme aus dem alten Viewer**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-075`, `STORY-079`, `STORY-080`, `STORY-070`.
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
  - Notes: `items/STORY-082/STORY-082_notes.md`.
  - Spec: `items/STORY-082/STORY-082_spec.md`.

- `STORY-083` **Betrieb: Container, Start-Skript, Logs und Backups des Neubaus**
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Open.
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
  - Spec: `items/STORY-083/STORY-083_spec.md`.

- `STORY-084` **Umstieg: der Neubau ersetzt den alten Viewer**
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
  - Notes: `items/STORY-084/STORY-084_notes.md`.
  - Spec: `items/STORY-084/STORY-084_spec.md`.
