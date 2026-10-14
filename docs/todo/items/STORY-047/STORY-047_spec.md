# STORY-047 — Spec: Notes als Markdown exportieren, importieren, abgleichen

## Was und warum
Notes leben in API und Datenbank. Die Markdown-Spiegelung ist eine Option, vor allem damit Claude Notes auch dort nutzen kann, wo der Viewer nicht erreichbar ist (Cloud), und damit Rechner abgleichen können. Es ist kein Normalbetrieb.

## Regeln (aus den Regeln für Spiegel in architecture.md §1)
- Der Abgleich ist ein ausdrücklicher Sync, nie automatisch und nie durch einen normalen Request. Er bietet eine Vorschau, löscht nichts ohne Bestätigung und lässt die Richtung wählen.
- Der Sync ist ein Use Case in `application` auf zwei Ports, keine Logik im Adapter.
- Ob sich der Spiegel seit dem letzten Sync geändert hat, ist ohne Änderung erkennbar.
- Eine Datei wird atomar geschrieben (temporäre Datei plus Umbenennen) und bricht mit Konflikt ab, wenn sie sich geändert hat.

## Format (Vorschlag)
- Pro Projekt ein Ordner `notes/` im Spiegel-Ordner. Pro Note eine Datei `NOTE-001.md` mit Kopfzeilen (Kurzfassung, Status, Topic als Pfad, Prüf-Datum, Auslöser, Modus, Links als `Projekt:Label` mit Rolle) und dem Langtext als Inhalt; Notizen und Specs als Dateien daneben (`NOTE-001_notes.md`, `NOTE-001_spec.md`). Die Topics stehen in einer Datei `topics.md` mit Baum, Termin und Label.
- Links sind Verweise auf Labels, nie auf `uid`.
- Beim Import vergeben fehlende Labels der Zielumgebung neue Labels; bei Kollisionen entscheidet die Vorschau.

## Betroffene Dateien
`domain/sync.py`, `application/services/sync.py`, neuer Notes-Spiegel-Adapter in `infrastructure/markdown/`, Einstellungsdialog `SyncDialog.tsx`.

## Abnahme
- Round-Trip ohne Verlust von Text, Notizen, Specs, Links, Auslösern und Terminen (Golden-File-Tests).
- Der Sync hat Vorschau, Richtungswahl und Konfliktabbruch wie der Backlog-Sync.
