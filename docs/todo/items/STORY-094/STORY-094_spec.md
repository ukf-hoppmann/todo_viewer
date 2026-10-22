# STORY-094 — Spec: Notiz- und Spec-Dokumente löschen

## Ziel

Ein Notiz- oder Spec-Dokument eines Items lässt sich löschen. Gelöscht wird in den Papierkorb; von dort lässt es sich
wiederherstellen oder endgültig löschen. Anlass: Eine Notiz wurde beim falschen Item eingetragen und konnte nur geleert,
nicht entfernt werden.

## Verhalten (entschieden)

- **Was gelöscht wird:** immer ein ganzes Dokument, über seinen Namen:
  - die Notiz `<ID>_notes.md` (ein Item hat höchstens eine),
  - die Haupt-Spec `<ID>_spec.md` oder eine Themen-Spec `<ID>_spec_<thema>.md`; alle Specs werden gleich behandelt.
- **Notiz:** Mit der Notiz gehen ihr Kopf (`## State`) und die Kurzfassung (`summary`) des Items. Damit bleibt die
  Regel erfüllt, dass ein Item mit Notiz eine Kurzfassung braucht.
- **Spec:** Das Löschen einer Spec hat keine weiteren Folgen.
- **Papierkorb:** Ein gelöschtes Dokument ist nicht weg, sondern liegt im Papierkorb. Es taucht in Listen und
  Abfragen des Items (Dokumentliste, `show`, Notiz-Kopf, Einträge) nicht mehr auf, als hätte es das Dokument nie gegeben.
  Danach kann eine neue Notiz bzw. eine Spec mit demselben Namen angelegt werden.
- **Wiederherstellen:** Das Dokument kommt mit seinem Inhalt zurück, eine Notiz zusätzlich mit Kopf und der
  Kurzfassung, die das Item beim Löschen hatte.
- **Endgültig löschen:** nur im Papierkorb, nach einem Backup der Datenbank, und wie bei Items sofort in die
  Spiegel-Dateien übertragen (Architektur §2). Wird ein Item endgültig gelöscht, gehen seine Dokumente im Papierkorb mit.
- **Versionsschutz:** Löschen nimmt die Version des Dokuments; ist es inzwischen geändert, gibt es `version_conflict`.

## Schnittstellen

- Operation „Dokument löschen“ (in den Papierkorb) für API und MCP, z. B. `DELETE /api/backlog/items/{ref}/documents/{name}`
  mit Version.
- Wiederherstellen über API und MCP; endgültiges Löschen nur über die API/Oberfläche, nicht als MCP-Werkzeug
  (Architektur §3).
- Harness-Helfer `backlog_api.py`: neuer Befehl `delete-doc <ID> <name> <version>`; Harness-Skill `api.md` beschreibt ihn.
- Doku: API-Beschreibung in `docs/techdocs/interfaces.md`, Papierkorb und Spiegel in `docs/techdocs/neubau-server.md`.

## Offen

- Wie ein Dokument im Papierkorb in den Spiegel-Dateien aussieht (Datei entfernen oder als gelöscht markieren).
- Wo gelöschte Dokumente im Papierkorb der Oberfläche erscheinen und wie der Papierkorb des Workspace-Plugins
  Einträge aufnimmt, die keine Elemente sind.
- Verhalten beim Wiederherstellen, wenn inzwischen ein Dokument mit demselben Namen existiert oder das Item selbst im
  Papierkorb liegt.
