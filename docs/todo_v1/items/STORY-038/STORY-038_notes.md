# STORY-038 — Datenmodell: Topics, Notes und Links in der Datenbank

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Tiefe, Labels, Projektwechsel, Dokumente an Notes
- Auslöser-Modus any/all im Modell

### Decided

- Tiefe 3, konfigurierbar.
- Labels ändern sich innerhalb eines Projekts nie; der Projektwechsel legt die Note im Zielprojekt neu an und löscht die alte.
- Notes bekommen Notizen und Specs wie Items, keine Unter-Notes.
- Auslöser-Modus any (Standard) oder all im Modell; Bedienung später.

### Open

- Link-Ziel Projekt plus Item-Label statt uid (hängt an STORY-037)
- Soll die gelöschte alte Note nach einem Projektwechsel wiederherstellbar sein? Sonst entsteht ein Duplikat.

## 2026-10-08 — Umsetzung

### Discussed

- Modell, Migration 6, Port, Adapter

### Decided

- Gelöschte Notes (auch nach Projektwechsel) liegen im Papierkorb und sind wiederherstellbar
- Ein abgelehnter Schreibvorgang verbraucht keine Label-Nummer (Zähler in derselben Transaktion)
- Optionen notes.max_topic_depth/review_days werden gelesen (infrastructure/config/notes.py), aber erst von STORY-039 verdrahtet
- Contract-Suite läuft vorerst nur gegen den Datenbank-Adapter (einzige Implementierung)

### Open

- Link-Prüfungen beim Projektwechsel (STORY-041): move_note übernimmt alle Links unverändert
