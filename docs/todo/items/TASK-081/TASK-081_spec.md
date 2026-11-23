# TASK-081 — Spec: Zuordnungen, Dokumente, entfernte Platzierungen und Papierkorb im Spiegel

Zu `STORY-105`; baut auf der Task „Teilnehmer für Knoten und Bäume“ auf (Format: `docs/techdocs/interfaces.md`,
„Mindmap-Dateien (Format Version 1)“).

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Umfang

- Zuordnungen: in der Datenbank die Verknüpfungen der Rolle `node` in `workspace_links` (`application/assignments.py`:
  `ROLE`, `AssignmentService`). Die Dateien nennen sie auf dem Knoten (`Items:`, `Memos:`). Beim Übernehmen aus Dateien
  über `AssignmentService.assign_item`/`link_memo` und die Löse-Operationen, nicht über SQL; die Regel „ein Item an
  höchstens einem Knoten“ gilt (ein Konflikt in den Dateien ist `rule_violation` schon beim Lesen, siehe Codec).
  Ein Item, das in den Dateien bei keinem Knoten mehr steht, wird gelöst (bleibt aber erhalten).
- Dokumente: Eintrag `mindmap.document` je Datei (`uid` = `<Knoten-uid>/<notes|spec|spec_…>`); Datenbank über
  `DocumentService` und `SqlDocumentRepository` (`application/documents.py`, `infrastructure/database/repository.py`).
  Löschung mit Absicht (Dokument in den Papierkorb legen) und das Backup davor: Architektur §2.
- Entfernte Platzierungen: `SqlMindmapRepository.mark_removed`, `removed_placements`, `removed_placements_of`
  (`application/ports.py`); `Removed:` im Baum (Format).
- Papierkorb: Knoten mit `deleted_at` (`workspace`-Register) und freie Maps (`Tree.deleted_at`, `MapService`,
  `MapTrash`); die Regeln des Papierkorbs (ein Ast wandert mit seinen Kindern; Items an gelöschten Knoten fallen an den
  Parent-Knoten zurück, sonst „Nicht zugeordnet“) bleiben die der API — der Sync ruft dieselben Dienste.
- Verweise: `resolve_labels` und `load` müssen Items (`EPIC-…`, `STORY-…`, `TASK-…`) und Memos (`MEMO-…`) des
  Projekts und, qualifiziert, anderer Projekte kennen (`workspace.registry`).
- Konflikte zwischen den Plugins: Der Mindmap-Sync darf nichts am Item selbst ändern (Items gehören dem Backlog),
  nur an der Verknüpfung.

## Tests

- Integration: `tests/implementation/integration/server/plugins/mindmap/test_mindmap_mirror_links.py`: Zuordnungen in
  beide Richtungen, Item bei zwei Knoten, unbekanntes Item, Item eines anderen Projekts, Dokumente schreiben, ändern,
  löschen, entfernte Platzierungen, Papierkorb eines Astes und einer Map, Rundlauf Datenbank → Dateien → leere
  Datenbank.
- Contract-Suite und Golden-Files der vorigen Tasks bleiben grün (Golden-Files ergänzen, Format nicht brechen).

## Nicht Teil

Oberfläche, Systemtest, Doku, Prompt (nächste Task).
