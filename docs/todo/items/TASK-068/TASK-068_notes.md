# TASK-068 — Backlog-Spiegel: Format Version 3 ohne Area

## State

- Goal/Status: Umgesetzt und getestet (2026-11-23); wartet auf die Bestätigung des Owners.
- Next step: Owner bestätigt; danach folgen `TASK-070` (Oberfläche) und `TASK-071` (Server und Datenbank).
- Open:
  - Nichts offen (2026-11-23)
- Decided:
  - Format Version 3 ohne Area; Version 2 und 3 werden gelesen, Area wird in beiden ignoriert (Owner, `STORY-106`) (2026-11-23)
  - Nur das Backlog bekommt Version 3, Alarme und Memos bleiben (Zuschnitt) (2026-11-23)
  - Geschrieben wird Version 3 nur in Dateien, die ohnehin geschrieben werden; ein Eintrag verliert `Area` nur, wenn er sich sonst ändert (2026-11-23)
  - Neue Golden-Files `tests/fixtures/mirror-v3/` für den Backlog-Teil; `mirror-v2` bleibt für Alarme, Memos und das Lesen von Version 2 (2026-11-23)
- References: Spec `TASK-068_spec.md`; Story `STORY-106`; Code `server/src/viewer/plugins/backlog/infrastructure/mirror/`; Doku `docs/techdocs/interfaces.md`

State confirmed after entry 2026-11-23 — Umsetzung (0ca9de76a361)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-106

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-106 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-106_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Format Version 3 ohne Area; Version 2 und 3 werden gelesen, Area wird in beiden ignoriert (Owner, `STORY-106`)
- Nur das Backlog bekommt Version 3, Alarme und Memos bleiben (Zuschnitt)

### Open

- Nichts.

## 2026-11-23 — Umsetzung

### Discussed

- Beim Schreiben bleibt offen, wann die Kennung wechselt und wann `Area` fällt. Option A: jede Datei sofort umschreiben; sie wäre dann bei jedem Sync verändert, auch ohne Inhalt. Option B: nur Dateien und Einträge, die ohnehin geändert werden. B passt zum Grundsatz des Codecs, nur Betroffenes zu ändern, und zur Spec („ein unveränderter Eintrag wird nicht allein wegen Area umgeschrieben“).
- Die Fixtures: `mirror-v2` wird auch von Alarmen und Memos benutzt und sichert das Lesen von Version 2; deshalb bleibt es unverändert und der Backlog-Teil bekommt `mirror-v3`.
- Das Modell und die Datenbank bleiben wie in der Spec; der Teilnehmer setzt `area=None`, nach dem Sync aus Dateien ist `area` in der Datenbank leer (gewollte Folge).

### Decided

- Option B; Fixtures `mirror-v3`; Tests: Unit für Codec (Lesen 2, 3 mit Area, 4 und fehlende Kennung abweisen, Schreiben ohne Area, Kennung 3, Upgrade einer Version-2-Datei), Integration für Import von Version 2, Rückschreiben als Version 3.

### Open

- Nichts.
