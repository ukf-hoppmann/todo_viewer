# STORY-095 — Sync-Konflikte erklären: Herkunft, Umbenennung, Empfehlung

## State

- Goal/Status: Konflikte im Sync-Dialog erklären (Herkunft, Umbenennung, Empfehlung); Spec steht, Umsetzung nicht begonnen.
- Next step: TASK-046 (Server-Ableitung) planen und umsetzen, danach TASK-047 (Dialog).
- Open:
- Decided:
  - Der Viewer erklärt und empfiehlt nur, ohne Vorauswahl und ohne automatische Löschung; Architektur §2 bleibt (2026-11-03)
  - Umbenennungen werden über Ähnlichkeit erkannt, nicht über git (2026-11-03)
  - Zuschnitt: TASK-046 Server, TASK-047 Dialog (2026-11-03)
- References: Spec STORY-095_spec.md; TASK-046, TASK-047; Beispiel image_refiner STORY-086_spec_nsfw-papierkorb.md → STORY-086_spec_sensibel-papierkorb.md (Commit 0fcb81ef)

State confirmed after entry 2026-11-03 — Anlass und Zuschnitt (0b8d856eff04)

## 2026-11-03 — Anlass und Zuschnitt

### Discussed

- Anlass: Im Sync-Dialog von image_refiner war der Konflikt 'STORY-086_spec_nsfw-papierkorb.md · in den Dateien gelöscht' unverständlich. Ursache laut git: Umbenennung in STORY-086_spec_sensibel-papierkorb.md (R074) in Commit 0fcb81ef. Der neue Name wurde als neuer Eintrag übernommen, der alte erschien als Löschkonflikt. Die Datenbankseite war seit dem Abgleich vom 22.10. unverändert.
- Ohne neue Daten ableitbar: welche Seite seit dem Abgleich geändert ist (Basis-Hash), Zeitpunkt des Abgleichs (synced_at), Umbenennungsverdacht über Ähnlichkeit (difflib), eine Empfehlung mit Begründung, ein Diff zwischen den Seiten.
- Nicht ableitbar ohne Erweiterung: bei both_changed, was sich auf welcher Seite geändert hat (bräuchte den Inhalt vom letzten Abgleich und eine Migration).
- Löschungen bei unveränderter Gegenseite automatisch zu übernehmen, widerspräche Architektur §2 (Löschung auf einer Seite ist ein Konflikt). Verworfen zugunsten von Hinweis und Empfehlung.
- git als Quelle für Umbenennungen: sicher, aber zusätzliche Abhängigkeit. Zunächst nicht, die Ähnlichkeitssuche reicht.

### Decided

- Besitzer stimmt dem Vorschlag zu (2026-11-03): Story unter EPIC-007 mit zwei Tasks, TASK-046 (Server-Ableitung) und TASK-047 (Dialog, hängt von TASK-046 ab).
- Der Viewer empfiehlt nur. Er wählt nichts vor und löscht nichts automatisch.
