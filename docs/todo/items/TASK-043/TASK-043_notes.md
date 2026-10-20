# TASK-043 — Notes zerlegt speichern: Tabellen, Migration, bisherige Endpunkte und Spiegel

## 2026-10-20 — Umsetzung abgeschlossen, Probelauf auf einer Kopie der echten Datenbank

### Discussed

- Umgesetzt im Worktree TASK-043: domain/notes.py (Zerlegen, Zusammensetzen, verlustfreies Zerlegen, Regel für PUT), Migration v3 mit backlog_notes und backlog_notes_entries, SqlNotesRepository, DocumentService und Typwechsel über die neuen Tabellen, Spiegel-Teilnehmer und Codec, Altdaten-Übernahme.
- Probelauf der Migration auf einer Kopie von configs/viewer.db: 313 Notes vorher und nachher, keine Abweichung, kein Rückfall in den Vorspann, Specs unverändert (167), Integritätsprüfung ok.
- Der Probelauf zeigte 55 Notes mit einer Titelzeile, die nicht zum Item passt (z. B. `— Notizen`, Halbgeviertstrich, altes Label). Mit dem Titel aus der Datei im Vergleich hätte das nach dem Update 55 Konflikte gegeben.
- Sync-Vorschau aller Spiegel-Projekte auf der migrierten Kopie: alle in_sync ohne Übertragungen; nur ezf-ui hat einen Konflikt (STORY-012_notes.md deleted_in_files), den es heute schon gibt.

### Decided

- Die Titelzeile ist im Spiegel abgeleitet und wird nicht verglichen: beim Einlesen gilt der Titel des Items aus TODO.md; abweichende alte Titelzeilen werden beim nächsten Schreiben der Datei erneuert, kein Massenlauf über die Repos.
- Statt eigener Golden-File-Ordner decken byte-genaue Erwartungen in den Spiegel-Tests die Notes-Fälle ab.
- Bestehender Test zum Typwechsel angepasst: die Titelzeile folgt jetzt dem neuen Label (behebt den Fehler mit `# TASK-020`).

### Open

- Zwei mypy-Fehler außerhalb der Änderung (import_legacy/writer.py:99, tests/helpers/server/mirror_plugin/plugin.py:98) und der Abbruch von check-next.sh an doppelten Modulnamen test_client_log bestehen schon auf main.
- Container erst nach Rückfrage beim Owner aktualisieren (mit frischem, geprüftem Backup).
