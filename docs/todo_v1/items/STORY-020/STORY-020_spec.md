# STORY-020 Spec: Contract-Suite und Routing je Projekt

Gemeinsame Festlegungen: siehe `EPIC-003_spec.md`.

## Was und warum

Der Port-Vertrag ist heute durch die Charakterisierungstests nur für Markdown festgelegt. Damit ein zweiter Adapter dasselbe Verhalten garantiert, wird der Vertrag adapter-unabhängig testbar. Zusätzlich muss die Anwendung je Projekt den passenden Adapter wählen.

## Änderungen

- `Source` (`domain/source.py`) bekommt `backend: str = "markdown"` (Werte `markdown` | `database`), sonst unverändert. Ohne Änderung an `Source.id` in dieser Story.
- Neues `infrastructure/routing.py` mit `RoutingBacklogRepository` und `RoutingDocumentStore`: implementieren die Ports und delegieren nach `source.backend`; unbekanntes Backend → `InvalidSourceError(code="unknown_backend")`. Verdrahtung nur in `bootstrap.py`.
- `backend/tests/contract/` (neu): parametrisierte Suite, die die Fälle aus `tests/characterization/test_edit.py` und `test_read.py` gegen `BacklogRepository` und `DocumentStore` formuliert (Fixture `repository_factory` liefert den Adapter samt Testdaten). Läuft gegen `MarkdownBacklogRepository` und einen In-Memory-Fake (`tests/fakes.py`, der in den Service-Tests schon ähnlich existiert).
- Die Golden-Tests für Markdown-Ausgabe bleiben unverändert und gehören weiter nur zum Markdown-Adapter.

## Schnittstelle zu den Nachbarn

STORY-021 fügt nur ein weiteres Element zur Adapter-Fixture hinzu.

## Abnahme

`scripts/check.sh` und alle bisherigen Tests grün, Verhalten der API unverändert; die Contract-Suite läuft für Markdown und Fake.

## Nicht Teil dieser Story

Kein DB-Code, keine Änderung an `config.json`.
