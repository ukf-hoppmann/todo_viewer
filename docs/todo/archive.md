# Project Backlog Archive

Completed and rejected work items, moved unchanged from `TODO.md` after the
project owner's decision.

Format: Claude_Harness backlog format version 2. The rules are defined in
`docs/techdocs/interfaces.md` of the ToDo Viewer.

## Work items

- `TASK-052` **Mindmap-Server: Knoten, Platzierungen und Projektbaum mit API und MCP**
  - Uid: 26d4cdfa-7632-4e6d-bacf-2a17a04a7334.
  - Type: Task.
  - Parent: `STORY-099`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-11-13.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Ein neues Server-Plugin speichert Knoten und ihre Platzierungen,
    führt je Projekt einen Baum und bietet Anlegen, Lesen, Ändern, Umhängen,
    Papierkorb und Wiederherstellen über API und MCP.
  - Completion criteria: 1. Knoten und Platzierungen liegen in eigenen
    Tabellen; ein Knoten ist ein Element des Workspace.
    2. Die Domain weist Kreise, fremde Projekte und einen Knoten zweimal im
    selben Baum ab.
    3. Die Operationen sind über API und MCP erreichbar und melden Ereignisse.
    4. Domain- und API-Tests sind grün, die Schnittstellen sind dokumentiert.
  - Resolution: Vom Projekteigner am 2026-11-16 bestätigt; gemergt nach `todo_mindmap`.

- `STORY-028` **Architekturregeln: Primärquelle und Spiegel statt genau einem Backend**
  - Uid: 010ef637-220f-49da-beab-0b7a96c81684.
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

- `STORY-009` **Notes und Specs über das Item schreiben**
  - Uid: 02135fbf-f68c-4914-a5c0-03f312a45ae6.
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

- `STORY-035` **Doku und Release für Primärquelle, Spiegel und Einstellungsmenü**
  - Uid: 0743a9f7-b9d0-44b5-8ba0-2e0abbb7e453.
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

- `TASK-018` **Notes-Bereich: Gerüst, Topic-Baum und Notes-Liste**
  - Uid: 0820773d-6951-4665-b3d6-e6a5f855e53a.
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

- `STORY-018` **Typ eines Items in der UI ändern**
  - Uid: 0b1c32be-f212-4a3d-9538-545526289fdc.
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

- `STORY-027` **Dokument-Port itembasiert statt pfadbasiert**
  - Uid: 0bc0f866-bee6-43e7-83c7-d43f92a8081f.
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

- `TASK-027` **Notes im gemeinsamen Sync-Dialog bedienen**
  - Uid: 11ce2207-4ee3-4efc-a42e-3df350fc2341.
  - Type: Task.
  - Parent: `STORY-047`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-058`, `TASK-026`.
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

- `EPIC-004` **Primärquelle und Spiegel pro Projekt, Einstellungsmenü**
  - Uid: 13ddda49-0b8f-4be0-8951-6a8dbf6b3812.
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

- `STORY-058` **Konflikte im Sync mit Diff-Ansicht entscheiden**
  - Uid: 15bed314-f3cc-4933-9306-4cc142e3cfdb.
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

- `TASK-031` **Automatisches Datenbank-Backup vor Migration und Sync**
  - Uid: 1ddf56f5-8384-459f-93f7-e30762ba6b80.
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

- `EPIC-006` **Markdown nicht mehr Normalbetrieb: Datenbank und API als Hauptanwendung**
  - Uid: 1f9fc77c-e0ed-4a41-bd4b-a2e657cff82d.
  - Type: Epic.
  - Status: Rejected.
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
  - Resolution: Im Neubau abgedeckt: Datenbank als Wahrheit, Markdown als
    Spiegel (STORY-065, STORY-075). Entscheidung des Inhabers, STORY-060
    Frage 3, 2026-10-17.

- `STORY-034` **Menüabschnitt „Projekte“: Primärquelle, Pfade und Sync je Projekt**
  - Uid: 1fa40d57-f13e-49bd-92a5-e81c89ff7091.
  - Type: Story.
  - Parent: `EPIC-004`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-030`, `STORY-031`, `STORY-032`, `STORY-033`.
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

- `STORY-001` **Bessere Platzierung der Fortschritts-Pie-Charts**
  - Uid: 205a1287-98f8-494f-bc08-5f395b34a156.
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

- `TASK-009` **Notes-Index, Fällig-Zähler, Fällig-Liste und Notes-Einstellungen**
  - Uid: 246d5ef2-6827-4b74-88ee-42f5e511ece0.
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

- `STORY-041` **Änderungshinweise zwischen Notes und Items**
  - Uid: 27f21d9d-4277-4852-b4d2-c919f6f772fa.
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Rejected.
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
  - Resolution: Im Neubau umgesetzt: Hinweise zwischen Notes und Items in
    STORY-078 (Entscheidung des Inhabers, STORY-060 Frage 3, 2026-10-17).

- `TASK-022` **Fällig-Modal mit Gruppierung und Aktionen**
  - Uid: 2cde2ec7-d29f-4140-8d6e-8a0d76b71839.
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-010`, `TASK-015`, `TASK-020`, `TASK-021`.
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

- `TASK-014` **Offenes Item zur Note zurückstufen (Backend)**
  - Uid: 2de8ce23-9380-4de5-baed-c49030bd75c1.
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

- `EPIC-003` **Wählbares Speicher-Backend: Markdown oder zentrale Datenbank**
  - Uid: 2e1377a4-9ba2-4630-b5a3-70044da1cf52.
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

- `TASK-010` **Hinweis-Modell: speichern, fällig machen, entscheiden**
  - Uid: 2e237397-8bdb-4ea3-bbf2-ca278c6bf2e3.
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

- `STORY-010` **API-Zugang für Agenten**
  - Uid: 30cfb092-3b55-4cab-bc92-edc8cb44d0fe.
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

- `STORY-003` **Items nur über ID adressieren**
  - Uid: 320438ac-3c4e-4fcc-be76-64998a8763f4.
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

- `STORY-011` **Papierkorb: Löschen markiert, Wiederherstellen und endgültig Löschen**
  - Uid: 33b649c7-ae5b-4a5e-a785-a3101a00a474.
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

- `TASK-011` **Hinweise an Notes bei Änderung eines verlinkten Items**
  - Uid: 35dc707b-4c24-416d-b616-358bc5502197.
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

- `TASK-001` **Area im Lean Index**
  - Uid: 3623c879-47a4-4da1-80b8-8d0de80dab28.
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

- `STORY-053` **Notes-Baum: Projektbalken und erweiterte Markierung der Topic-Ebenen**
  - Uid: 390cc0b6-bf9d-4dbf-834f-4c01e870ff8c.
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

- `STORY-012` **Felder im Bearbeiten-Modus ändern**
  - Uid: 391f9624-0f9b-42f4-ab6c-307af07e6802.
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

- `STORY-004` **Lean Index**
  - Uid: 3a1c42be-bbdd-4b3b-bd7b-2696bafe524b.
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

- `TASK-005` **Notes-API: anlegen, lesen, ändern, Projekt wechseln**
  - Uid: 3d92cb0d-f201-4938-a9b8-b77c271702af.
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

- `STORY-049` **Notes-Bereich: Filter, Großansicht, Steuerung oben und sichtbare Schachtelung**
  - Uid: 47cc4636-766d-4f2a-bf68-b3b5a45377fd.
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

- `TASK-021` **Rotes Ausrufezeichen mit Zähler und Tab-Titel**
  - Uid: 55eb41c2-296e-4945-bea9-a1c739a3b18f.
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

- `TASK-023` **Verlinkte Notes am Backlog-Item und Notes-Einstellungen**
  - Uid: 5703e21b-4905-4085-b4e0-7668d79ae65b.
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-007`, `TASK-009`, `TASK-012`, `TASK-019`.
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

- `EPIC-002` **Backlog-Pflege in der UI**
  - Uid: 5a2e476e-3591-4f1a-8b34-fde2b3095564.
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

- `STORY-016` **Wichtige Schritte und Fehler systematisch protokollieren**
  - Uid: 5c506e1d-b51c-4f98-88fd-4e11d4cad351.
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

- `STORY-051` **Notes als Baum darstellen wie im Backlog (Projekt → Topic → Note)**
  - Uid: 5d128bb5-24cf-4e8a-9d8c-c5f603ac9243.
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

- `STORY-013` **Items in der UI anlegen**
  - Uid: 5dc66222-ed79-4093-a013-d19569895970.
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

- `STORY-038` **Datenmodell: Topics, Notes und Links in der Datenbank**
  - Uid: 60dffe96-86fd-4c1f-9d00-278fad4ec5c4.
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

- `STORY-006` **Weitere Felder bearbeitbar**
  - Uid: 63b6635c-8612-416c-90a9-55ee6d016a46.
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

- `STORY-046` **Doku und Release für Notes und Topics**
  - Uid: 64ab63d0-6a49-4721-8877-ba743b2b801b.
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

- `STORY-021` **SQLite-Adapter für Items, Archiv, Papierkorb und Dokumente**
  - Uid: 6c2bfed9-05e5-437b-883c-eabfae5c3649.
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

- `TASK-004` **Topics-API: anlegen, lesen, ändern, verschieben, löschen**
  - Uid: 6c4bfb16-ea57-44a1-92c8-5a9ceb3ec9a8.
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

- `STORY-043` **Archiv und Papierkorb für Notes**
  - Uid: 71590695-a0c8-48e9-acbf-6e1ffe1cee21.
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

- `STORY-055` **Topics ins Archiv verschieben und wieder aktivieren**
  - Uid: 757faaf3-a5d4-4cc6-9f48-b9a2939a4870.
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Rejected.
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
  - Resolution: Im Neubau umgesetzt: Topics ins Archiv in STORY-077
    (Entscheidung des Inhabers, STORY-060 Frage 3, 2026-10-17).

- `STORY-017` **Klare Antwort und Wiederöffnen-Angebot bei geschlossenem Parent**
  - Uid: 771eb9c9-febe-425f-b0db-180aad431c42.
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

- `TASK-025` **Notes-Spiegel: Port und Datei-Adapter mit atomarem Schreiben**
  - Uid: 78a6cbef-54f7-4ad8-98e0-d09b3dff4faf.
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

- `STORY-056` **Eigenständige Erinnerungen: an Note, Item oder frei, zu einem Zeitpunkt**
  - Uid: 7d65d295-e591-4940-9caa-d224f915a2ac.
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: Yes.
  - Status: Rejected.
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
  - Resolution: Im Neubau umgesetzt: eigenständige Wecker in STORY-080
    (Entscheidung des Inhabers, STORY-060 Frage 3, 2026-10-17).

- `STORY-042` **Beförderung und Rückstufung zwischen Note und Item**
  - Uid: 7fe0fe54-9c9b-4e7e-ade6-54c9e14619e5.
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

- `TASK-019` **Notes-Bereich: Detailansicht, Dokumente und Links**
  - Uid: 7fe35a5a-f921-4521-b7cf-24e31ad8b53a.
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-007`, `TASK-008`, `TASK-018`.
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

- `STORY-050` **Sidebar als tababhängige Filterhülle; Notes-Status als Sidebar-Filter**
  - Uid: 85963e7c-7b5b-42c7-9374-5e771321fd16.
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

- `TASK-020` **Notes-Bereich: Auslöser anzeigen, bearbeiten und Zurückstellen**
  - Uid: 85e7ea85-d20b-4459-a233-1c07017fde35.
  - Type: Task.
  - Parent: `STORY-045`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-006`, `TASK-019`.
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

- `STORY-039` **API für Topics, Notes und Links inklusive schlanker Übersicht**
  - Uid: 87e761b8-d080-4187-8491-bdd3de9cd77b.
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

- `TASK-034` **Architekturregeln für den Neubau schreiben und freigeben lassen**
  - Uid: 8ba15d1e-2995-45b9-a470-b86e87c95d92.
  - Type: Task.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Architektur des Neubaus aus `EPIC-007_spec.md` ist als
    verbindliche Regeln in `docs/development/architecture.md` und Scopes
    festgehalten; die heutigen Regeln gelten bis zum Umstieg nur noch für
    den Altcode.
  - Completion criteria: 1. `architecture.md` enthält die projektweiten
    Regeln des Neubaus. 2. Scopes `server` (`server/**`), `client`
    (`client/**`) und `legacy` (`backend/**`, `web/**`) sind eingetragen;
    die heutigen Regeln 1–3 und die Scopes `backend`/`web` stehen in
    `legacy`. 3. Mechanisch prüfbare Regeln nennen ihren Test
    (import-linter, ESLint). 4. Der Projektinhaber hat die Änderungen
    freigegeben.
  - Summary: Die neuen Architekturregeln aufschreiben und von dir freigeben
    lassen. Ohne sie darf kein Code des Neubaus entstehen.
  - Resolution: Vom Projektinhaber am 2026-10-16 bestätigt:
    Architekturregeln für den Neubau freigegeben und übernommen.

- `STORY-002` **Alle Tasks/Stories ein- und ausklappen**
  - Uid: 8d655468-caeb-4af1-a147-297cb182ee55.
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

- `STORY-052` **Papierkorb: Mehrfachauswahl mit Alle-Haken, Auswahl löschen oder wiederherstellen, Icon-Buttons**
  - Uid: 92e7e5bf-32c7-445d-a4aa-888e91d099fe.
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

- `TASK-017` **Nicht erreichbare Projekte: Link markieren und Hinweis erzeugen**
  - Uid: 94177a13-65aa-452d-b1c6-22344e7552cb.
  - Type: Task.
  - Parent: `STORY-044`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-08.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-010`, `TASK-016`.
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

- `STORY-020` **Port-Vertrag als Contract-Suite und Routing je Projekt**
  - Uid: 94f48cca-8a2e-4b57-a099-7642f5b3fb4b.
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

- `STORY-029` **Primärquelle und Spiegel pro Projekt in Modell und API**
  - Uid: 99ed7e73-fc0f-463b-9305-3e408748dbaf.
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

- `TASK-030` **Notes-Status als Sidebar-Filter, Notes-Filterleiste verschlanken**
  - Uid: 9baa1793-7a7d-4888-8bf2-81abb1886f29.
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

- `STORY-040` **Auslöser und Wiedervorlage im Viewer**
  - Uid: 9c4a18ee-ddc9-4dd2-831a-4e1acc7b18fd.
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

- `TASK-035` **Markdown-Format Version 2 festlegen**
  - Uid: a0b47ae8-3579-4b1b-92fb-dbb4eaf01f07.
  - Type: Task.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-034`.
  - Goal: Das Markdown-Format des Spiegels (Backlog, Notes, Topics, Wecker)
    ist mit UUIDs und Platzhaltern für neue Einträge vollständig beschrieben
    und mit Beispielen belegt, sodass Codecs und Harness danach gebaut
    werden können.
  - Completion criteria: 1. `docs/techdocs/interfaces.md` beschreibt Format
    Version 2 vollständig: Dateien, Felder, `Uid`, Platzhalter, Verweise,
    Prüfregeln mit Fehlercodes. 2. Unter `tests/fixtures/mirror-v2/` liegt
    ein vollständiges Beispiel-Projekt (gültig) und je Prüfregel ein
    ungültiges Beispiel. 3. Der Projektinhaber hat das Format freigegeben.
  - Summary: Das Dateiformat festlegen, mit dem die LLM in der Cloud
    arbeitet: wie Version 1, dazu eine Uid je Eintrag und Platzhalter für
    neue Einträge.
  - Resolution: Vom Projektinhaber am 2026-10-16 bestätigt: Format Version 2
    freigegeben, beschrieben und mit Beispielen belegt.

- `STORY-015` **Notes und Specs in der UI schreiben und ändern**
  - Uid: a1ad0cbf-791f-4f47-a7fb-5122f585c673.
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

- `STORY-037` **Architekturregeln für Topics, Notes und Links**
  - Uid: a28a4f79-df36-40ca-b288-8fb1673f0d20.
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

- `EPIC-001` **Backlog-Pflege per API statt direkter Dateizugriffe**
  - Uid: a6d1c256-a508-4d65-b553-189d517abda8.
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

- `STORY-024` **Speicher-Backend und Sync in der UI bedienen**
  - Uid: a75ce60d-3c43-41b3-98af-25191de0f4ad.
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

- `STORY-008` **Items löschen**
  - Uid: ab7ff1a9-66b7-4d85-b6b7-cca033f5d463.
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

- `STORY-057` **Abgleich pro Eintrag mit Konfliktmeldung**
  - Uid: aba63dbf-a232-49d1-9023-7f97ad3d0f5e.
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

- `STORY-047` **Notes in Markdown spiegeln und zwischen Rechnern abgleichen**
  - Uid: b0de7bdc-62c1-415e-8045-a74ef38e9ae0.
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

- `TASK-032` **Stand je Eintrag speichern und Änderungsseite erkennen**
  - Uid: b1657efe-2c9d-4e9f-a357-cb0ee44adc55.
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

- `TASK-015` **UI-Dialoge für Beförderung und Rückstufung**
  - Uid: b53ecac4-04f8-4a37-93fa-d8f085d4236e.
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

- `STORY-014` **Löschen und Papierkorb-Ansicht**
  - Uid: b5b24f18-7825-46a5-8025-2d56c88943cc.
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

- `STORY-022` **Projekte und UI-State in der zentralen Datenbank**
  - Uid: b6a00fdc-dd4f-434c-8efc-4e590fb20f34.
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

- `STORY-045` **Bereich Notes: Topic-Baum, Notes und rotes Ausrufezeichen**
  - Uid: b84b7145-13a0-43fa-98dc-99afd6982083.
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

- `STORY-032` **Sync-Status: Spiegel extern geändert erkennen**
  - Uid: b91f7d5d-f4da-4648-9d85-91d48ffd8a78.
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

- `STORY-030` **Sync mit wählbarer Richtung, voller Umfang, Wechsel der Primärquelle**
  - Uid: bfc4f2f8-b092-4e78-b51d-6319e6e7b241.
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

- `STORY-031` **Backup vor dem Wechsel der Primärquelle**
  - Uid: c07fc2c9-28d4-43fb-93d3-d98e54df2f95.
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

- `STORY-025` **Doku und Release für das wählbare Speicher-Backend**
  - Uid: c532428c-c3fe-4bc3-bbf6-eebeb4287027.
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

- `TASK-006` **Notes-API: Lebenszyklus, Auslöser, Archiv und Papierkorb**
  - Uid: c7e72117-3483-4264-ad77-e9fb2c79d3ca.
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

- `TASK-012` **Hinweise an Items, wenn eine verlinkte Note verworfen oder befördert wird**
  - Uid: ca63b3b1-198c-497a-bb0e-4afa5df94078.
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

- `STORY-048` **Notes und Topics ohne Projekt anlegen**
  - Uid: cda6c4f3-ec92-4e7a-8f72-2c60a951ea7a.
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Rejected.
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
  - Resolution: Im Neubau umgesetzt: projektlose Notes im eingebauten
    Projekt 'Allgemein' (STORY-068, STORY-077; STORY-060 Frage 2 und 3).

- `STORY-019` **Architekturregeln für wählbares Speicher-Backend öffnen**
  - Uid: ceab73de-4712-47bc-9ae1-e737f920b29f.
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

- `TASK-033` **Konflikte beim Sync entscheiden: Datenbank, Datei oder aufschieben**
  - Uid: cf277ea8-bfec-49c8-87f6-de40417fe1d4.
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

- `TASK-016` **Projektübergreifende Links und Ereignis-Auslöser prüfen und absichern**
  - Uid: d12ff94c-67f2-472e-8b55-898b73cda8c5.
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

- `EPIC-005` **Notizen und Wiedervorlage: Topics, Notes, Auslöser**
  - Uid: d2dd0366-c727-466f-a353-c0fc1aa3c819.
  - Type: Epic.
  - Status: Rejected.
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
  - Resolution: Im Neubau abgedeckt: Notes und Topics (STORY-077), Hinweise
    (STORY-078), Wecker (STORY-080). Entscheidung des Inhabers, STORY-060
    Frage 3, 2026-10-17.

- `STORY-007` **Items anlegen**
  - Uid: d3ac0c49-748a-4ced-b016-2046342baa4f.
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

- `TASK-024` **Notes-Dateiformat: Serialisieren und Parsen mit Golden-Files**
  - Uid: d575122d-2d0a-4be2-a317-34abbd446676.
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

- `STORY-054` **Topic mit Notizen löschen: Auswahldialog statt stilles Mitlöschen**
  - Uid: db1b1e71-b503-45f4-b6bf-311e2462798d.
  - Type: Story.
  - Parent: `EPIC-005`.
  - Required for parent: No.
  - Status: Rejected.
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
  - Resolution: Im Neubau umgesetzt: Notes und Topics in STORY-077
    (Entscheidung des Inhabers, STORY-060 Frage 3, 2026-10-17).

- `STORY-044` **Projektübergreifende Links**
  - Uid: dc7de715-5ecd-4f1b-b58f-a3debe1bde29.
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

- `TASK-002` **Typ eines Items ändern**
  - Uid: ddd10ff9-985c-487e-87bd-a84e493aff73.
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

- `TASK-013` **Note zu Task, Story oder Epic befördern (Backend)**
  - Uid: e044a2d7-aef2-438b-b6a3-54b1023cc3a6.
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

- `STORY-026` **Postgres als zweiter Datenbank-Typ (optional)**
  - Uid: e1ac9faa-40bf-4dca-93ed-5df68efd0e34.
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

- `TASK-026` **Notes in den gemeinsamen Sync aufnehmen**
  - Uid: e463874b-8869-4aa8-9749-cc98ea572ec8.
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

- `STORY-023` **Sync zwischen Datenbank und Markdown (to_md / from_md)**
  - Uid: e5a436f2-ace2-4e24-a421-37bd776bcf83.
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

- `TASK-007` **Links-API: setzen, lösen, in beide Richtungen abfragen**
  - Uid: e80a5d41-4500-45c3-aba5-aab7c1064714.
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

- `TASK-003` **Backend-Wechsel per PUT nach Sync**
  - Uid: e9584a35-6ef8-4e55-9c32-8cd980a8794e.
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

- `STORY-033` **Einstellungsmenü: erweiterbarer Rahmen und Abschnitt „Allgemein“**
  - Uid: ee0f5b1d-301c-4925-8327-c2d87daed3ec.
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

- `STORY-005` **Parent-Lifecycle-Regeln im Domain erzwingen**
  - Uid: f1f8f151-09c7-4e06-8e18-67eb7e8e4b6b.
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

- `TASK-028` **Notes-Index: Filter nach mehreren Status**
  - Uid: f4cc6a99-a566-4226-9cef-63db224e11c2.
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

- `STORY-059` **Auto-Sync für Projekte mit Spiegel (abschaltbar)**
  - Uid: f563415f-4904-436f-82ab-83181e154ac7.
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

- `STORY-036` **Spiegel-Ordner bleibt beim Ausschalten erhalten**
  - Uid: f64517dc-4548-47c4-9fed-6189df2d8d5c.
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

- `TASK-008` **Dokumente einer Note: Notizen und Specs lesen und schreiben**
  - Uid: fa2565bf-278c-4417-8c4f-3c79adb6ac3b.
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

- `TASK-029` **Sidebar als Hülle mit tababhängigen Filterabschnitten**
  - Uid: fe6c7c7a-06a0-466f-b2db-c08266f22a18.
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

- `STORY-077` **Notes und Topics (Plugin notes)**
  - Uid: 10590159-c19b-41e2-88a6-26b3ec076cc1.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-091` **Fällig-Glocke in der Projektleiste: Wecker und fällige Notes in einer Liste, global und je Projekt**
  - Uid: 1145a9d5-6c90-48b2-9849-dd3ccf0d5ad6.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `TASK-036` **Seitengerüst: Flags sidebar und detail, leere Bereiche, usePageDetail**
  - Uid: 15f20c68-6b88-42df-943f-e59f8a5eea52.
  - Type: Task.
  - Parent: `STORY-088`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-065` **Generischer Sync-Dienst über Datenbank und Dateien**
  - Uid: 1f81c8d1-0f65-4cbc-b6d1-b6d695afa384.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-074` **Abhängigkeiten-Graph**
  - Uid: 2fd09b0c-6e9b-419f-a0df-7d1e35454830.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `TASK-038` **Slot workspace.element-detail mit ElementDetail**
  - Uid: 32938d29-5762-408f-8801-03b5ab7a9f89.
  - Type: Task.
  - Parent: `STORY-088`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-080` **Wecker (Plugin alarms)**
  - Uid: 359ff9f5-f044-4b38-93bd-d13c5fca22ab.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-081` **KI-Schnittstelle vollständig: MCP und API für den Harness**
  - Uid: 36c33cae-a5d3-4751-8166-6a52e634ea3e.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `TASK-041` **Wecker-Server: mehrere Elemente, Erlöschen, Aufräumen nach 24 h, Spiegel**
  - Uid: 377708ff-c0fe-46c2-b138-0a59bbed6b9e.
  - Type: Task.
  - Parent: `STORY-089`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-066` **Client-Grundgerüst: ezf-ui-Core ohne Login, Layout, SSE, UI-Zustand**
  - Uid: 4c0ed26f-22a2-47fb-b843-4fd28fbe4b95.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-079` **Notes im Markdown-Spiegel**
  - Uid: 4ef07551-4f17-43b0-a998-df1c4b43b5d9.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-076` **Sync in der Oberfläche: Spiegel-Einstellungen, Sync-Dialog, Status**
  - Uid: 5bd639b9-e1a4-4f6f-9fae-179d867a4b92.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-070` **Papierkorb für alle Elementtypen**
  - Uid: 60317713-7ce3-4a3d-b2ed-83716a12a45b.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `TASK-042` **Wecker-Client: Liste nach Zeit, Detail mit Erinnerungsleiste und Karten, Formular mit mehreren Elementen**
  - Uid: 644841f7-ff68-42f0-9d45-89a85882273e.
  - Type: Task.
  - Parent: `STORY-089`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-071` **Backlog anzeigen: Baum, Filter, Suche, Detail (Plugin backlog)**
  - Uid: 94d0bd73-f76f-4538-b09c-6ef8306da2db.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-061` **Server-Grundgerüst: Core mit Plugin-Host, HTTP, Ereignissen und SSE**
  - Uid: 96d662b7-90d3-44df-8682-a00e35b5fd90.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-073` **Backlog-Dokumente: Notizen und Specs**
  - Uid: 97a30881-3e01-4981-bd5b-feec02b40d91.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-067` **Gemeinsame UI-Bausteine für alle Plugins**
  - Uid: 98d859b2-3756-458f-8fdf-50b07c37572d.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-078` **Notes-Auslöser, Änderungshinweise, Befördern und Zurückstufen**
  - Uid: a4bb2496-ca9c-46bf-af39-c0a247644494.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-063` **Infrastruktur Datenbank: Migrationen je Plugin, Transaktionen, Backups**
  - Uid: aae84a1a-1da0-4af4-b808-22d37fee89be.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-088` **Wiederverwendbares Seitengerüst mit Sidebar und Detailspalte; Wecker zeigt sein Ziel**
  - Uid: b65219ae-c972-4a08-a26b-9574b8d0dd41.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-068` **Projekte, Suche und Element-Register (Plugin workspace)**
  - Uid: b921c649-42fa-4bfd-b11b-904881297231.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-082` **Datenübernahme aus dem alten Viewer**
  - Uid: b94a9306-7f06-4126-9a9b-668fc60f8a44.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `TASK-037` **Backlog, Notes, Graph und Papierkorb auf das Seitengerüst umstellen**
  - Uid: cef9ec92-6c32-4692-80ac-07591fda8f34.
  - Type: Task.
  - Parent: `STORY-088`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `TASK-039` **Wecker: Zeile klickbar, Ziel in der Detailspalte, Icon-Aktionen**
  - Uid: d5810abe-8c93-4fd4-8dbb-82b51202b2a5.
  - Type: Task.
  - Parent: `STORY-088`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-075` **Backlog im Markdown-Spiegel**
  - Uid: d5ed7b91-c359-4820-b1aa-7406e85a2e21.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-090` **Projektleiste schlanker: Bearbeiten oben, Sync-Symbole als Aktion bzw. beim Hovern**
  - Uid: e2855cf3-e6e6-44dd-8aa3-2af63212036f.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-062` **MCP-Host: Operationen als MCP-Tools für LLMs**
  - Uid: e4e63c0a-4210-42be-81c9-d3851026e148.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-087` **Browser-Logs ins viewer.log schreiben**
  - Uid: e86b8042-b480-4a30-b7f8-9b3c562d14cc.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `TASK-040` **Grundlagen: kurzlebige Spiegel-Einträge und Zustand „offen“ im Register**
  - Uid: e9d19c3e-68bb-43e9-bb48-693e780fc796.
  - Type: Task.
  - Parent: `STORY-089`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-064` **Infrastruktur Dateien: atomares Schreiben, Konflikte, Merge-Marker**
  - Uid: ee9eb2da-3413-44b5-a2c9-370b833bdf54.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-072` **Backlog bearbeiten: Felder, Formular, Anlegen, Typwechsel, Drag & Drop**
  - Uid: f14e59f7-2cec-44a6-90b4-73c45131ed6b.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-083` **Betrieb: Container, Start-Skript, Logs und Backups des Neubaus**
  - Uid: f4ce031d-079d-4d7f-8a5a-460393c5f36c.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-089` **Wecker als Erinnerung: mehrere Elemente, Erlöschen und Aufräumen nach 24 h**
  - Uid: f6066bb8-fe33-447b-859f-8ed7455742e9.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-069` **Verknüpfungen zwischen Elementen**
  - Uid: f748deeb-1b0d-4706-a578-d85ccbb4c4ad.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber bestätigt (2026-10-19).

- `STORY-060` **Noch zu klären: offene Fragen zum Neubau**
  - Uid: e82954be-70bf-4ad6-9b73-cca74503771c.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Confirmed by the project owner on 2026-10-19.

- `STORY-084` **Umstieg: der Neubau ersetzt den alten Viewer**
  - Uid: 1d71c607-6a99-4e28-ab92-cfad65a29d99.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Projektinhaber als umgesetzt bestätigt (2026-10-19).

- `STORY-085` **Serienwecker: Wiederholung am Wecker**
  - Uid: 409b1dce-0f22-4222-91b9-7fb867234356.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-10-17.
  - Area: Backend-API.
  - Priority: Prospective.
  - Dependencies: `STORY-080`.
  - Goal: Ein Wecker kann sich wiederholen (täglich, wöchentlich, monatlich,
    jährlich); nach langer Pause erscheint er einmal, mit der Zahl der
    verpassten Termine.
  - Completion criteria: 1. Der Wecker hat ein Feld Wiederholung (keine,
    täglich, wöchentlich, monatlich, jährlich) und einen Serienstart in
    Datenbank (Migration v3), API, MCP, Formular und Markdown-Spiegel;
    Dateien ohne die Felder bleiben gültig. 2. Beim Fälligwerden bleibt der
    Wecker Due; beim Erledigen rückt er auf den ersten Termin der Serie nach
    jetzt, gerechnet vom Serienstart, mit Kürzung am Monatsende; ein
    Serienwecker wird nie Done. 3. Serientermine werden in der Zeitzone des
    Rechners gerechnet, auf dem das Backend läuft: der Container bekommt TZ
    und Zeitzonendaten, 11 Uhr bleibt 11 Uhr über die Sommerzeit-Umstellung.
    4. Verpasste Termine erscheinen als ein Wecker mit Zähler (abgeleitet,
    nicht gespeichert; Anzeige, wenn optisch gut umsetzbar). 5. Tests für
    Regeln (Monatsende, Schaltjahr, Sommerzeit, lange Pause), Migration,
    Spiegel, API/MCP und Oberfläche sind grün.
  - Summary: Folge zu Frage 5 in STORY-060: Serien kommen nach dem
    Live-Gang. Wecker hängen schon an jedem Element, die Wiederholung ist
    nur ein Feld am Wecker.
  - Resolution: Umgesetzt und vom Projektinhaber bestätigt am 2026-10-19
    (Release v0.8.12).

- `TASK-043` **Notes zerlegt speichern: Tabellen, Migration, bisherige Endpunkte und Spiegel**
  - Uid: 1069e00b-b5e9-4498-9bc0-3e2159d1a7d8.
  - Type: Task.
  - Parent: `STORY-093`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-20.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Notes der Items liegen zerlegt in Kopf, Vorspann und
    Protokolleinträgen in eigenen Tabellen. Die bisherigen Endpunkte und der
    Spiegel arbeiten unverändert auf der zusammengesetzten Datei; die
    Titelzeile wird aus dem Item erzeugt.
  - Completion criteria: 1. Zerlegen und Zusammensetzen sind reine
    Funktionen in domain mit Unit-Tests; Notes ohne Kopf ergeben bis auf die
    Titelzeile denselben Text. 2. Migration v3 legt backlog_notes und
    backlog_notes_entries an und überführt alle Notes ohne Textverlust
    (Rückfall in den Vorspann). 3. get_document, put_document,
    list_documents und append_note arbeiten über die neuen Tabellen;
    bestehende Tests laufen unverändert. 4. Der Spiegel setzt zusammen und
    zerlegt, übernimmt den Stempel aus der Datei und leert den Kopf ohne ##
    Stand; Golden Files dazu. 5. Probelauf der Migration auf einer Kopie der
    echten Datenbank ohne Verlust. 6. Techdocs nachgezogen.
  - Summary: Die Notes werden intern in Kopf und Einträge zerlegt
    gespeichert; nach außen bleibt alles wie bisher.
  - Resolution: Vom Owner bestätigt (2026-10-22). Notes liegen zerlegt in
    backlog_notes und backlog_notes_entries; in Betrieb seit v0.8.14,
    Kopf-Überschriften seit v0.9.0 englisch.

- `TASK-044` **Kopf-Endpunkte, Zustand und Hinweise für Item-Notes**
  - Uid: 91ad95f5-8d8c-4392-8715-fa6aabf8a30c.
  - Type: Task.
  - Parent: `STORY-093`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-20.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-043`.
  - Goal: Der Harness kann den Kopf der Notes ohne Protokoll lesen, ersetzen
    und bestätigen und sieht, ob er aktuell ist.
  - Completion criteria: 1. Prüfsumme nach format.md des Harness mit
    gemeinsamen Testvektoren. 2. Operationen get_notes_state,
    put_notes_state, confirm_notes_state, list_notes_entries über HTTP und
    MCP; append_note nimmt optional state und state_version. 3. show und
    index melden notes_state; schreibende Antworten enthalten hints
    (notes_state_stale, notes_state_long, notes_history_rewritten). 4.
    Vertragstests und Systemtest; interfaces.md nachgezogen.
  - Summary: Neue Schnittstellen, um den Kopf der Notes zu lesen, zu
    ersetzen und zu bestätigen, und Meldungen, wenn er veraltet ist.
  - Resolution: Vom Owner bestätigt (2026-10-22). Kopf-Endpunkte, Zustand
    und Hinweise in Betrieb; Marker und Meldungstexte seit v0.9.0 englisch,
    Protokollvergleich ignoriert Zeilenenden und Leerzeilen am Ende.

- `STORY-093` **Item-Notes mit Kopf und Protokoll: getrennt gespeichert, Stempel und Zustand**
  - Uid: 70cb741a-f5be-4430-951f-080f2fa6aa63.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-10-20.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Notes eines Backlog-Items bestehen aus einem Kopf mit dem
    geltenden Stand und einem Protokoll mit datierten Einträgen. Beide
    werden in eigenen Tabellen gespeichert und lassen sich unabhängig lesen
    und bearbeiten. Ein Stempel mit der Prüfsumme des Protokolls zeigt, ob
    der Kopf noch zum Protokoll passt. So kann der Harness (STORY-051 im
    Claude_Harness) den Kopf ohne das Protokoll laden und nach jeder
    Änderung prüfen lassen.
  - Completion criteria: 1. Kopf (1:1 zum Item, mit Inhalt, Stempel und
    eigener Revision) und Protokolleinträge (1:n, mit Datum, Thema,
    unverändertem Markdown-Text und Reihenfolge) liegen in eigenen Tabellen;
    die Migration zerlegt bestehende Notes ohne Textverlust, ein vorhandener
    Abschnitt `## Stand` wird zum Kopf. 2. Die Prüfsumme wird nach der
    gemeinsamen Definition in `format.md` des Harness berechnet; ein Test
    mit gemeinsamen Beispielen zeigt dasselbe Ergebnis wie `backlog.py`. 3.
    Es gibt Endpunkte (API und MCP) zum Lesen des Kopfs ohne Protokoll, zum
    Ersetzen und zum Bestätigen des Kopfs (beide setzen den Stempel); `POST
    …/notes` nimmt optional einen neuen Kopf mit; `GET/PUT` auf
    `<ID>_notes.md` arbeiten weiter auf der zusammengesetzten Datei. 4.
    `show` und `index` melden den Zustand des Kopfs (`current`, `stale`,
    `missing`); schreibende Antworten auf Notes weisen auf einen veralteten
    Kopf hin. 5. Der Spiegel setzt die Datei aus Titelzeile (immer aus dem
    aktuellen Item), Kopf, Stempelzeile und Protokoll zusammen und zerlegt
    sie beim Einlesen wieder, den Stempel aus der Datei eingeschlossen. 6.
    Die Oberfläche zeigt den Kopf oben, markiert einen veralteten Kopf und
    lässt das Protokoll einklappen. 7. Vertragstests decken Endpunkte,
    Prüfsumme, Migration und Spiegel in beide Richtungen ab; die technische
    Dokumentation ist nachgezogen.
  - Summary: Die Notizen zu einem Item bekommen oben einen Kopf mit dem
    aktuellen Stand und darunter das Protokoll. Beide werden getrennt
    gespeichert, und der Viewer zeigt an, wenn der Kopf nach neuen Einträgen
    nicht mehr geprüft wurde.
  - Resolution: Vom Owner bestätigt (2026-10-22). Kopf und Protokoll sind
    getrennt gespeichert (TASK-043), Endpunkte, Prüfsumme, Zustand und
    Hinweise sind in Betrieb (TASK-044, Marker und Texte seit v0.9.0
    englisch), die Oberfläche zeigt Kopf und Protokoll (TASK-045, v0.9.3).
    Kopf ersetzen und bestätigen in der Oberfläche bleibt dem Harness
    überlassen.

- `TASK-045` **Kopf und Protokoll der Item-Notes in der Oberfläche**
  - Uid: 7e806f03-76ea-4c41-83e8-6e6d7f09acd6.
  - Type: Task.
  - Parent: `STORY-093`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-10-20.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-044`.
  - Goal: In der Detailansicht eines Items stehen bei den Notes oben der
    Kopf und darunter das einklappbare Protokoll; ein veralteter oder
    fehlender Kopf ist markiert.
  - Completion criteria: 1. Kopf oben, Protokoll standardmäßig eingeklappt.
    2. Markierung bei stale oder missing als Symbol mit Tooltip. 3. Daten
    über die RTK-Query-API, Neuladen nach backlog.document.changed, Typen
    aus OpenAPI erzeugt. 4. Client-Tests mit Test-IDs.
  - Summary: Die Oberfläche zeigt den aktuellen Stand der Notes oben und
    markiert, wenn er nicht mehr geprüft ist.
  - Resolution: Vom Owner bestätigt (2026-10-22), in Betrieb seit v0.9.3.
    Kopf oben in der Detailansicht, Protokoll eingeklappt, Notizsymbol mit
    Hovertext erst beim Darüberfahren in der Liste; Schlüssel des Kopfs
    übersetzt und abgesetzt.

- `STORY-094` **Notiz- und Spec-Dokumente löschen: Lösch-Befehl in API und MCP**
  - Uid: 564c047d-2845-4699-a295-e8b7f1bf680d.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-10-20.
  - Area: Backend-API.
  - Priority: Urgent.
  - Dependencies: None.
  - Goal: Für Notiz- und Spec-Dokumente eines Items gibt es bisher keinen
    Lösch-Befehl; nur Ersetzen mit put-doc ist möglich. Man muss ein
    Dokument deshalb bis auf die Überschrift leeren und kann die Kurzfassung
    (Summary) nicht entfernen. Es soll ein Lösch-Befehl für Notiz- und
    Spec-Dokumente (inkl. Themen-Specs) über API, MCP und Harness-Helfer
    geben, der auch die zugehörige Kurzfassung entfernt, wenn kein Dokument
    mehr übrig ist.
  - Completion criteria: Ein Notiz- oder Spec-Dokument lässt sich über API
    und MCP löschen; die Kurzfassung des Items wird mit dem letzten
    Notizdokument entfernt; Spiegel und
    Papierkorb-/Wiederherstellungsverhalten sind geklärt; Tests und Doku
    (API-Beschreibung, Harness-Skill api.md) sind angepasst.
  - Summary: Dringend: Notiz- und Spec-Dokumente können bisher nicht
    gelöscht, nur geleert werden. Ein Lösch-Befehl fehlt.
  - Resolution: Vom Owner bestätigt (2026-10-23): Lösch-Befehl für Notiz-
    und Spec-Dokumente in API und MCP umgesetzt.

- `TASK-046` **Server: Konflikte um Herkunft, Umbenennungspartner und Empfehlung ergänzen**
  - Uid: cf20df9d-07c9-45ef-95a2-3e3d6b46b4ef.
  - Type: Task.
  - Parent: `STORY-095`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Owner am 2026-11-04 bestätigt; Umsetzung gegen Code und
    Tests geprüft (Server- und Client-Tests grün, tsc sauber).

- `TASK-047` **Sync-Dialog: Konflikte erklärt darstellen (Klartext, Empfehlung, Diff)**
  - Uid: e4a3ddbf-f7b3-4500-aa7c-82c16f59d924.
  - Type: Task.
  - Parent: `STORY-095`.
  - Required for parent: Yes.
  - Status: Completed.
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
  - Resolution: Vom Owner am 2026-11-04 bestätigt; Umsetzung gegen Code und
    Tests geprüft (Server- und Client-Tests grün, tsc sauber).

- `STORY-095` **Sync-Konflikte erklären: Herkunft, Umbenennung, Empfehlung**
  - Uid: 02d22676-5584-4eff-a2cc-7f3fe65e9d5c.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
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
  - Resolution: Vom Owner am 2026-11-04 bestätigt; Umsetzung gegen Code und
    Tests geprüft (Server- und Client-Tests grün, tsc sauber).

- `TASK-049` **Einstellungen: Projektliste kompakt mit Icons und Tooltips**
  - Uid: c10a31b8-7eef-4f6c-845e-9405c4dbfb03.
  - Type: Task.
  - Parent: `STORY-096`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-11-03.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-048`.
  - Goal: Die Projekte in der Gruppe „Projekte“ stehen als kompakte Zeilen:
    Name, Status-Chip, Modus (Aus/Manuell/Auto) und Icon-Aktionen mit Tooltip
    (Bearbeiten, Sync). Pfad, Richtung und letzter Sync stehen in einem
    aufklappbaren Detail, standardmäßig eingeklappt.
  - Completion criteria: 1. Bei gleicher Fensterhöhe sind deutlich mehr
    Projekte sichtbar als bisher. 2. Alle bisherigen Aktionen (Modus ändern,
    bearbeiten, Sync, Spiegel einrichten) bleiben erreichbar. 3. Texte in
    de/en, Tests für Zeile und Detail.
  - Resolution: Vom Owner am 2026-11-04 bestätigt; Umsetzung gegen Code und
    Tests geprüft (Server- und Client-Tests grün, tsc sauber).

- `TASK-048` **Einstellungen: Gruppen und Seitennavigation**
  - Uid: cf36a44d-d391-4c4a-8c88-f1a5e7a6e97a.
  - Type: Task.
  - Parent: `STORY-096`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-11-03.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Slot `core.settings-sections` bekommt ein Gruppenattribut; die
    Einstellungsseite zeigt links eine Navigation mit Unterrouten und rechts
    die Abschnitte der gewählten Gruppe. Die bestehenden Abschnitte werden den
    Gruppen „Projekte“ und „System“ zugeordnet (Notes und Wecker nach System).
  - Completion criteria: 1. Jede Gruppe ist über eine eigene Unterroute
    erreichbar und direkt aufrufbar. 2. Abschnitte ohne Gruppe erscheinen unter
    „System“ und gehen nicht verloren; die Slot-Prüfung kennt das Attribut.
    3. Texte in de/en, Test-IDs nach Client-Regeln, Tests für Navigation und
    Zuordnung.
  - Resolution: Vom Owner am 2026-11-04 bestätigt; Umsetzung gegen Code und
    Tests geprüft (Server- und Client-Tests grün, tsc sauber).

- `TASK-051` **Einstellungen: Auto-Sync-Intervall in der Gruppe „System“**
  - Uid: 6322b1dd-c9b2-43fe-8f63-987f5158981d.
  - Type: Task.
  - Parent: `STORY-096`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-11-03.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-048`, `TASK-050`.
  - Goal: Ein Abschnitt „Auto-Sync“ in der Gruppe „System“ zeigt das Intervall
    und lässt es ändern; ist es per Umgebung gesetzt, ist das Feld gesperrt und
    nennt den Grund.
  - Completion criteria: 1. Ändern und Speichern wirkt ohne Neustart.
    2. Gesperrt mit Hinweis, wenn der Server meldet, dass die Umgebung den Wert
    setzt. 3. Texte in de/en, Test-IDs nach Client-Regeln, Tests.
  - Resolution: Vom Owner am 2026-11-04 bestätigt; Umsetzung gegen Code und
    Tests geprüft (Server- und Client-Tests grün, tsc sauber).

- `TASK-050` **Server: Auto-Sync-Intervall zur Laufzeit ändern**
  - Uid: dfd71aab-74fc-4913-892b-3dc2401f22ac.
  - Type: Task.
  - Parent: `STORY-096`.
  - Required for parent: Yes.
  - Status: Completed.
  - Created: 2026-11-03.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Das Intervall des Auto-Syncs (`auto_sync_interval_seconds`) kann über
    die API gelesen und geschrieben werden, nach dem Vorbild von
    `PUT /api/v2/notes/settings`; der Timer übernimmt den neuen Wert ohne
    Neustart. Die Umgebungsvariable `AUTO_SYNC_INTERVAL` gewinnt weiter.
  - Completion criteria: 1. Lesen liefert Wert und ob er aus der Umgebung
    stammt; Schreiben ist dann mit einem Fehler abgelehnt. 2. Der Wert wird in
    die Konfiguration geschrieben (Bereich geprüft, `0` = Timer aus) und gilt
    sofort. 3. Tests für Lesen, Schreiben, Sperre durch die Umgebung und
    Neustart des Timers; Techdocs (Konfiguration, Schnittstellen) sind
    nachgezogen.
  - Resolution: Vom Owner am 2026-11-04 bestätigt; Umsetzung gegen Code und
    Tests geprüft (Server- und Client-Tests grün, tsc sauber).

- `STORY-096` **Einstellungen übersichtlich gliedern: Gruppen, kompakte Projektliste, Sync-Intervall**
  - Uid: 7d5433dc-85d6-41e5-a77a-07bab0ff9927.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-11-03.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Die Seite „Einstellungen“ ist keine lange Kartenliste mehr, sondern
    in Gruppen mit Seitennavigation gegliedert: „Projekte“ (alles
    Projektspezifische, platzsparend dargestellt) und „System“ (Notes, Wecker,
    Auto-Sync). Das Auto-Sync-Intervall ist dort ohne Neustart einstellbar.
    Die Sprache bleibt in der Kopfzeile.
  - Completion criteria: 1. Die Einstellungen haben links eine Navigation mit
    Unterrouten; rechts steht nur die gewählte Gruppe. 2. „Projekte“ zeigt
    eine Zeile je Projekt mit Name, Status, Modus und Icon-Aktionen mit
    Tooltip; Pfad und letzter Sync stehen im eingeklappten Detail. 3. „System“
    enthält Notes, Wecker und Auto-Sync; neue Abschnitte ordnen sich über ein
    Gruppenattribut des Slots ein. 4. Das Auto-Sync-Intervall lässt sich in
    der Oberfläche ändern und gilt ohne Neustart; ist `AUTO_SYNC_INTERVAL`
    gesetzt, gewinnt die Umgebung und das Feld ist gesperrt. 5. Texte in
    de/en, Tests und Techdocs sind nachgezogen.
  - Summary: Die Einstellungen werden aufgeräumt: Gruppen „Projekte“ und
    „System“ mit Seitennavigation, eine kompakte Projektliste und ein
    Auto-Sync-Intervall, das man in der Oberfläche einstellt.
  - Resolution: Vom Owner am 2026-11-04 bestätigt; Umsetzung gegen Code und
    Tests geprüft (Server- und Client-Tests grün, tsc sauber).

- `STORY-097` **Sync: Platzhalter auch im Fließtext durch das vergebene Label ersetzen**
  - Uid: 33c72624-ae75-4b35-8e23-fa2c67eb161a.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-11-04.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Wenn der Sync einem neuen Eintrag (Platzhalter NEW-<kurzname>, bei
    Notizen new-<kurzname>) sein Label gibt, ersetzt er den Platzhalter
    nicht nur in den Verweisfeldern, sondern auch im Fließtext aller
    Einträge (Ziel, Kriterien, Zusammenfassung, Notizen, Specs, Notiztexte)
    in Datenbank und Dateien. Bisher mussten solche Stellen von Hand
    angepasst werden.
  - Completion criteria: 1. Nach dem Sync steht in Textfeldern und
    Dokumenten das vergebene Label statt des Platzhalters, in Datenbank und
    Dateien.
    2. Nur ganze IDs werden ersetzt; ähnliche Namen (NEW-route-2) und echte
    Labels bleiben unverändert.
    3. Der nächste Sync meldet dafür keinen Konflikt.
    4. Tests (Unit und Sync-Ablauf) und Techdocs sind ergänzt.
  - Resolution: Umgesetzt und vom Owner abgenommen: Der Sync ersetzt
    Platzhalter beim Vergeben des Labels auch im Fließtext (Felder, Notizen,
    Specs) in Datenbank und Dateien (v0.9.6).

- `STORY-098` **Note heißt Memo: Umbenennung des Eintragstyps, damit „Note“ nur noch die Item-Notiz meint**
  - Uid: af351412-f693-47b6-a5ef-cf3a0825b4bc.
  - Type: Story.
  - Parent: `EPIC-007`.
  - Required for parent: No.
  - Status: Completed.
  - Created: 2026-11-12.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Der Eintragstyp Note heißt in allen Schichten Memo (Plugin-ID
    memos, Tabellen memos_*, Routen /api/memos/..., Label MEMO-xxx,
    Mirror-Ordner memos/, Client, Tests, Doku), und Notice heißt Hint (UI
    deutsch: Hinweis). Das Wort Note kommt danach nur noch für die Notiz zu
    einem Backlog-Item vor. Bestandsdaten (Datenbank, Mirror-Dateien,
    Verweise in Texten) werden mitumgestellt.
  - Completion criteria: 1. Eine Migration benennt Plugin-Besitzer,
    Tabellen, Elementtyp, Label-Präfix, Zähler, Labels und Label-Historie
    von notes/NOTE auf memos/MEMO um und ist mit einer Datenbank im alten
    Stand getestet.
    2. Alle Routen liegen unter /api/memos/...; unter /api/notes/ gibt es
    keine Memo-Routen mehr.
    3. Der Markdown-Spiegel schreibt und liest MEMO-xxx.md und
    MEMO-xxx_notes.md im Ordner memos/; ein Bestandsspiegel mit NOTE-Dateien
    wird beim ersten Sync umgestellt.
    4. Client, Texte (de, en) und Test-IDs sprechen von Memo und Hint;
    „Note“ taucht nur in den Item-Notizen auf.
    5. Verweise NOTE-xxx in Backlog-Einträgen, Memo-Texten und Doku (ohne
    alte Tagesberichte) sind auf MEMO-xxx umgestellt.
    6. Alle Tests (Server, Client, Architektur) laufen; Techdocs,
    Architektur-Docs und Interface-Doku sind angepasst.
    7. Eine Zuordnung alt → neu (Routen, Labels, Ordner, Typnamen) liegt für
    die Umstellung des Harness bereit.
  - Summary: Der Eintrag mit Wiedervorlage (bisher Note, NOTE-001) und die
    Notiz zu einem Backlog-Item (<ID>_notes.md) tragen denselben Namen und
    werden von der KI verwechselt. Der Eintrag heißt künftig Memo
    (MEMO-001), der Hinweis (Notice) künftig Hint; „Note“ bleibt allein die
    Item-Notiz.
  - Resolution: Confirmed by the project owner on 2026-11-12.

- `TASK-064` **Mindmap: Machbarkeit prüfen und Ideen sammeln**
  - Uid: 35c27972-ff20-497b-bcb3-4f9d60903207.
  - Type: Task.
  - Parent: None.
  - Status: Completed.
  - Created: 2026-11-13.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Klären, ob und wie eine Mindmap als eigenes Datenmodell in den
    Viewer passt: ein Gerüst aus Themenknoten zum Brainstormen, in das
    Backlog-Items verlinkt werden können, sodass sie zugleich eine
    übersichtliche Darstellung des Backlogs ist. Ideen und Entscheidungen
    werden in den Notizen gesammelt.
  - Completion criteria: 1. Die Notizen halten die besprochenen Ideen, die
    Entscheidungen des Owners und die offenen Fragen fest.
    2. Ein Konzept (Spec) beschreibt Datenmodell, Zuordnung von Items,
    Darstellung und die Rolle der KI und nennt, welche vorhandenen
    Bausteine genutzt werden.
    3. Der Owner hat entschieden, ob daraus ein Epic mit Stories wird oder
    die Idee verworfen wird.
  - Summary: Idee einer Mindmap: Themen sammeln und ordnen, unabhängig vom
    Backlog, und Backlog-Einträge an die Themen hängen, um einen
    schnellen Überblick zu bekommen, was es gibt und was kommt. Erst
    einmal nur Machbarkeit und Ideensammlung.
  - Resolution: Vom Owner am 2026-11-13 bestätigt, nachdem die Entscheidungen
    in Epic EPIC-008 und seine Stories übertragen waren.
