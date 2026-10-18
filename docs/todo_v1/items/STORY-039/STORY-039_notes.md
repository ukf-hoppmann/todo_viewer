# STORY-039 — API für Topics, Notes und Links inklusive schlanker Übersicht

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Index-Felder und Filter
- Zähler-Abfrage für das Ausrufezeichen
- Rechte

### Decided

- Index mit Label, Status, Fälligkeit, Kurzfassung; Filter Topic, Projekt, Status, fällig, verlinktes Item.
- Eigene Zähler-Abfrage und globale Fällig-Liste.
- Die API erzwingt keine Rechte; sie liegen im Harness.

### Open

- Genaue Pfade und Fehlercodes legt die Umsetzung fest.

## 2026-10-08 — Umsetzung der Notes-API

### Discussed

- Pfade, Fehlercodes und Zuschnitt der Dienste.
- Beim Test der Links fiel auf: Der RetypeService übergab die Source-ID statt des Projektnamens an relink_item, Links auf umgetypte Items blieben auf dem alten Label.

### Decided

- Topics und Notes liegen unter /api/v2/projects/{project}/…, adressiert über den Projektnamen und das Label; projektübergreifend sind nur /api/v2/notes/index, /notes/due, /notes/due/count und /notes/settings.
- Der Index filtert nach project, topic (mit Unter-Topics, braucht project), status, due, linked_item (mit linked_project) und archived; ein abgeschlossener status liest das Archiv.
- Über HTTP gibt es kein Purge und kein Befördern; finish kennt nur done und dropped.
- Links akzeptieren die Rollen reference und origin; die Rolle trigger entsteht nur über Ereignis-Auslöser.
- Die Optionen review_days und max_topic_depth ändert PUT /notes/settings, gespeichert in config.json, wirksam ohne Neustart (Bereiche 1–3650 bzw. 1–10).
- Retype-Fehler behoben: relink_item bekommt jetzt den Projektnamen; die Tests, die die UUID festschrieben, sind korrigiert.

### Open

- Befördern (STORY-042) ergänzt die Aktion promote in der Fällig-Liste und im Abschluss.
