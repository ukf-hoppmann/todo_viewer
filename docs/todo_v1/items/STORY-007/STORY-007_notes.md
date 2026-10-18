# STORY-007 — Items anlegen

## 2026-09-30 — Wiedergeöffnet für Typwechsel

### Discussed

- Ein Typwechsel ist eine Umbenennung der ID (Präfix = Typ). Nötig: neue ID über die nächste freie Nummer des Zieltyps, Umschreiben von Header, parent und dependencies aller Items (TODO.md und archive.md), Umbenennen von items/<ID>/ sowie Nachziehen der ID-Erwähnungen in Notes und Specs, da diese Teil des Backlogs sind.
- Verweise außerhalb des Backlogs (Tagesberichte, Commits, Techdocs) können nicht nachgezogen werden.

### Decided

- Variante B: neue ID vergeben und alles mitziehen, über einen eigenen Endpunkt POST /items/{source}/{id}/retype statt über PATCH.
