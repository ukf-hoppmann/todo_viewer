# TASK-079 — Mindmap-Spiegel: Dateiformat und Codec mit Golden-Files

## State

- Goal/Status: Umgesetzt und geprüft (Awaiting confirmation): Format-Kapitel, `MindmapCodec` und Golden-Files stehen, alle Tests grün.
- Next step: Owner bestätigt; danach `TASK-080` (Teilnehmer) auf dem Codec aufbauen.
- Open:
  - Nichts offen für die Umsetzung (2026-11-23)
- Decided:
  - Der Inhalt eines Knotens steht einmal in einer Datei; jeder Baum ist eine Datei mit Verweisen; mehrfache Platzierungen sind Verweise (Owner) (2026-11-23)
  - Dateiname je Knoten `NODE-nnn.md`, Bäume `project.md` und `maps/<name>.md`; Identität ist die Uid, nicht der Dateiname (Zuschnitt) (2026-11-23)
  - Das Format hat eine eigene Versionszählung (Version 1), unabhängig vom Backlog-Format (Zuschnitt) (2026-11-23)
  - Baum-Einträge (`mindmap.tree`) haben kein Label, nur Uid oder Platzhalter; Verweise `nodes`, `removed_nodes`, `removed_parents`, `removed_groups`, Tiefen in `fields` (2026-11-23)
  - Freie Maps haben nur dann eindeutige Namen, wenn sie nicht im Papierkorb liegen (wie in der Datenbank); Dokument ohne Knoten ist `file_label_mismatch` (2026-11-23)
- References: Spec `TASK-079_spec.md`; Story `STORY-105` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: keine

State confirmed after entry 2026-11-23 — Umsetzung (5dc50b8bd7da)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-105

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-105 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-105_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Der Inhalt eines Knotens steht einmal in einer Datei; jeder Baum ist eine Datei mit Verweisen; mehrfache Platzierungen sind Verweise (Owner)
- Dateiname je Knoten `NODE-nnn.md`, Bäume `project.md` und `maps/<name>.md`; Identität ist die Uid, nicht der Dateiname (Zuschnitt)
- Das Format hat eine eigene Versionszählung (Version 1), unabhängig vom Backlog-Format (Zuschnitt)

### Open

- Nichts.

## 2026-11-23 — Umsetzung

### Discussed

- Umgesetzt nach dem Plan: Format-Kapitel in `docs/techdocs/interfaces.md` zuerst, dann Tests und Golden-Files, dann
  `syntax.py`, `decode.py`, `encode.py`, `codec.py` unter `plugins/mindmap/infrastructure/mirror/`.
- Darstellung der Bäume als Einträge: eigene gleichwertige Form (Spec erlaubt das): kein Label, Verweise auf Knoten als
  Label oder Platzhalter in Tiefensuche, Tiefen und Positionen der entfernten Platzierungen in `fields`.
- Dateiname einer Map: Slug des Namens (Umlaute umschrieben), bei Kollision `-2`; eine vorhandene Datei bleibt, solange
  ihr Name zum Slug passt, sonst wird umbenannt.
- Merge-Marker prüft der Codec selbst (`has_merge_markers` des Kerns) und meldet die Zeile.

### Decided

- Wie oben; Plugin-Definition unverändert, der Codec ist noch nicht registriert (`TASK-080`).
- `mypy` über alle Testordner scheitert schon vorher an einem doppelten Modulnamen `test_sync_settings`
  (nicht Teil dieser Task); die Typprüfung lief über `src`, die Helfer und die Mindmap-Tests.

### Open

- Nichts.
