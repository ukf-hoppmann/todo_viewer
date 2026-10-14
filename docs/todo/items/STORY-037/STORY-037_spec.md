# STORY-037 — Spec: Architekturregeln für Topics, Notes und Links

## Was und warum
Notes, Topics und Links passen nicht in die heutigen Regeln. Diese Story ändert die Regeln, bevor Code entsteht. Jede Änderung wird erst verbindlich, wenn der Besitzer sie freigibt (Skill `claude-harness:conflicts`).

## Konflikte mit den geltenden Regeln
1. **architecture.md §1** (genau eine Primärquelle pro Projekt, Markdown oder Datenbank; keine weitere Kopie der Daten). Notes liegen nur in der zentralen Datenbank, unabhängig von der Primärquelle des Projekts. Vorschlag: §1 gilt ausdrücklich für das Backlog; neuer Abschnitt für Notes und Topics (siehe unten).
2. **backend.md §5** („`uid` darf nicht in domain, application oder API erscheinen; Items werden über ihr Label angesprochen"). Links müssen Items auch nach einem Typwechsel (retype) finden und können auf Items in Projekten zeigen, deren Primärquelle Markdown ist (dort gibt es keine `uid`). Vorschlag: Ein Link auf ein Item speichert (Projekt, Item-Label); der retype-Use-Case aktualisiert die Links in derselben Operation. Notes und Topics haben eine interne `uid` nur im Datenbank-Adapter; nach außen gilt Projekt plus Label. Das hält §5 ein und funktioniert für beide Quellen.
3. **backend.md §5** („Storage-Adapter nur über Routing-Adapter"). Notes haben nur einen Adapter und brauchen kein Routing.

## Vorgeschlagene neue Regeln
- **Notes und Topics (architecture.md, neuer Abschnitt):** Notes, Topics, Links und Auslöser MUSS die zentrale Datenbank allein halten, nie TODO.md und nie ein anderes Markdown. Sie werden nur über den optionalen Export (STORY-047) als Dateien gespiegelt, nie durch normale Requests.
- **Ports (backend.md):** Eigener Port `NoteRepository` in `application/ports.py`, getrennt von `BacklogRepository`. Eine Implementierung in `infrastructure/database/`. Contract-Suite wie beim Backlog.
- **Auslöser:** Die Bewertung ist eine reine Funktion in `domain` (`jetzt` kommt als Parameter über einen Clock-Port). Zeit-Auslöser werden beim Lesen bewertet, Ereignis-Auslöser in dem Use Case, der den Item-Status ändert. Es gibt keinen Hintergrund-Takt. Der Adapter enthält keine Auslöser-Logik.
- **Projektübergreifend:** Der Zugriff auf andere Projekte läuft über die vorhandene Quellenverwaltung, nicht über Adapter-Imports.
- **Zeit:** Zeitpunkte werden mit Zeitzone der Rechner-Uhr erzeugt und angezeigt; gespeichert wird eindeutig (UTC).
- **Web (web.md):** Notes-Daten über TanStack Query; Gruppierung der Fälligkeiten, Regeln für Schnellaktionen und Zählung als reine Funktionen in `src/domain/`.
- **API:** Feld- und Statusnamen englisch; Fehler als `{code, message, details}`; Typen aus OpenAPI.

## Betroffene Dateien
`docs/development/architecture.md`, `docs/development/architecture/backend.md`, `docs/development/architecture/web.md`, `pyproject.toml` (`[tool.importlinter]`), ggf. ein neuer Architekturtest.

## Abnahme
- Die Regeln sind ergänzt, jeweils mit Begründung, und vom Besitzer freigegeben.
- Mechanisch prüfbare Regeln nennen ihren Test. Import-Linter-Verträge verbieten: Markdown-Adapter importieren Notes-Module nicht; `domain` und `application` kennen keine Datenbank-Treiber auch für Notes.
- `scripts/check.sh` läuft grün, die Architekturprüfung kennt die neuen Bausteine.
