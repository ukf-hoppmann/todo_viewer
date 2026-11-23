# TASK-069 — Area ist beim Anlegen nicht mehr Pflicht

## State

- Goal/Status: Umgesetzt und getestet; wartet auf Bestätigung (2026-11-23).
- Next step: Owner bestätigt; danach die Oberfläche ohne Area (`TASK-070`).
- Open:
  - Nichts (2026-11-23)
- Decided:
  - Entfernung in drei Schritten, damit Server und Oberfläche getrennt umgebaut werden können: Area optional, Oberfläche ohne Area, Feld entfernen (Zuschnitt) (2026-11-23)
  - Ohne Area bleibt der Wert leer (`None`); `list_areas`, Index, Spiegel und Datenbank blieben unverändert (2026-11-23)
- References: Spec `TASK-069_spec.md`; Story `STORY-106` (Notes mit den Entscheidungen des Owners); Techdoc `docs/techdocs/neubau-server.md`

State confirmed after entry 2026-11-23 — Umsetzung (82113b444341)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-106

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-106 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-106_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Entfernung in drei Schritten, damit Server und Oberfläche getrennt umgebaut werden können: Area optional, Oberfläche ohne Area, Feld entfernen (Zuschnitt)

### Open

- Nichts.

## 2026-11-23 — Umsetzung

### Discussed

- Test zuerst: drei neue bzw. angepasste Tests (Domain, Item-Anlegen, Beförderung) schlugen vor der Änderung fehl.
- `area` aus `REQUIRED_TEXT` und der Pflichtprüfung in `build_new_item` entfernt; Beschreibungen von `create_item`, `CreateItem`, `promote_memo`, `PromoteMemo` und `promote` angepasst; Techdoc `neubau-server.md` nachgezogen.
- Server-Tests grün, `ruff` (E501) und `mypy` ohne neue Befunde, Schichtregeln eingehalten; Client-Tests grün (ein einmaliger Fehlschlag im ersten Lauf trat im Wiederholungslauf nicht mehr auf, der Client wurde nicht geändert).

### Decided

- Ohne Angabe bleibt `area` leer; vorhandenes Verhalten mit Area unverändert.

### Open

- Nichts.
