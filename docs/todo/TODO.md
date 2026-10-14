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
  - Dependencies: `STORY-057`, `STORY-058`.
  - Goal: Notes mit Topics, Links, Auslösern, Dokumenten sowie Archiv- und
    Papierkorbstand lassen sich als Markdown-Dateien im Spiegel-Ordner des
    Projekts ablegen und wieder einlesen — im selben Sync, mit derselben
    Vorschau, demselben Status und denselben Konfliktentscheidungen wie der
    Backlog (STORY-057, STORY-058). So kann Claude Notes in der Cloud
    (claude.ai) als Dateien lesen und bearbeiten; sie kommen über Git zurück
    und werden lokal in die Datenbank übernommen. Notes bleiben in API und
    Datenbank zu Hause, Markdown ist nur Export, Import und Sync-Option. In
    den Dateien neu angelegte Notes tragen kein Label; die Datenbank vergibt
    es beim Import. Links bleiben im Spiegel Verweise auf Labels.
  - Completion criteria: - Round-Trip Datenbank → Dateien → leere Datenbank
    ohne Verlust von Text, Notizen, Specs, Links, Auslösern (inkl. fired_at
    und already_met), Terminen, Topic-Baum, Archiv- und Papierkorbstand und
    Label-Zählern. - Notes und Backlog laufen in einem Sync (eine Vorschau,
    ein Status, ein Konflikt-Dialog). - Eine in den Dateien ohne Label
    angelegte Note erhält beim Import das nächste freie Label; die Datei
    heißt danach NOTE-xxx.md; Verweise darauf werden umgeschrieben. - Links
    auf unbekannte Ziele bleiben erhalten. - Änderungshinweise werden nicht
    gespiegelt. - Das Dateiformat ist in docs/techdocs/interfaces.md
    beschrieben, damit der Harness dagegen bauen kann. - Tests und
    scripts/check.sh sind grün.
  - Summary: Notes (mit Topics, Links, Auslösern und Dokumenten) lassen sich
    im selben Sync wie der Backlog als Markdown ablegen und einlesen, damit
    Claude sie in der Cloud nutzen kann; Markdown bleibt nur Sync-Option.
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
  - Goal: Eine Note mit Kurzfassung, Status, Topic (Label), Prüf-Datum,
    Auslösern (inkl. fired_at und already_met), Modus, Links,
    Created/Updated, Archiv- und Papierkorbstand und Langtext, die
    Topic-Struktur und die Label-Zähler lassen sich in Markdown-Text
    umwandeln und wieder einlesen. Auch Notes und Topics ohne Label (in der
    Cloud angelegt) sind Teil des Formats. Der Round-Trip verliert nichts.
    Das Format ist durch Golden-Files festgelegt.
  - Completion criteria: Round-Trip ohne Verlust für Text, Status, Topic,
    Prüf-Datum, Auslöser, Modus, Links, Termine, Created/Updated, Archiv-
    und Papierkorbstand und Zähler; Notes und Topics ohne Label sind
    abgedeckt; Golden-File-Tests pinnen das Format; scripts/check.sh ist
    grün.
  - Summary: Reine Funktionen, die Notes und Topics in Markdown-Dateien
    schreiben und wieder einlesen, ohne Verlust.
  - Notes: `items/TASK-024/TASK-024_notes.md`.
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
  - Goal: Es gibt einen Port NotesMirror und einen Datei-Adapter (Paket
    infrastructure/notes_files/), der pro Projekt den Ordner notes/ im
    Spiegel-Ordner liest und schreibt: NOTE-xxx.md, die zugehörigen
    Notizen-/Spec-Dateien, topics.md und counters.md, auch Notes ohne Label
    (new-<kurzname>.md) sowie archivierte und Papierkorb-Notes. Schreiben
    ist atomar; eine Datei, die sich seit dem Lesen geändert hat, führt zu
    einem Konfliktfehler. Ob der Spiegel sich geändert hat, lässt sich ohne
    Änderung erkennen.
  - Completion criteria: Lesen, Schreiben, atomares Ersetzen, Konflikt und
    Änderungserkennung sind per Test abgedeckt; die Importlinter-Regeln
    halten; scripts/check.sh ist grün.
  - Summary: Port und Adapter, die Notes samt Dokumenten als Dateien in den
    Spiegel-Ordner schreiben und von dort lesen, atomar und mit
    Konflikterkennung.
  - Notes: `items/TASK-025/TASK-025_notes.md`.
  - Spec: `items/TASK-025/TASK-025_spec.md`.

- `TASK-026` **Notes in den gemeinsamen Sync aufnehmen**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-024`, `TASK-025`, `TASK-033`.
  - Goal: Topics, Notes, Links, Auslöser, Note-Dokumente und Label-Zähler
    laufen im bestehenden Sync (derselbe Endpunkt, dieselbe Vorschau,
    dasselbe Token, derselbe Status, dieselben Konfliktentscheidungen aus
    STORY-057). Beim Import erhalten Notes und Topics ohne Label das nächste
    freie Label des Projekts, Verweise darauf werden umgeschrieben, die
    Zähler laufen weiter, Labels werden nie wiederverwendet. Notes liegen
    immer in der Datenbank, die Dateiseite ist für Notes immer der Spiegel.
    Der Round-Trip verliert nichts.
  - Completion criteria: - Round-Trip Datenbank → Spiegel → leere Datenbank
    (Golden-File-Test über die ganze Kette) ohne Verlust von Text, Notizen,
    Specs, Links, Auslösern inkl. fired_at und already_met, Terminen,
    Topic-Baum, Archiv- und Papierkorbstand und Zählern. - Vorschau, Status
    (Spiegel extern geändert, Konflikte) und Ausführen decken Backlog und
    Notes gemeinsam ab; Konflikte werden wie im Backlog entschieden. -
    Label-lose Notes bekommen beim Import ein neues Label; Verweise werden
    umgeschrieben; der Zähler steigt nie rückwärts. - Links auf unbekannte
    Ziele bleiben erhalten. - Tests (inkl. Prüfung an einer Kopie der echten
    Datenbank); scripts/check.sh ist grün.
  - Summary: Sync-Use-Case, der Notes zwischen Datenbank und Spiegel
    abgleicht, mit Vorschau, Richtungswahl, Konfliktabbruch und
    Label-Kollisionsbehandlung beim Import.
  - Notes: `items/TASK-026/TASK-026_notes.md`.
  - Spec: `items/TASK-026/TASK-026_spec.md`.

- `TASK-027` **Notes im gemeinsamen Sync-Dialog bedienen**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-026`, `STORY-058`.
  - Goal: Der gemeinsame Sync-Dialog (Einstellungsmenü) zeigt in der
    Vorschau auch Topics, Notes und Note-Dokumente (neu, geändert,
    unverändert, nur im Ziel) und nutzt für Konflikte den Konflikt-Dialog
    aus STORY-058. Der Status „Spiegel extern geändert“ und die Zahl offener
    Konflikte erfassen Notes mit. Es gibt keinen eigenen Notes-Sync-Dialog.
  - Completion criteria: - Die Vorschau im Sync-Dialog listet auch Topics,
    Notes und Note-Dokumente. - Konflikte bei Notes werden im
    Konflikt-Dialog entschieden (Datenbank, Datei, aufschieben). - Das
    Statussymbol erscheint auch bei extern geänderten Notes-Dateien. -
    Komponenten- und Unit-Tests; Screenshot als Beleg; scripts/check.sh ist
    grün.
  - Summary: Im Sync-Dialog der Projekte lässt sich der Notes-Sync mit
    Vorschau, Richtung und Entscheidungen ausführen; der Änderungsstatus
    wird angezeigt.
  - Notes: `items/TASK-027/TASK-027_notes.md`.
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

- `STORY-057` **Abgleich pro Eintrag mit Konfliktmeldung**
  - Type: Story.
  - Parent: `EPIC-006`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-14.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Sync zwischen Datenbank und Markdown-Spiegel merkt sich für
    jeden Eintrag (Item, Papierkorb-Eintrag, Dokument), welchen Stand er
    beim letzten Sync hatte, und erkennt dadurch pro Eintrag, welche Seite
    ihn geändert hat. Ein Lauf überträgt jeden Eintrag von der Seite, die
    ihn geändert hat, auf die andere (beidseitiger Abgleich). Wurde ein
    Eintrag auf beiden Seiten geändert, auf beiden Seiten mit derselben ID
    neu angelegt oder auf einer Seite gelöscht, meldet der Sync einen
    Konflikt und überschreibt oder löscht nichts. Beim Ausführen wird je
    Konflikt Datenbank, Datei oder Aufschieben gewählt; aufgeschobene
    Konflikte bleiben auf beiden Seiten unberührt und werden beim nächsten
    Abgleich wieder gemeldet. Vor jeder Schema-Migration und vor jedem Sync,
    der in die Datenbank schreibt, legt der Viewer automatisch ein Backup
    an. So lässt sich der Backlog zwischen Rechnern und Cloud über Git
    abgleichen, ohne dass Änderungen stillschweigend verloren gehen.
  - Completion criteria: - Änderung auf beiden Seiten, dieselbe neue ID auf
    beiden Seiten oder Löschung auf einer Seite führt nie zu stillem
    Überschreiben, Löschen oder Wiederbeleben, sondern zu einem gemeldeten
    Konflikt. - Ein Lauf überträgt konfliktfreie Änderungen in beide
    Richtungen; `direction` schränkt nur ein. - Jeder Konflikt lässt sich
    per API mit Datenbank, Datei oder Aufschieben entscheiden; Einträge ohne
    Konflikt werden trotz aufgeschobener Konflikte abgeglichen. - Der
    Sync-Status nennt die Zahl der offenen Konflikte. - Der Stand je Eintrag
    überlebt die Migration der echten Datenbank (an einer Kopie geprüft). -
    Vor Migration und datenbankschreibendem Sync liegt ein Backup in
    configs/backups. - Tests und scripts/check.sh sind grün; Architektur-
    und Technikdoku sind aktuell.
  - Summary: Der Sync merkt sich pro Eintrag den Stand des letzten
    Abgleichs, meldet echte Konflikte statt zu überschreiben und lässt dich
    je Konflikt zwischen Datenbank, Datei und Aufschieben wählen.
  - Notes: `items/STORY-057/STORY-057_notes.md`.
  - Spec: `items/STORY-057/STORY-057_spec.md`.

- `STORY-058` **Konflikte im Sync mit Diff-Ansicht entscheiden**
  - Type: Story.
  - Parent: `EPIC-006`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-14.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-057`.
  - Goal: Im Sync-Dialog des Einstellungsmenüs zeigt die UI die Konflikte
    des Abgleichs einzeln an: Items feldweise nebeneinander (Datenbank und
    Datei), Dokumente und Texte als Textvergleich mit hervorgehobenen
    Unterschieden. Zu jedem Konflikt wählt der Besitzer Datenbank
    übernehmen, Datei übernehmen oder Aufschieben; ausgeführt wird erst nach
    Bestätigung. Aufgeschobene Konflikte bleiben als offen sichtbar, sodass
    der Besitzer sie später nach händischen Änderungen wieder aufnehmen
    kann.
  - Completion criteria: - Der Sync-Dialog zeigt jeden Konflikt mit beiden
    Fassungen und den Unterschieden (Items feldweise, Texte als
    Textvergleich). - Pro Konflikt sind die drei Entscheidungen möglich; sie
    gehen mit der Bestätigung an die API. Ausführen ist erst nach der
    Vorschau möglich. - Aufgeschobene Konflikte erscheinen im Status als
    offen (Zahl) und werden beim nächsten Sync wieder angeboten. -
    Komponenten- und Unit-Tests; Screenshot als Beleg; scripts/check.sh
    grün; Doku aktuell.
  - Summary: Im Sync-Dialog siehst du jeden Konflikt mit beiden Fassungen
    und den Unterschieden und entscheidest pro Konflikt: Datenbank
    übernehmen, Datei übernehmen oder aufschieben.
  - Notes: `items/STORY-058/STORY-058_notes.md`.
  - Spec: `items/STORY-058/STORY-058_spec.md`.

- `TASK-031` **Automatisches Datenbank-Backup vor Migration und Sync**
  - Type: Task.
  - Parent: `STORY-057`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-14.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Datenbank wird automatisch gesichert, bevor eine
    Schema-Migration läuft und bevor ein Sync in die Datenbank schreibt. Die
    Sicherung ist eine konsistente Kopie (auch im WAL-Betrieb) in
    configs/backups und besteht eine Integritätsprüfung; von den automatisch
    angelegten Sicherungen bleiben die letzten 10. Scheitert die Sicherung,
    läuft die Migration bzw. der Sync nicht, und der Fehler wird gemeldet.
  - Completion criteria: - Vor jeder Migration, die etwas ändert, und vor
    jedem Sync, der in die Datenbank schreibt, liegt ein Backup (Dateiname
    mit Zeitstempel und Anlass). - Test mit festgelegter Uhr: Dateiname und
    Aufbewahrung der letzten 10; von Hand angelegte Sicherungen bleiben
    unberührt. - Scheitert das Backup, bleiben Datenbank und Spiegel
    unverändert, und der Fehler kommt mit stabilem Code zurück. - Das Backup
    besteht die Integritätsprüfung. - scripts/check.sh grün; Betriebsdoku
    beschreibt Ort und Aufbewahrung.
  - Summary: Vor jeder Migration und vor jedem Sync, der die Datenbank
    ändert, legt der Viewer selbst eine geprüfte Sicherung an; bei einem
    Fehler geht so nichts verloren.
  - Spec: `items/TASK-031/TASK-031_spec.md`.

- `TASK-032` **Stand je Eintrag speichern und Änderungsseite erkennen**
  - Type: Task.
  - Parent: `STORY-057`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-14.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-031`.
  - Goal: Nach jedem Sync speichert die Datenbank pro Eintrag (Item,
    Papierkorb-Eintrag, Dokument) dessen Stand; eine versionierte Migration
    legt die Tabelle an. Die Sync-Vorschau nennt pro Eintrag, welche Seite
    ihn seit dem letzten Sync geändert hat (keine, Datenbank, Datei, beide,
    auf beiden Seiten neu, auf einer Seite gelöscht), und zählt die
    Konflikte (beide geändert, beidseitig neu mit verschiedenem Inhalt,
    gelöscht); der Sync-Status nennt diese Zahl. Für Einträge ohne
    gespeicherten Stand (vor dem ersten Sync nach der Migration) gilt: nur
    auf einer Seite vorhanden = dort neu; auf beiden Seiten vorhanden und
    verschieden = Konflikt.
  - Completion criteria: - Nach einem Sync ist der Stand jedes abgeglichenen
    Eintrags gespeichert; die Migration läuft an einer Kopie der echten
    Datenbank fehlerfrei. - Die Vorschau unterscheidet pro Eintrag:
    unverändert, nur Datenbank geändert, nur Datei geändert, beide geändert,
    auf beiden Seiten neu. - Der Sync-Status enthält die Zahl der Konflikte.
    - Die Klassifikation ist eine reine Funktion in domain mit Unit-Tests
    für alle Fälle; Contract-Test für den neuen Speicher; scripts/check.sh
    grün; Technikdoku aktuell.
  - Summary: Der Sync merkt sich pro Eintrag den Stand des letzten Abgleichs
    und zeigt in der Vorschau, welche Seite was geändert hat und wo echte
    Konflikte liegen.
  - Spec: `items/TASK-032/TASK-032_spec.md`.

- `TASK-033` **Konflikte beim Sync entscheiden: Datenbank, Datei oder aufschieben**
  - Type: Task.
  - Parent: `STORY-057`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-14.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-032`.
  - Goal: Der Sync-Aufruf nimmt je Konflikt eine Entscheidung entgegen:
    Datenbank übernehmen, Datei übernehmen oder aufschieben; das gilt auch
    für Löschungen auf einer Seite. Entschiedene Konflikte werden in die
    gewählte Richtung übertragen. Aufgeschobene und nicht entschiedene
    Konflikte bleiben auf beiden Seiten unverändert und behalten ihren alten
    Stand, sodass sie beim nächsten Abgleich wieder gemeldet werden. Alle
    Einträge ohne Konflikt werden regulär abgeglichen, in beide Richtungen.
    Die Vorschau liefert zu jedem Konflikt beide Fassungen (Item-Felder bzw.
    Dokumenttext), damit eine UI sie vergleichen kann; das Token schützt wie
    bisher vor Änderungen zwischen Vorschau und Ausführen.
  - Completion criteria: - Entscheidung „Datenbank“ überschreibt die Datei,
    „Datei“ überschreibt die Datenbank, „aufschieben“ ändert an dem Eintrag
    nichts. - Ein Lauf mit aufgeschobenen Konflikten gleicht alle übrigen
    Einträge ab; der nächste Lauf meldet die aufgeschobenen wieder. - Ein
    Konflikt ohne Entscheidung gilt als aufgeschoben (der Lauf bricht nicht
    ab). - Macht der Besitzer beide Seiten eines aufgeschobenen Eintrags von
    Hand gleich, ist der Konflikt danach weg. - Tests für jede Entscheidung,
    den Mischfall und das Token; OpenAPI neu erzeugt; scripts/check.sh grün;
    Technikdoku aktuell.
  - Summary: Beim Ausführen des Syncs wählst du pro Konflikt Datenbank,
    Datei oder Aufschieben; Aufgeschobenes bleibt unberührt und wird beim
    nächsten Abgleich wieder gemeldet.
  - Spec: `items/TASK-033/TASK-033_spec.md`.

- `STORY-059` **Auto-Sync für Projekte mit Spiegel (abschaltbar)**
  - Type: Story.
  - Parent: `EPIC-006`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-14.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-057`.
  - Goal: Der Viewer gleicht ein Projekt mit Spiegel-Ordner automatisch ab,
    wenn sich eine Seite geändert hat, zum Beispiel nach einem Pull aus der
    Cloud, ohne dass der Besitzer daran denken muss. Der Auto-Sync ist pro
    Projekt ein- und ausschaltbar (Standard: aus). Er überträgt alles
    Konfliktfreie in die jeweils andere Seite. Konflikte, Löschungen und
    Unlesbares überträgt er nie, sondern lässt sie offen und zeigt sie an,
    bis der Besitzer im Sync-Dialog entscheidet. Vor einem Lauf, der in die
    Datenbank schreibt, liegt ein Backup (mit Aufbewahrung, die häufige
    Läufe aushält). Letzter Lauf und Zahl offener Konflikte sind sichtbar.
  - Completion criteria: - Pro Projekt gibt es einen Schalter im
    Einstellungsmenü und in der API (Standard: aus). Ausgeschaltet verändert
    der Viewer nichts von selbst. - Eingeschaltet übernimmt der Viewer
    Änderungen der Dateien (z. B. nach einem Pull) und der Datenbank
    innerhalb des eingestellten Intervalls in die jeweils andere Seite, ohne
    Klick; beim Start läuft ein Abgleich. - Konflikte und Löschungen werden
    nie automatisch übertragen; sie bleiben offen und im Status sichtbar. -
    Dateien mit Git-Merge-Markern oder unlesbare Dateien werden nicht
    eingelesen; der Lauf pausiert mit Meldung. Ein noch laufender Pull wird
    abgewartet (Beruhigungszeit). - Vor einem automatischen Lauf, der in die
    Datenbank schreibt, liegt ein Backup; häufige Läufe verdrängen ältere
    Sicherungen nicht. - Tests ohne echten Timer (feste Uhr);
    Architekturregel §1 ist geändert und vom Besitzer freigegeben;
    scripts/check.sh grün; Doku aktuell.
  - Summary: Der Viewer gleicht ein Projekt mit Spiegel-Ordner von selbst
    ab, wenn du den Schalter eingeschaltet hast, damit du nach einem Pull
    aus der Cloud den Sync nicht vergessen kannst. Konflikte und Löschungen
    bleiben offen, bis du entscheidest.
  - Spec: `items/STORY-059/STORY-059_spec.md`.
