# STORY-095 — Sync-Konflikte erklären: Herkunft, Umbenennung, Empfehlung

## State

- Goal/Status: Konflikte im Sync-Dialog erklären; Server (TASK-046) und Dialog (TASK-047) umgesetzt und getestet, wartet auf Abnahme.
- Next step: Abnahme durch den Besitzer, Sync-Dialog im laufenden Viewer an einem echten Konflikt ansehen (Container neu bauen).
- Open:
  - Test startApp "stores the language …" im Client schlägt fehl, unabhängig vom Sync (2026-11-03)
- Decided:
  - Der Viewer erklärt und empfiehlt nur, ohne Vorauswahl und ohne automatische Löschung; Architektur §2 bleibt (2026-11-03)
  - Umbenennungen werden über Ähnlichkeit erkannt (ab 0,6), nicht über git; der Partner muss nicht neu sein (2026-11-03)
- References: Spec STORY-095_spec.md; TASK-046, TASK-047

State confirmed after entry 2026-11-03 — Umsetzung TASK-046 und TASK-047 (8fcba1b1cf2c)

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

## 2026-11-03 — Umsetzung TASK-046 und TASK-047

### Discussed

- Server: explain_conflict in core/domain/sync.py (rein), SyncStateStore.synced_times je Eintrag, ConflictOut um database_changed, files_changed, synced_at, renamed_to, recommendation, reason erweitert; OpenAPI-Typen neu erzeugt.
- Dialog: Herkunftssatz, Kontext statt kind/item-Zeilen, Umbenennungshinweis, Empfehlung als Chip mit Begründung, Zeilen-Diff bei Texten auf beiden Seiten.
- Der Umbenennungspartner muss nicht neu sein: im Beispiel stand der neue Name schon in der Datenbank und in der Basis. Die Spec war an der Stelle falsch und ist korrigiert.

### Decided

- Ähnlichkeitsschwelle 0,6; die Empfehlung ist nur ein Vorschlag, nichts ist vorausgewählt.

### Open

- Test startApp 'stores the language …' schlägt im Client aktuell fehl; er berührt den Sync nicht und wurde nicht angefasst.
