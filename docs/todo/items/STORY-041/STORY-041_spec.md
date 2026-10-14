# STORY-041 — Spec: Änderungshinweise zwischen Notes und Items

## Was und warum
Nichts darf still verschwinden. Ändert sich ein verlinktes Item oder eine verlinkte Note, bekommt die andere Seite einen Hinweis, der bleibt, bis jemand entscheidet.

## Hinweise
- **An der Note**, wenn ein verlinktes Item: abgeschlossen oder verworfen wird (bei Links mit Rolle `reference`; bei Rolle `trigger` entscheidet der Auslöser), gelöscht wird, im Typ geändert wird (der Link überlebt, die Note erfährt es), oder dessen Projekt nicht erreichbar ist.
- **Am Item**, wenn eine verlinkte Note verworfen oder befördert wird.
- **Optionen an der Note:** behalten (Link bleibt, Hinweis erledigt, Prüf-Datum neu), abkoppeln (Link entfernen), verwerfen, befördern (STORY-042). Am Item sind es: zur Kenntnis nehmen.
- Ein offener Hinweis macht die Note fällig (Grund `notice`) und erscheint im Modal des Ausrufezeichens (STORY-045).
- Hinweise sind Daten in der Datenbank: Ursache, betroffene Seite, Zeitpunkt, Entscheidung, Zeitpunkt der Entscheidung. Wer entscheidet, regelt der Harness; der Viewer erzwingt es nicht.

## Wo ausgelöst wird
In den bestehenden Use Cases für Statuswechsel, Löschen und `retype` sowie in der Projekt-Erreichbarkeitsprüfung (STORY-044). Kein Hintergrund-Takt.

## Betroffene Dateien
`domain/notes.py` (Hinweisarten), `application/services/items.py`, `retype.py`, `trash.py`, `application/services/notes.py`, `infrastructure/database/notes.py`.

## Abnahme
- Für jede genannte Änderung entsteht in beide Richtungen ein Hinweis (Testmatrix).
- Ein Hinweis bleibt bis zur Entscheidung; jede Option führt zum beschriebenen Zustand.
- Keine Note und kein Link verschwindet ohne Spur.
