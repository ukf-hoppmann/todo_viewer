# STORY-057 — Abgleich pro Eintrag mit Konfliktmeldung

## 2026-10-14 — Anlage und Abstimmung (2026-10-14)

### Discussed

- Ziel des Besitzers: Backlog und Notes in claude.ai-Sitzungen (Cloud) nutzen, über Git abgleichen und lokal in der Datenbank bearbeiten.
- Der Sync kennt nur den Stand ganzer Seiten; bei Änderungen auf beiden Seiten oder gleicher neuer ID geht still etwas verloren.
- Aufwand eines Git-ähnlichen Merges (Drei-Wege innerhalb von Einträgen) gegenüber Entscheidung je Eintrag.

### Decided

- Jeder Konflikt wird gemeldet; Entscheidung je Konflikt: Datenbank, Datei oder aufschieben. Aufschieben hat keinen eigenen Zustand.
- Kein Drei-Wege-Merge innerhalb von Einträgen; Git führt die Dateiseite zusammen. Pro Eintrag wird nur die Version gespeichert.
- Reihenfolge TASK-031 (Backup) → TASK-032 → TASK-033; danach STORY-058 und STORY-047.
- Vorgabe des Besitzers: Vor großen Änderungen ein Datenbank-Backup. Manuelles Backup von 2026-10-14 15:27 liegt unter configs/backups/todo-20261014-152748-vor-notes-sync.db (Integrität und Zeilenzahlen geprüft); ab TASK-031 legt der Viewer es selbst an.
- Auslieferung (./todo.sh update) darf der Assistent nach grünen Tests durchführen, aber nur mit frischem Backup davor.

### Open

- Richtung: beidseitiger Abgleich pro Eintrag mit direction als Einschränkung (Vorschlag) oder Richtung wie bisher mit Konflikt bei Änderung nur auf der Zielseite.
- Gelöschte Einträge: weiter als „fehlt“ melden (Vorschlag) oder als Konflikt.

## 2026-10-14 — Entscheidungen vom 2026-10-14 (Richtung, Löschungen, Auto-Sync)

### Decided

- Variante A: beidseitiger Abgleich pro Eintrag; direction nur als Einschränkung.
- Löschungen werden wie Konflikte entschieden (Datenbank, Datei, aufschieben); delete_missing entfällt (Vorschlag).
- Der Besitzer will einen echten, abschaltbaren Auto-Sync: STORY-059. Er berührt Architektur §1 und §3; der Wortlaut der Änderung steht zur Freigabe.

### Open

- Merge: automatisches Zusammenführen von Konflikten gewünscht (Aussage „Konflikte sollten gemerged sein“)? Wirkt auf TASK-032 (Snapshot statt Hash).

## 2026-10-14 — Merge entschieden (2026-10-14)

### Decided

- Variante (a): Konflikte liegen zur Entscheidung bereit (Datenbank, Datei, aufschieben; Diff-Ansicht in STORY-058). Kein automatischer Merge; gespeichert wird die Version (Hash) je Eintrag. Ein automatischer Merge wäre eine spätere eigene Story.

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.
- Nach dem Update zeigen `ezf-ui` (15) und `image_refiner` (25) offene Konflikte: Ohne gespeicherten Stand gilt „auf beiden Seiten vorhanden und verschieden“ als Konflikt. Nichts wurde verändert.

### Decided

- Beidseitiger Abgleich pro Eintrag (Variante A); `direction` schränkt nur ein. Konflikte werden nie überschrieben oder gelöscht; Löschungen sind Konflikte. Kein automatischer Merge innerhalb eines Eintrags, gespeichert wird nur die Version.
- Backup vor jeder Migration und vor jedem Sync, der in die Datenbank schreibt (TASK-031). Release v0.8.8; der Wegfall von `delete_missing` und die geänderte Antwort von `POST /sources/{id}/sync` sind für API-Aufrufer ein Bruch.

### Open

- `ezf-ui` und `image_refiner`: die offenen Konflikte im Sync-Dialog entscheiden (Besitzer).
