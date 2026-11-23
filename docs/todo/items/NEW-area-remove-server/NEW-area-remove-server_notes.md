# NEW-area-remove-server — Area aus Server und Datenbank entfernen

## State

- Goal/Status: Geplant; Spec geschrieben, die Task ist für eine eigene Session vorbereitet.
- Next step: In eigener Session umsetzen: Plan aus `NEW-area-remove-server_spec.md` ableiten, vorlegen und freigeben lassen.
- Open:
  - Nichts offen für die Umsetzung (2026-11-23)
- Decided:
  - Kein abgeleiteter Ersatzwert: die Index-Zeilen verlieren die Spalte Area ersatzlos (Owner, `STORY-106`) (2026-11-23)
  - Der Import aus dem alten Viewer ignoriert die Bereiche (Folge der Entscheidung, das Feld sofort zu entfernen) (2026-11-23)
- References: Spec `NEW-area-remove-server_spec.md`; Story `STORY-106` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: NEW-area-mirror-v3, NEW-area-client

State confirmed after entry 2026-11-23 — Zuschnitt aus der Planung von STORY-106 (2413bd045d66)

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
