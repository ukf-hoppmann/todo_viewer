# TASK-071 — Area aus Server und Datenbank entfernen

## State

- Goal/Status: Umgesetzt und geprüft (2026-11-24); wartet auf die Abnahme des Owners.
- Next step: Abnahme durch den Owner; danach der Prompt für die KI und für Claude_Harness (nächste Task von `STORY-106`).
- Open:
  - Nichts offen (2026-11-24)
- Decided:
  - Kein abgeleiteter Ersatzwert: die Index-Zeilen verlieren die Spalte Area ersatzlos (Owner, `STORY-106`) (2026-11-23)
  - Der Import aus dem alten Viewer ignoriert die Bereiche (2026-11-23)
  - Migration 5 baut `backlog_items` neu auf, weil SQLite die Spalte mit Fremdschlüssel nicht per `DROP COLUMN` entfernt; abhängige Tabellen werden vorher gesichert, damit `ON DELETE CASCADE` nichts löscht (2026-11-24)
  - Die Spalte `area` entfällt auch aus dem Lesen der alten Datenbank (`legacy_schema.py`) (2026-11-24)
- References: Spec `TASK-071_spec.md`; Story `STORY-106`; Abhängigkeiten: TASK-068, TASK-070

State confirmed after entry 2026-11-24 — Umsetzung (5607233f0752)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-106

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-106 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-106_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Kein abgeleiteter Ersatzwert: die Index-Zeilen verlieren die Spalte Area ersatzlos (Owner, `STORY-106`)
- Der Import aus dem alten Viewer ignoriert die Bereiche (Folge der Entscheidung, das Feld sofort zu entfernen)

### Open

- Nichts.

## 2026-11-24 — Umsetzung

### Discussed

- Test zuerst: der Migrationstest (`test_area_removal_migration.py`, Datenbank der Vorversion mit Items, Eltern, Abhängigkeit, Dokumenten, Notes, Papierkorb) schlug fehl und ist nach der Migration grün.
- `ALTER TABLE … DROP COLUMN` scheitert an `area_uid` (Fremdschlüssel). `DROP TABLE backlog_items` würde über `ON DELETE CASCADE` die Zeilen der abhängigen Tabellen löschen, und der Verweis `parent_uid` auf die eigene Tabelle verletzt den Fremdschlüssel beim Löschen. Gewählt: abhängige Tabellen und die Eltern der Items in Zwischentabellen sichern, Tabellen neu aufbauen, Eltern am Ende setzen. Verworfen: `PRAGMA foreign_keys=OFF` (wirkt innerhalb der Transaktion der Migration nicht).
- Entfernt: `area` in Domain, Anwendung, Repository, Spiegel-Teilnehmer, Memos (Beförderung), Import; Operation `list_areas`; Index-Kopf jetzt `ID | Type | Status | Title | Parent | Notes`. Client-Typen neu erzeugt, `tsc -b` grün.
- Doku: `interfaces.md`, `neubau-server.md`. Die `README.md` nennt Area nicht.
- Teststand: Server 1413 bestanden, 1 übersprungen; Client 1473 von 1473. Ruff (5× E501 in fremden Dateien), mypy (Duplikat-Modulname im Testordner) und Client-Lint (5 Fehler in `usePersistentState.ts`) waren schon vorher nicht sauber.

### Decided

- Siehe Kopf.

### Open

- Nichts.
