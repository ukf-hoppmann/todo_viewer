# STORY-045 — Spec: Bereich Notes in der UI

## Was und warum
Der Besitzer pflegt Notes in der UI und sieht auf einen Blick, was Aufmerksamkeit braucht. Die UI ist nur ein Client der API v2 (architecture.md §2); die Logik für Gruppieren und Zählen liegt in `web/src/domain/` als reine Funktionen.

## Bestandteile
- **Bereich Notes:** eigener Bereich neben dem Backlog. Topic-Baum links, Notes des gewählten Topics rechts (Kurzfassung, Status, Fälligkeit). Detailansicht mit Kurzfassung, Langtext, Auslösern, Links, Notizen und Specs (wie `DetailPanel` und `DocumentDialog` beim Backlog).
- **Auslöser bearbeiten:** Zeitpunkt (Datum und Uhrzeit in der Zeitzone des Rechners), Ereignis (Item wählen und Zielstatus), Topic-Termin. Der Modus any/all ist vorbereitet, aber nicht bedienbar. Bereits erfüllte Ziele werden vor dem Speichern angezeigt.
- **Rotes Ausrufezeichen:** neben dem Titel „ToDo-Viewer" oben links. Es steht, solange es fällige Notes oder offene Hinweise gibt, und zeigt die Anzahl. Der Zähler gilt global über alle Projekte. Er wird alle ~60 Sekunden und beim Fokussieren des Fensters abgefragt. Die Anzahl steht zusätzlich im Tab-Titel.
- **Modal bei Klick:** alle fälligen Notes, gruppiert nach Grund (Auslöser, Prüfung, Termin, Änderungshinweis). Aktionen je Zeile: zurückstellen (morgen, in einer Woche, in 30 Tagen, eigenes Datum, bei Ereignis), erledigen, verwerfen, befördern, in Notes öffnen. Bei Hinweisen zusätzlich: behalten, abkoppeln. Das Modal bleibt, bis die Zeile bearbeitet ist; kein Popup außerhalb davon.
- **Am Backlog-Item:** die verlinkten Notes, auch aus anderen Projekten, mit Status.
- **Einstellungen:** Prüf-Intervall (Standard 30) und maximale Topic-Tiefe (Standard 3) im Abschnitt „Allgemein" des Einstellungsmenüs.
- **Texte:** Anzeige über die Lokalisation (`web/src/i18n`), Keys englisch.

## Betroffene Dateien
`web/src/views/` (Notes-Ansicht), `web/src/components/` (Topic-Baum, Note-Dialog, Fällig-Modal), `web/src/domain/notes.ts` (+ Test), `web/src/api/` (Hooks, generierte Typen), `web/src/i18n/`, `components/settings/GeneralSection.tsx`, `App.tsx`.

## Abnahme
- Der Besitzer legt Topics und Notes an, setzt Auslöser, sieht Fälliges, handelt darauf und erreicht Notes vom Item aus.
- Das Ausrufezeichen erscheint und verschwindet mit dem Zustand der Daten.
- Domain-Funktionen haben Unit-Tests; die Komponenten haben Komponententests wie die bestehenden.
