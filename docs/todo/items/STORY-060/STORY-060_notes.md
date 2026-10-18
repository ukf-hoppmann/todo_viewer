# STORY-060 — Noch zu klären: offene Fragen zum Neubau

## 2026-10-16 — Antworten des Projektinhabers

### Decided

- Frage 9 (2026-10-16): Annahme bestätigt. Bereiche bekommen eine eigene Tabelle backlog_areas je Projekt; neue Bereiche legt man im Feld an; ein unbekannter Bereich aus den Dateien wird beim Sync angelegt.
- Alle übrigen Fragen: Die Annahmen gelten für die Umsetzung; der Projektinhaber entscheidet sie spätestens vor dem Umstieg (STORY-084).

## 2026-10-16 — Fragen aus der Umsetzung (Cloud-Sitzung)

### Open

- Frage 13 (betrifft STORY-061): Die Spec nennt „Plugin-Definition und Operation als Datentypen“ in `core/domain`. `PluginDefinition.build` braucht aber einen Kontext mit Ports (`Clock`, `EventBus`, `Scheduler`), und Ports gehören nach Architektur-Scope `server` §2 nach `application/ports.py`; `domain` darf `application` nicht importieren. Annahme: `Operation`, `HttpBinding`, `Subscription`, `Migration` und die reine Prüfung (gegen ein Protokoll `PluginShape`) liegen in `core/domain`, `PluginDefinition` und `PluginContext` in `core/application`. Ein Operations-Handler hat die Form `handler(services, input)`.

- Frage 14 (betrifft STORY-063): „Vor jeder Migration ein Backup“ (Architektur §2): ein Backup je Start oder je einzelner Migration? Annahme: ein Backup je Start, bevor die erste ausstehende Migration läuft; nicht bei einer Datenbank ohne Tabellen. Die letzten 10 je Grund bleiben.
- Frage 15 (betrifft STORY-063): Muss `PUT /api/core/ui-state/{owner}` ein Versions-Token nehmen (Architektur §3: schreibende Operationen nehmen eins)? Annahme: nein, der UI-Zustand ist ein Dokument je Besitzer ohne Konfliktprüfung (letzter Schreiber gewinnt); das UI hält je Besitzer genau eine Sitzung.
- Frage 16 (betrifft STORY-064): Die Spec nennt `inspect(folder)`; das Prüfen auf Merge-Marker braucht aber die Dateimuster des Spiegels. Annahme: `inspect(folder, patterns=("**/*.md",))`, und `read` und `write` prüfen mit denselben Mustern bzw. den betroffenen Dateien.
- Frage 17 (betrifft STORY-065): Die Spec nennt `execute(project, token, decisions, delete_missing)` und §7.3 „Löschungen nur mit eigener Entscheidung“. Annahme: Eine auf einer Seite fehlende Datei bzw. ein fehlender Eintrag ist ein Konflikt; wer die Löschung ausführen will, wählt je Konflikt die Seite, die sie bedeutet, und bestätigt mit `delete_missing=true`. Ohne das Flag wird so eine Entscheidung abgewiesen (`deletion_not_confirmed`).
- Frage 18 (betrifft STORY-065, STORY-068): `SyncParticipant.assign_labels` bekommt zusätzlich die offene Transaktion, damit die Label-Zähler zusammen mit den Einträgen festgeschrieben werden; der Teilnehmer nutzt sie für den Zugriff auf `workspace`. Außerdem `resolve_labels(project, labels)`, damit alte Labels (Label-Historie) vor dem Vergleich auf das aktuelle Label abgebildet werden. Annahme: beides ist in Ordnung, Plugin-Specs nehmen es auf.
- Frage 19 (betrifft STORY-066): Die Spec nennt die Slots `layout.header-actions` und `layout.sidebar-sections`; Architekturregel (Scope client §3) und Plugin-Vertrag verlangen `<owner-id>.<name>` mit der Plugin-ID als Besitzer. Annahme: Die Slots heißen `layout-header-sidebar.header-actions` und `layout-header-sidebar.sidebar-sections`; Plugins, die hineinbeitragen, tragen `layout-header-sidebar` in `requires` ein. Der Rahmen (Kopfzeile, Seitenleiste) kommt über ein neues Feld `frame` der Plugin-Definition vom Layout-Plugin.
- Frage 20 (betrifft STORY-066, STORY-083): Der Client schreibt Logs nur in die Konsole; es gibt (anders als in `ezf-ui`) keine Log-Schnittstelle am Server. Annahme: Das reicht für den Neubau; eine Log-Schnittstelle (Einträge des Browsers ins `viewer.log`) kann später als eigene Operation des Core folgen.
- Frage 21 (betrifft STORY-067): Die Spec nennt `ConfirmDialog` und `ChoiceDialog` „über die Modals des Core“; `shared` darf aber nur Pakete von Dritten importieren. Annahme: Beide sind schlichte MUI-Dialoge in `shared` mit Texten als Eigenschaften; die Dialoge des Core (`useModals`) bleiben für Fehler und einfache Bestätigungen, Plugins wählen je nach Bedarf.
- Frage 22 (betrifft STORY-068): Das feste Datenmodell von `workspace_projects` hat weder `revision` noch `deleted_at`. Annahme: Beide kommen dazu (Versions-Token für schreibende Operationen; ein mit Bestätigung entferntes Projekt wird samt Inhalt in den Papierkorb gelegt, ein leeres wirklich gelöscht). Außerdem gilt: Anlegen, Ändern, Ordnen und Entfernen von Projekten sind wegen der Spiegel- und Sync-Einstellungen keine MCP-Tools (Architektur §3), das Lesen und das Auflösen von Labels sind es.
- Frage 23 (betrifft STORY-068): Die Spec nennt Einträge von `workspace.create-types` als `{kind, title, icon, form}`; der Plugin-Vertrag kennt für Widgets nur `name`, `component`, `order`, `when`. Annahme: `name` ist der Typ, `component` die Maske; der Titel ist der Text `create.<name>` im Namensraum des beitragenden Plugins, ein Symbol entfällt. Die Maske schließt den Dialog mit `useCreateDialog().close()`. Der Plugin-Vertrag wird dafür nicht erweitert.
- Frage 24 (betrifft STORY-069): Die Spec nennt einen Slot `workspace.detail-sections` für den Abschnitt „Verknüpfungen“. Ein Widget im Slot bekommt keine Eigenschaften (Plugin-Vertrag), der Abschnitt braucht aber das Element, zu dem er gehört. Annahme: `workspace` exportiert die Komponente `LinksSection` (Eigenschaft `elementUid`) und die Hooks; die Plugins mit Detailpanel bauen sie dort ein. Ein Slot entfällt. Dazu kommt eine Operation `search_elements(query)`, mit der der Auswahldialog Ziele über alle Projekte findet (die Spec nennt sie nicht, der `EntityPicker` braucht sie).
- Frage 25 (betrifft STORY-069 und alle Fach-Plugins): Das Register kennt keinen Titel, die Suche und die Anzeige von Verknüpfungen brauchen aber „Label — Titel“. Annahme: `workspace_elements` bekommt eine Spalte `title` (Migration v2); das Fach-Plugin gibt den Titel bei `register(…, title)` mit und ruft bei jeder Titeländerung `set_title`. Der Titel steht damit doppelt (im Register als Anzeigetext, im Fach-Plugin als Wahrheit).
- Frage 26 (betrifft STORY-070): Die Spec nennt `restore_element(uid)` und `purge_element(uid)`. Die Vorfahren-Regel bei Sammelaktionen braucht den Elementbaum, den nur der Server kennt (über die `ChildrenProvider`). Annahme: Die Operationen heißen `restore_elements` und `purge_elements` und nehmen eine Liste von `uid`s (eine Liste mit einem Element ist der Einzelfall); der Server übergeht gewählte Nachkommen gewählter Elemente. Die Ports melden die Plugins beim Bau über `context.required["workspace"].trash.register(kind, …)` an.
- Frage 27 (betrifft STORY-071): Die Spec nennt als Standard der Filter „wie heute: offene Status“, der alte Viewer blendet aber nichts aus. Annahme: Standard ist, dass `Open`, `In progress` und `Awaiting confirmation` sichtbar sind und `Completed` und `Rejected` ausgeblendet; die Wahl wird im UI-Zustand gemerkt. Außerdem: Es gibt nur noch die Baumansicht, deshalb ist `backlog/main` eine Seite (Baum und Detailpanel) und keine Hauptroute mit Unterseite „Baum“.
- Frage 28 (betrifft STORY-075): `unknown_reference` verlangt eine Datei- und Zeilenangabe, kann aber nur mit der Datenbank (frühere Labels) entschieden werden, nicht vom Codec beim Lesen. Annahme: `MirrorEntry` bekommt ein Feld `source` (Datei, Zeile), das nicht zum Vergleich und nicht zum Hash gehört; der Teilnehmer wirft den Fehler beim Schreiben der Datenbank (vor jeder Änderung, in der Transaktion) mit dieser Angabe. Folge: Die Vorschau zeigt den Fehler erst beim Ausführen.
- Frage 29 (betrifft STORY-077): Die Notizen-Einträge (`NotesEntry`, Anhängen) braucht auch `notes`, Plugins dürfen einander aber nicht importieren. Annahme: Das Plugin `notes` hat eine eigene kleine Kopie des Eintragsbaus; ein gemeinsamer Baustein im Kern ist ein späteres Aufräumen, wenn ein drittes Plugin ihn braucht.
- Frage 30 (betrifft STORY-077): Die Spec lässt offen, ob das allgemeine Wiederherstellen aus dem Papierkorb (STORY-070) eine Note wie früher auf „wartet“ mit neuem Prüfdatum setzt. Annahme: Das Wiederherstellen aus dem Papierkorb stellt nur den Papierkorb-Zustand her (Status und Prüfdatum bleiben); „zurück auf wartet mit neuem Prüfdatum“ gilt für die Operation `restore_note` (aus dem Archiv).
- Frage 31 (betrifft STORY-078): Die Spec beschreibt `notes_notices(uid, note_uid, source_uid, kind, created_at, decided)`. Der alte Viewer kennt Hinweise aber auch **an Items** („eine verknüpfte Note wurde verworfen oder befördert“, Entscheidung `acknowledge`), und die Entscheidung muss gespeichert werden. Annahme: Die Tabelle heißt `notes_notices(uid, side, subject_uid, source_uid, kind, created_at, decided_at, decision)`: `subject_uid` ist, wer informiert wird (Note oder Item), `side` sagt welches, `decided_at`/`decision` ersetzen `decided`. Der Hinweis „Projekt nicht erreichbar“ entfällt (eine Datenbank).
- Frage 32 (betrifft STORY-079): Verweise der Notes stehen in den Dateien mit Projektname (`Beispiel:STORY-001`), der Codec kennt den Namen aber nicht, und der Sync ersetzt Platzhalter über blanke Labels. Annahme: `MirrorConfig` bekommt das Feld `name`; ein Codec, der `for_project(name)` anbietet, wird damit gebunden und löst den eigenen Projektnamen (und `topic:`/`note:`) zu blanken Labels auf. Außerdem: Die Spec sagt, Verweise in andere Projekte seien „ungeprüft erhalten“; in der Datenbank hängen Verknüpfungen aber an `uid`s und können kein unbekanntes Ziel halten. Annahme: Ein Ziel anderer Projekte wird über Projektname und Label aufgelöst, ein unbekanntes ist `unknown_reference` (nur Wecker, STORY-080, behalten ihr Ziel als Text, falls die Spec das dort so vorsieht).
- Frage 33 (betrifft STORY-080): `alarms_alarms.target_uid` ist ein Fremdschlüssel auf Elemente, das Format erlaubt aber ein Ziel in einem anderen Projekt, das die Datenbank nicht kennt („ungeprüft erhalten“). Annahme: Die Tabelle hat zusätzlich `target_text`; ein auflösbares Ziel steht in `target_uid`, ein unauflösbares `Projekt:LABEL` nur als Text (beide leer: freier Wecker).
- Frage 34 (betrifft STORY-080): Die Spec nennt den Slot `workspace.detail-sections` für „Wecker stellen“ im Detail jedes Elements. Ein Widget bekommt keine Eigenschaften (Frage 24). Annahme: `workspace` bietet den Slot an und exportiert die Komponente `DetailSections` (Eigenschaften `uid`, `label`), die die Widgets in einem Kontext zeigt, aus dem `useDetailElement()` das Element liest; die Detailpanels von `backlog` und `notes` binden sie ein.
- Frage 35 (betrifft STORY-082): Das Abschlusskriterium 1 sagt, der Befehl lese „die alte DB und Markdown-primäre Ordner“; der Umfang (und Frage 1) sagt, er breche bei einem noch Markdown-primären Projekt ab. Annahme: Der Umfang gilt; das Projekt wird vorher im alten Viewer in seine Datenbank gespiegelt, der Befehl nennt es beim Abbruch.

## 2026-10-17 — Antworten zu Frage 1, 3, 4, 12 (Weg zum Live-Gang)

### Discussed

- Frage 4: In configs/todo.db ist item_extra_fields bei 514 Items leer; es geht kein Inhalt verloren.
- Frage 3: Der Import übernimmt die DB unverändert; offene Altitems kommen als Open mit. Ablehnen ist ein Statuswechsel danach, kein Teil des Imports.

### Decided

- Frage 1/35: Annahme bestätigt. Markdown-primäre Projekte werden vor dem Import im alten Viewer in ihre DB gespiegelt; die DB ist die Wahrheit.
- Frage 3: Import unverändert. Danach werden EPIC-005, EPIC-006 und STORY-041/048/054/055/056 im neuen Viewer über das MCP auf Rejected gesetzt, mit Verweis auf die Neubau-Storys; zugleich ein Test der MCP-Schnittstelle.
- Frage 4: entfällt (keine Zusatzfelder in der DB); der Eintrag 'Übernommene Zusatzfelder' bleibt als Vorkehrung im Importer.
- Frage 12: Annahme bestätigt. Name 'ToDo Viewer' und Adresse http://todo.localhost:5411 bleiben.

### Open

- Weitere Fragen für den Live-Gang: 7, 11, 13 bis 35.

## 2026-10-17 — Antworten zu Frage 6, 7, 11, 27

### Decided

- Frage 6: Annahme bestätigt. Fälliger Wecker: Banner in der UI, Zähler in der Kopfzeile, zusätzlich Browser-Benachrichtigung, wenn erlaubt.
- Frage 7: Annahme bestätigt. Zeit-Auslöser an Notes werden beim Import zu Weckern mit der Note als Ziel; Notes behalten Prüfdatum, Ereignis-Auslöser und Topic-Termin.
- Frage 11: Annahme bestätigt. Version beim Umstieg: 1.0.0.
- Frage 27: Annahme bestätigt. Standard-Filter im Baum: Completed und Rejected ausgeblendet; die Wahl wird im UI-Zustand gemerkt.

### Open

- Weitere Fragen: 13 bis 26, 28 bis 35 (außer 35 durch Frage 1 entschieden); 2, 5, 8, 10 noch nicht bestätigt.

## 2026-10-17 — Antworten zu Frage 2, 5, 8, 10

### Decided

- Frage 2: Annahme bestätigt. Projektlose Notes landen im eingebauten Projekt 'Allgemein'.
- Frage 5: Serienwecker kommen nach dem Live-Gang als STORY-085 (Feld Wiederholung am Wecker; nach langer Pause ein Wecker mit Zähler der verpassten Termine; Folgetermin ab Fälligkeit). Wecker hängen schon als Verweis an jedem Element, auch an Epics, Stories und Tasks.
- Frage 8: Takt (Standard 30 s) bleibt; er ist über AUTO_SYNC_INTERVAL oder auto_sync_interval_seconds in der Konfiguration einstellbar (auch 1 s). Keine Dateiüberwachung.
- Frage 10: Ziehen im Baum wie beschrieben (Parent mit Regelprüfung, Reihenfolge, Note zu Topic, Topic unter Topic), nicht zwischen Projekten. Der Umwandeln-Dialog beim Ziehen (Story auf Story als Task) kommt nach dem Live-Gang als STORY-086; bis dahin lehnt der Server ab.

### Open

- Fragen 13 bis 34 (technische Annahmen aus der Cloud-Sitzung) noch nicht bestätigt.

## 2026-10-17 — Antwort zu Frage 17

### Decided

- Frage 17: Annahme bestätigt. Ein fehlender Eintrag oder eine fehlende Datei ist ein Konflikt; eine Löschung braucht die Wahl der löschenden Seite und zusätzlich delete_missing=true, sonst deletion_not_confirmed.

### Open

- Fragen 13 bis 16, 18 bis 26 und 28 bis 34 noch nicht bestätigt.

## 2026-10-17 — Antworten zu Frage 14, 15, 22, 30

### Decided

- Frage 14: Annahme bestätigt. Ein Backup je Start vor der ersten ausstehenden Migration (nicht bei leerer DB); die letzten 10 je Grund bleiben.
- Frage 15: Annahme bestätigt. UI-Zustand ohne Konfliktprüfung, der letzte Schreiber gewinnt.
- Frage 22: Annahme bestätigt. Projekt entfernen legt es samt Inhalt in den Papierkorb (leere werden gelöscht); Projektverwaltung ist kein MCP-Tool, Lesen und Label auflösen schon.
- Frage 30: Annahme bestätigt. Wiederherstellen aus dem Papierkorb lässt Status und Prüfdatum; 'zurück auf wartet mit neuem Prüfdatum' gilt nur für restore_note aus dem Archiv.

### Open

- Fragen 13, 16, 18 bis 21, 23 bis 26, 28, 29, 31 bis 34 noch nicht bestätigt.

## 2026-10-17 — Antworten zu Frage 26, 28, 31, 32, 33

### Decided

- Frage 26: Annahme bestätigt. restore_elements und purge_elements nehmen eine Liste; gewählte Nachkommen gewählter Elemente übergeht der Server (Vorfahren-Regel).
- Frage 28: Annahme bestätigt. Ein Verweis auf ein unbekanntes Element wird erst beim Ausführen erkannt (Fehler mit Datei und Zeile, vor jeder Änderung, in der Transaktion); die Vorschau zeigt ihn nicht.
- Frage 31: Annahme bestätigt. notes_notices mit side, subject_uid, source_uid, kind, created_at, decided_at, decision; Hinweise an Notes und Items; 'Projekt nicht erreichbar' entfällt.
- Frage 32: Annahme bestätigt. MirrorConfig bekommt name; Verweise auf andere Projekte werden über Projektname und Label aufgelöst, ein unbekanntes Ziel ist unknown_reference.
- Frage 33: Annahme bestätigt. Nur Wecker halten ein unauflösbares Ziel als Text (target_text) neben target_uid.

### Open

- Fragen 13, 16, 18 bis 21, 23 bis 25, 29, 34 (Architektur) noch nicht bestätigt.

## 2026-10-17 — Architektur-Annahmen bestätigt (13, 16, 18 bis 21, 23 bis 25, 29, 34)

### Discussed

- Die Architekturregeln gelten weiter (verbindlich, import-linter, Hook); die Annahmen sind im Code umgesetzt, eine Ablehnung wäre ein Umbauauftrag.

### Decided

- Frage 13, 16, 18, 19, 21, 23, 24, 25, 29, 34: Annahmen bestätigt wie in den Fragen beschrieben.
- Frage 20: Annahme bestätigt (Client loggt vorerst nur in die Konsole); die Log-Schnittstelle zum viewer.log kommt als STORY-087 ins Backlog.

### Open

- Keine Frage mehr offen; alle 35 sind beantwortet. Abschlusskriterien 1 bis 3 sind damit erfüllt; die Story bleibt für neue Fragen aus der Umsetzung offen, bis der Inhaber sie abnimmt.

## 2026-10-18 — Prüfung vor der Abnahme

### Discussed

- Abgleich der 35 Antworten: Die fachlichen Antworten (1–12) stehen in den Specs der betroffenen Storys; die technischen (13–35) stehen als begründete Abweichung in den Notizen der umsetzenden Storys (061, 063–071, 074, 075, 077–080, 082), nicht in deren Specs. Die Specs waren Eingabe der Umsetzung und sind abgeschlossen.
- Umsetzung per Stichprobe im Code bestätigt (u. a. PluginShape in core/domain und PluginDefinition in core/application, delete_missing/deletion_not_confirmed, resolve_labels, LinksSection, search_elements, set_title, restore_elements/purge_elements, notes_notices mit subject_uid/decided_at, target_text, DetailSections, for_project, Projekt Allgemein). Frage 3: die Altitems sind Rejected. Frage 20 ist durch STORY-087 überholt (BackendSink an /api/core/client-log).
- Noch nicht umgesetzt, gehört aber zu STORY-084 (Umstieg): Version 1.0.0 (Frage 11) und Port 5411 (Frage 12); der Neubau läuft noch als todo-viewer-next auf 5412.

### Decided

- Abschlusskriterien 1 und 2 sind erfüllt (Kriterium 2 über die Notizen der betroffenen Items); Status Awaiting confirmation.

### Open

- Abnahme durch den Projektinhaber.
