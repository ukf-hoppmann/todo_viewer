# STORY-005 — Notizen

## 2026-09-28 — Entwurf

### Discussed

- Bestehende Backlogs können Regelverstöße schon enthalten (z. B. von Hand
  bearbeitet). Eine strikte Prüfung würde dann jede Bearbeitung blockieren.
- Regeln betreffen oft ein anderes Item als das bearbeitete: Wird ein Kind
  unter einem abgeschlossenen Parent wieder geöffnet, verletzt der Parent
  die Regel.

### Decided

- Die Regeln werden im Domain (`lifecycle.py`) als Verstöße über den ganzen
  Backlog berechnet. Abgelehnt wird eine Änderung nur, wenn sie einen neuen
  Verstoß erzeugt oder einen bestehenden um weitere Items erweitert.
  Altlasten blockieren nicht; Änderungen, die Verstöße verringern, bleiben
  erlaubt.
- Verstöße liefern 409 mit dem Regel-Code, `details.id` (betroffenes Item)
  und `details.items` (auslösende Items).
- „Epic braucht Pflichtkind vor Verlassen von Open“ gilt für In progress,
  Awaiting confirmation und Completed, nicht für Rejected: Ein leeres Epic
  muss ablehnbar bleiben.
- Als Pflichtkind zählt nur `Required for parent: Yes`; fehlt das Feld bei
  einem Item mit Parent, ist das ein eigener Verstoß.

## 2026-09-28 — Umsetzung abgeschlossen

### Decided

- Die Regeln liegen in `domain/lifecycle.py`; der `ItemService` lädt den
  Backlog einmal, berechnet das Item nach der Änderung und prüft vorher gegen
  nachher, bevor geschrieben wird.
- Der bisherige Golden-Fall „erstes Epic abschließen“ verstößt jetzt gegen
  die Regeln. Die Dateimechanik dieses Falls wird deshalb direkt am Adapter
  mit derselben Golden-Datei geprüft; über die API wird die Ablehnung
  geprüft.

### Open

- Struktur- und Zyklusregeln greifen erst mit `STORY-006` und `STORY-007`
  (Parent, Dependencies und Anlegen sind heute noch nicht bearbeitbar).
