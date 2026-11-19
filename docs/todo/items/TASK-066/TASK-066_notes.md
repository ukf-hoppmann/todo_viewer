# TASK-066 — Mindmap: entfernte Platzierungen merken und wieder einsetzen

## State

- Goal/Status: Vom Projekteigner am 2026-11-19 bestätigt (`Completed`); auf `main`, Release v0.11.0.
- Next step: Keiner; der Eintrag ist abgeschlossen.
- Open:
  - Keine
- Decided:
  - Entfernte Platzierungen werden gemerkt statt gelöscht und lassen sich wieder einsetzen (Weg 1) (2026-11-19)
  - Ein Ast wird als Gruppe entfernt und kommt als Gruppe zurück (2026-11-19)
  - Ersatzregel: Fehlt der alte Parent (nicht mehr im Baum, im Papierkorb oder selbst noch entfernt), steht der Ast unter der Wurzel der Map; die Oberfläche sagt es vorher und nachher (2026-11-19)
  - Die alte Stelle ist nie „belegt“: Geschwister rücken nach; abgelehnt wird nur, wenn der Knoten im Baum schon wieder steht (2026-11-19)
  - Gemerkt wird mit einer Spalte `removed_root` (Migration v5, Tabelle ohne Selbst-Fremdschlüssel neu aufgebaut) (2026-11-19)
- References: Spec `TASK-066_spec.md`; Story-Spec `STORY-102_spec.md`; Vorgänger `TASK-063`; Folge `TASK-067`

State confirmed after entry 2026-11-19 — Umsetzung (f2c1c2c71d91)

## 2026-11-19 — Übernahme der Entscheidungen aus STORY-102

### Discussed

- Frage: Wie macht man „Hier entfernen“ rückgängig? Der Papierkorb kennt Knoten, keine Platzierungen, und der Owner möchte den Ort nicht im Kopf behalten müssen.
- Weg 1: Platzierung nur als entfernt markieren (neue Spalte, Migration v4). Abfragen, Summen und die Regel „höchstens einmal je Baum“ nehmen markierte Zeilen aus. Wiederherstellen braucht Regeln, wenn Parent oder Platz fehlt oder der Knoten dort schon steht; ein Ast kommt als Gruppe zurück; API, MCP und eine Stelle am Knoten („Früher in …“). Aufwand mittel, Einschätzung am Code ohne Messung.
- Weg 2: nur „Rückgängig“ direkt danach: klein, hilft später nicht. Weg 3: weglassen: kein Aufwand, die alte Position ginge verloren.

### Decided

- Weg 1, als eigener Task nach `TASK-063`, damit dieser klein bleibt; nicht Pflicht für die Story (Owner). Verworfen: Weg 2 (hilft später nicht) und Weg 3 (alte Position verloren).

### Open

- Ersatzregel beim Wiedereinsetzen; Prüfung, ob der Knoten inzwischen im Baum steht.

## 2026-11-19 — Umsetzung

### Discussed

- Speicherform: Eine Spalte `removed_root` (Knoten, dessen Ast mit der Platzierung entfernt wurde; leer = gültig) statt zweier Spalten oder einer eigenen Tabelle. Die Gruppe ist „gleicher Baum, gleiches `removed_root`“; ein Zeitpunkt wird nicht gebraucht. Alternative eigene Tabelle: sauberer getrennt, aber jede Abfrage und der Austausch beim erneuten Setzen wären aufwendiger.
- Fremdschlüssel: Der Selbst-Fremdschlüssel `(tree_uid, parent_uid)` hätte das Umhängen eines Asts (Löschen der Quell-Platzierungen) blockiert, solange eine entfernte Platzierung auf den Parent zeigt. Gewählt: Migration v5 baut die Tabelle ohne ihn neu auf (Daten bleiben, getestet); die Domäne prüft den Parent weiter (`check_parent`). Verworfen: gemerkte Parents beim Löschen auf NULL setzen (verlöre den Ort).
- Wiedereinsetzen eines Unterknotens: kommt nur sein eigener Teilbaum aus der Gruppe zurück; ist sein alter Parent noch entfernt, gilt die Ersatzregel (Wurzel).
- Mitglieder der Gruppe im Papierkorb bleiben samt Teilbaum entfernt gemerkt (`nodes_skipped`), statt den Ast zu blockieren. Vorsichtige Annahme.
- „Knoten löschen“ merkt die Platzierungen der Unterknoten, die anderswo stehen, ebenfalls (gleiche Gruppe, Wurzel = gelöschter Knoten). So lassen sie sich nach dem Wiederherstellen des Knotens aus dem Papierkorb wieder einsetzen.
- Erneutes Setzen eines Knotens in einen Baum (Übertragen, Umhängen, neuer Unterknoten) ersetzt die gemerkte Platzierung; „steht im Baum schon wieder“ ist damit die Ablehnung beim Wiedereinsetzen.
- Oberfläche: Abschnitt „Früher in …“ im Knoten-Detail (der Knoten steht dann in einem anderen Baum und ist dort sichtbar); Menü und Karte bleiben unverändert.

### Decided

- Umgesetzt wie oben: Server (`domain/branches.py` `plan_restore`, `application/branches.py`, Operationen `restore_node_placement`, `list_removed_placements`), Migration v5, Oberfläche `RemovedPlacementsSection`, Doku in `neubau-server.md`, `neubau-client.md`, `interfaces.md`.
- Nicht Teil: Papierkorb-Ansicht (`TASK-067`).

### Open

- Keine.
