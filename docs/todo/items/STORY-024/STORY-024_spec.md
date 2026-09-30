# STORY-024 Spec: Backend und Sync in der UI

Gemeinsame Festlegungen: siehe `EPIC-003_spec.md`.

## Was und warum

Die Backend-Wahl und der Sync sollen ohne Konsole bedienbar sein.

## Umfang

- **Projekt-Dialog** (`web/src/components/SourceDialog.tsx`): Backend wählen (Markdown-Ordner | Datenbank), Sync-Pfad (nur bei Datenbank, mit dem vorhandenen Ordner-Browser), Markdown-Pfad (nur bei Markdown).
- **Sync-Dialog** (neu, `SyncDialog.tsx`): Richtung wählen, „Vorschau“ ruft den Endpunkt aus STORY-023 mit `confirm=false`, zeigt Neu/Geändert/Unverändert und die Warnliste `missing` mit Checkbox „Fehlende Einträge löschen“; „Ausführen“ sendet `confirm=true`. Fehlercodes werden über `web/src/i18n` übersetzt (`sync_path_missing`, `sync_stale`, …).
- **Backend wechseln** als geführter Ablauf: Hinweis, zuerst zu synchronisieren, dann Umschalten; das Umschalten selbst ist `PUT /sources/{id}` mit neuem `backend`.
- TypeScript-Typen werden aus OpenAPI regeneriert (Regel 2), nicht von Hand geschrieben.

## Abnahme

Komponententests (`components.test.tsx`) für Backend-Wahl, Vorschau, Warnliste und Bestätigung; im Dev-Server wurde Backend-Wahl und Sync für ein Projekt von Hand durchgespielt.

## Nicht Teil dieser Story

Neue Backend-Logik; alles nutzt die Endpunkte aus 022/023.
