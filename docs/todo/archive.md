# Projekt-Backlog-Archiv

Erledigte und abgelehnte Einträge, nach Entscheidung des Projektverantwortlichen
unverändert aus `TODO.md` hierher verschoben.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `STORY-047` **Notes in Markdown spiegeln und zwischen Rechnern abgleichen**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/STORY-047/STORY-047_notes.md`.
  - Spec: `items/STORY-047/STORY-047_spec.md`.

- `TASK-024` **Notes-Dateiformat: Serialisieren und Parsen mit Golden-Files**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/TASK-024/TASK-024_notes.md`.
  - Spec: `items/TASK-024/TASK-024_spec.md`.

- `TASK-025` **Notes-Spiegel: Port und Datei-Adapter mit atomarem Schreiben**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/TASK-025/TASK-025_notes.md`.
  - Spec: `items/TASK-025/TASK-025_spec.md`.

- `TASK-026` **Notes in den gemeinsamen Sync aufnehmen**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/TASK-026/TASK-026_notes.md`.
  - Spec: `items/TASK-026/TASK-026_spec.md`.

- `TASK-027` **Notes im gemeinsamen Sync-Dialog bedienen**
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/TASK-027/TASK-027_notes.md`.
  - Spec: `items/TASK-027/TASK-027_spec.md`.

- `STORY-057` **Abgleich pro Eintrag mit Konfliktmeldung**
  - Type: Story.
  - Parent: `EPIC-006`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/STORY-057/STORY-057_notes.md`.
  - Spec: `items/STORY-057/STORY-057_spec.md`.

- `STORY-058` **Konflikte im Sync mit Diff-Ansicht entscheiden**
  - Type: Story.
  - Parent: `EPIC-006`.
  - Required for parent: No.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/STORY-058/STORY-058_notes.md`.
  - Spec: `items/STORY-058/STORY-058_spec.md`.

- `TASK-031` **Automatisches Datenbank-Backup vor Migration und Sync**
  - Type: Task.
  - Parent: `STORY-057`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/TASK-031/TASK-031_notes.md`.
  - Spec: `items/TASK-031/TASK-031_spec.md`.

- `TASK-032` **Stand je Eintrag speichern und Änderungsseite erkennen**
  - Type: Task.
  - Parent: `STORY-057`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/TASK-032/TASK-032_notes.md`.
  - Spec: `items/TASK-032/TASK-032_spec.md`.

- `TASK-033` **Konflikte beim Sync entscheiden: Datenbank, Datei oder aufschieben**
  - Type: Task.
  - Parent: `STORY-057`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/TASK-033/TASK-033_notes.md`.
  - Spec: `items/TASK-033/TASK-033_spec.md`.

- `STORY-059` **Auto-Sync für Projekte mit Spiegel (abschaltbar)**
  - Type: Story.
  - Parent: `EPIC-006`.
  - Required for parent: No.
  - Status: Completed.
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
  - Resolution: Vom Besitzer am 2026-10-16 abgenommen; umgesetzt in der
    Cloud (Block A bis C), lokal geprüft und mit v0.8.8 ausgerollt.
  - Notes: `items/STORY-059/STORY-059_notes.md`.
  - Spec: `items/STORY-059/STORY-059_spec.md`.

- `STORY-001` **Bessere Platzierung der Fortschritts-Pie-Charts**
  - Type: Story.
  - Parent: None.
  - Status: Completed.
  - Created: 2026-09-25.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Fortschritts-Pie-Charts sitzen sichtbar beim zugehörigen Namen
    (z. B. direkt dahinter oder am Namen ausgerichtet) statt abgesetzt
    davon. Die genaue Platzierung wird vorher besprochen.
  - Completion criteria: Die abgestimmte Platzierung ist in den betroffenen
    Ansichten umgesetzt und vom Projektverantwortlichen geprüft.
  - Summary: Die kleinen Fortschrittskreise sollen näher an den Namen der
    Einträge rücken. Wie genau, ist noch offen.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-001/STORY-001_notes.md`.

- `STORY-002` **Alle Tasks/Stories ein- und ausklappen**
  - Type: Story.
  - Parent: None.
  - Status: Completed.
  - Created: 2026-09-25.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Eine Bedienoption klappt mit einem Klick alle Tasks und Stories
    auf bzw. zu.
  - Completion criteria: Die Option ist in der UI vorhanden; ein Klick
    klappt alle Einträge auf, ein weiterer alle zu.
  - Summary: Zwei Buttons im Baum klappen alle Epics bzw. alle Stories auf
    oder zu – für markierte Projekte oder, ohne Markierung, für alle.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-002/STORY-002_notes.md`.

- `STORY-003` **Items nur über ID adressieren**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Items werden in API, Application-Ports und UI nur über `source_id`
    und ID angesprochen. `location` und `line` verschwinden aus dem Vertrag;
    „archiviert“ ist ein Attribut des Items. Externe Änderungen werden über
    ein undurchsichtiges Versions-Token erkannt. `GET
    /api/v2/items/{source_id}/{id}` liefert ein einzelnes Item, egal ob
    aktiv oder archiviert.
  - Completion criteria: Einzelabruf und Bearbeiten funktionieren nur mit ID
    und Versions-Token; ein veraltetes Token führt zu einem Konfliktfehler;
    eine unbekannte ID liefert 404 mit stabilem Code; die UI nutzt die neue
    Adressierung; Golden-File-Tests bleiben grün.
  - Summary: Einträge werden nur noch über ihre ID angesprochen, nicht mehr
    über Datei und Zeile. Einfache Checklisten ohne IDs werden nicht mehr
    unterstützt.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-003/STORY-003_notes.md`.

- `STORY-005` **Parent-Lifecycle-Regeln im Domain erzwingen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Regeln des Backlog-Formats (Epic ohne Parent, Pflichtfeld
    `Required for parent`, Pflichtkind vor Verlassen von Open, Blockade
    durch offene oder abgelehnte Pflichtkinder, kein Abschluss mit aktiven
    Kindern, keine Zyklen in Parent und Dependencies) werden im Domain
    geprüft und bei jeder Änderung durchgesetzt.
  - Completion criteria: Verstöße liefern Fehler mit stabilen Codes; jede
    Regel ist durch Domain-Tests abgedeckt; die UI übersetzt die neuen
    Codes.
  - Summary: Der Server lehnt Änderungen ab, die gegen die Regeln für Epics,
    Stories und ihre Kinder verstoßen, statt das dem Agenten zu überlassen.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-005/STORY-005_notes.md`.

- `STORY-006` **Weitere Felder bearbeitbar**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`, `STORY-005`.
  - Goal: Über die API lassen sich zusätzlich Titel, Goal, Completion
    criteria, Summary, Area, Parent und Dependencies ändern; Dependencies
    werden als Liste übergeben.
  - Completion criteria: Jedes Feld ist per API änderbar, Änderungen
    betreffen nur das Feld (Golden Files), Lifecycle-Regeln greifen bei
    Parent- und Dependency-Änderungen.
  - Summary: Über die API lassen sich jetzt auch Titel, Texte, Area, Parent
    und Abhängigkeiten ändern, mehrere Felder in einem Schritt.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-006/STORY-006_notes.md`.

- `STORY-008` **Items löschen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`.
  - Goal: `DELETE /api/v2/items/{source_id}/{id}` entfernt ein Item. Solange
    andere Items per Parent oder Dependencies darauf verweisen, wird das
    Löschen mit einem Konfliktfehler abgelehnt.
  - Completion criteria: Löschen ohne Verweise entfernt genau den Eintrag;
    Löschen mit Verweisen liefert einen Konfliktfehler, der die verweisenden
    IDs nennt.
  - Summary: Ein Item wird samt seiner Notes- und Spec-Dateien gelöscht,
    aber nicht, solange andere Items darauf verweisen.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-008/STORY-008_notes.md`.

- `STORY-009` **Notes und Specs über das Item schreiben**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`.
  - Goal: Notes und Specs werden über das Item adressiert statt über
    Dateipfade: Lesen und Ersetzen von Specs mit Versions-Token sowie ein
    strukturierter Endpunkt, der einen datierten Notes-Eintrag
    (Discussed/Decided/Open) anhängt. Der Server pflegt dabei die Felder
    `Notes`, `Spec` und die Pflicht zur `Summary`.
  - Completion criteria: Notes-Einträge und Specs lassen sich ohne Kenntnis
    von Dateipfaden lesen und schreiben; konkurrierende Änderungen liefern
    Konfliktfehler; das Format der Notes entspricht dem Backlog-Format.
  - Summary: Notizen und Specs lassen sich über das Item lesen und
    schreiben, ohne Dateipfade zu kennen.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-009/STORY-009_notes.md`.

- `STORY-010` **API-Zugang für Agenten**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`, `STORY-004`, `STORY-005`, `STORY-006`,
    `STORY-007`, `STORY-008`, `STORY-009`.
  - Goal: Ein Agent kann die API zuverlässig erreichen und nutzen; es ist
    geklärt und umgesetzt, wie der Server für Agenten verfügbar ist
    (dauerhaft laufend, bei Bedarf gestartet oder anderer Weg), und die
    Nutzung ist in den techdocs beschrieben.
  - Completion criteria: Die Zugangsvariante ist mit dem
    Projektverantwortlichen entschieden und umgesetzt; README bzw. techdocs
    beschreiben die Agent-Nutzung; ein Agent kann damit einen vollständigen
    Pflege-Durchlauf ohne Dateizugriff ausführen.
  - Summary: Agenten sprechen den dauerhaft laufenden Container per HTTP an;
    der Umgang mit einem nicht erreichbaren Server liegt im Harness.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-010/STORY-010_notes.md`.

- `STORY-011` **Papierkorb: Löschen markiert, Wiederherstellen und endgültig Löschen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-008`.
  - Goal: Löschen markiert ein Item als gelöscht, statt es zu entfernen.
    Gelöschte Items liegen in einem Papierkorb mit eigener Route, aus dem
    sie wiederhergestellt oder endgültig gelöscht werden. Löschen und
    Wiederherstellen kaskadieren auf Kind-Items; vorher warnt die API und
    verlangt eine Bestätigung.
  - Completion criteria: Gelöschte Items verschwinden aus Übersicht und
    Index und erscheinen im Papierkorb; Wiederherstellen und endgültiges
    Löschen funktionieren samt Kindern; ohne Bestätigung liefert die API
    eine Warnung mit den betroffenen Kindern; Tests und Doku sind vorhanden.
  - Summary: Gelöschte Einträge landen erst im Papierkorb und können
    zurückgeholt werden.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-011/STORY-011_notes.md`.

- `STORY-012` **Felder im Bearbeiten-Modus ändern**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-006`.
  - Goal: Im Detail-Panel öffnet ein Knopf „Bearbeiten“ ein Formular für
    Titel, Goal, Completion criteria, Summary, Area, Parent und
    Dependencies. Speichern schreibt alle Änderungen in einem Schritt,
    Abbrechen verwirft sie. Bei einem Versionskonflikt bleiben die Eingaben
    erhalten und der aktuelle Stand wird angezeigt.
  - Completion criteria: Alle genannten Felder sind über den
    Bearbeiten-Modus änderbar; ohne Bearbeiten-Modus ist nichts
    versehentlich änderbar; Regelverstöße und Versionskonflikte werden
    verständlich angezeigt; Komponententests decken Speichern, Abbrechen und
    Konflikt ab.
  - Summary: Einträge lassen sich über einen eigenen Bearbeiten-Modus
    ändern, nicht durch versehentliches Klicken.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-012/STORY-012_notes.md`.

- `STORY-013` **Items in der UI anlegen**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-007`.
  - Goal: Ein Knopf „Neu“ oben legt ein Epic, eine Story oder einen Task
    ohne Parent an; „Kind anlegen“ im Detail-Panel belegt den Parent vor.
    Der Dialog fragt Typ und Pflichtfelder ab und wählt das neue Item danach
    aus.
  - Completion criteria: Anlegen funktioniert über beide Einstiege;
    Pflichtfelder und Regelverstöße werden im Dialog gemeldet;
    Komponententests vorhanden.
  - Summary: Neue Einträge lassen sich direkt in der Oberfläche anlegen.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-013/STORY-013_notes.md`.

- `STORY-014` **Löschen und Papierkorb-Ansicht**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-011`.
  - Goal: Im Detail-Panel verschiebt „Löschen“ ein Item in den Papierkorb;
    hat es Kinder, zeigt die UI sie als Warnung und löscht sie erst nach
    Bestätigung mit. Eine eigene Ansicht „Papierkorb“ neben Baum,
    Abhängigkeiten und Kanban listet gelöschte Items und bietet
    Wiederherstellen und endgültiges Löschen.
  - Completion criteria: Löschen, Wiederherstellen und endgültiges Löschen
    sind in der UI bedienbar, jeweils samt Kindern; endgültiges Löschen
    verlangt eine Bestätigung; Komponententests vorhanden.
  - Summary: Gelöschte Einträge landen in einer eigenen Papierkorb-Ansicht
    und lassen sich zurückholen oder endgültig entfernen.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-014/STORY-014_notes.md`.

- `STORY-015` **Notes und Specs in der UI schreiben und ändern**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-009`.
  - Goal: Im Dokument-Dialog lässt sich ein Notes-Eintrag (Thema, Discussed,
    Decided, Open) anhängen, und Notizen wie Specs lassen sich als ganzer
    Text mit Markdown-Vorschau ändern oder neu anlegen: GET holt den Text,
    PUT schreibt den neuen. Beim ersten Notes-Dokument fragt die UI nach
    einer Summary, falls keine vorhanden ist.
  - Completion criteria: Notes-Einträge anhängen sowie Notizen und Specs
    ändern und anlegen funktioniert in der UI und per API; Versionskonflikte
    werden gemeldet, ohne die Eingabe zu verlieren; Komponententests
    vorhanden.
  - Summary: Notizen und Specs lassen sich direkt in der Oberfläche
    schreiben und nachträglich ändern.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt.
  - Notes: `items/STORY-015/STORY-015_notes.md`.

- `TASK-001` **Area im Lean Index**
  - Type: Task.
  - Parent: `STORY-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: `GET /api/v2/index` liefert je Item zusätzlich `area`
    (`IndexItemOut` in `backend/todo_viewer/api/v2/schemas.py`), damit sich
    aus der flachen Liste besser einschätzen lässt, welche Items relevant
    sind, bevor einzelne mit `show` geladen werden.
  - Completion criteria: Das OpenAPI-Schema des Index enthält `area`;
    API-Tests prüfen `area` für aktive und archivierte Items;
    `docs/techdocs/interfaces.md` beschreibt das Feld; `backlog_api.py
    index` im Claude_Harness zeigt die Area ohne weitere Änderung an.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt: GET
    /api/v2/index liefert area (fb61bd5).

- `STORY-004` **Lean Index**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: `GET /api/v2/index` liefert für aktive und archivierte Items nur
    `source_id`, `id`, `type`, `status`, `title`, `parent` und `area`,
    optional gefiltert auf eine Quelle.
  - Completion criteria: Der Endpunkt hat ein festes Schema im
    OpenAPI-Vertrag, liefert genau diese Felder und ist durch API-Tests
    abgedeckt.
  - Summary: Die Übersichtsliste aller Einträge soll schlank bleiben. Sie
    zeigt nur das Nötigste, jetzt zusätzlich den Bereich, damit man
    schneller sieht, welche Einträge man sich genauer ansehen muss.
  - Resolution: Vom Projektverantwortlichen am 2026-09-28 bestätigt: Lean
    Index mit festem Schema inkl. area, durch API-Tests abgedeckt (fb61bd5,
    TASK-001).
  - Notes: `items/STORY-004/STORY-004_notes.md`.

- `STORY-017` **Klare Antwort und Wiederöffnen-Angebot bei geschlossenem Parent**
  - Type: Story.
  - Parent: None.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Wer ein aktives Kind an ein abgeschlossenes Epic oder eine
    abgeschlossene Story hängt, erfährt eindeutig, dass der Parent
    geschlossen ist und wie man ihn wieder öffnet; KI-Agenten verstehen die
    Antwort ohne Rätselraten, die UI bietet das Wiederöffnen direkt an.
  - Completion criteria: Der Server antwortet in diesem Fall mit 409
    parent_closed statt children_still_active, nennt das Kind und die zu
    öffnenden geschlossenen Vorfahren in Öffnungsreihenfolge und beschreibt
    in der Meldung den Weg zum Wiederöffnen; children_still_active bleibt
    für das Schließen eines Parents mit aktiven Kindern; der Anlegen-Dialog
    der UI fragt bei parent_closed, ob die Vorfahren wieder geöffnet werden
    sollen, und legt das Item danach an; übrige UI-Stellen zeigen die klare
    Meldung (de/en); interfaces.md beschreibt den Fehlercode und das
    Wiederöffnen per PATCH; Tests decken Domain, API und UI ab.
  - Summary: Auslöser: Der Harness bekam beim Anlegen einer Story unter dem
    abgeschlossenen EPIC-004 nur die missverständliche Meldung
    children_still_active und legte die Story ohne Parent an.
  - Resolution: Vom Projektverantwortlichen bestätigt: 409 parent_closed mit
    Vorfahren in Öffnungsreihenfolge, Wiederöffnen-Nachfrage im
    Anlegen-Dialog, Doku in interfaces.md und README (Merge f6a69ab).

- `STORY-016` **Wichtige Schritte und Fehler systematisch protokollieren**
  - Type: Story.
  - Parent: None.
  - Status: Completed.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Fehler lassen sich allein anhand des Logs analysieren:
    Start-Konfiguration, alle schreibenden Aktionen, abgelehnte Requests
    (4xx), Serverfehler (5xx) und bisher still geschluckte Fehler sind mit
    Kontext protokolliert. Das Log liegt außerhalb des Containers und bleibt
    beim Entfernen des Containers erhalten. Bisher gibt es im Backend kein
    Logging; nur das uvicorn-Zugriffslog zeigt Statuscodes.
  - Completion criteria: Beim Start werden Version und aktive Pfade
    (CONFIG_DIR, FRONTEND_DIR, BROWSE_START) geloggt; jede schreibende
    Aktion erzeugt eine INFO-Zeile mit Quelle, Item-ID bzw. Ziel und
    Ergebnis; jede 4xx-Antwort erzeugt eine Zeile mit Methode, Pfad,
    Statuscode, Fehlercode und details, jede 5xx zusätzlich den Stacktrace;
    still behandelte Fehler (unlesbare Quelle, defekte ui_state.json,
    OSError im Ordner-Browser) erzeugen eine WARNING; jede Zeile trägt eine
    Request-ID; Format einzeilig key=value, per grep durchsuchbar; LOG_FILE
    und LOG_LEVEL per Umgebungsvariable, ohne LOG_FILE Konsole; Rotation
    nach Größe (5 MB, 5 Dateien); docker-compose bindet ./logs als Volume
    ein, logs/ steht in .gitignore; Tests decken u. a. einen
    409-Regelverstoß, einen 500-Fehler und eine Schreibaktion ab;
    Konfiguration, Betrieb und Suche im Log sind in den Techdocs
    beschrieben.
  - Summary: Das Backend soll alle wichtigen Schritte und Fehler so
    protokollieren, dass sich Fehler allein über das Log (per grep, ohne
    vollständiges Lesen) analysieren lassen. Die Logdatei liegt in ./logs
    außerhalb des Containers.
  - Resolution: Confirmed by the project owner on 2026-09-28.
  - Notes: `items/STORY-016/STORY-016_notes.md`.

- `TASK-002` **Typ eines Items ändern**
  - Type: Task.
  - Parent: `STORY-007`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein eigener Endpunkt `POST /api/v2/items/{source}/{id}/retype`
    ändert den Typ eines Items (Epic, Story, Task). Das Item erhält die
    nächste freie ID des Zieltyps; Header, `parent` und `dependencies` aller
    Items (aktiv, Archiv, Papierkorb), der Ordner `items/<ID>/` sowie
    ID-Erwähnungen in Notes und Specs des Backlogs werden atomar mitgezogen.
    Die Antwort enthält einen Hinweis, dass Techdocs und andere Stellen
    außerhalb des Backlogs die alte ID noch nennen können; UI und Agenten
    können ihn anzeigen bzw. darauf aufbauen.
  - Completion criteria: Der Typwechsel liefert das Item mit neuer ID und
    Version und lässt keine Verweise auf die alte ID im Backlog zurück. Die
    Antwort nennt alte und neue ID und trägt einen Hinweis mit stabilem Code
    auf mögliche Verweise außerhalb des Backlogs. Die Lifecycle-Regeln (z.
    B. Epic ohne Parent, Epic mit Pflichtkind) werden geprüft und verletzen
    sie, bleibt alles unverändert. Tests decken aktive und archivierte
    Items, Kinder, Abhängigkeiten und Dokumente ab; OpenAPI und Techdocs
    sind aktualisiert.
  - Summary: Den Typ eines Items ändern, ohne dass Verweise im Backlog
    brechen.
  - Resolution: Vom Projektverantwortlichen am 2026-09-30 bestätigt.
  - Notes: `items/TASK-002/TASK-002_notes.md`.

- `STORY-007` **Items anlegen**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-003`, `STORY-005`.
  - Goal: `POST /api/v2/items` legt ein Epic, eine Story oder einen Task an.
    Der Server vergibt die nächste freie ID des Typs über aktive und
    archivierte Items, setzt Status Open und das heutige Datum als Standard
    für Created.
  - Completion criteria: Neu angelegte Items sind formatgültig, haben eine
    eindeutige ID und werden als Item zurückgegeben; ungültige Eingaben
    liefern Fehler mit stabilen Codes.
  - Summary: Neue Epics, Stories und Tasks lassen sich über die API anlegen;
    der Server vergibt die ID und prüft die Regeln.
  - Resolution: Vom Projektverantwortlichen am 2026-09-30 bestätigt.
  - Notes: `items/STORY-007/STORY-007_notes.md`.

- `EPIC-001` **Backlog-Pflege per API statt direkter Dateizugriffe**
  - Type: Epic.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Agenten (Ablösung der Schreibzugriffe des todo-Skills) und die UI
    lesen und pflegen Backlogs vollständig über `/api/v2`. Der Vertrag
    adressiert Items nur über `source_id` und ID und kennt weder Dateien,
    Zeilen noch Locations, sodass `TODO.md` später durch eine Datenbank
    ersetzt werden kann, ohne die API zu ändern.
  - Completion criteria: Alle Pflichtkinder sind abgeschlossen; ein Agent
    kann Items lesen, anlegen, bearbeiten, löschen und Notes/Specs
    schreiben, ohne Backlog-Dateien direkt anzufassen; kein Item-Endpunkt
    enthält Dateipfade, Zeilen oder Locations (der Ordnerpfad einer Quelle
    in `/sources` und `/folders` gehört zur Konfiguration und ist
    ausgenommen).
  - Summary: Statt dass der Agent die Backlog-Dateien selbst bearbeitet,
    geht alles über die API des ToDo-Viewers. Die API wird so gebaut, dass
    die Markdown-Dateien später durch eine Datenbank ersetzt werden können.
  - Resolution: Vom Projektverantwortlichen am 2026-09-30 bestätigt.
  - Notes: `items/EPIC-001/EPIC-001_notes.md`.
  - Spec: `items/EPIC-001/EPIC-001_spec_harness.md`.

- `STORY-018` **Typ eines Items in der UI ändern**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-002`.
  - Goal: Im Detail-Panel lässt sich der Typ eines Items ändern. Die UI ruft
    den Typwechsel der API auf, wählt das Item danach unter seiner neuen ID
    aus und zeigt den Hinweis der API, dass Techdocs und andere Stellen
    außerhalb des Backlogs die alte ID noch nennen können.
  - Completion criteria: Ein Item lässt sich im Detail-Panel auf einen
    anderen Typ umstellen; danach ist es unter der neuen ID ausgewählt und
    die Ansichten zeigen es dort. Regelverstöße der API (z. B. Epic mit
    Parent) erscheinen als übersetzte Meldung ohne Änderung. Der Hinweis auf
    mögliche Verweise außerhalb des Backlogs ist sichtbar und enthält die
    alte und die neue ID. Texte sind in Deutsch und Englisch vorhanden;
    Typecheck, Lint und Web-Tests sind grün.
  - Summary: Den Typ eines Items direkt in der Oberfläche ändern, samt
    Hinweis auf Verweise außerhalb des Backlogs.
  - Resolution: Vom Projektverantwortlichen am 2026-09-30 bestätigt.
  - Notes: `items/STORY-018/STORY-018_notes.md`.

- `STORY-019` **Architekturregeln für wählbares Speicher-Backend öffnen**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Architekturregeln erlauben je Projekt wahlweise Markdown oder
    eine zentrale Datenbank hinter dem BacklogRepository-Port. Regel 1
    (Markdown als einzige Wahrheit) wird entsprechend umformuliert; das
    Backend-Scope-Dokument bekommt Regeln für DB-Adapter und Migrationen.
  - Completion criteria: architecture.md und
    docs/development/architecture/backend.md sind angepasst und vom
    Projekteigner freigegeben; Verweise auf die bisherige Regel 1 (Tests,
    Doku) sind konsistent.
  - Summary: Regel 1 und der Backend-Scope werden so geändert, dass Markdown
    und Datenbank gleichrangige Backends sind.
  - Resolution: Architekturregeln (Regel 1, Backend-Scope Abschnitt 5,
    import-linter) am 2026-09-30 vom Projekteigner bestätigt; Commit
    f64b4cc.
  - Spec: `items/STORY-019/STORY-019_spec.md`.

- `STORY-020` **Port-Vertrag als Contract-Suite und Routing je Projekt**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-019`.
  - Goal: Die Charakterisierungstests laufen als parametrisierte
    Contract-Suite gegen jeden BacklogRepository-/DocumentStore-Adapter. Ein
    RoutingRepository wählt je Source.backend (markdown | database) den
    Adapter; Verdrahtung in bootstrap.py.
  - Completion criteria: Die Contract-Suite läuft gegen den Markdown-Adapter
    und einen In-Memory-Fake, alle bisherigen Tests sind grün, das Verhalten
    ist unverändert, Source hat das Feld backend (Standard markdown).
  - Summary: Bestehende Tests werden zu einem wiederverwendbaren Maßstab für
    neue Adapter; Routing je Projekt kommt dazu.
  - Resolution: Vom Projekteigner bestätigt am 2026-09-30; umgesetzt in
    Merge d44626d, Release v0.2.2.
  - Spec: `items/STORY-020/STORY-020_spec.md`.

- `STORY-027` **Dokument-Port itembasiert statt pfadbasiert**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-020`.
  - Goal: Domain und Application adressieren Notizen und Specs nur noch über
    Item-ID und Dokumentname. Wo und wie ein Dokument liegt (Ordner
    items/<ID>/, Dateinamen, Umbenennen beim Typwechsel), weiß nur der
    Speicher-Adapter. Damit muss ein Datenbank-Adapter keine Ordnerstruktur
    nachbauen.
  - Completion criteria: Der DocumentStore-Port nimmt Item-ID und
    Dokumentname statt Pfaden; domain/documents.py und RetypePlanner kennen
    keine Pfade mehr; die HTTP-API und die Markdown-Dateien verhalten sich
    unverändert (Markdown-Goldens byte-gleich; in JSON-Goldens ändern sich
    nur die version-Werte von Items mit Dokumenten); die Contract-Suite
    prüft den neuen Port für Markdown und den Fake.
  - Summary: Umbau vor dem Datenbank-Adapter: Dokumente werden über Item und
    Namen angesprochen, die Ablage entscheidet der Adapter.
  - Resolution: Vom Projekteigner bestätigt am 2026-09-30; umgesetzt in
    Merge 909e4c8.
  - Notes: `items/STORY-027/STORY-027_notes.md`.

- `STORY-021` **SQLite-Adapter für Items, Archiv, Papierkorb und Dokumente**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-020`, `STORY-027`.
  - Goal: Ein Datenbank-Adapter (SQLAlchemy Core, SQLite) implementiert
    BacklogRepository und DocumentStore, inklusive Archiv, Papierkorb,
    Notizen und Specs. Die Daten werden normalisiert in Tabellen gespeichert
    (Items mit UUID und Label, Beziehungen, Zusatzfelder, Dokumente) mit
    versioniertem Schema (Migrationen) und einer Spalte position für die
    Reihenfolge. apply_all läuft in einer Transaktion, Versionskonflikte
    über Item.version.
  - Completion criteria: Die Contract-Suite ist für SQLite grün; ein Projekt
    mit backend=database funktioniert über die API Ende zu Ende (lesen,
    anlegen, ändern, archivieren, löschen, Dokumente).
  - Summary: Neuer DB-Adapter, der dieselbe Contract-Suite besteht wie
    Markdown.
  - Resolution: Vom Projekteigner bestätigt am 2026-09-30; umgesetzt in
    Merge 95fcb7a, Release v0.3.0.
  - Notes: `items/STORY-021/STORY-021_notes.md`.
  - Spec: `items/STORY-021/STORY-021_spec.md`.

- `STORY-022` **Projekte und UI-State in der zentralen Datenbank**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-021`.
  - Goal: Die Projektliste (bisher Source) und der UI-State liegen in der
    zentralen DB. Ein Projekt hat eine stabile Id statt Pfad-Hash, ein
    backend und optional einen Sync-Pfad zu seinen .md-Dateien. config.json
    behält nur storage_url (mit Zugangsdaten, lokal in Ordnung) und
    Markdown-Projekte. Bestehende Installationen werden ohne Datenverlust
    migriert.
  - Completion criteria: Projekte lassen sich in der DB anlegen, ändern und
    löschen; bestehende config.json-Quellen laufen unverändert weiter oder
    werden migriert; ui_state kommt aus der DB.
  - Summary: Ein zentraler Ort für Projekte, Einstellungen und Inhalte;
    Sync-Pfad je Projekt konfigurierbar.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.
  - Notes: `items/STORY-022/STORY-022_notes.md`.
  - Spec: `items/STORY-022/STORY-022_spec.md`.

- `STORY-023` **Sync zwischen Datenbank und Markdown (to_md / from_md)**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-022`.
  - Goal: Ein Sync-Service überträgt auf Knopfdruck oder API-Aufruf (POST
    /api/v2/sources/{id}/sync mit direction=to_md|from_md) alle Daten eines
    Projekts: TODO.md, archive.md und alle Items samt Notizen und Specs.
    Vorher gibt es eine Vorschau (neu, geändert, fehlend), Überschreiben nur
    mit Bestätigung; Konflikte werden über den Versionshash je Item erkannt.
    Löschungen (Einträge, die auf der Zielseite existieren, auf der
    Quellseite aber fehlen) werden als Warnung angezeigt und nur nach
    Rückfrage ausgeführt.
  - Completion criteria: Sync in beide Richtungen funktioniert per API mit
    Vorschau und Bestätigung. Der Export ist stabil (export -> import ->
    export ergibt identische Dateien) und der Import gibt dieselben Items
    zurück (gleiche Item.version); die .md müssen nicht byte-gleich zum
    Ausgangstext sein. Fehlende Einträge werden in der Vorschau als Warnung
    gemeldet und nur nach ausdrücklicher Nachfrage gelöscht. Ohne Sync-Pfad
    wird mit klarem Fehlercode abgelehnt.
  - Summary: Zweiseitiger Sync auf Knopfdruck, keine automatische
    Spiegelung.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.
  - Notes: `items/STORY-023/STORY-023_notes.md`.
  - Spec: `items/STORY-023/STORY-023_spec.md`.

- `TASK-003` **Backend-Wechsel per PUT nach Sync**
  - Type: Task.
  - Parent: `STORY-024`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Projekt lässt sich an Ort und Stelle auf das andere
    Speicher-Backend umstellen, mit gleicher source_id und gleichen
    Item-IDs. Markdown → Datenbank: Sync from_md (Vorschau, Bestätigung)
    liest den Ordner in die Datenbank, danach schaltet PUT /sources/{id} mit
    backend=database um; der Ordner wandert von path nach sync_path.
    Datenbank → Markdown: Sync to_md, danach PUT mit backend=markdown;
    sync_path wandert nach path. Der Sync akzeptiert dafür auch ein
    Markdown-Projekt (nur from_md).
  - Completion criteria: Der Wechsel funktioniert in beide Richtungen über
    die API: PUT mit neuem backend wird nur akzeptiert, wenn die Daten zuvor
    synchronisiert wurden (sonst klarer Fehlercode, nichts ändert sich);
    source_id und Item-IDs bleiben gleich; path und sync_path wandern wie im
    EPIC-003-Spec beschrieben; der Markdown-path bleibt eindeutig.
    Contract-, Service- und API-Tests decken beide Richtungen und die
    Fehlerfälle ab; Techdocs und OpenAPI sind angepasst.
  - Summary: Backend-Wechsel ohne neue Projekt-Id: erst Sync, dann PUT mit
    neuem backend.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.
  - Notes: `items/TASK-003/TASK-003_notes.md`.

- `STORY-024` **Speicher-Backend und Sync in der UI bedienen**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-023`.
  - Goal: Im UI lässt sich je Projekt das Backend wählen, der Sync-Pfad
    einstellen und der Sync (to_md / from_md) mit Vorschau-Dialog und
    Bestätigung auslösen. Fehlercodes werden übersetzt, TypeScript-Typen aus
    OpenAPI neu generiert.
  - Completion criteria: Alle Backend- und Sync-Funktionen sind ohne Konsole
    über die UI nutzbar; UI-Tests decken Backend-Wahl, Vorschau und
    Bestätigung ab.
  - Summary: Backend-Wahl und Sync-Knöpfe im Projekt-Dialog.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.
  - Notes: `items/STORY-024/STORY-024_notes.md`.
  - Spec: `items/STORY-024/STORY-024_spec.md`.

- `STORY-025` **Doku und Release für das wählbare Speicher-Backend**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-024`.
  - Goal: README und Techdocs beschreiben Backend-Wahl, storage_url,
    DB-Sicherung, Sync-Ablauf und Migration; Tagesbericht und Release
    (voraussichtlich 0.3.0).
  - Completion criteria: Doku entspricht dem Ist-Zustand, Release ist
    getaggt, das eigene Backlog wurde probeweise in die DB übernommen.
  - Summary: Dokumentation und Release des Epics.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.
  - Notes: `items/STORY-025/STORY-025_notes.md`.
  - Spec: `items/STORY-025/STORY-025_spec.md`.

- `STORY-026` **Postgres als zweiter Datenbank-Typ (optional)**
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: No.
  - Status: Rejected.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-021`.
  - Goal: Der DB-Adapter läuft zusätzlich gegen Postgres (Treiber,
    URL-Konfiguration, Dialekt-Unterschiede in den Migrationen); dieselbe
    Contract-Suite. Nur nötig, wenn Postgres tatsächlich gebraucht wird.
  - Completion criteria: Die Contract-Suite ist für SQLite und Postgres
    grün; Postgres-Tests werden übersprungen, wenn kein Server erreichbar
    ist.
  - Summary: Optionaler zweiter Datenbank-Typ.
  - Resolution: Vom Projektinhaber am 2026-09-30 vorerst verworfen: SQLite
    genügt für den lokalen Einzelbetrieb; Postgres nur bei echtem Bedarf neu
    aufnehmen.
  - Notes: `items/STORY-026/STORY-026_notes.md`.
  - Spec: `items/STORY-026/STORY-026_spec.md`.

- `EPIC-003` **Wählbares Speicher-Backend: Markdown oder zentrale Datenbank**
  - Type: Epic.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Jedes Projekt kann wahlweise in Markdown-Dateien (wie bisher) oder
    in einer zentralen lokalen Datenbank gespeichert werden. Die Datenbank
    nimmt die komplette Struktur auf (Items, Archiv, Papierkorb, Notizen,
    Specs). Per Knopfdruck oder API-Aufruf lässt sich ein Projekt zwischen
    Datenbank und Markdown synchronisieren (to_md / from_md).
  - Completion criteria: Ein Projekt lässt sich je nach Wahl mit Markdown
    oder SQLite betreiben. Sync in beide Richtungen ist per API und UI
    möglich und ergibt beim Roundtrip md -> db -> md dieselben Items
    (gleiche Versionen) und Dokumente; Export -> Import -> Export ergibt
    identische Dateien. Die Architekturregeln erlauben beide Backends, Doku
    und Release sind aktualisiert.
  - Summary: Neben den Markdown-Dateien wird eine zentrale SQLite-Datenbank
    als Speicher wählbar, mit Sync in beide Richtungen auf Knopfdruck.
  - Resolution: Vom Projektinhaber am 2026-09-30 bestätigt.
  - Notes: `items/EPIC-003/EPIC-003_notes.md`.
  - Spec: `items/EPIC-003/EPIC-003_spec.md`.

- `STORY-029` **Primärquelle und Spiegel pro Projekt in Modell und API**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-028`.
  - Goal: Jedes Projekt hat in Datenbank und API eine primäre Quelle und je
    Seite einen optionalen Spiegel mit eigenem Speicherort (Markdown-Ordner
    bzw. Datenbank). Beide Richtungen sind möglich. Bestehende Projekte
    werden ohne Verlust übernommen.
  - Completion criteria: - GET /sources nennt je Projekt Primärquelle und
    Spiegel; POST/PUT setzen sie. - Ein Markdown-Projekt kann einen
    Datenbank-Spiegel halten und umgekehrt. - Bestehende Projekte kommen per
    versionierter Migration unverändert weiter: Backend bleibt primär,
    sync_path wird zum Spiegel-Ordner. - Die Contract-Suite deckt beide
    Kombinationen ab; OpenAPI und TypeScript-Typen sind neu erzeugt.
  - Summary: Projekte kennen jetzt Primärquelle und optionalen Spiegel; die
    API zeigt beides und lässt den Spiegel setzen.
  - Resolution: Vom Projekteigner bestätigt; umgesetzt mit v0.6.1.
  - Notes: `items/STORY-029/STORY-029_notes.md`.

- `STORY-030` **Sync mit wählbarer Richtung, voller Umfang, Wechsel der Primärquelle**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-029`.
  - Goal: Der Sync läuft standardmäßig von der primären zur anderen Seite;
    die Richtung ist pro Lauf wählbar (z. B. wenn eine KI die
    Markdown-Dateien verändert hat). Er umfasst alles: Backlog, Archiv,
    Notes, Specs und Papierkorb. Beim Wechsel der Primärquelle läuft vorher
    ein Sync, damit die neue primäre Quelle aktuell ist.
  - Completion criteria: - Vorschau und Ausführung gelten für beide
    Richtungen und den gesamten Umfang, auch Notes, Specs und Papierkorb. -
    Nichts wird ohne Bestätigung auf dem Ziel gelöscht. - Der Wechsel der
    Primärquelle verlangt einen vorherigen Sync, sonst sync_required. - Es
    gibt keinen automatischen Sync.
  - Summary: Der Sync hat eine Standardrichtung von der Primärquelle zum
    Spiegel; alles andere war schon vorhanden und ist jetzt auch für
    Markdown mit Datenbank-Spiegel getestet.
  - Resolution: Vom Projekteigner bestätigt; umgesetzt mit v0.6.2.
  - Notes: `items/STORY-030/STORY-030_notes.md`.

- `STORY-028` **Architekturregeln: Primärquelle und Spiegel statt genau einem Backend**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Regel 1 der Architektur (genau ein Backend pro Projekt, keine
    zweite Kopie) wird so geändert, dass ein Projekt eine primäre Quelle hat
    und die andere Seite optional als Spiegel hält. Der Sync bleibt immer
    ausdrücklich, nie automatisch.
  - Completion criteria: - docs/development/architecture.md beschreibt
    Primärquelle und Spiegel; die Regel zu Sync (Vorschau, nichts löschen
    ohne Bestätigung) bleibt. - Die Änderung ist vom Projekteigner
    freigegeben, bevor sie gilt. - Die Contract-Suite nennt, was für einen
    Spiegel zusätzlich gilt.
  - Summary: Regel 1 der Architektur kennt jetzt Primärquelle und Spiegel
    pro Projekt.
  - Resolution: Vom Projekteigner bestätigt.
  - Notes: `items/STORY-028/STORY-028_notes.md`.

- `STORY-031` **Backup vor dem Wechsel der Primärquelle**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-029`.
  - Goal: Vor einem Wechsel der Primärquelle legt der Dienst ein Backup der
    bisherigen primären Seite an, damit sich der Wechsel zurückrollen lässt.
  - Completion criteria: - Vor jedem Wechsel entsteht ein Backup
    (Datenbank-Export bzw. Kopie der Markdown-Dateien) an einem
    dokumentierten Ort. - Schlägt das Backup fehl, findet kein Wechsel
    statt; die Antwort nennt den Grund. - Ein Test prüft, dass sich aus dem
    Backup der alte Stand herstellen lässt.
  - Summary: Vor jedem Wechsel der Primärquelle wird die bisherige
    gesichert; scheitert das, wird nichts umgeschaltet.
  - Resolution: Vom Projekteigner bestätigt.
  - Notes: `items/STORY-031/STORY-031_notes.md`.

- `STORY-032` **Sync-Status: Spiegel extern geändert erkennen**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-030`.
  - Goal: Der Dienst erkennt, ob sich eine Seite seit dem letzten Sync
    geändert hat (z. B. KI hat Markdown-Dateien bearbeitet) und liefert
    Status und Zeitpunkt des letzten Syncs je Projekt. Er synchronisiert
    dabei nie von selbst.
  - Completion criteria: - GET /sources nennt je Projekt den Sync-Status (in
    Sync, Spiegel geändert, primäre Quelle geändert, beide geändert) und den
    letzten Sync-Zeitpunkt. - Die Erkennung braucht keinen Sync und ändert
    keine Daten. - Tests decken alle vier Zustände ab.
  - Summary: Jedes Projekt mit Spiegel meldet, welche Seite sich seit dem
    letzten Sync geändert hat; das Lesen ändert nichts.
  - Resolution: Vom Projekteigner bestätigt; umgesetzt mit v0.6.5.
  - Notes: `items/STORY-032/STORY-032_notes.md`.

- `STORY-033` **Einstellungsmenü: erweiterbarer Rahmen und Abschnitt „Allgemein“**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-029`.
  - Goal: Ein Einstellungsmenü (Zahnrad in der Sidebar) besteht aus
    Abschnitten, die in einer Liste registriert werden; ein neuer Abschnitt
    ist ein neuer Eintrag. Der erste Abschnitt „Allgemein“ zeigt den
    Datenbank-Ort nur lesend (Bearbeiten bleibt in der config.json) und
    stellt das Standard-Backend für neue Projekte ein.
  - Completion criteria: - Das Menü öffnet sich über die Sidebar und zeigt
    die Abschnitte als Navigation. - Abschnitte werden aus einer Liste
    gerendert; ein Test zeigt, dass ein zusätzlicher Eintrag ohne weitere
    Änderung erscheint. - „Allgemein“ zeigt Datenbank-Typ und -Ort nur
    lesend und speichert das Standard-Backend im UI-Zustand. - Das
    Standard-Backend ist beim Hinzufügen eines Projekts vorausgewählt.
  - Summary: Die Sidebar hat ein Zahnrad, das ein Einstellungsmenü mit
    erweiterbarer Abschnittsliste öffnet; Allgemein zeigt die Datenbank
    lesend und stellt den Standard-Speicherort für neue Projekte ein.
  - Resolution: Vom Projekteigner bestätigt; umgesetzt mit v0.6.6.
  - Notes: `items/STORY-033/STORY-033_notes.md`.

- `STORY-034` **Menüabschnitt „Projekte“: Primärquelle, Pfade und Sync je Projekt**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-033`, `STORY-030`, `STORY-031`, `STORY-032`.
  - Goal: Pro Projekt eine Karte: primäre Quelle umschalten, Pfade beider
    Seiten (Markdown-Ordner, Spiegel) einstellen, Sync mit Richtung
    auslösen, Sync-Status sehen. Der Bearbeiten-Dialog der Sidebar behält
    nur den Namen; Entfernen und Reihenfolge bleiben in der Sidebar. Das
    Sync-Badge in der Sidebar öffnet das Menü bei diesem Projekt.
  - Completion criteria: - Jede Karte zeigt Primärquelle, beide Pfade,
    Status und letzten Sync. - Wechsel der Primärquelle führt über Sync und
    Backup aus dem Menü. - Sync-Richtung ist wählbar; Standard ist von der
    primären Seite zur anderen. - Das Badge erscheint bei geändertem Spiegel
    und öffnet das Menü bei diesem Projekt. - Der Bearbeiten-Dialog enthält
    nur noch den Namen. - Web-Tests decken Karte, Richtung und Badge ab.
  - Summary: Das Einstellungsmenü hat einen Abschnitt Projekte mit einer
    Karte je Projekt; ein Badge in der Sidebar zeigt einen geänderten
    Spiegel und öffnet die Karte.
  - Resolution: Vom Projekteigner bestätigt; umgesetzt mit v0.6.7.
  - Notes: `items/STORY-034/STORY-034_notes.md`.

- `STORY-035` **Doku und Release für Primärquelle, Spiegel und Einstellungsmenü**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `STORY-034`.
  - Goal: Technische Dokumentation und Release für die neuen Funktionen.
  - Completion criteria: - README und docs/techdocs (Konfiguration,
    Schnittstellen, Betrieb) beschreiben Primärquelle, Spiegel,
    Sync-Richtung, Status und Backup. - Ein Tagesbericht und ein Release
    (SemVer) sind erledigt.
  - Summary: README und Techdocs beschreiben Primärquelle, Spiegel,
    Sync-Richtung, Status und Backup durchgehend; Releases und Tagesberichte
    sind erledigt.
  - Resolution: Vom Projekteigner bestätigt; README und Techdocs aktuell,
    Releases v0.6.1 bis v0.6.7.
  - Notes: `items/STORY-035/STORY-035_notes.md`.

- `STORY-036` **Spiegel-Ordner bleibt beim Ausschalten erhalten**
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Wer den Markdown-Spiegel eines Datenbank-Projekts ausschaltet und
    wieder einschaltet, muss den Ordner nicht neu wählen: Ausschalten merkt
    sich den Ordner und schaltet nur den Spiegel ab.
  - Completion criteria: - Ausschalten des Spiegels behält den Ordner; ein
    Flag am Projekt (Migration) hält fest, dass der Spiegel aus ist. -
    Einschalten braucht keinen neuen Pfad. - Status und Sync behandeln ein
    Projekt mit ausgeschaltetem Spiegel wie eines ohne Spiegel; bestehende
    Projekte mit Ordner bleiben eingeschaltet. - Das Menü zeigt „Spiegel
    ausschalten“/„Spiegel einschalten“ und den Ordner; ein leerer Pfad im
    Ordner-Dialog löscht ihn wirklich. - Tests und Doku sind aktuell.
  - Summary: Der Markdown-Spiegel eines Datenbank-Projekts lässt sich aus-
    und wieder einschalten, ohne den Ordner neu zu wählen.
  - Resolution: Confirmed by the project owner on 2026-09-30.
  - Notes: `items/STORY-036/STORY-036_notes.md`.

- `EPIC-004` **Primärquelle und Spiegel pro Projekt, Einstellungsmenü**
  - Type: Epic.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Jedes Projekt hat eine primäre Quelle (Datenbank oder Markdown)
    und darf die andere Seite als Spiegel halten. Ein eigenes
    Einstellungsmenü bündelt alles Speicher-Bezogene: Primärquelle je
    Projekt, Pfade der Markdown-Seite, Sync mit wählbarer Richtung und den
    Sync-Status. Ziel im Alltag: auf der Datenbank arbeiten, Markdown als
    aktueller Spiegel. Das Menü ist in Abschnitten aufgebaut, damit weitere
    Einstellungen ohne Umbau dazukommen.
  - Completion criteria: - Pro Projekt lässt sich die primäre Quelle im Menü
    wählen; beim Wechsel läuft vorher ein Sync, und vorher wird ein Backup
    angelegt. - Beide Seiten dürfen als Spiegel gehalten werden; der Sync
    läuft standardmäßig von der primären zur anderen Seite, die Richtung ist
    pro Lauf wählbar. - Ein Projekt, dessen Spiegel seit dem letzten Sync
    extern geändert wurde, trägt in der Sidebar ein Badge, das das Menü bei
    diesem Projekt öffnet. - Der Sync umfasst alles (Backlog, Archiv, Notes,
    Specs, Papierkorb). - Es gibt nie einen automatischen Sync; die
    Architekturregeln sind entsprechend angepasst und vom Projekteigner
    freigegeben. - Das Menü ist über eine Abschnittsliste erweiterbar; die
    Doku ist aktuell.
  - Summary: Projekte haben eine Primärquelle und einen optionalen Spiegel;
    ein Einstellungsmenü bündelt Primärquelle, Pfade, Sync und Status.
  - Resolution: Confirmed by the project owner on 2026-09-30.
  - Notes: `items/EPIC-004/EPIC-004_notes.md`.

- `STORY-046` **Doku und Release für Notes und Topics**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Techdocs (Architektur, Schnittstellen, Betrieb, Konfiguration
    inklusive Prüf-Intervall), README und Release.
  - Completion criteria: Doku beschreibt Modell, API, Auslöser und
    Bedienung; Release ist getaggt.
  - Summary: Techdocs (Architektur, Schnittstellen, Betrieb, Konfiguration
    inklusive Prüf-Intervall), README und Release.
  - Resolution: Vom Besitzer bestätigt am 2026-10-08: Techdocs zu Notes und
    Topics ergänzt (Betriebsteil), Routen, Antwortfelder und Fehlercodes
    gegen den Code abgeglichen; kein eigenes Release, da nur Doku (v0.8.0
    trägt die Funktionen).
  - Notes: `items/STORY-046/STORY-046_notes.md`.
  - Spec: `items/STORY-046/STORY-046_spec.md`.

- `TASK-004` **Topics-API: anlegen, lesen, ändern, verschieben, löschen**
  - Type: Task.
  - Parent: `STORY-039`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Topics lassen sich über API v2 anlegen, lesen, umbenennen, mit
    Termin versehen, verschieben (Tiefe und Schleifen werden geprüft), in
    den Papierkorb löschen (mit Kaskade) und wiederherstellen. Der Rahmen
    für alle Notes-Routen (Router-Gruppe, Schemas, Fehlerabbildung,
    Container) steht.
  - Completion criteria: Alle genannten Topic-Operationen sind per API-Test
    abgedeckt, inklusive der Fehlerfälle; test_openapi.py ist grün;
    scripts/check.sh ist grün.
  - Summary: HTTP-Routen für Topics samt Service-Rahmen, Fehlercodes und
    Verdrahtung; die Basis für alle weiteren Notes-Routen.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Spec: `items/TASK-004/TASK-004_spec.md`.

- `TASK-005` **Notes-API: anlegen, lesen, ändern, Projekt wechseln**
  - Type: Task.
  - Parent: `STORY-039`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-004`.
  - Goal: Notes lassen sich über API v2 anlegen, lesen (mit Auslösern und
    abgeleitetem Zustand), ändern (Kurzfassung, Langtext, Topic,
    Auslöser-Modus), als geprüft behalten und in ein anderes Projekt
    verschieben. Gleichzeitige Änderungen werden über den Versionstoken
    erkannt.
  - Completion criteria: Alle Operationen sind per API-Test abgedeckt,
    inklusive Versionskonflikt und Projektwechsel; scripts/check.sh ist
    grün.
  - Summary: HTTP-Routen für Notes (anlegen, lesen, ändern, behalten,
    Projektwechsel) mit Versionstoken.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Spec: `items/TASK-005/TASK-005_spec.md`.

- `TASK-006` **Notes-API: Lebenszyklus, Auslöser, Archiv und Papierkorb**
  - Type: Task.
  - Parent: `STORY-039`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-005`.
  - Goal: Der Lebenszyklus einer Note ist über API v2 bedienbar: erledigen,
    verwerfen, zurückstellen (mit neuem Datum oder neuem Auslöser), Auslöser
    anlegen und entfernen, löschen, wiederherstellen, Papierkorb lesen.
    Endgültiges Löschen gibt es nicht über HTTP.
  - Completion criteria: Jede Operation ist per API-Test abgedeckt, auch die
    abgelehnten Übergänge; es gibt keine Purge-Route; scripts/check.sh ist
    grün.
  - Summary: HTTP-Routen für Erledigen, Verwerfen, Zurückstellen, Auslöser
    setzen/entfernen, Löschen, Wiederherstellen und die Papierkorb-Liste.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Spec: `items/TASK-006/TASK-006_spec.md`.

- `TASK-007` **Links-API: setzen, lösen, in beide Richtungen abfragen**
  - Type: Task.
  - Parent: `STORY-039`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-005`.
  - Goal: Links lassen sich über API v2 setzen und lösen und in beide
    Richtungen abfragen (Links einer Note; Notes, die auf ein Item, Topic
    oder eine Note zeigen). Das Ziel wird geprüft.
  - Completion criteria: Links setzen, lösen und beide Abfragen sind per
    API-Test abgedeckt, auch das nicht gefundene Ziel; ein Link auf ein Item
    übersteht retype; scripts/check.sh ist grün.
  - Summary: HTTP-Routen und Service für Links von Notes auf Items, Topics
    und andere Notes; Abfrage der Notes zu einem Item.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Spec: `items/TASK-007/TASK-007_spec.md`.

- `TASK-008` **Dokumente einer Note: Notizen und Specs lesen und schreiben**
  - Type: Task.
  - Parent: `STORY-039`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-005`.
  - Goal: Notizen und Specs einer Note lassen sich über API v2 lesen,
    vollständig ersetzen und (für Notizen) mit einem datierten Eintrag
    ergänzen. Der Versionstoken schützt vor gleichzeitigen Änderungen.
  - Completion criteria: Lesen, Schreiben, Anhängen und Versionskonflikt
    sind per API-Test abgedeckt; unzulässige Dateinamen werden abgelehnt;
    scripts/check.sh ist grün.
  - Summary: HTTP-Routen und Service für Notizen und Specs einer Note, wie
    beim Backlog, mit Versionstoken.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Spec: `items/TASK-008/TASK-008_spec.md`.

- `TASK-009` **Notes-Index, Fällig-Zähler, Fällig-Liste und Notes-Einstellungen**
  - Type: Task.
  - Parent: `STORY-039`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-006`, `TASK-007`.
  - Goal: Ein LLM und die UI laden nur das Nötige: ein Index mit Label,
    Status, Fälligkeit und Kurzfassung (filterbar), eine billige
    Zähler-Abfrage und eine projektübergreifende Fällig-Liste mit Grund und
    möglichen Aktionen. Die Notes-Einstellungen (Prüf-Intervall,
    Topic-Tiefe) sind lesbar und schreibbar und wirken ohne Neustart.
  - Completion criteria: Index (alle Filter, nie Langtexte), Zähler und
    Fällig-Liste sind per API-Test abgedeckt; der Zähler ändert sich, wenn
    eine Note fällig wird oder aufgelöst wird; Einstellungen wirken sofort;
    test_openapi.py ist grün.
  - Summary: Schlanker Index ohne Langtexte mit Filtern, billiger Zähler und
    globale Fällig-Liste; dazu Lesen und Schreiben der Notes-Einstellungen.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Spec: `items/TASK-009/TASK-009_spec.md`.

- `TASK-010` **Hinweis-Modell: speichern, fällig machen, entscheiden**
  - Type: Task.
  - Parent: `STORY-041`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-009`.
  - Goal: Es gibt Änderungshinweise als Daten in der Datenbank. Ein offener
    Hinweis macht die Note fällig (Grund notice), erscheint im Zähler und in
    der Fällig-Liste und bleibt, bis jemand entscheidet. Die Entscheidungen
    behalten, abkoppeln und verwerfen sind über API v2 möglich; die
    Entscheidung befördern wird von STORY-042 angeschlossen.
  - Completion criteria: Hinweise lassen sich speichern, lesen und
    entscheiden; jede Entscheidung führt zum beschriebenen Zustand; ein
    offener Hinweis macht die Note fällig und zählt im Zähler; Migration und
    Contract-Suite sind grün; scripts/check.sh ist grün.
  - Summary: Datenmodell, Service und API für Änderungshinweise; offene
    Hinweise machen eine Note fällig; Entscheidungen behalten, abkoppeln,
    verwerfen.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-010/TASK-010_notes.md`.
  - Spec: `items/TASK-010/TASK-010_spec.md`.

- `TASK-011` **Hinweise an Notes bei Änderung eines verlinkten Items**
  - Type: Task.
  - Parent: `STORY-041`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-010`.
  - Goal: Wird ein Item, auf das eine Note per Link der Rolle reference
    zeigt, abgeschlossen, verworfen, gelöscht oder im Typ geändert, bekommt
    die Note einen offenen Hinweis. Bei Links der Rolle trigger und origin
    entsteht kein Hinweis.
  - Completion criteria: Für jede der vier Ursachen entsteht genau ein
    Hinweis (Testmatrix, auch projektübergreifend); trigger- und
    origin-Links erzeugen keinen; scripts/check.sh ist grün.
  - Summary: Abschluss, Verwerfen, Löschen und Typwechsel eines verlinkten
    Items erzeugen einen Hinweis an der Note.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-011/TASK-011_notes.md`.
  - Spec: `items/TASK-011/TASK-011_spec.md`.

- `TASK-012` **Hinweise an Items, wenn eine verlinkte Note verworfen oder befördert wird**
  - Type: Task.
  - Parent: `STORY-041`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-010`.
  - Goal: Wird eine Note verworfen oder befördert, bekommen die Items, auf
    die sie per Link der Rolle reference zeigt, einen Hinweis, den man zur
    Kenntnis nehmen kann. Der Hinweis ist über die API am Item abfragbar.
  - Completion criteria: Verwerfen und Befördern erzeugen je einen Hinweis
    pro verlinktem Item; acknowledge schließt ihn; scripts/check.sh ist
    grün.
  - Summary: Verwerfen oder Befördern einer Note erzeugt einen Hinweis an
    den verlinkten Items zur Kenntnisnahme.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-012/TASK-012_notes.md`.
  - Spec: `items/TASK-012/TASK-012_spec.md`.

- `TASK-013` **Note zu Task, Story oder Epic befördern (Backend)**
  - Type: Task.
  - Parent: `STORY-042`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-007`, `TASK-008`, `TASK-010`.
  - Goal: Eine Note wird über die API zu einem Task, einer Story oder einem
    Epic: Das Item entsteht über den normalen Anlageweg mit allen
    Backlog-Prüfungen, Langtext, Notizen und Specs der Note wandern an das
    Item, die Note gilt als befördert und wird archiviert, der Link origin
    bleibt. Ein abgebrochener Vorgang ist erkennbar und wiederholbar.
  - Completion criteria: Beförderung funktioniert für alle drei Typen;
    fehlende Pflichtfelder und geschlossener Parent werden abgelehnt;
    Notizen und Specs sind am Item vorhanden; ein Abbruch nach dem Anlegen
    verliert nichts und die Wiederholung legt kein zweites Item an;
    scripts/check.sh ist grün.
  - Summary: Service und API-Route, die aus einer Note ein Backlog-Item
    machen, Notizen und Specs mitnehmen und die Herkunft verlinken.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-013/TASK-013_notes.md`.
  - Spec: `items/TASK-013/TASK-013_spec.md`.

- `TASK-014` **Offenes Item zur Note zurückstufen (Backend)**
  - Type: Task.
  - Parent: `STORY-042`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-013`.
  - Goal: Ein Item im Status Open ohne Kinder, das weder Parent noch
    Dependency eines anderen Items ist, lässt sich über die API zur Note
    zurückstufen: Die Note übernimmt Kurzfassung, Notizen und Specs und
    bekommt den Link origin; das Item wird mit der Resolution 'zur Notiz
    zurückgestuft' abgeschlossen. Unzulässige Rückstufungen werden mit Grund
    abgelehnt.
  - Completion criteria: Erfolgsfall und jeder Ablehnungsgrund sind per Test
    abgedeckt; Notizen und Specs stehen an der Note; ein Abbruch nach dem
    Anlegen der Note verliert nichts und die Wiederholung legt keine zweite
    Note an; scripts/check.sh ist grün.
  - Summary: Service und API-Route, die ein noch nicht begonnenes Item ohne
    Anhang in eine Note zurückverwandeln, mit Ablehnungsgründen.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-014/TASK-014_notes.md`.
  - Spec: `items/TASK-014/TASK-014_spec.md`.

- `TASK-015` **UI-Dialoge für Beförderung und Rückstufung**
  - Type: Task.
  - Parent: `STORY-042`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-014`, `TASK-019`.
  - Goal: Der Besitzer befördert eine Note über ein vorausgefülltes Formular
    (Typ, Bereich, Ziel, Abschlusskriterien, Parent) zu einem Item und stuft
    ein offenes Item über einen Dialog zur Note zurück. Fehler der API
    werden mit Grund angezeigt.
  - Completion criteria: Beide Dialoge funktionieren gegen die API, zeigen
    Ablehnungsgründe lokalisiert und sind mit Komponententests abgedeckt;
    die Herkunft ist am Item und an der Note sichtbar; scripts/check.sh ist
    grün.
  - Summary: Beförderung und Rückstufung sind in der Oberfläche bedienbar,
    die Herkunft ist verlinkt.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-015/TASK-015_notes.md`.
  - Spec: `items/TASK-015/TASK-015_spec.md`.

- `TASK-016` **Projektübergreifende Links und Ereignis-Auslöser prüfen und absichern**
  - Type: Task.
  - Parent: `STORY-044`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-007`.
  - Goal: Ein Link darf auf ein Item eines anderen registrierten Projekts
    zeigen. API und Anzeige nennen es als Projekt und Label. Ein
    Ereignis-Auslöser in Projekt A feuert, wenn das Item in Projekt B den
    Zielstatus erreicht. Die Rückrichtung ist am Item im anderen Projekt
    abfragbar.
  - Completion criteria: Zwei-Projekte-Integrationstest: Merker in A mit
    Auslöser auf ein Item in B wird fällig, wenn das Item den Zielstatus
    erreicht; links-to zeigt die Note von B aus; unbekannte Projekte werden
    abgelehnt; scripts/check.sh ist grün.
  - Summary: Links und Ereignis-Auslöser dürfen auf Items anderer
    registrierter Projekte zeigen; Anzeige, Rückrichtung und Auslösung sind
    per Zwei-Projekte-Test belegt.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-016/TASK-016_notes.md`.
  - Spec: `items/TASK-016/TASK-016_spec.md`.

- `TASK-017` **Nicht erreichbare Projekte: Link markieren und Hinweis erzeugen**
  - Type: Task.
  - Parent: `STORY-044`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-016`, `TASK-010`.
  - Goal: Ist das Zielprojekt eines Links entfernt oder seine Quelle nicht
    lesbar, wird der Link als nicht erreichbar gemeldet und die Note bekommt
    einen Hinweis, ohne dass ein Fehler entsteht. Wird das Projekt wieder
    erreichbar, verschwindet die Markierung; der Hinweis bleibt, bis jemand
    entscheidet.
  - Completion criteria: Entferntes und nicht lesbares Projekt führen zu
    unreachable und genau einem Hinweis, nicht zu einem Fehler; nach
    Rückkehr des Projekts ist der Link wieder erreichbar und der Hinweis
    noch offen; scripts/check.sh ist grün.
  - Summary: Entfernte oder nicht lesbare Projekte markieren den Link als
    nicht erreichbar und erzeugen einen Hinweis statt eines Fehlers.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-017/TASK-017_notes.md`.
  - Spec: `items/TASK-017/TASK-017_spec.md`.

- `TASK-018` **Notes-Bereich: Gerüst, Topic-Baum und Notes-Liste**
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-004`, `TASK-005`, `TASK-006`, `TASK-009`.
  - Goal: Es gibt einen Bereich Notes neben dem Backlog. Links der
    Topic-Baum, rechts die Notes des gewählten Topics (Kurzfassung, Status,
    Fälligkeit). Topics und Notes lassen sich anlegen, ändern und löschen.
    Die Grundlagen (Query-Hooks, reine Domain-Funktionen, i18n-Keys) stehen
    für die weiteren UI-Tasks.
  - Completion criteria: Der Besitzer legt Topics und Notes an, sieht sie im
    Baum und in der Liste, ändert und löscht sie; die Domain-Funktionen
    haben Unit-Tests, die Komponenten Komponententests; scripts/check.sh ist
    grün.
  - Summary: Der Bereich Notes mit Topic-Baum und Notes-Liste ist da; Topics
    und Notes lassen sich anlegen, ändern, verschieben und löschen.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-018/TASK-018_notes.md`.
  - Spec: `items/TASK-018/TASK-018_spec.md`.

- `TASK-019` **Notes-Bereich: Detailansicht, Dokumente und Links**
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-018`, `TASK-007`, `TASK-008`.
  - Goal: Eine gewählte Note zeigt ihre Kurzfassung und ihren Langtext
    (bearbeitbar), ihre Links (setzen und lösen, auch auf Items anderer
    Projekte) sowie ihre Notizen und Specs (lesen und schreiben wie beim
    Backlog). Konflikte durch gleichzeitige Änderungen werden angezeigt.
  - Completion criteria: Kurzfassung und Langtext lassen sich ändern, Links
    setzen und lösen, Notizen und Specs lesen und schreiben; ein
    Versionskonflikt erscheint als Meldung; Komponententests;
    scripts/check.sh ist grün.
  - Summary: Eine gewählte Note zeigt Kurzfassung, Langtext, Links und
    Notizen/Specs; alles lässt sich ändern, Versionskonflikte werden
    gemeldet.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-019/TASK-019_notes.md`.
  - Spec: `items/TASK-019/TASK-019_spec.md`.

- `TASK-020` **Notes-Bereich: Auslöser anzeigen, bearbeiten und Zurückstellen**
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-019`, `TASK-006`.
  - Goal: Auslöser einer Note lassen sich in der Detailansicht anlegen und
    entfernen: Zeitpunkt (Datum und Uhrzeit in der Zeitzone des Rechners),
    Ereignis (Item und Zielstatus wählen) und Topic-Termin. Bereits erfüllte
    Ziele werden vor dem Speichern angezeigt. Zurückstellen ist mit
    Schnellwahl (morgen, in einer Woche, in 30 Tagen, eigenes Datum, bei
    Ereignis) möglich. Der Modus any/all ist vorbereitet, aber nicht
    bedienbar.
  - Completion criteria: Alle drei Auslöser-Arten lassen sich anlegen und
    entfernen; ein bereits erreichter Zielstatus wird vor dem Speichern
    gemeldet; Zurückstellen mit den Schnellwahlen funktioniert;
    Domain-Funktionen und Komponenten sind getestet; scripts/check.sh ist
    grün.
  - Summary: Auslöser lassen sich anlegen und entfernen, Notes lassen sich
    zurückstellen, Topics bekommen einen Termin.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-020/TASK-020_notes.md`.
  - Spec: `items/TASK-020/TASK-020_spec.md`.

- `TASK-021` **Rotes Ausrufezeichen mit Zähler und Tab-Titel**
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-009`, `TASK-018`.
  - Goal: Neben dem Titel 'ToDo-Viewer' oben links steht ein dezentes rotes
    Ausrufezeichen, solange es fällige Notes oder offene Hinweise gibt, mit
    der Anzahl (global über alle Projekte). Der Zähler wird alle etwa 60
    Sekunden und beim Fokussieren des Fensters abgefragt. Die Anzahl steht
    auch im Tab-Titel. Ohne Fälliges verschwindet das Icon.
  - Completion criteria: Das Icon erscheint und verschwindet mit dem Zustand
    der Daten; der Zähler wird per Intervall und bei Fensterfokus abgefragt;
    der Tab-Titel trägt die Zahl; Domain-Funktion und Komponente sind
    getestet; scripts/check.sh ist grün.
  - Summary: Das rote Ausrufezeichen zeigt die Zahl fälliger Notes neben dem
    Titel und im Tab-Titel.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-021/TASK-021_notes.md`.
  - Spec: `items/TASK-021/TASK-021_spec.md`.

- `TASK-022` **Fällig-Modal mit Gruppierung und Aktionen**
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-021`, `TASK-020`, `TASK-015`, `TASK-010`.
  - Goal: Ein Klick auf das Ausrufezeichen öffnet ein Modal mit allen
    fälligen Notes, gruppiert nach Grund (Auslöser, Prüfung, Termin,
    Änderungshinweis). Je Zeile gibt es die Aktionen zurückstellen
    (Schnellwahlen), erledigen, verwerfen, befördern und in Notes öffnen;
    bei Hinweisen zusätzlich behalten und abkoppeln. Die Zeile bleibt, bis
    sie bearbeitet ist; es gibt kein Popup außerhalb des Modals.
  - Completion criteria: Das Modal zeigt alle fälligen Notes nach Grund
    gruppiert, jede Aktion wirkt und die Zeile verschwindet erst nach der
    Bearbeitung; Gruppierung und Aktionsregeln sind Unit-getestet;
    scripts/check.sh ist grün.
  - Summary: Das Fällig-Modal zeigt alle fälligen Notes nach Grund gruppiert
    mit den Aktionen; eine Zeile bleibt, bis die Aktion beim Server gelang.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-022/TASK-022_notes.md`.
  - Spec: `items/TASK-022/TASK-022_spec.md`.

- `TASK-023` **Verlinkte Notes am Backlog-Item und Notes-Einstellungen**
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-019`, `TASK-007`, `TASK-009`, `TASK-012`.
  - Goal: Im Detail eines Backlog-Items erscheinen die Notes, die darauf
    verweisen, auch aus anderen Projekten, mit Status und Sprung zur Note,
    sowie offene Hinweise zur Kenntnisnahme. Im Einstellungsabschnitt
    'Allgemein' lassen sich Prüf-Intervall (Standard 30) und maximale
    Topic-Tiefe (Standard 3) einstellen.
  - Completion criteria: Das Item-Detail zeigt verlinkte Notes mit Status
    und Link in die Notes-Ansicht; offene Item-Hinweise lassen sich zur
    Kenntnis nehmen; die Einstellungen werden gelesen und gespeichert;
    Komponententests; scripts/check.sh ist grün.
  - Summary: Das Item-Detail zeigt verlinkte Notes und offene Hinweise; die
    Notes-Optionen stehen im Einstellungsmenü.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/TASK-023/TASK-023_notes.md`.
  - Spec: `items/TASK-023/TASK-023_spec.md`.

- `STORY-037` **Architekturregeln für Topics, Notes und Links**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die verbindlichen Architekturregeln beschreiben, wo Topics, Notes
    und Links in den Schichten liegen: Notes sind datenbankprimär, nur in
    der zentralen Datenbank, nie in TODO.md; Links zeigen auf die interne
    uid; die Auslöser-Prüfung liegt im Viewer.
  - Completion criteria: Die Regeln in docs/development/architecture.md sind
    ergänzt und mit Begründung versehen; die Architektur-Prüfung kennt die
    neuen Bausteine.
  - Summary: Die verbindlichen Architekturregeln beschreiben, wo Topics,
    Notes und Links in den Schichten liegen: Notes sind datenbankprimär, nur
    in der zentralen Datenbank, nie in TODO.md; Links zeigen auf die in
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/STORY-037/STORY-037_notes.md`.
  - Spec: `items/STORY-037/STORY-037_spec.md`.

- `STORY-038` **Datenmodell: Topics, Notes und Links in der Datenbank**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Relationales Modell mit Migration: Topic (uid, label, Name,
    Eltern-Topic, Tiefe standardmäßig 3, konfigurierbar, optionaler Termin),
    Note (uid, label, Kurzfassung, optionaler Langtext, Status, Topic,
    Prüf-Datum, Heimatprojekt, Modus für Auslöser 'any' oder 'all'), Link
    (Note zu Item, Topic oder Note; Rolle Bezug, Auslöser oder Herkunft;
    auch projektübergreifend) und Auslöser (Zeitpunkt, Ereignis,
    Topic-Termin; jeder mit eigenem Zustand und Eintreffzeitpunkt). Eine
    Note kann wie ein Backlog-Item Notizen und Specs als Dokumente tragen.
    Labels NOTE-001 und TOPIC-001 zählen pro Projekt und Typ und ändern sich
    innerhalb eines Projekts nie. Ein Projektwechsel legt die Note im
    Zielprojekt neu an (neues Label) und löscht die alte; die Link-Prüfungen
    greifen dabei automatisch.
  - Completion criteria: Migration läuft auf bestehender Datenbank; Tiefe
    (Standard 3, konfigurierbar), Label-Vergabe, Link-Rollen und
    Auslöser-Modus sind per Tests abgedeckt; ein Link überlebt einen
    Typwechsel (retype) des Items; Notizen und Specs an einer Note lassen
    sich speichern und lesen; ein Projektwechsel erzeugt im Zielprojekt eine
    Note mit neuem Label und löscht die alte, Links werden dabei geprüft.
  - Summary: Datenmodell mit Migration für Topics (Tiefe 3), Notes (mit
    Notizen und Specs), Links und Auslöser; Labels zählen pro Projekt, ein
    Projektwechsel legt die Note neu an.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/STORY-038/STORY-038_notes.md`.
  - Spec: `items/STORY-038/STORY-038_spec.md`.

- `STORY-039` **API für Topics, Notes und Links inklusive schlanker Übersicht**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Anlegen, Lesen, Ändern, Verschieben (Topic; bei Notes auch
    Projektwechsel als Neuanlegen mit neuem Label und Löschen der alten
    Note), Löschen für Topics und Notes sowie Links setzen und lösen.
    Notizen und Specs einer Note lassen sich wie beim Backlog lesen und
    schreiben. Ein schlanker Index liefert je Topic und Note nur Label,
    Status, Fälligkeit und Kurzfassung, filterbar nach Topic, Projekt,
    Status, fällig und verlinktem Item (Notes zu Item X); dazu eine reine
    Zähler-Abfrage für fällige Notes. So lädt ein LLM nur relevante
    Langtexte. Version-Token gegen gleichzeitige Änderungen wie beim
    Backlog.
  - Completion criteria: Ein LLM kann über die API alle Operationen
    ausführen; der Index ist ohne Langtexte nutzbar; Konflikte werden
    erkannt.
  - Summary: API für Topics, Notes und Links inklusive Projektwechsel,
    Notizen und Specs, schlankem Index und Zähler-Abfrage für fällige Notes.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/STORY-039/STORY-039_notes.md`.
  - Spec: `items/STORY-039/STORY-039_spec.md`.

- `STORY-040` **Auslöser und Wiedervorlage im Viewer**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Viewer prüft selbst, ohne LLM und ohne Hintergrund-Takt:
    Zeitpunkt erreicht (beim Lesen ausgewertet, Zeitzone des Rechners),
    Ereignis an einem verlinkten Item (Status In progress, Awaiting
    confirmation, Completed oder Rejected erreicht; ist das Ziel bei Anlage
    schon erreicht, feuert der Auslöser sofort und ist so markiert),
    Topic-Termin erreicht. Eine Note kann mehrere Auslöser haben; jeder
    reagiert einzeln, zusätzlich wird erkannt, wenn alle eingetroffen sind.
    Ein Modus 'any' (Standard) oder 'all' ist im Modell vorgesehen, die
    Bedienung folgt später. Jede Note hat ein Prüf-Datum (Standard 30 Tage,
    globale Option); es wird bei Anlage, Textänderung, Zurückstellen und
    'behalten' zurückgesetzt und gilt für alle Notes. Ausgelöst ist nicht
    erledigt: Zustände wartend, fällig, zurückgestellt (setzt gefeuerte
    Auslöser zurück, wieder wartend mit neuem Datum oder Ereignis),
    erledigt, verworfen, befördert. Eine fällige Note bleibt fällig, bis sie
    zurückgestellt, erledigt, verworfen oder gelöscht ist. Zeiten sind
    konkrete Zeitpunkte; die Auflösung von 'morgen früh' macht der Aufrufer.
  - Completion criteria: Zeit-, Ereignis- und Termin-Auslöser lösen ohne
    offene Sitzung aus; Zurückstellen setzt die Note wieder auf wartend;
    Wiedervorlage und Standardwert sind per Test geprüft.
  - Summary: Der Viewer erkennt Zeit-, Ereignis- und Termin-Auslöser sowie
    die 30-Tage-Wiedervorlage selbst, ohne LLM und ohne Hintergrund-Takt;
    fällige Notes bleiben fällig, bis sie bearbeitet sind.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/STORY-040/STORY-040_notes.md`.
  - Spec: `items/STORY-040/STORY-040_spec.md`.

- `STORY-042` **Beförderung und Rückstufung zwischen Note und Item**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Note wird zu Task, Story oder Epic: Kurzfassung wird Titel und
    Kurzfassung, Langtext, Notizen und Specs werden die Notizen und Specs
    des Items, die Note gilt als befördert und wird archiviert, der Link
    Herkunft bleibt. Fehlende Pflichtfelder (Typ, Bereich, Ziel,
    Abschlusskriterien, Parent) liefert der Aufrufer; die UI zeigt ein
    vorausgefülltes Formular, alle Backlog-Prüfungen laufen. Item wird zur
    Note nur im Status Open, ohne Kinder, ohne dass es Parent oder
    Dependency eines anderen Items ist: das Item wird mit Resolution 'zur
    Notiz zurückgestuft' abgeschlossen, seine Notizen und Specs wandern an
    die neue Note, die Note erhält den Link Herkunft. Beide behalten ihre
    eigene ID.
  - Completion criteria: Beide Richtungen funktionieren über API und UI;
    Herkunft ist an Note und Item sichtbar; unzulässige Rückstufungen werden
    mit Grund abgelehnt.
  - Summary: Eine Note wird zu Task, Story oder Epic und umgekehrt ein
    offenes Item ohne Anhang zur Note; Notizen und Specs wandern in beide
    Richtungen mit, die Herkunft bleibt sichtbar.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/STORY-042/STORY-042_notes.md`.
  - Spec: `items/STORY-042/STORY-042_spec.md`.

- `STORY-043` **Archiv und Papierkorb für Notes**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Erledigte, verworfene und beförderte Notes wandern ins Archiv,
    gelöschte in den Papierkorb, jeweils wiederherstellbar; endgültiges
    Löschen nur durch den Besitzer. Orientierung ist das Backlog.
  - Completion criteria: Lebenszyklus, Archiv, Papierkorb und
    Wiederherstellen sind per Test abgedeckt.
  - Summary: Erledigte, verworfene und beförderte Notes wandern ins Archiv,
    gelöschte in den Papierkorb, jeweils wiederherstellbar; endgültiges
    Löschen nur durch den Besitzer
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/STORY-043/STORY-043_notes.md`.
  - Spec: `items/STORY-043/STORY-043_spec.md`.

- `STORY-044` **Projektübergreifende Links**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-06.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein Link darf auf ein Item in einem anderen registrierten Projekt
    zeigen; Anzeige und API nennen es als Projekt und Label.
    Ereignis-Auslöser funktionieren projektübergreifend; die Rückrichtung
    erscheint am Item im anderen Projekt. Ist das Projekt nicht erreichbar,
    wird der Link als nicht erreichbar markiert und löst einen
    Änderungshinweis aus.
  - Completion criteria: Ein Merker in Projekt A, der auf ein Item in
    Projekt B wartet, löst bei dessen Abschluss aus; ein entferntes Projekt
    erzeugt einen Hinweis statt eines Fehlers.
  - Summary: Ein Link darf auf ein Item in einem anderen registrierten
    Projekt zeigen; Anzeige und API nennen es als Projekt und Label
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/STORY-044/STORY-044_notes.md`.
  - Spec: `items/STORY-044/STORY-044_spec.md`.

- `STORY-045` **Bereich Notes: Topic-Baum, Notes und rotes Ausrufezeichen**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-06.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Eigener Bereich neben dem Backlog: Topic-Baum, Notes mit
    Kurzfassung und Langtext, Links setzen. Ein dezentes rotes
    Ausrufezeichen zeigt fällige Notes; ein Klick öffnet die Liste mit den
    Aktionen zurückstellen, erledigen, verwerfen, befördern. Am Backlog-Item
    erscheinen verlinkte Notes. Anzeigetexte über die Lokalisation, Keys
    englisch. Kein Popup in dieser Stufe.
  - Completion criteria: Der Besitzer legt Topics und Notes an, sieht
    Fälliges, handelt darauf und erreicht Notes vom Item aus.
  - Summary: Eigener Bereich Notes mit Topic-Baum, Notes, Auslösern, rotem
    Ausrufezeichen, Fällig-Modal und Notes am Backlog-Item.
  - Resolution: Vom Projektinhaber bestätigt (2026-10-08).
  - Notes: `items/STORY-045/STORY-045_notes.md`.
  - Spec: `items/STORY-045/STORY-045_spec.md`.

- `STORY-052` **Papierkorb: Mehrfachauswahl mit Alle-Haken, Auswahl löschen oder wiederherstellen, Icon-Buttons**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-10-09.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Im Papierkorb lassen sich mehrere Items auf einmal endgültig
    löschen oder wiederherstellen; die Aktionen sind Icon-Buttons.
  - Completion criteria: 1. Jede Zeile hat eine Checkbox; ein Haken oben
    wählt alle sichtbaren Items an oder ab (teilweise gewählt wird
    angezeigt). 2. „Auswahl endgültig löschen“ löscht nach einer Bestätigung
    mit der Anzahl alle gewählten Items samt Kindern; „Auswahl
    wiederherstellen“ holt sie zurück. 3. Ist ein Item und sein Vorfahre
    gewählt, wird nur der Vorfahre angefragt; Fehler einzelner Items werden
    gemeldet, die übrigen trotzdem bearbeitet. 4. Wiederherstellen und
    Löschen sind auch je Zeile Icon-Buttons mit Hovertext. 5. Tests und Doku
    sind angepasst.
  - Summary: Der Papierkorb bekommt Checkboxen, einen Alle-Haken und
    Aktionen für die Auswahl, alles mit Icons.
  - Resolution: Vom Owner am 2026-10-09 bestätigt.

- `EPIC-002` **Backlog-Pflege in der UI**
  - Type: Epic.
  - Status: Completed.
  - Created: 2026-09-27.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: In der UI lassen sich Items anlegen und löschen, ihre
    Freitext-Felder (Titel, Goal, Completion criteria, Summary, Area,
    Parent, Dependencies) bearbeiten sowie Notes-Einträge und Specs
    schreiben. Die UI nutzt dafür die Endpunkte aus `EPIC-001`.
  - Completion criteria: Alle Pflichtkinder sind abgeschlossen; jede
    genannte Funktion ist in der UI bedienbar, Fehlercodes der API werden
    übersetzt angezeigt, und der Projektverantwortliche hat die Bedienung
    geprüft.
  - Summary: Alles, was künftig ein Agent über die API am Backlog ändern
    kann, soll auch direkt in der Oberfläche möglich sein.
  - Resolution: Confirmed by the project owner on 2026-10-09.
  - Notes: `items/EPIC-002/EPIC-002_notes.md`.

- `TASK-028` **Notes-Index: Filter nach mehreren Status**
  - Type: Task.
  - Parent: `STORY-050`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-09.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Notes-Index der API v2 filtert in einem Aufruf nach einer
    Liste von Status, einschließlich des abgeleiteten Status „fällig“.
  - Completion criteria: Der Index nimmt mehrere Status an und liefert genau
    die Notes mit einem dieser effektiven Status; ohne Angabe bleibt das
    bisherige Verhalten. API-Tests, OpenAPI-Schema und interfaces.md sind
    angepasst.
  - Resolution: Vom Owner am 2026-10-09 bestätigt. (mit STORY-050)

- `TASK-029` **Sidebar als Hülle mit tababhängigen Filterabschnitten**
  - Type: Task.
  - Parent: `STORY-050`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-09.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Sidebar zeigt Suche und Projekte immer und darunter die
    Filterabschnitte, die der aktive Tab vorgibt.
  - Completion criteria: Baum, Kanban und Graph zeigen wie bisher Status und
    Priorität; der Papierkorb zeigt nur Suche und Projekte. Das Verhalten
    der Backlog-Filter bleibt unverändert; Komponententests decken die
    Abschnitte je Tab ab.
  - Resolution: Vom Owner am 2026-10-09 bestätigt. (mit STORY-050)

- `TASK-030` **Notes-Status als Sidebar-Filter, Notes-Filterleiste verschlanken**
  - Type: Task.
  - Parent: `STORY-050`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-09.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Im Notes-Bereich filtert die Sidebar nach den Note-Status
    (mehrfach wählbar) und die Sidebar-Suche ersetzt die eigene Notes-Suche.
  - Completion criteria: Note-Status erscheinen als Checkboxen mit Farben,
    Standard wartet/fällig/zurückgestellt; die Auswahl wird getrennt von den
    Backlog-Filtern gespeichert. Status-Dropdown, „Nur fällige“ und das
    Notes-Suchfeld sind entfernt. Tests sind angepasst.
  - Resolution: Vom Owner am 2026-10-09 bestätigt. (mit STORY-050)

- `STORY-050` **Sidebar als tababhängige Filterhülle; Notes-Status als Sidebar-Filter**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-10-09.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-049`.
  - Goal: Die linke Sidebar ist eine einheitliche Filterebene für alle
    Bereiche: Suche und Projekte stehen immer dort, die übrigen Abschnitte
    füllt der aktive Tab. Im Notes-Bereich filtert die Sidebar nach den
    Note-Status statt nach Backlog-Status und Priorität.
  - Completion criteria: 1. Sidebar zeigt immer Suche und Projekte;
    Baum/Kanban/Graph zusätzlich Status und Priorität des Backlogs, Notes
    die Note-Status (wartet, fällig, zurückgestellt, erledigt, verworfen,
    befördert), Papierkorb keine weiteren Abschnitte. 2. Note-Status sind
    mehrfach wählbar; Standard sind wartet, fällig und zurückgestellt
    (entspricht „Offene Notes“). 3. Status-Dropdown, „Nur fällige“ und das
    eigene Suchfeld entfallen in der Notes-Filterleiste; „Unterthemen
    einbeziehen“ und „Gruppieren“ bleiben. 4. Die Notes-Status-Auswahl wird
    getrennt von den Backlog-Filtern gespeichert und beeinflusst diese
    nicht. 5. Der Notes-Index der API akzeptiert mehrere Status in einem
    Aufruf. 6. Tests und technische Doku sind angepasst.
  - Summary: Die Sidebar wird zur Hülle, die je nach Tab passende Filter
    zeigt. Notes bekommen dort ihre eigenen Status als Checkboxen; eine
    Priorität für Notes ist bewusst nicht Teil dieser Story.
  - Resolution: Vom Owner am 2026-10-09 bestätigt.
  - Notes: `items/STORY-050/STORY-050_notes.md`.

- `STORY-051` **Notes als Baum darstellen wie im Backlog (Projekt → Topic → Note)**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-10-09.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-050`.
  - Goal: Der Notes-Bereich zeigt Topics und Notes als aufklappbaren Baum im
    Hauptbereich, aufgebaut wie der Backlog-Baum. Der eigene Topic-Baum
    links entfällt, die Sidebar bleibt die einzige Navigations- und
    Filterebene.
  - Completion criteria: 1. Notes erscheinen als Baum Projekt → Topic →
    Unterthema → Note, auf- und zuklappbar wie im Backlog-Baum. 2. Notes
    ohne Topic stehen unter einem Knoten „Ohne Thema“ direkt unter dem
    Projekt. 3. Leere Topics bleiben sichtbar und lassen sich bearbeiten. 4.
    Jede Topic-Zeile bietet ihre Aktionen (+ Note, Unterthema, Umbenennen,
    Termin, Verschieben, Löschen) als Icons in der Zeile; eine neue Note
    landet in diesem Topic. 5. Die eigene Topic-Spalte sowie die Schalter
    „Gruppieren“ und „Unterthemen einbeziehen“ entfallen. 6. Die
    Sidebar-Filter aus STORY-050 wirken auf den Baum. 7. Tests und
    technische Doku sind angepasst.
  - Summary: Notes und Topics werden wie das Backlog als Baum gezeigt. Damit
    gibt es links nur noch die Sidebar, und Gruppierung sowie Schachtelung
    zeigt der Baum von selbst.
  - Resolution: Vom Owner am 2026-10-09 bestätigt.
  - Notes: `items/STORY-051/STORY-051_notes.md`.

- `STORY-053` **Notes-Baum: Projektbalken und erweiterte Markierung der Topic-Ebenen**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-10-09.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Projekte und Topics sind im Notes-Baum optisch klar gruppiert;
    eine Checkbox wechselt zwischen der markierten und der schlichten
    Ansicht.
  - Completion criteria: 1. Unter jedem Projekttitel liegt ein durchgehender
    Balken als Trenner (kein Fortschritt). 2. Mit „Erweiterte Markierung“
    ist der Bereich eines Topics der Ebene 1 (Zeile samt Inhalt) dezent
    grünlich hinterlegt, der Bereich eines Topics der Ebene 2 darin dezent
    grau; tiefere Ebenen und Notes ohne eigene Fläche. 3. Die Checkbox
    „Erweiterte Markierung“ in der Kopfzeile des Notes-Bereichs schaltet
    zwischen dieser und der schlichten Ansicht; die Wahl wird mit dem
    UI-Zustand gespeichert, Standard ist an. 4. Der Balken im Backlog-Baum
    bleibt unverändert. 5. Tests und Doku sind angepasst.
  - Summary: Der Notes-Baum bekommt Projektbalken und zwei dezente Flächen
    für Topic-Ebene 1 und 2, abschaltbar per Checkbox.
  - Resolution: Confirmed by the project owner on 2026-10-09.
  - Notes: `items/STORY-053/STORY-053_notes.md`.

- `STORY-049` **Notes-Bereich: Filter, Großansicht, Steuerung oben und sichtbare Schachtelung**
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-10-09.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Notes-Bereich lässt sich wie das Backend filtern, eine Note
    lässt sich groß lesen und bearbeiten, die Aktionen stehen oben im Detail
    und die Themen-Schachtelung ist so gut sichtbar wie im To-do-Baum.
  - Completion criteria: 1. Filterleiste (Status, nur fällig, Projekt,
    Suche) schickt Status, fällig und Projekt als Query an /notes/index; der
    Umfang eines Themas (inkl. Unterthemen) ist abschaltbar; Zähler im Baum
    zeigen die Summe inkl. Unterthemen. 2. Großansicht einer Note mit
    Inhaltsverzeichnis und Bearbeiten (Vorschau neben dem Editor). 3. Feste
    Kopfleiste im Detail mit Aktionen als Icon-Buttons mit Hovertext;
    Auslöser, Links und Notizen/Specs als einklappbare Abschnitte mit
    Hinzufügen-Buttons in der Überschrift. 4. Themen-Baum mit Einrückung,
    Führungslinien und Auf-/Zuklappen; Gruppierung nach Topic in der Liste;
    Topic-Pfad im Detail. 5. Icon-Buttons mit Hovertext statt großer
    Textbuttons, wo sinnvoll. Tests und Doku angepasst.
  - Summary: Der Notes-Bereich bekommt echte Filter, eine Großansicht, die
    Steuerung oben im Detail, Icon-Buttons mit Hovertext und eine gut
    sichtbare Themen-Schachtelung.
  - Resolution: Confirmed by the project owner on 2026-10-09.
  - Notes: `items/STORY-049/STORY-049_notes.md`.
