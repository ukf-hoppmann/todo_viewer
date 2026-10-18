# `STORY-062` — MCP-Host

Grundlage: `EPIC-007_spec.md`, Abschnitte 5, 6, 11.

## Umfang

- Neue Abhängigkeit: offizielles MCP-SDK für Python (`mcp`), in
  `server/pyproject.toml`.
- `viewer.core.api.mcp`: baut aus allen Operationen mit `mcp=True` je ein
  Tool `<owner>_<name>`; Beschreibung aus `summary`, Eingabe-Schema aus
  demselben `TypeAdapter` wie die HTTP-Route; Ausgabe als JSON-Text.
- Eingehängt in die FastAPI-App unter `/mcp` (Streamable HTTP), im selben
  Prozess.
- Fehler: `DomainError` → Tool-Ergebnis mit `isError` und JSON
  `{code, message, details}`.
- `read`-Operationen werden als nur lesend markiert (Tool-Annotation).

## Nicht im Umfang

Die Vollständigkeit der Tools für den Harness (`STORY-081`).

## Tests

Test zuerst: Integrationstest mit dem MCP-Client des SDK gegen den laufenden
Test-Server (Tool-Liste, Aufruf, Fehler).
