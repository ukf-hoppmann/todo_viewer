# STORY-040 — Auslöser und Wiedervorlage im Viewer

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Prüfung ohne Takt
- Ereignis-Zielstatus und bereits erfüllte Ziele
- Zustände und Prüf-Datum
- mehrere Auslöser

### Decided

- Zeit wird beim Lesen bewertet, Ereignisse beim Statuswechsel; kein Hintergrund-Takt.
- Zielstatus: In progress, Awaiting confirmation, Completed, Rejected; bereits erfüllte Ziele feuern sofort und werden gekennzeichnet.
- Das Prüf-Datum gilt für alle Notes und wird bei Anlage, Textänderung, Zurückstellen und behalten neu gesetzt.
- Fällige Notes bleiben im Modal, bis sie zurückgestellt, erledigt, verworfen oder gelöscht sind.
- Mehrere Auslöser: jeder einzeln, zusätzlich Erkennung 'alle eingetroffen', Modus any/all im Modell.

### Open

- Ist `snoozed` ein eigener Zustand oder nur eine Anzeige von `waiting` (Vorschlag: wie waiting ausgewertet, Name bleibt)?
- Ereignisse, die am Viewer vorbei entstehen (Markdown extern geändert), werden erst beim nächsten Sync erkannt.

## 2026-10-08 — Umsetzung (Domain und Service)

### Discussed

- Ob 'snoozed' ein eigener Zustand ist
- Zurückstellen bei Zeit-Auslösern, die schon verstrichen sind

### Decided

- 'snoozed' bleibt gespeichert und wird wie 'waiting' ausgewertet; 'due' wird beim Lesen abgeleitet und nie gespeichert.
- Zurückstellen setzt gefeuerte Ereignis-Auslöser zurück; verstrichene Zeit- und Topic-Auslöser werden entfernt, sonst wäre die Note sofort wieder fällig. Ein neuer Auslöser ersetzt alle alten.
- Der Ereignis-Hook ist ItemService.edit -> NoteService.item_status_changed (Port ItemStatusListener); Auslöser anderer Projekte werden über die Links mit Rolle trigger gefunden.
- Umfang: Domain, NoteService und Port-Erweiterungen mit Tests; HTTP-Routen folgen in STORY-039.

### Open

- Ereignisse, die am Viewer vorbei entstehen (Markdown extern geändert), werden erst beim nächsten Sync erkannt; dafür gibt es noch keinen Aufruf des Hooks.
