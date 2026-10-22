# STORY-094 — Spec: Notiz- und Spec-Dokumente löschen

## Ziel

Ein Notiz- oder Spec-Dokument eines Items lässt sich löschen. Gelöscht wird in den Papierkorb; von dort lässt es sich
wiederherstellen oder endgültig löschen. Anlass: Eine Notiz wurde beim falschen Item eingetragen und konnte nur geleert,
nicht entfernt werden.

## Verhalten

- **Was gelöscht wird:** immer ein ganzes Dokument, über seinen Namen:
  - die Notiz `<ID>_notes.md` (ein Item hat höchstens eine),
  - die Haupt-Spec `<ID>_spec.md` oder eine Themen-Spec `<ID>_spec_<thema>.md`; alle Specs werden gleich behandelt.
- **Notiz:** Mit der Notiz gehen ihr Kopf (`## State`) und die Kurzfassung (`summary`) des Items. Damit bleibt die
  Regel erfüllt, dass ein Item mit Notiz eine Kurzfassung braucht.
- **Spec:** Das Löschen einer Spec hat keine weiteren Folgen.
- **Papierkorb:** Ein gelöschtes Dokument ist nicht weg, sondern liegt im Papierkorb. Es taucht in Listen und
  Abfragen des Items (Dokumentliste, `show`, Notiz-Kopf, Einträge) nicht mehr auf. Danach kann eine neue Notiz bzw.
  eine Spec mit demselben Namen angelegt werden.
- **Versionsschutz:** Löschen nimmt die Version des Dokuments; ist es inzwischen geändert, gibt es `version_conflict`.
  Ein Item im Papierkorb hat keine löschbaren Dokumente (wie bei anderen Änderungen an gelöschten Items).

## Papierkorb

- Gelöschte Dokumente erscheinen als eigene Einträge im zentralen Papierkorb, neben den Items, z. B. „Notiz zu
  STORY-012“ bzw. „Spec STORY-012_spec_api.md“, mit Item, Dokumentname und Löschzeitpunkt.
- Der Papierkorb gehört dem Workspace-Plugin und kennt bisher nur Elemente. Er bekommt eine Erweiterung, über die ein
  Plugin eigene Papierkorb-Einträge beisteuert (auflisten, wiederherstellen, endgültig löschen). Das Backlog-Plugin
  meldet darüber seine Dokumente an. Die Erweiterung ist allgemein, damit andere Plugins sie später nutzen können
  (Architektur §1).
- **Wiederherstellen:** Das Dokument kommt mit seinem Inhalt zurück, eine Notiz zusätzlich mit Kopf und der
  Kurzfassung, die das Item beim Löschen hatte. Abgewiesen wird es,
  - wenn das Item inzwischen ein gleichnamiges Dokument hat (`document_exists`; bei der Notiz: irgendeine Notiz),
  - solange das Item selbst im Papierkorb liegt (erst das Item wiederherstellen).
- **Endgültig löschen:** nur im Papierkorb, nach einem Backup der Datenbank. Wird ein Item endgültig gelöscht, gehen
  seine Dokumente im Papierkorb mit.
- Wird ein Item in den Papierkorb gelegt und wiederhergestellt, bleiben seine einzeln gelöschten Dokumente im
  Papierkorb; sie kommen nur einzeln zurück.

## Spiegel

- Kommt ein Dokument in den Papierkorb, wird seine Datei sofort aus den Spiegel-Dateien entfernt, ohne Konflikt,
  sofern sie seit dem letzten Abgleich unverändert ist; ist sie geändert, bleibt es ein Konflikt
  (`deleted_in_database`). Das geht über denselben Weg wie das endgültige Löschen von Items
  (`SyncService.carry_purged`), nicht über eine Formatänderung. Architekturregel §2 ist dafür erweitert.
- Das Dateiformat (Version 2) ändert sich nicht: Ein Dokument im Papierkorb hat keine Datei.
- Wiederherstellen legt das Dokument in der Datenbank wieder an; der nächste Abgleich schreibt die Datei wie jedes
  neue Dokument (auch der automatische Abgleich).
- Endgültiges Löschen eines Dokuments ändert die Dateien nicht mehr; die Datei ist schon weg.

## Schnittstellen

- Backlog-Operation „Dokument löschen“ (in den Papierkorb) für API und MCP:
  `DELETE /api/backlog/items/{ref}/documents/{name}` mit Version; Fehler `document_not_found`, `version_conflict`.
- Wiederherstellen über die Papierkorb-Operationen (API und MCP); endgültiges Löschen nur über API und Oberfläche,
  nicht als MCP-Werkzeug (Architektur §3).
- Ereignisse an die Oberfläche wie bei anderen Dokumentänderungen, damit Detailansicht und Papierkorb neu laden.
- Oberfläche: Löschen-Aktion je Dokument in der Detailansicht des Items (IconButton mit Tooltip, mit Rückfrage).
- Harness-Helfer `backlog_api.py`: neuer Befehl `delete-doc <ID> <name> <version>`; der Harness-Skill `api.md`
  beschreibt ihn, ebenso wie Wiederherstellen eines Dokuments.
- Doku: API-Beschreibung in `docs/techdocs/interfaces.md`, Papierkorb und Spiegel in `docs/techdocs/neubau-server.md`.
