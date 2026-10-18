# STORY-042 — Spec: Beförderung und Rückstufung

## Was und warum
Eine Note kann zu Arbeit werden, und ein noch nicht begonnenes Item kann zur Notiz zurückgehen. Beide Seiten behalten ihre eigene ID; die Herkunft bleibt sichtbar. Notizen und Specs wandern mit, damit nichts verloren geht.

## Note → Item
- Der Aufrufer liefert Typ (Task, Story, Epic), Bereich, Ziel, Abschlusskriterien und Parent (soweit der Typ einen braucht). Die UI zeigt ein vorausgefülltes Formular (Titel und Zusammenfassung aus der Kurzfassung).
- Die Anlage läuft über denselben Weg wie jede Item-Anlage; alle Backlog-Prüfungen greifen (z. B. geschlossener Parent, `parent_closed`).
- Der Langtext, die Notizen und die Specs der Note werden Notizen und Specs des Items. Der Langtext wird als erster datierter Eintrag der Notizen übernommen; vorhandene Dokumente der Note werden unverändert angehängt oder angelegt.
- Die Note erhält Status `promoted`, geht ins Archiv und bekommt einen Link `origin` auf das neue Item.

## Item → Note
- Zulässig nur bei Status Open, ohne Kinder, und wenn das Item weder Parent noch Dependency eines anderen Items ist. Sonst lehnt der Viewer mit Grund ab (z. B. `demote_has_children`, `demote_referenced`, `demote_not_open`).
- Das Item wird mit Resolution „zur Notiz zurückgestuft" abgeschlossen; da die Rückstufung selbst die Entscheidung des Besitzers ist, braucht sie keine zweite Bestätigung des Status.
- Die neue Note übernimmt Titel und Zusammenfassung als Kurzfassung, die Notizen und Specs des Items als ihre Dokumente, und erhält den Link `origin` auf das Item.
- Das Item wird beim Abschließen archiviert (wie jedes abgeschlossene Item).

## Ablauf über zwei Speicher
Item und Note können in verschiedenen Speichern liegen (Primärquelle des Projekts kann Markdown sein, Notes liegen in der Datenbank). Es gibt keine gemeinsame Transaktion. Reihenfolge: zuerst die Seite anlegen, die neu entsteht, dann die alte Seite umstellen. Bricht der zweite Schritt ab, muss der Zustand erkennbar und wiederholbar sein (der Link `origin` ist der Beleg, der Vorgang idempotent). Das gehört in die Tests.

## Betroffene Dateien
`application/services/notes.py`, `items.py`, `domain/notes.py`, `domain/creation.py`, `domain/lifecycle.py`, `api/v2/`, UI-Dialog in `web/src/components/`.

## Abnahme
- Beide Richtungen funktionieren über API und UI; Herkunft ist an Note und Item sichtbar.
- Unzulässige Rückstufungen werden mit Grund abgelehnt (Testfälle je Grund).
- Notizen und Specs sind danach auf der Zielseite vorhanden; ein Abbruch zwischen den beiden Schritten hinterlässt keine verlorenen Daten.
