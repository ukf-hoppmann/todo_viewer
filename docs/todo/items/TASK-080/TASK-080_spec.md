# TASK-080 — Spec: Teilnehmer für Knoten und Bäume

Zu `STORY-105`. Der Codec (Task „Dateiformat und Codec“) und das Format stehen in `docs/techdocs/interfaces.md`,
Abschnitt „Mindmap-Dateien (Format Version 1)“. Dieser Schritt verbindet Datenbank und Einträge.

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Umfang

- `server/src/viewer/plugins/mindmap/infrastructure/mirror/participant.py` (`MindmapParticipant`) nach dem Muster von
  `memos/infrastructure/mirror/participant.py` und `backlog/infrastructure/mirror/participant.py`; das Protokoll
  `SyncParticipant` in `server/src/viewer/core/application/sync.py`:
  - `load(project)`: alle Knoten des Projekts (auch im Papierkorb) und alle Bäume (Projektbaum, freie Maps, auch
    gelöschte) als `MirrorEntry`, Verweise als aktuelle Labels.
  - `resolve_labels(project, labels)`: frühere Labels auf aktuelle abbilden (`workspace` führt den Verlauf).
  - `assign_labels(project, entries, tx, taken)`: für Platzhalter-Knoten das nächste freie `NODE-nnn` im Register
    reservieren (`workspace.registry`, wie `MemosParticipant`); neue Bäume bekommen nur eine Uid (Bäume haben kein
    Label).
  - `apply(project, changes, tx)`: schreibt in einer Transaktion Knoten über `MindmapService` und
    `SqlMindmapRepository` (`application/service.py`, `infrastructure/database/repository.py`), Bäume über
    `MapService` (`application/maps.py`), Platzierungen über `BranchService` (`application/branches.py`) bzw. die
    Regeln der Domain (`domain/tree.py`, `domain/branches.py`); die Regeln (ein Knoten höchstens einmal je Baum, kein
    Zyklus, Parent im selben Baum) gelten wie in der API und melden `rule_violation` mit Datei und Zeile.
- Registrierung: `plugin.py` bekommt `mirror=lambda services: MirrorBinding("mindmap", MindmapCodec(),
  services.participant)` wie `memos/plugin.py`; `MindmapServices` bekommt `participant`.
- Reihenfolge innerhalb von `apply`: Bäume, Knoten, Platzierungen (ein Knoten muss existieren, bevor ihn eine
  Platzierung nennt; ein neuer Baum, bevor Platzierungen in ihm stehen).
- Der Projektbaum entsteht beim ersten Zugriff (wie bisher); eine Datei `project.md` ohne Uid-Entsprechung in der
  Datenbank erzeugt keinen zweiten Projektbaum, sondern wird dem vorhandenen zugeordnet.
- Nicht in dieser Task: Zuordnungen, Dokumente, `Removed:`, Papierkorb-Zustand der Bäume (nächste Task). Der Sync darf
  in der Datenbank vorhandene Zuordnungen und Dokumente nicht löschen, weil die Dateien sie in dieser Stufe nicht
  tragen: der Teilnehmer lässt sie unberührt.
- Ephemere Einträge: nein (`ephemeral=False`).

## Tests

- Integration: `tests/implementation/integration/server/plugins/mindmap/test_mindmap_mirror.py` (Muster:
  `…/memos/test_memo_mirror.py`): Datenbank → Dateien (Golden-Vergleich), Dateien → Datenbank, neue Knoten und Maps
  aus Dateien, umgehängter Ast, übertragener Ast, Konflikt bei beidseitiger Änderung, Wiederholung ohne Änderung
  ergibt keinen Unterschied (`in_sync`).
- Contract: `tests/implementation/integration/server/contract/` (die Contract-Suite der Codecs und Teilnehmer; prüfen,
  wie die Memos eingebunden sind) um Mindmap ergänzen.
- Unit: Regeln beim Übernehmen von Platzierungen (Zyklus, doppelt im Baum) mit Fakes.

## Nicht Teil

Zuordnungen, Dokumente, entfernte Platzierungen, Papierkorb (nächste Task), Oberfläche.
