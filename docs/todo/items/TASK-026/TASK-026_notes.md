# TASK-026 — Notes in den gemeinsamen Sync aufnehmen

## 2026-10-14 — Umbau auf den gemeinsamen Sync

### Decided

- Kein eigener Notes-Sync mehr (keine notes-sync-Routen, keine Tabelle notes_sync_state, keine eigenen Richtungen und Kollisionsentscheidungen): Notes laufen im bestehenden Sync mit dem Stand je Eintrag und den Entscheidungen Datenbank, Datei oder aufschieben aus STORY-057.
- Label-Kollisionen entfallen als Sonderfall, weil nur die Datenbank Labels vergibt (Notes ohne Label aus der Cloud).
- Neue Abhängigkeit auf TASK-033.
