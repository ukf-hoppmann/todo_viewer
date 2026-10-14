# STORY-045 — Bereich Notes: Topic-Baum, Notes und rotes Ausrufezeichen

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Platz und Verhalten des roten Ausrufezeichens
- Inhalt des Modals
- Einstellungen

### Decided

- Ausrufezeichen neben dem Titel oben links; Zähler global; Klick öffnet ein Modal mit allen fälligen Notes und den Aktionen.
- Fällige Notes bleiben im Modal, bis sie zurückgestellt, erledigt, verworfen oder gelöscht sind; das Icon bleibt, solange Einträge existieren.
- Zusätzlich: Gruppierung nach Grund, Schnellaktionen zum Zurückstellen, Zähler im Tab-Titel.

## 2026-10-08 — Umsetzung

### Discussed

- Umsetzung aller Tasks (TASK-018 bis TASK-023) und TASK-015 aus STORY-042 in einem Zug.

### Decided

- Anzeige im Browser geprüft (Topic und Note anlegen, Auslöser in die Vergangenheit setzen: Icon und Tab-Titel, Fällig-Modal, Zurückstellen, Einstellungen).
- Kein Popup außerhalb des Modals; keine Benachrichtigung außerhalb der Seite.

### Open

- Laufender Container nicht geprüft (Neubau mit `./todo.sh update`).
