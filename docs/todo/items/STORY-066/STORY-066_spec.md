# `STORY-066` — Client-Grundgerüst

Grundlage: `EPIC-007_spec.md`, Abschnitte 2, 3, 4, 8.

## Umfang

- `client/` mit `package.json`, Vite, TypeScript, ESLint, Vitest
  (Tests unter `tests/implementation/unit/client/`); Abhängigkeiten nach §2.
- Kopie aus `../ezf-ui/src/core` nach `client/src/core` und von
  `src/plugins/layout-header-sidebar`; ESLint-Regel
  `configs/eslint/architectureBoundaries.ts` aus ezf-ui mit ihren Tests.
- Entfernen: `core/auth`, `LoginPage`, Auth-Schritte in `startApp`,
  Keycloak-Konfiguration; der Start lädt direkt Plugins und Router.
- Plugin-Auswahl: feste Liste in `client/src/app` statt `plugins.json`.
- Verbindung: Basis-URL `/api`; Fehlerform `{code, message, details}`;
  Übersetzung über `code`.
- SSE: `core/events` mit `EventSource('/api/core/events')`, Neuverbinden mit
  Backoff, nach Neuverbinden Ereignis `core.reconnected`; Plugins
  registrieren `eventHandlers: Record<topic, (payload, api) => void>` in ihrer
  Definition (Erweiterung des Plugin-Vertrags).
- UI-Zustand: Core-Endpunkt `ui-state/{owner}`; Hook
  `usePersistentState(owner, key, default)`.
- Layout: Slots `layout.header-actions`, `layout.sidebar-sections`
  (Abschnitte mit `when: route[]`); Hauptroute `core/settings` mit Slot
  `core.settings-sections`. Dunkles MUI-Thema mit den Farben des heutigen
  Viewers (`web/src/styles` als Vorlage).
- Erzeugte API-Typen: `client/src/shared/api/schema.d.ts` aus
  `server`-OpenAPI (`npm run gen:api`).

## Nicht im Umfang

Fachliche Plugins und gemeinsame Bausteine (`STORY-067`).

## Tests

Kopierte Tests aus ezf-ui mitnehmen und anpassen; Test zuerst für SSE-Verteilung
und `usePersistentState`.
