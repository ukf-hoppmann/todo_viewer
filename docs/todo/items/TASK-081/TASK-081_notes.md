# TASK-081 — Mindmap-Spiegel: Zuordnungen, Dokumente, entfernte Platzierungen und Papierkorb

## State

- Goal/Status: Umgesetzt und getestet; wartet auf die Bestätigung des Owners (2026-11-24).
- Next step: Owner bestätigt; danach `TASK-082` (Sync-Dialog, Cloud-Test, Doku, Prompt).
- Open:
  - Nichts offen (2026-11-24)
- Decided:
  - Die Zuordnung steht auf dem Knoten, nicht im Item, weil die Dateien der Items dem Harness gehören (Zuschnitt) (2026-11-23)
  - Der Sync ändert nur Verknüpfungen, nie Items selbst (Zuschnitt) (2026-11-23)
  - Der Teilnehmer rechnet mit den Regeln der Domäne und schreibt über die Ports, statt `AssignmentService`/`MapService` aufzurufen, weil deren Dienste eigene Transaktionen öffnen (2026-11-24)
  - Fremdes Projekt, Papierkorb und falsche Art eines Verweises sind `rule_violation`, ein unbekannter Verweis `unknown_reference`, beide mit Datei und Zeile (2026-11-24)
  - `Removed:` ist das Gedächtnis der Datei: nicht mehr genannte Zeilen werden vergessen, solange der Knoten nicht wieder in der Liste steht; Kinder unter einem entfernten Knoten werden abgewiesen (2026-11-24)
  - Papierkorb einer Map aus den Dateien nutzt `trash_map` der API und führt nie zum endgültigen Löschen (2026-11-24)
- References: Spec `TASK-081_spec.md`; Story `STORY-105`; Code `server/src/viewer/plugins/mindmap/infrastructure/mirror/participant.py`, `domain/listing.py`, `application/maps.py` (`trash_map`); Tests `test_mindmap_mirror_links.py`, `test_mirror_placements.py`; Doku `docs/techdocs/interfaces.md`, `neubau-server.md`

State confirmed after entry 2026-11-24 — Umsetzung (a9e8128d8a89)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-105

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-105 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-105_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Die Zuordnung steht auf dem Knoten, nicht im Item, weil die Dateien der Items dem Harness gehören (Zuschnitt)
- Der Sync ändert nur Verknüpfungen, nie Items selbst (Zuschnitt)

### Open

- Nichts.

## 2026-11-24 — Umsetzung

### Discussed

- Die Spec nennt `AssignmentService.assign_item`/`link_memo`. Deren Dienste öffnen eigene Transaktionen, der Sync bringt seine mit (wie schon bei `BranchService` in `TASK-080`). Option A: Dienste aufrufen (verschachtelte Transaktionen, geht nicht). Option B: dieselben Regeln der Domäne (`check_assign`) und die Ports `Links`/`ElementRegistry` in der Transaktion des Sync. Gewählt: B. Die Regel „ein Item an höchstens einem Knoten“ gilt dadurch unverändert.
- Ein Item, das in den Dateien den Knoten wechselt, steht zugleich in zwei Knotendateien. Darum schreibt der Teilnehmer erst alle gelösten, dann die neuen Zuordnungen. Hängt ein Item in der Datenbank an A und die Datei nennt es bei B, ohne dass A in den Dateien geändert wurde, ist das ein `rule_violation` (nichts wird ersetzt).
- Ein Verweis auf ein Element eines anderen Projekts (`Projekt:LABEL`) ist bekannt, aber nicht zuordenbar, wie in der API (`mindmap_other_project`); unbekanntes Projekt oder Label ist `unknown_reference`.
- `Removed:`: Zeilen, die die Datei nicht mehr nennt, werden vergessen (die Datei ist für den Baum maßgeblich), sonst ließe sich eine entfernte Platzierung nie aus den Dateien löschen. Zeilen im Baum und im Codec sind nach Knoten sortiert, sonst vergliche der Sync verschieden geordnete, gleiche Inhalte als geändert.
- Ein entfernter Knoten mit lebenden Kindern im Baum wäre ein Baum ohne Parent: wird mit `rule_violation` abgewiesen (der ganze Ast gehört unter `Removed:`).
- Ein Parent unter `Removed:`, den es nicht mehr gibt, wird beim Schreiben zur Wurzel (`-`).
- Papierkorb: `trash_map` (neu, `application/maps.py`) ist die Regel von `MapService.delete_map`, jetzt auch vom Sync genutzt; das Zurückholen läuft über `MapTrash.restore` samt Namensprüfung. Die Knotendateien tragen ihr eigenes `Deleted:`; fehlt es bei den Knoten, die nur in der Map stehen, zieht die Datenbank sie mit und der nächste Sync schreibt es in die Dateien.
- Löschen: Dokumente haben keinen Papierkorb. Eine gelöschte Datei ist ein Konflikt, erst die Entscheidung „Dateien“ löscht in der Datenbank (`DocumentRepository.delete`, neu); das endgültige Löschen eines Knotens trägt der Sync bereits in die Dateien, wenn sie unverändert sind (Test).

### Decided

- Der Teilnehmer nutzt die Regeln der Domäne und die Ports statt der Dienste (Transaktion des Sync)
- Fremdes Projekt, Papierkorb und falsche Art sind `rule_violation`, Unbekanntes `unknown_reference`, jeweils mit Datei und Zeile
- `Removed:` ersetzt das Gedächtnis; Kinder unter einem entfernten Knoten werden abgewiesen
- Papierkorb einer Map aus den Dateien nutzt `trash_map`; nie endgültiges Löschen
- Bekannte Grenze: der Sync meldet keine SSE-Ereignisse der Mindmap (`mindmap.node.changed`); die Oberfläche lädt nach dem Sync über dessen Statusereignis neu (Umfang von `TASK-082`, falls die Oberfläche es braucht)

### Open

- Nichts.
