# STORY-025 Spec: Doku und Release

Gemeinsame Festlegungen: siehe `EPIC-003_spec.md`.

## Umfang

- `README.md` und `docs/techdocs/{architecture,interfaces,configuration,operations}.md`: Backend-Wahl je Projekt, `storage_url` in `config.json`, Schema und Migrationen, Sicherung der DB-Datei, Sync (Vorschau, Bestätigung, `delete_missing`), Fehlercodes, neue Endpunkte, Docker-Volume für `configs/`.
- Tagesbericht (`docs/daily/`), Release über den Skill `claude-harness:semver` (voraussichtlich 0.3.0).
- Eigenmigration: das Backlog dieses Projekts probeweise in die DB übernehmen (`from_md`) und mit `to_md` zurückprüfen; Ergebnis im Tagesbericht festhalten. Danach entscheidet der Projekteigner, welches Backend dieses Projekt dauerhaft nutzt.

## Abnahme

Doku entspricht dem Ist-Zustand; Release-Tag gesetzt; Probe-Migration dokumentiert.
