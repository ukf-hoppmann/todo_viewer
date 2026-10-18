# STORY-006 — Notizen

## 2026-09-28 — Umsetzung

### Decided

- `PATCH` nimmt mehrere Felder auf einmal (`{version, fields, resolution?}`),
  damit zusammengehörige Änderungen wie `parent` und `required_for_parent`
  gemeinsam geprüft und geschrieben werden.
- Unbekannte Felder im Request werden abgelehnt statt ignoriert, damit ein
  Tippfehler eines Agenten nicht still verloren geht.
- Die Felder werden in fester Reihenfolge verarbeitet, damit die Datei
  deterministisch geschrieben wird.
- Zwei neue Regeln: Verweise auf unbekannte IDs (`unknown_reference`) und
  Summary als Pflicht, sobald Notes existieren
  (`summary_required_with_notes`).
- Neue Felder werden wie bisher am Ende des Eintrags eingefügt; die
  bestehenden Golden-Dateien bleiben byte-gleich.

### Open

- Die UI bearbeitet weiterhin nur Status, Priorität und Pflicht für Parent;
  die übrigen Felder kommen mit `EPIC-002`.
