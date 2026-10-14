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

- `STORY-047` **Notes in Markdown spiegeln und zwischen Rechnern abgleichen**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Notes sind in der API und Datenbank zu Hause; Markdown ist nur
    Export, Import und Sync-Option, kein Normalbetrieb. Notes inklusive
    Notizen und Specs werden über den vorhandenen Spiegel-Mechanismus als
    Dateien exportiert und wieder eingelesen, damit Claude sie auch in der
    Cloud nutzen kann. Links bleiben im Spiegel Verweise auf Labels.
  - Completion criteria: Round-Trip ohne Verlust von Text, Notizen, Specs,
    Links, Auslösern und Terminen.
  - Summary: Notes mit Notizen und Specs lassen sich als Markdown
    exportieren, importieren und abgleichen, damit Claude sie auch in der
    Cloud nutzen kann; Markdown ist dabei nur Sync-Option.
  - Notes: `items/STORY-047/STORY-047_notes.md`.
  - Spec: `items/STORY-047/STORY-047_spec.md`.

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

- `TASK-024` **Notes-Dateiformat: Serialisieren und Parsen mit Golden-Files**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Eine Note mit Kurzfassung, Status, Topic-Pfad, Prüf-Datum,
    Auslösern, Modus, Links und Langtext (sowie die Topic-Struktur) lässt
    sich in Markdown-Text umwandeln und wieder einlesen. Der Round-Trip
    verliert nichts. Das Format ist durch Golden-Files festgelegt.
  - Completion criteria: Round-Trip ohne Verlust für Text, Status, Topic,
    Prüf-Datum, Auslöser, Modus, Links und Termine; Golden-File-Tests pinnen
    das Format; scripts/check.sh ist grün.
  - Summary: Reine Funktionen, die Notes und Topics in Markdown-Dateien
    schreiben und wieder einlesen, ohne Verlust.
  - Spec: `items/TASK-024/TASK-024_spec.md`.

- `TASK-025` **Notes-Spiegel: Port und Datei-Adapter mit atomarem Schreiben**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-024`.
  - Goal: Es gibt einen Port NotesMirror und einen Datei-Adapter, der pro
    Projekt den Ordner notes/ im Spiegel-Ordner liest und schreibt:
    NOTE-xxx.md, die zugehörigen Notizen-/Spec-Dateien und topics.md.
    Schreiben ist atomar; eine Datei, die sich seit dem Lesen geändert hat,
    führt zu einem Konfliktfehler. Ob der Spiegel sich geändert hat, lässt
    sich ohne Änderung erkennen.
  - Completion criteria: Lesen, Schreiben, atomares Ersetzen, Konflikt und
    Änderungserkennung sind per Test abgedeckt; die Importlinter-Regeln
    halten; scripts/check.sh ist grün.
  - Summary: Port und Adapter, die Notes samt Dokumenten als Dateien in den
    Spiegel-Ordner schreiben und von dort lesen, atomar und mit
    Konflikterkennung.
  - Spec: `items/TASK-025/TASK-025_spec.md`.

- `TASK-026` **Notes-Sync: Vorschau, Richtung, Konflikte und Label-Kollisionen**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-025`.
  - Goal: Ein Sync-Use-Case gleicht die Notes eines Projekts zwischen
    Datenbank und Notes-Spiegel ab. Er bietet eine Vorschau, löscht nichts
    ohne Bestätigung, lässt die Richtung wählen (Standard: Datenbank →
    Spiegel) und bricht bei Konflikten ab. Beim Import vergibt die
    Zielumgebung für fehlende Labels neue; bei Kollisionen entscheidet die
    Vorschau. Der Round-Trip verliert nichts.
  - Completion criteria: Round-Trip ohne Verlust von Text, Notizen, Specs,
    Links, Auslösern und Terminen (Golden-File-Test über die ganze Kette);
    Vorschau, Richtung, Konfliktabbruch und Kollisionsbehandlung sind
    getestet; Änderungs-Erkennung funktioniert; scripts/check.sh ist grün.
  - Summary: Sync-Use-Case, der Notes zwischen Datenbank und Spiegel
    abgleicht, mit Vorschau, Richtungswahl, Konfliktabbruch und
    Label-Kollisionsbehandlung beim Import.
  - Spec: `items/TASK-026/TASK-026_spec.md`.

- `TASK-027` **Notes-Sync im Einstellungsmenü bedienen**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-026`.
  - Goal: Der Besitzer kann im Einstellungsmenü für ein Projekt den
    Notes-Sync starten: Richtung wählen, Vorschau ansehen, Kollisionen
    entscheiden, Löschen bestätigen und ausführen. Ein geänderter Spiegel
    wird angezeigt.
  - Completion criteria: Vorschau, Richtungswahl, Kollisionsentscheidung,
    Bestätigung des Löschens und Ausführen sind in der UI möglich; der
    Status 'Spiegel extern geändert' erscheint; Komponententests;
    scripts/check.sh ist grün.
  - Summary: Im Sync-Dialog der Projekte lässt sich der Notes-Sync mit
    Vorschau, Richtung und Entscheidungen ausführen; der Änderungsstatus
    wird angezeigt.
  - Spec: `items/TASK-027/TASK-027_spec.md`.

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
