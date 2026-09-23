# Umbau: Onion-Architektur + React

Branch: `refactor/onion`. Jede Etappe endet mit grünen Tests, lauffähiger App und
einem Commit.

## Zielarchitektur

```
backend/todo_viewer/
  domain/          Item, Source, ChangeSet, Status-Regeln, Fehler mit Codes (keine äußeren Imports)
  application/     Ports (Protocols) + kleine Use-Case-Services
  infrastructure/  Adapter: Markdown-Backlogs, JSON-Config/UI-State, Dateisystem
  api/             FastAPI-Router, Pydantic-Schemas, Fehler → HTTP
  bootstrap.py     Composition Root (Konstruktor-Injection, kein DI-Framework)
frontend/          React + Vite + TypeScript (ab Etappe 6)
```

Abhängigkeiten zeigen nur nach innen: `api`/`infrastructure` → `application` → `domain`.
Wird per `import-linter` geprüft (`scripts/check.sh`: ruff, mypy --strict, import-linter, pytest).

## Etappen

| # | Etappe | Status |
|---|---|---|
| 0 | Sicherheitsnetz: pytest/ruff/mypy, Characterization-Tests (Parser, Edits, Archiv, API) | erledigt |
| 1 | Domain-Kern: Item, Source, Status-Regeln, ChangeSet, Fehlercodes | erledigt |
| 2 | Markdown-Adapter: parser.py in kleine Klassen, atomares Schreiben + Lock | erledigt |
| 3 | Application-Services + Ports, JSON-Adapter für Config/UI-State, Composition Root | erledigt |
| 4 | FastAPI, alte Endpoints kompatibel, Docker | erledigt |
| 5 | API v2 (`/api/v2`): stabile Quell-IDs, Item-Referenzen, 409 bei Konflikten, import-linter | erledigt |
| 6 | React-Grundgerüst in `web/`: Vite/TS/TanStack Query, OpenAPI → TS-Typen, Sidebar, Filter, i18n, UI-State | erledigt |
| 7 | React-Views: Baum, Kanban, Graph, Detail/Edit, Dialoge; Umschalten auf React + Docker multi-stage | offen |
| 8 | Aufräumen: altes Frontend + Kompat-Endpoints entfernen, README, CI | offen |

## Leitplanken

- Testdaten sind synthetisch (`backend/tests/fixtures`), keine Kopien echter Backlogs.
- Dateiinhalte nach Edits bleiben bytegenau wie im alten Verhalten (Characterization-Tests).
- Das alte Frontend funktioniert bis Etappe 7 gegen die kompatiblen Endpoints.

## Gefundene Bugs

- CRLF-Dateien wurden beim Bearbeiten auf LF umgestellt (`read_text()` normalisiert
  Zeilenenden vor der Erkennung). Behoben in Etappe 2.
- Schreiben war nicht atomar und überschrieb parallele externe Änderungen still.
  Seit Etappe 2: temp-Datei + `os.replace`, mtime/size-Prüfung → Fehlercode `file_changed`.
- `/api/items/update` schrieb in jede übergebene Datei, nicht nur in konfigurierte
  Quellen. Seit Etappe 5 nur noch in konfigurierte Quellen (`source_gone` sonst);
  v2 adressiert Items per Quell-ID + Ref und kennt keine Dateipfade mehr.
