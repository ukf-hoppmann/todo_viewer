# STORY-063 — Infrastruktur Datenbank: Migrationen je Plugin, Transaktionen, Backups

## 2026-10-16 — Entscheidungen

### Decided

- Die DB speichert rein relational; das Schema ist fest, keine freien Zusatzfelder. Neues kommt als Schemaänderung.
- Jedes Plugin hat eigene Tabellen und Migrationen; Fremdschlüssel nur auf Plugins aus requires.
