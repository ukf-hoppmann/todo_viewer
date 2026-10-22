# TASK-045 — Kopf und Protokoll der Item-Notes in der Oberfläche

## Ziel

Der Stand der Notizen eines Items ist ohne Öffnen der Notiz sichtbar; das Protokoll gibt es nur in der Detailansicht.

## Verhalten

**Detailansicht** (Abschnitt „Dokumente“, nur bei Items mit Notizen):

- Oberhalb der Dateiliste steht der Kopf als formatierter Text unter der Überschrift „Stand“ (`GET …/notes/state`).
- Ist der Kopf `stale` oder `missing`, steht neben der Überschrift ein Warnsymbol; ein Tooltip nennt den Grund. Ohne Kopf steht „Noch kein Stand eingetragen.“.
- Darunter steht der Knopf „Protokoll“. Er klappt die Einträge (`GET …/notes/entries`) auf und zu, neuester zuerst, je mit Datum und Thema. Standardmäßig ist das Protokoll eingeklappt und wird erst beim Aufklappen geladen.
- Die Dateiknöpfe, der Dokument-Dialog, „Eintrag anlegen“ und „Spec anlegen“ bleiben unverändert. Der Kopf ist in der Oberfläche nur lesbar; Ersetzen und Bestätigen bleibt dem Harness.

**Liste (Baum):**

- Jedes Item mit Notizen (`notes_state` des Index nicht leer) trägt ein kleines Notizsymbol rechts neben dem Titel; ohne Notizen erscheint keines.
- Farbe: `current` grau, `missing` gedimmt (der Normalfall älterer Notizen, damit die Liste ruhig bleibt), `stale` in Warnfarbe.
- Fährt man mit der Maus darüber, zeigt ein Tooltip den Kopf (Ziel/Status, nächster Schritt, Offenes, Beschlossenes). Er wird erst beim ersten Hover geladen. Das Protokoll kommt in der Liste nicht vor.

## Umsetzung

- `getNotesState` und `listNotesEntries` in der API des Plugins `backlog` (Tag `Documents`); Neuladen nach `backlog.document.changed` wie bei den Dokumenten.
- `NotesHead` (Detailansicht) und `NotesPeek` (Liste); der gemeinsame `TreeView` bekommt `trailing` für Dauerinhalt rechts neben dem Titel.
- Texte `notes.*` in `de.json` und `en.json`; Test-IDs `backlog.notes-*`.

## Offen

- Auf Touch-Geräten gibt es kein Hovern; der Tooltip erscheint dort durch langes Drücken (MUI-Standard). Ein eigener Tipp-Auslöser ist nicht gebaut.
- Kopf ersetzen und bestätigen in der Oberfläche wäre eine eigene Aufgabe.
