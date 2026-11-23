# STORY-106 — Area durch die Mindmap ersetzen

## State

- Goal/Status: Geplant und in Tasks geschnitten; die Specs der Tasks sind geschrieben; läuft vor `STORY-103`.
- Next step: Tasks in der Reihenfolge der Abhängigkeiten umsetzen, jede in eigener Session mit Plan; erste Tasks sind `NEW-area-mirror-v3` und `NEW-area-optional`.
- Open:
  - Nichts offen für die Planung (2026-11-23)
- Decided:
  - Das Feld Area entfällt ganz, ohne abgeleiteten Ersatzwert und ohne Zwischenzustand als Endlösung (2026-11-23)
  - Die Schichten Web-UI und Backend-API sind keine eigene Einordnung mehr; der Owner braucht sie nicht, wenn der Baum gut ist (2026-11-23)
  - Der Themenbaum wird nicht von Hand aufgebaut und nicht mechanisch aus den Areas erzeugt, sondern von einer KI aus den vorhandenen Items; der Owner bekommt dafür nach der Umsetzung einen fertigen Prompt (2026-11-23)
  - Das Feld wird direkt entfernt, nicht erst nach dem Erzeugen der Bäume; ein Import einer Markdown-Datei mit dem Feld darf nicht abstürzen, das Feld wird ignoriert (2026-11-23)
  - Die KI baut den Baum aus Titel, Ziel und Text der Items; die alten Area-Werte sind kein Hinweis mehr (2026-11-23)
  - Kriterien 1 bis 3 und Ziel sind entsprechend angepasst (2026-11-23)
  - Format Version 3 des Backlog-Dateiformats ohne Area; Version 2 und 3 werden gelesen, Area wird ignoriert (Owner) (2026-11-23)
  - Kriterium 4 lautet: Dokumentation angepasst und fertiger Prompt für Claude_Harness (Owner) (2026-11-23)
  - Zuschnitt in fünf Tasks: Spiegel Version 3, Area optional, Oberfläche ohne Area, Area aus Server und Datenbank entfernen, Prompts (2026-11-23)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Zuordnung und wirksamer Knoten in `STORY-100_spec.md`; Tasks `NEW-area-mirror-v3`, `NEW-area-optional`, `NEW-area-client`, `NEW-area-remove-server`, `NEW-area-prompts`

State confirmed after entry 2026-11-23 — Zuschnitt in Tasks und Format Version 3 (4c724fac9162)

## 2026-11-23 — Art des Ersatzes und Aufbau der Bäume

### Discussed

- Frage: Was wird aus dem Feld Area, wenn die Mindmap die Einordnung übernimmt?
- Option A: Feld entfällt ganz; eine Wahrheit, aber Anzeige, Filter, API, MCP und Spiegel müssen umgebaut werden.
- Option B: Area bleibt als aus dem Knoten abgeleiteter Wert; bestehende Stellen laufen weiter, aber zwei Begriffe für dasselbe und ein Zwischenzustand, der bald überholt wäre.
- Option C: Area bleibt als freies Feld; widerspricht dem Epic-Beschluss, dass die Mindmap Area ersetzt.
- Erste Empfehlung war B als Übergang mit A als Ziel. Der Owner will eine dauerhaft gute Lösung statt eines Zustands, der bald überholt ist. Neue Empfehlung: A, ohne Zwischenstufe.
- Unterfrage: Die heutigen Areas sind Schichten (Web-UI, Backend-API), keine Themen. Option a: Schicht fällt weg; Option b: Schicht bleibt als Oberthema im Baum.
- Der Owner braucht die Schichten nicht, wenn der Baum gut erstellt wurde, und will den ersten Baum nicht von Hand bauen.

### Decided

- A, mit Option a: Area entfällt ganz, die Schichten fallen weg. Wo Area stand, zeigt die Oberfläche den Namen des Themas, und der Filter schließt Unterthemen ein.
- Der Baum entsteht durch eine KI aus den vorhandenen Items; der Owner bekommt nach der Umsetzung einen fertigen Prompt, mit dem er in die Projekte geht. Die KI führt den Umbau nicht selbst aus.
- Verworfen: B, weil sie ein Übergang wäre, der bald überholt ist; C, weil sie dem Epic-Beschluss widerspricht; die mechanische Umwandlung jeder Area in einen Knoten, weil die Schichten als Themen nichts taugen.

### Open

- Reihenfolge: Das Feld bleibt lesbar, bis die Bäume erzeugt sind, und wird danach entfernt (Vorschlag).

## 2026-11-23 — Reihenfolge: Feld sofort entfernen

### Discussed

- Vorschlag war: Das Feld bleibt lesbar, bis die Bäume erzeugt sind, und wird danach entfernt, damit die KI die alten Areas als Hinweis lesen kann.
- Der Owner: Das Feld kann direkt raus, das ist am sinnigsten. Es darf nur nicht abstürzen, wenn eine Markdown-Datei mit dem Feld importiert wird.
- Folge: Die alten Area-Werte gehen mit dem Entfernen verloren; die KI baut den Baum aus Titel, Ziel und Text der Items. Items selbst gehen nicht verloren.

### Decided

- Das Feld wird direkt entfernt. Ein Import mit dem Feld wird toleriert (Feld ignorieren, kein Fehler).
- Verworfen: Das Feld erst nach dem Erzeugen der Bäume zu entfernen, weil es eine Zwischenstufe wäre.

### Open

- Offen für die Planung ist nichts mehr.

## 2026-11-23 — Zuschnitt in Tasks und Format Version 3

### Discussed

- Das Backlog-Dateiformat gehört Claude_Harness, dessen Prüfung verlangt heute Area in jedem Eintrag. Der Owner wählt: Format Version 3 ohne Area, Version 2 und 3 werden gelesen, Area wird in beiden ignoriert; eine alte Prüfung meldet dann „anderes Format“ statt vieler Einzelfehler.
- Kriterium 4 wurde wie bei `STORY-104` und `STORY-105` auf „fertiger Prompt für Claude_Harness“ geändert; der Owner hat zugestimmt.
- Beim Zuschnitt zeigte sich: Es gibt heute keinen Filter nach Area, und das Thema eines Items steht schon im Abschnitt „Knoten“ der Mindmap im Detail. Kriterium 1 wurde entsprechend berichtigt (kein Filter, keine Spalte, Anzeige im Abschnitt „Knoten“); der Owner prüft die Berichtigung.
- Damit Server und Oberfläche getrennt gebaut werden können, ohne dass der Build bricht, wird Area in drei Schritten entfernt: Area optional, Oberfläche ohne Area, Feld ganz entfernen. Der mittlere Zustand lebt nur während der Umsetzung.
- `STORY-106` läuft vor `STORY-103` und `STORY-104`: danach verlangt das Anlegen aus einem Knoten kein Area mehr.

### Decided

- Fünf Tasks mit Specs und Notes angelegt; Kriterium 4 und Kriterium 1 angepasst

### Open

- Der Owner prüft die Berichtigung von Kriterium 1 (kein Filter nach Thema).
