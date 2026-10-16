# Vorlage: ezf-ui

Schnappschuss aus dem Projekt `ezf-ui` (Commit `e851c691`, 2026-10-16) als
Vorlage für das Client-Grundgerüst des Neubaus (`STORY-066`). Er liegt hier,
damit auch Sitzungen ohne Zugriff auf `ezf-ui` (z. B. in der Cloud) den Core
kopieren können.

Enthalten: `src/app`, `src/core`, die Plugins `layout-header-sidebar`,
`example` und `example-addon`, die ESLint-Regel `architecture/boundaries`
(`configs/eslint`), die Vite-Konfiguration, die Unit-Tests von App, Configs
und Core, die Test-Helfer, `package.json`, die `tsconfig`-Dateien und die
Architekturregeln von `ezf-ui`.

Nur lesen: Nichts im Neubau importiert von hier; Code wird kopiert und
angepasst (Regel 0 in `docs/development/architecture.md`). Der Ordner wird
erst nach der Abnahme des Neubaus durch den Projektinhaber entfernt.
