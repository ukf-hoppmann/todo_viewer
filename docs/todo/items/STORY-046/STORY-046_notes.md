# STORY-046 — Doku und Release für Notes und Topics

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Umfang der Doku
- Stand des Harness-Prompts

### Decided

- Die Doku folgt dem Stand nach der Umsetzung; der Harness-Prompt wird vor der Weitergabe angepasst.

### Open

- Der Besitzer klärt Befugnisse und Hooks im Harness; die Doku verweist darauf.

## 2026-10-08 — Umsetzung

### Discussed

- Stand der Techdocs gegen den Code geprüft: Architektur, Schnittstellen, Konfiguration und README waren durch die vorigen Storys schon aktuell

### Decided

- Ergänzt wurde der Betriebsteil zu Notes in operations.md (Speicherort und Sicherung, Zeitzone, kein Takt, nicht erreichbare Projekte)
- Kein Release: nur Doku geändert, v0.8.0 trägt die Notes-Funktionen schon (Regel semver: none)

### Open

- docs/notes-harness-prompt.md existiert nicht im Repository und konnte nicht angepasst werden; der Besitzer liefert die Datei oder streicht den Punkt
- Die Spec nennt eine neue Minor-Version; der Besitzer entscheidet, ob er trotzdem ein Release will
