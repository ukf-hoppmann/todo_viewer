# STORY-043 — Spec: Archiv und Papierkorb für Notes

## Was und warum
Notes sollen sich wie Backlog-Items aufräumen lassen, ohne dass etwas endgültig verloren geht. Die Regeln folgen dem Backlog (`domain/trash.py`, Archiv-Verschiebung).

## Regeln
- **Archiv:** `done`, `dropped` und `promoted` sind Endzustände. Eine Note in einem Endzustand liegt im Archiv und taucht nicht mehr in Fällig-Listen und im Standard-Index auf. Das Archiv ist abfragbar (Filter).
- **Papierkorb:** Löschen verschiebt Note oder Topic in den Papierkorb, mit Datum. Ein Topic mit Notes lässt sich nur mit Kaskade löschen (wie Items mit Kindern, `--cascade`-Prinzip).
- **Wiederherstellen:** aus Archiv und Papierkorb. Eine wiederhergestellte Note wird wartend, mit neuem Prüf-Datum. Ein Topic wird nur wiederhergestellt, wenn sein Eltern-Topic existiert.
- **Endgültig löschen:** nur der Besitzer, in der UI; nicht über die API für Claude (wie beim Backlog).
- Labels gelöschter Notes werden nie wieder vergeben.

## Betroffene Dateien
`domain/notes.py` (Lebenszyklus), `application/services/notes.py`, `infrastructure/database/notes.py`, `api/v2/`.

## Abnahme
- Lebenszyklus, Archiv, Papierkorb, Kaskade und Wiederherstellen sind per Test abgedeckt.
- Endgültiges Löschen gibt es nur in der Besitzer-Funktion.
