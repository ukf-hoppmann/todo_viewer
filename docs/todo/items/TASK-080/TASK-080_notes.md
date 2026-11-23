# TASK-080 — Mindmap-Spiegel: Teilnehmer für Knoten und Bäume

## State

- Goal/Status: Umgesetzt und getestet; wartet auf die Bestätigung des Owners (2026-11-23).
- Next step: Owner bestätigt; danach `TASK-081` (Zuordnungen, `Removed:`, Papierkorb der Bäume, Dokumente löschen).
- Open:
  - Nichts offen (2026-11-23)
- Decided:
  - Bäume haben kein Label; neue Maps bekommen nur eine Uid, Knoten das Label NODE-nnn (Zuschnitt) (2026-11-23)
  - Mit dieser Stufe laufen Zuordnungen und Dokumente noch nicht über den Sync; der Teilnehmer lässt Zuordnungen unberührt, um keine Daten zu löschen (Zuschnitt) (2026-11-23)
  - Dokumente der Knoten werden schon jetzt angelegt und geändert (nicht gelöscht), damit ein neuer Knoten mit Dokument aus der Cloud keine verwaisten Dateien hinterlässt (2026-11-23)
  - Platzierungen: nur Geschwistergruppen mit geänderten Mitgliedern oder Reihenfolge werden geschrieben; nicht genannte Knoten behalten ihren Parent (2026-11-23)
- References: Spec `TASK-080_spec.md`; Story `STORY-105`; Code `server/src/viewer/plugins/mindmap/infrastructure/mirror/participant.py`, `domain/listing.py`; Tests `test_mindmap_mirror.py`, `test_mirror_placements.py`

State confirmed after entry 2026-11-23 — Umsetzung (67759c6a9af6)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-105

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-105 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-105_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Bäume haben kein Label; neue Maps bekommen nur eine Uid, Knoten das Label NODE-nnn (Zuschnitt)
- Mit dieser Stufe laufen Zuordnungen und Dokumente noch nicht über den Sync; der Teilnehmer lässt sie unberührt, um keine Daten zu löschen (Zuschnitt)

### Open

- Nichts.

## 2026-11-23 — Umsetzung

### Discussed

- Der Teilnehmer folgt `MemosParticipant`; die Platzierungen schreibt er über reine Funktionen der Domain (`placements_from_listing`, `changed_placements`, `check_acyclic`), nicht über `BranchService`, weil dessen Dienste eigene Transaktionen öffnen und der Sync die seine mitbringt.
- Ohne Dokumente würde ein neuer Knoten aus der Cloud mit `new-x_notes.md` eine verwaiste Datei hinterlassen (der Knoten wird in `NODE-nnn.md` umbenannt, das Dokument nicht). Option A: Dokumente jetzt mitnehmen (klein, Muster Memos). Option B: erst in `TASK-081`, dann bleibt der Fehler bis dahin. Gewählt: A, ohne Löschen von Dokumenten.
- Ein Knoten, den die Baumliste nicht nennt, behält seinen Platz; das Entfernen von Platzierungen gehört zu `TASK-081`.

### Decided

- Dokumente der Knoten werden schon jetzt angelegt und geändert (nicht gelöscht)
- Platzierungen: nur Geschwistergruppen mit geänderten Mitgliedern oder Reihenfolge werden geschrieben; nicht genannte Knoten behalten ihren Parent
- Bekannte Grenze bis `TASK-081`: eine Datei mit `Items:`, `Memos:`, `Removed:` oder `Deleted:` einer Map weicht dauerhaft von der Datenbank ab, weil `load` sie nicht trägt

### Open

- Nichts.

