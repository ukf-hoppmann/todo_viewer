# STORY-044 — Spec: Projektübergreifende Links

## Was und warum
Ein Merker in Projekt A kann auf ein Item in Projekt B warten und von dort ausgelöst werden. Die zentrale Datenbank hält alle Notes und Links, deshalb ist die Rückrichtung am Item in jedem Projekt abfragbar.

## Regeln
- Ein Link-Ziel ist (Projekt, Item-Label), das Projekt muss registriert sein. Anzeige und API nennen es „Projekt · Label".
- **Ereignisse:** Der Use Case, der den Status eines Items ändert, sucht Auslöser über alle Projekte hinweg, nicht nur im eigenen.
- **Rückrichtung:** Am Item erscheinen die Notes, die auf es zeigen, auch aus anderen Projekten.
- **Erreichbarkeit:** Ist das Projekt entfernt oder seine Quelle nicht lesbar, wird der Link als `unreachable` markiert und erzeugt einen Änderungshinweis (STORY-041). Es gibt keinen Fehler. Wird das Projekt wieder erreichbar, hebt sich die Markierung auf; der Hinweis bleibt, bis jemand entscheidet.
- Bei Markdown-Primärquellen werden Ereignisse nur erkannt, wenn die Änderung über den Viewer läuft. Eine Änderung außerhalb wird beim Sync erkannt (STORY-040).

## Betroffene Dateien
`application/services/items.py`, `notes.py`, `sources.py`, `domain/notes.py`, `infrastructure/database/notes.py`.

## Abnahme
- Eine Note in Projekt A mit Auslöser auf ein Item in Projekt B wird fällig, wenn das Item dort den Zielstatus erreicht (Integrationstest mit zwei Projekten).
- Ein entferntes oder nicht lesbares Projekt führt zu `unreachable` und zu einem Hinweis, nicht zu einem Fehler.
