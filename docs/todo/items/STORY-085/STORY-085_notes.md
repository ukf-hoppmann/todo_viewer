# STORY-085 — Serienwecker: Wiederholung am Wecker

## 2026-10-19 — Planung Serienwecker

### Discussed

- Kriterium 2 (Vorrücken beim Erledigen oder Fälligwerden) gegen das heutige Due; Monatsende; Zeitzone; verpasste Termine; Serie und Elemente

### Decided

- Beim Fälligwerden bleibt Due; erst beim Erledigen rückt at auf den ersten Termin nach jetzt vor, gerechnet ab dem Fälligkeitstermin. Ein Serienwecker wird nie Done, Rückgängig entfällt.
- Die Serie speichert ihren Startpunkt (series_from); Termine werden davon aus berechnet und am Monatsende gekürzt (31. -> 28. Feb -> 31. Mär).
- Verpasste Termine werden aus at, repeat und jetzt abgeleitet, nicht gespeichert.
- Expired beendet die Serie.
- Fehlt das Feld im Spiegel, gilt keine Wiederholung; Format Version 2 bleibt kompatibel.

### Open

- Zeitzone und Sommerzeit: Serie in einer gespeicherten Zeitzone rechnen; erst prüfen, wie at heute erfasst und gespeichert wird (UTC).

## 2026-10-19 — Zeitzone: die Zeit kommt vom Backend

### Discussed

- Ob der Browser seine Zeitzone mitschicken soll. Architektur §4: Zeiten in UTC speichern, in der Zone des Rechners zeigen und eingeben, auf dem der Viewer läuft.
- Der Container todo-viewer-next hat heute kein TZ und rechnet deshalb in UTC.

### Decided

- Kein Browser-Anteil und keine Zone je Wecker: gültig ist die Zeitzone des Rechners, auf dem das Backend läuft.
- Der Container bekommt TZ mit der Zone des Macs (über todo.sh bzw. .env) und tzdata im Image; damit kennt das Backend Sommer- und Winterzeit.
- Die Domain rechnet die Wiederholung in dieser Zone; die Zone kommt als Parameter in die reine Funktion. 11 Uhr bleibt 11 Uhr über die Umstellung.
- Gespeichert werden nur repeat und series_from.

## 2026-10-19 — Abschlusskriterien an die Spec angepasst

### Decided

- Abschlusskriterien auf Wunsch des Projektinhabers an die Spec vom 2026-10-19 angepasst.
