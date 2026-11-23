# Architektur

<!-- Überblick über Komponenten, Datenfluss und Entscheidungen. Die verbindlichen Regeln stehen in docs/development. -->

Der ToDo-Viewer ist ein lokaler Dienst für Backlogs, Memos, Wecker und eine Mindmap. Verbindliche Regeln:
[Architekturregeln](../development/architecture.md) und die Scopes [server](../development/architecture/server.md) und
[client](../development/architecture/client.md). Entwurf und Entscheidungen: Epic `EPIC-007`
([Spec](../todo/items/EPIC-007/EPIC-007_spec.md)).

## Komponenten

| Komponente | Aufgabe | Details |
|---|---|---|
| Server (`server/`, Python, FastAPI) | Kern ohne Fachlichkeit plus Plugins; liefert HTTP-API, MCP, Ereignisstrom und die gebaute Oberfläche | [Neubau: Server](neubau-server.md) |
| Client (`client/`, React, Vite, TypeScript) | Oberfläche aus einem Kern und Plugins mit Seiten, Slots und Zustand | [Neubau: Client](neubau-client.md) |
| Plugins `workspace`, `backlog`, `memos`, `alarms`, `mindmap` | Je ein Server- und ein Client-Teil: Projekte und Verknüpfungen; Epics/Stories/Tasks; Memos und Topics; Wecker; Themenbaum | in den beiden Dokumenten oben |
| Datenbank (SQLite) | Einzige Quelle der Wahrheit; Tabellen gehören je einem Plugin (Präfix) | [Neubau: Server](neubau-server.md#datenbank) |
| Markdown-Spiegel | Optionale Dateikopie eines Projekts (Backlog-Format Version 3) zum Mitnehmen über Git, auch in die Cloud | [Schnittstellen](interfaces.md) |
| MCP-Server (`/mcp`) | Dieselben Operationen als Werkzeuge für den Harness und andere KI-Agenten | [Schnittstellen](interfaces.md) |
| Proxy (nginx) | Macht den Viewer ohne Port unter `todo.localhost` erreichbar | [Betrieb](operations.md) |

## Datenfluss

1. Die Oberfläche ruft die HTTP-API; schreibende Aufrufe tragen ein Versionstoken, ein veralteter Stand wird mit
   `version_conflict` abgewiesen.
2. Jede Operation eines Plugins erscheint als HTTP-Route und als MCP-Tool. Plugins schreiben keine Routen von Hand.
3. Nach einer Änderung sendet der Server ein Ereignis über Server-Sent Events. Die Oberfläche lädt die betroffenen Daten
   neu; sie fragt nie im Takt ab.
4. Normale Anfragen lesen und schreiben nur die Datenbank. Nur der Sync berührt die Spiegel-Dateien: Er gleicht Eintrag
   für Eintrag ab, zeigt vorher eine Vorschau und überschreibt oder löscht bei Konflikten nichts.

## Entscheidungen

| Entscheidung | Kurzbegründung |
|---|---|
| Kern ohne Fachlichkeit, Fachlichkeit in Plugins mit fester Liste an der Composition Root | Neue Fähigkeiten sollen vor allem vorhandene Bausteine konfigurieren; Schichten prüfen import-linter und eine ESLint-Regel |
| Datenbank als einzige Quelle der Wahrheit, Markdown nur als Spiegel | Ein Datenmodell mit Verknüpfungen und Papierkorb statt Dateien als Primärquelle |
| Operationen als gemeinsame Quelle für HTTP und MCP | Die KI-Schnittstelle bleibt vollständig und konsistent |
| Zeiten in UTC gespeichert, in der Zeitzone des Rechners angezeigt; Timer nur über den Scheduler des Kerns | Tests mit fester Uhr; ein ruhender Viewer kostet nichts |
| Mindmap als Gerippe, das Items und Memos verlinkt statt kopiert | Übersicht des Backlogs ohne Menge an Tasks in der Darstellung (`EPIC-008`) |
| Ein Branch pro größerem Umbau, kleine Schritte mit eigenem Test | Fehler fallen früh und billig auf |
