# TASK-082 — Mindmap-Spiegel: Sync-Dialog, Cloud-Ablauf, Doku und Prompt für Claude_Harness

## State

- Goal/Status: Umgesetzt und geprüft: Sync-Dialog mit lesbaren Namen und Ordnung als Liste, Systemtest „Cloud-Sitzung“, Doku, Prompt für Claude_Harness; wartet auf die Abnahme (2026-11-24)
- Next step: Owner nimmt ab und gibt den Prompt (`TASK-082_spec_prompt-harness.md`) an Claude_Harness weiter; danach `STORY-105` prüfen.
- Open:
  - Nichts offen (2026-11-24)
- Decided:
  - Der Prompt für Claude_Harness wird dem Owner gegeben; die KI übergibt nichts selbst (Owner) (2026-11-23)
  - Der Sync-Dialog bleibt allgemein; die Mindmap bekommt nur lesbare Namen und Diff der Ordnung (Zuschnitt) (2026-11-23)
  - Ordnung eines Baums und entfernte Platzierungen erscheinen im Feldvergleich als Zeilenliste (eingerückte Labels, Zeile je entfernter Platzierung), nicht als Zahlen und Labels; Namen nur für Knoten, Maps, Bäume und Notizen von Knoten (2026-11-24)
  - Der Systemtest vergleicht eine Cloud-Sitzung (nur Dateien) mit denselben Schritten über MCP im Zweitprojekt und prüft den Konflikt (2026-11-24)
- References: Spec `TASK-082_spec.md`, Prompt `TASK-082_spec_prompt-harness.md`; Story `STORY-105`; Abhängigkeiten: TASK-081; Test `tests/implementation/system/server/test_mindmap_mirror_flow.py`

State confirmed after entry placeholder

State confirmed after entry 2026-11-24 — Umsetzung (6c2aad5241d7)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-105

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-105 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-105_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Der Prompt für Claude_Harness wird dem Owner gegeben; die KI übergibt nichts selbst (Owner)
- Der Sync-Dialog bleibt allgemein; die Mindmap bekommt nur lesbare Namen und Diff der Ordnung (Zuschnitt)

### Open

- Nichts.

## 2026-11-24 — Umsetzung

### Discussed

- Sync-Dialog: Der Server schickt für Bäume kein Label, der Dialog hätte `mindmap.tree` gezeigt. Namen entstehen im Client aus den Feldern des Konflikts (`entryName` in `sync.ts`): „Knoten NODE-001 · Titel“, „Map „Name““, „Projektbaum der Mindmap“; Übertragungen tragen keine Felder, dort steht „Mindmap-Baum“ ohne Namen. Die Ordnung (`depths` + Verweis `nodes`) wird zu einer eingerückten Liste, `removed` zu einer Zeile je Platzierung; so greift der vorhandene Zeilen-Diff.
- Notizen eines Knotens zeigen „Notiz zu Knoten NODE-001“ statt der Zeile `node`; `documentContext` liefert dafür `node`.
- Systemtest: Projekte anlegen ist kein MCP-Tool, darum HTTP für das Anlegen, sonst MCP. Die Sitzung liest Labels aus den Knotendateien nach und ändert nur Textdateien. Eine leere Map hat nach dem Kopf keine Leerzeile; wer die Liste anfügt, muss sie ergänzen (jetzt in `interfaces.md` genannt).
- Prompt: Regeln 1–8 für Dateien, die Regel aus `STORY-104` im Datei-Modus, und was `todo`-Skill, `format.md`, `backlog.py` und Vorlagen ergänzen sollen (`mindmap/` nicht als unbekannte Dateien melden).

### Decided

- Umsetzung wie in der Spec; keine Änderung am Server nötig.
- Der Prompt liegt als Datei neben der Spec und wird dem Owner im Abschlussbericht vollständig gegeben.

### Open

- Nichts.
