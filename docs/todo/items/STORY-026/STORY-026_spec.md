# STORY-026 Spec: Postgres (optional)

Gemeinsame Festlegungen: siehe `EPIC-003_spec.md`.

## Was und warum

Nur relevant, falls ein Server-Datenbanktyp gebraucht wird; für Einzelnutzer lokal genügt SQLite. Der DB-Adapter aus STORY-021 ist über SQLAlchemy vorbereitet, hier kommen Treiber und Dialekt-Unterschiede dazu. MariaDB ist bewusst nicht Teil.

## Umfang

- Treiber `psycopg` (v3) als optionale Abhängigkeit; `storage_url` z. B. `postgresql+psycopg://user:pass@host/db` (Zugangsdaten in `config.json`, wie festgelegt).
- Migrationen dialektneutral halten (UUID, Boolean, Text); Unterschiede (Autoinkrement/Sequenzen für `position`, `PRAGMA` nur bei SQLite) im Adapter kapseln.
- Contract-Suite und Migrationstests laufen zusätzlich gegen Postgres. Die Postgres-Tests werden übersprungen, wenn `TEST_POSTGRES_URL` nicht gesetzt ist; `docker-compose` bekommt ein optionales Profil mit Postgres.

## Abnahme

Contract-Suite grün für SQLite und Postgres; ohne Postgres laufen die übrigen Tests unverändert.
