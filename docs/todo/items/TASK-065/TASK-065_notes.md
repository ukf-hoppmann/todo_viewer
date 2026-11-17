# TASK-065 — Mindmap: Markierungen „verworfen“ und „später“ an Ideen-Knoten

## State

- Goal/Status: Umgesetzt, im Browser geprüft und vom Owner bestätigt (2026-11-17).
- Next step: STORY-100 gegen ihre Kriterien prüfen (2026-11-17)
- Open:
- Decided:
  - Speicherung als Nachschlagetabelle `mindmap_marks` und Spalte `mindmap_nodes.mark` (Migration 3); gespeichert englisch `discarded`, `later` (2026-11-17)
  - Setzen und Löschen über `update_node` (`mark`, leer löscht) mit Versionstoken; keine eigene Operation (2026-11-17)
  - Darstellung: Verworfen mit Symbol, Durchstreichen und stärkerer Dimmung, Später mit Symbol; Setzen im Knoten-Detail, keine Schnellaktion in der Map (2026-11-17)
  - Filter „Markierung“ neben den Zuständen, standardmäßig alles sichtbar; ein ausgeblendeter Knoten nimmt seinen Ast mit (2026-11-17)
- References: Spec TASK-065_spec.md; Story-Spec STORY-100_spec.md; Doku neubau-server.md und neubau-client.md, Abschnitt Plugin `mindmap`

State confirmed after entry 2026-11-17 — Bestätigung (60dd95a61fb5)

## 2026-11-17 — Plan und Umsetzung

### Discussed

- Plan in sechs Abschnitten: Server-Regel, Migration, Operation und Typen, Client-Domain, Oberfläche, Integration; je Abschnitt test first.
- Eigene Operation oder `update_node` erweitern: empfohlen und freigegeben ist die Erweiterung (ein Versionstoken, eine MCP-Operation).
- Ausblenden mit Ast oder Kinder nachrücken lassen: empfohlen und freigegeben ist das Ausblenden mit Ast wie beim Zustandsfilter. Das ist eine Abwägung gegen Kriterium 3: Die Markierung bleibt am Knoten selbst, die Unterknoten tragen keine und zählen weiter, sind aber unsichtbar, solange der Parent ausgeblendet ist. Nachrücken wäre aufwendiger (Kanten und Layout).
- Standard des Filters: alles sichtbar, damit nichts unerwartet verschwindet.

### Decided

- Siehe Kopf.

### Prüfung

- Server: Unit- und Integrationstests der Mindmap (141 inklusive OpenAPI-Typen) grün; `mypy` und `lint-imports` ohne Fehler; `ruff` auf den geänderten Teilen ohne Fehler.
- Client: 1307 Tests grün; ESLint meldet nur die 5 Fehler in `usePersistentState.ts`, die schon vorher bestanden.
- Browser (lokaler Server, Beispieldaten, Chromium): Markierung im Detail setzen, wechseln und löschen; Symbole in der Map; Filter blendet Verworfen samt Ast und Später aus und wieder ein; Zustand und Zahl eines markierten Knotens bleiben unverändert. Keine Konsolenfehler.

## 2026-11-17 — Bestätigung

### Decided

- Der Owner hat den Task bestätigt (`Completed`); er ist archiviert. Das Ausblenden markierter Knoten samt Ast bleibt wie umgesetzt.
