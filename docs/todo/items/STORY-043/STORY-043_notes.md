# STORY-043 — Archiv und Papierkorb für Notes

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Archiv und Papierkorb wie im Backlog

### Decided

- Archiv und Papierkorb folgen dem Backlog; endgültiges Löschen nur durch den Besitzer.

### Open

- Alte Note nach einem Projektwechsel: wiederherstellbar oder nicht (siehe STORY-038)?

## 2026-10-08 — Umsetzung (Domain und Service)

### Discussed

- Wiederherstellen von Topics mit Notes
- Alte Note nach Projektwechsel

### Decided

- Endzustände done/dropped/promoted setzen 'archived'; Löschen setzt 'deleted' (Papierkorb). Beides ist wiederherstellbar, die Note wird wartend mit neuem Prüf-Datum.
- Ein Topic mit Unter-Topics oder Notes wird nur mit Kaskade gelöscht; Wiederherstellen bringt, was zum selben Zeitpunkt gelöscht wurde, und braucht ein vorhandenes Eltern-Topic.
- Endgültiges Löschen (purge_note, purge_topic) gibt es nur im NoteService für den Besitzer; keine Route, die Claude erreicht. Labels werden nie wiedervergeben.
- Nach einem Projektwechsel liegt die alte Note im Papierkorb des Ursprungsprojekts und lässt sich dort wie jede andere wiederherstellen; die neue im Zielprojekt hat ein neues Label.

### Open

- Die HTTP-Routen und die Besitzer-Funktion in der UI folgen mit STORY-039 und STORY-045.
