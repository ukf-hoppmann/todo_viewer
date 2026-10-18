# EPIC-003 — Wählbares Speicher-Backend: Markdown oder zentrale Datenbank

## 2026-09-30 — Abschluss: Abnahmekriterium zum Roundtrip angepasst, Stand des Epics

### Discussed

- Das Kriterium verlangte byte-gleiche Dateien beim Roundtrip md -> db -> md. Die Epic-Spec (Festlegung 3) und STORY-023 hatten das schon anders beschlossen: Der Export ist normalisiert, aber stabil. Die Probe-Migration (STORY-025) bestätigt das: gleiche Item-Versionen und Dokumentinhalte, Export -> Import -> Export byteidentisch; gegenüber der Handschrift sind Kopfzeilen, Zeilenumbruch und die Stellung von Notes/Spec normalisiert.

### Decided

- Der Projekteigner hat den Satz am 2026-09-30 angepasst: gleiche Items (gleiche Versionen) und Dokumente beim Roundtrip; Export -> Import -> Export ergibt identische Dateien.
- Alle Stories sind geschlossen: STORY-019 bis 025 und 027 abgeschlossen, STORY-026 (Postgres) vorerst verworfen. Releases: v0.3.0 (SQLite-Adapter), v0.4.0 (Projekte in der Datenbank), v0.5.0 (Sync), v0.5.1 (Backend-Wechsel per PUT), v0.6.0 (UI). Das Epic wartet auf die Bestätigung des Projekteigners.
