# `TASK-034` — Architekturregeln für den Neubau

Grundlage: `EPIC-007_spec.md`, Abschnitte 3–9.

## Warum zuerst

Die heutigen Regeln in `docs/development/architecture.md` widersprechen dem
Neubau an mehreren Stellen:

- Regel 1: Primärquelle je Projekt wählbar → im Neubau ist die DB immer die
  Wahrheit (§7.3).
- Regel 2: nur `/api/v2`, Typen aus OpenAPI → im Neubau `/api/<owner>/…` und
  MCP unter `/mcp` (§5); die Typen bleiben generiert.
- Regel 3: Notes nur in der DB, kein Hintergrund-Timer → im Neubau werden Notes
  gespiegelt, und der Wecker braucht einen Zeitgeber im laufenden Server (§5,
  Baustein „Zeitgeber“).
- Scope `backend` §5: die `uid` darf nicht in die API → im Neubau ist die
  `uid` der Schlüssel des Syncs und steht in den Dateien (§7.3, §10).

Die Regeln sind bindend erst nach Freigabe durch den Projektinhaber (Skill
`claude-harness:architecture`).

## Umfang

- `architecture.md` neu: projektweite Regeln des Neubaus
  1. Speicher: DB ist die Wahrheit, Markdown der Spiegel, Daten wandern nur
     über den Sync; Regeln des Syncs aus §7.3.
  2. Ein HTTP-Vertrag `/api/<owner>/…` plus MCP `/mcp` aus denselben
     Operationen; Fehler `{code, message, details}`; TS-Typen generiert.
  3. Zeit: UTC speichern, in der Zeitzone des Rechners zeigen; die
     Fällig-Entscheidung ist eine reine Funktion mit der Uhr als Parameter;
     Zeitgeber nur über den `Scheduler`-Port, ein Termin je Besitzer, kein
     Polling.
  4. Plugins: feste Liste in der Composition Root; ein Plugin importiert nur
     Core und Plugins aus `requires`; Tabellen-Präfix je Plugin.
- Scope `server` (`server/**`): Zwiebel je Core und Plugin (§4), Ports und
  Konstruktor-Injektion nur in `viewer/app/composition.py`, `DomainError` mit
  Code, Migrationen nur vorwärts, Fremdschlüssel nur auf `requires`.
  Enforced by: `server/pyproject.toml` (`[tool.importlinter]`).
- Scope `client` (`client/**`): Regeln 1–9 des ezf-ui sinngemäß (§4, §8),
  angepasst an die Ordner hier; Test-IDs; neue npm-Abhängigkeiten nur mit
  Freigabe. Enforced by: ESLint-Regel `architecture/boundaries`.
- Scope `legacy` (`backend/**`, `web/**`): die heutigen Regeln 1–3 und die
  Scopes `backend`/`web` unverändert, mit dem Hinweis, dass der Scope beim
  Umstieg (`STORY-084`) entfällt.

## Nicht im Umfang

Code, Tests, import-linter- und ESLint-Konfiguration (die entstehen mit
`STORY-061` bzw. `STORY-066`).

## Akzeptanz

Die Abschlusskriterien des Items. Der Projektinhaber gibt die Regeln frei;
erst danach beginnen `STORY-061` und `STORY-066`.
