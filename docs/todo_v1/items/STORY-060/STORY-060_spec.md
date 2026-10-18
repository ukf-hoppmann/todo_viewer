# `STORY-060` — Noch zu klären

Sammelstelle für offene Fragen zum Neubau (`EPIC-007`). Jede Frage hat eine
**Annahme**: Solange der Projektinhaber nicht anders entscheidet, setzt die
Umsetzung die Annahme um. Eine Antwort wird in den Notizen dieser Story
festgehalten und in die Spec des betroffenen Items übernommen. Neue Fragen aus
der Umsetzung kommen hier dazu, mit Annahme und betroffenem Item.

| # | Frage | Annahme | Betrifft |
|---|---|---|---|
| 1 | Heute gibt es Projekte mit Markdown als Primärquelle (Kennzeichen „MD“). Im Neubau ist die DB immer die Wahrheit. Ist das für alle Projekte in Ordnung? | Ja. Solche Projekte werden bei der Übernahme DB-Projekte mit Markdown-Spiegel. | `STORY-068`, `STORY-082` |
| 2 | Notes ohne Projekt (`STORY-048`): wie abbilden? | Ein eingebautes Projekt „Allgemein“ ohne Ordner nimmt sie auf. | `STORY-068`, `STORY-077` |
| 3 | Offene Items im Altcode (`EPIC-005` mit `STORY-041`, `STORY-048`, `STORY-054`, `STORY-055`, `STORY-056`; `EPIC-006`): noch im alten Viewer umsetzen? | Nein. Ihr Inhalt ist im Neubau abgedeckt (054/055 → `STORY-077`, 041 → `STORY-078`, 056 → `STORY-080`, 048 → Frage 2, EPIC-006 → `STORY-065`). Beim Umstieg werden sie mit Verweis abgelehnt (Entscheidung des Inhabers). | `STORY-084` |
| 4 | Freitext-Zusatzfelder alter Items (`Implementation`, `Verification`, `Context` …) entfallen im festen Schema. Was passiert mit ihrem Inhalt? | Er wird bei der Übernahme als datierter Eintrag „Übernommene Zusatzfelder“ in die Notiz des Items geschrieben. | `STORY-082` |
| 5 | Wiederholende Wecker (täglich, wöchentlich)? | Nicht im ersten Wurf. | `STORY-080` |
| 6 | Wie meldet sich ein fälliger Wecker? | Banner in der UI und Zähler in der Kopfzeile; zusätzlich eine Browser-Benachrichtigung, wenn der Browser sie erlaubt. | `STORY-080` |
| 7 | Zeit-Auslöser an Notes und Wecker überschneiden sich. | Zeit-Auslöser an Notes werden bei der Übernahme zu Weckern mit der Note als Ziel. Notes behalten Prüfdatum, Ereignis-Auslöser und Topic-Termin. | `STORY-078`, `STORY-080`, `STORY-082` |
| 8 | Auto-Sync: Takt oder Dateiüberwachung? | Takt wie heute (`AUTO_SYNC_INTERVAL`, Standard 30 s), nur solange mindestens ein Projekt Auto-Sync an hat. | `STORY-065` |
| 9 | Bereiche (`Area`) sind heute freier Text. Im festen Schema? | Eigene Tabelle `backlog_areas` je Projekt; neue Bereiche legt man wie heute im Feld an. | `STORY-071`, `STORY-072` |
| 10 | Was soll Drag & Drop können? | Items unter ein anderes Epic/eine andere Story ziehen (Parent-Wechsel mit Regelprüfung), Reihenfolge unter einem Parent ändern, Notes in ein anderes Topic und Topics unter ein anderes Topic ziehen. | `STORY-072`, `STORY-077` |
| 11 | Version des neuen Viewers beim Umstieg? | `1.0.0`. | `STORY-084` |
| 12 | Name und Adresse nach dem Umstieg? | Unverändert: „ToDo Viewer“ unter `http://todo.localhost:5411`. | `STORY-083`, `STORY-084` |
