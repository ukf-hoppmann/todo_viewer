# STORY-062 — MCP-Host: Operationen als MCP-Tools für LLMs

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- Das installierte MCP-SDK ist 2.3.0 (`MCPServer` statt `FastMCP`). Für Tools aus Operationen eignet sich der Low-Level-`Server` mit `on_list_tools`/`on_call_tool` besser als der Decorator-Weg: Schema und Aufruf kommen aus den `Operation`-Dataclasses, nicht aus Funktionssignaturen.
- Die Route `/mcp` und die Lebensdauer des Session-Managers werden in die FastAPI-App eingehängt, nicht als Unter-App gemountet (ein Mount würde `/mcp` auf `/mcp/` umleiten).

### Decided

1. **Tool-Tabelle**: aus `PluginHost` alle Operationen mit `mcp=True` zu Tools `<owner>_<name>` (Bindestriche als `_`), Beschreibung aus `summary`, Eingabe-Schema aus `TypeAdapter(input)`, `read_only_hint` für `kind == "read"`. Test zuerst (Unit).
2. **Aufruf und Fehler**: Argumente mit demselben `TypeAdapter` prüfen, `PluginHost.call`, Ausgabe als JSON-Text; `DomainError`, ungültige Argumente und unerwartete Fehler als `is_error` mit `{code, message, details}`.
3. **Einhängen**: `/mcp` (Streamable HTTP) in der App, Session-Manager im Lifespan; Integrationstest mit dem MCP-Client des SDK gegen den laufenden Test-Server (Tool-Liste, Aufruf, Fehler mit demselben `code` wie über HTTP).
4. **Integration**: `scripts/check-next.sh` grün, `mcp` in `server/pyproject.toml`, Techdoku.

### Open

- Keine.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant mit dem Low-Level-`Server` des SDK 2.3.0; `/mcp` wird als Route in die FastAPI-App gehängt, der Session-Manager läuft im Lifespan der App. Erlaubte Hosts gegen DNS-Rebinding: `127.0.0.1`, `localhost`, `[::1]` und `todo.localhost` (das SDK kennt nur Port-Wildcards, keine Host-Wildcards).
- `mcp` ist die im Scope `server` §7 freigegebene Abhängigkeit; `mcp_types` kommt als deren Abhängigkeit mit.

### Decided

- Abschlusskriterien geprüft: (1) `/mcp` antwortet dem Client des SDK über Streamable HTTP; (2) Tool-Liste mit Beschreibung und JSON-Schema und ein erfolgreicher Aufruf gegen den laufenden Test-Server (`test_mcp.py`); (3) `DomainError` kommt mit demselben Inhalt `{code, message, details}` an wie über HTTP (`test_domain_error_arrives_with_the_same_code_as_over_http`); (4) Tests für Liste, Aufruf, Fehler, ungültige Argumente und unbekannte Tools sind grün.
- `scripts/check-next.sh` grün (60 Tests); `scripts/check.sh` des alten Viewers grün.
- Status: `Awaiting confirmation`.

### Open

- Keine.
