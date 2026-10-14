# EPIC-006 — Markdown nicht mehr Normalbetrieb: Datenbank und API als Hauptanwendung

## 2026-10-08 — Anlage

### Discussed

- Der Besitzer will Markdown für das Backlog im Normalgebrauch abschaffen und die API zur Hauptanwendung machen; Markdown bleibt als Export, Import und Sync-Option.

### Decided

- Eigener Epic, getrennt von EPIC-005.

### Open

- Stories sind noch nicht angelegt.
- Umfang im Harness: Standard-Backend, Hooks und Skills, die TODO.md voraussetzen.
- Verhältnis zu den Primärquellen aus EPIC-004: bestehende Markdown-Projekte migrieren oder weiter unterstützen.
- Abhängigkeit zu STORY-047 (Notes-Export).

## 2026-10-14 — Stories für den Abgleich angelegt (2026-10-14)

### Decided

- STORY-057 (Abgleich pro Eintrag mit Konfliktmeldung, Pflicht) und STORY-058 (Konflikt-Dialog mit Diff-Ansicht) hängen unter diesem Epic, weil sie den Markdown-Abgleich für Cloud und Git verlustfrei machen.
- STORY-047 (Notes im Sync, unter EPIC-005) hängt von beiden ab.

### Open

- Verhältnis zu den Harness-Änderungen (Dateimodus in der Cloud) bleibt beim Besitzer.
