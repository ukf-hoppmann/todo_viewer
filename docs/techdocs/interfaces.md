# Schnittstellen

<!-- Nur öffentliche Schnittstellen: API, CLI, Dateiformate, Hooks, Ereignisse. -->

Das vollständige Schema der HTTP-API liegt in `web/src/api/openapi.json`
(erzeugt mit `backend/scripts/export_openapi.py`).

## HTTP-API v2

- Zweck: Lesen und Bearbeiten der konfigurierten Backlogs, Verwaltung der
  Quellen, UI-Zustand.
- Aufruf / Endpunkt: Präfix `/api/v2`, Standard-Port 5411.

| Methode und Pfad | Zweck |
|---|---|
| `GET /backlog` | Alle Quellen (mit `item_count` und ggf. `problem`) und alle Items. Ohne `config.json` leer. |
| `POST /items/edit` | Ändert `status`, `priority` oder `required_for_parent` (`Yes`/`No`) eines Items. |
| `GET /sources` | Konfigurierte Quellen. |
| `POST /sources` | Quelle hinzufügen (`path`, optional `project`; ohne Namen der des Git-Repos). |
| `PUT /sources/{source_id}` | Quelle ändern. |
| `DELETE /sources/{source_id}` | Quelle entfernen. |
| `GET /sources/{source_id}/document?path=…` | Notes-/Spec-Markdown innerhalb des Backlog-Ordners lesen. |
| `GET /folders?path=…` | Unterordner für den Ordner-Browser, mit Markierung, ob eine `TODO.md` enthalten ist. |
| `GET /ui-state`, `PUT /ui-state` | UI-Zustand lesen bzw. vollständig ersetzen (freies JSON-Objekt). |

- Eingabe:
  - Items werden per `ref` adressiert: `{source_id, location ("active"|"archive"), id, line}`.
  - `POST /items/edit`: `{ref, field, value, resolution?}`; `resolution` ist
    Pflicht bei `Completed`/`Rejected`.
  - Quellen: `{path, project?}`; `source_id` ist eine stabile, pfadbasierte ID.
- Ausgabe:
  - Items mit `key` (`<source>/<location>/<id>`), `ref`, `project`, `format`
    (`backlog_v2`|`checkbox`), den geparsten Feldern, `extra_fields` für alle
    weiteren Freitext-Felder und `archive_supported`.
  - Ein Edit liefert das geänderte Item zurück; bei `Completed`/`Rejected` ist
    es danach im Archiv, beim Zurücksetzen wieder in `TODO.md`.
- Fehler: immer `{code, message, details}`.

| HTTP | Codes |
|---|---|
| 400 | `bad_request` (Validierung), `invalid_value`, `not_editable`, `checkbox_status_only`, `resolution_required`, `missing_path`, `not_found`, `not_a_dir`, `no_todo` |
| 403 | `forbidden` (Dokument außerhalb des Backlog-Ordners oder nicht `.md`/`.markdown`/`.txt`) |
| 404 | `source_gone`, `config_missing`, `file_not_found` |
| 409 | `file_changed` (Datei zwischen Lesen und Schreiben extern geändert), `entry_moved`, `duplicate` |
| 500 | `write_failed` (z. B. fehlende Schreibrechte) |

Alle übrigen Pfade liefern das gebaute Frontend aus `web/dist`; fehlt der
Build, antwortet der Server mit 503 und einem Hinweis.

## Dateiformat: Backlog-Ordner

- Zweck: Quelle der angezeigten Items.
- Aufruf / Endpunkt: ein Ordner mit `TODO.md`; `archive.md` im selben Ordner
  wird mitgelesen; `Notes`/`Spec` verweisen auf Dateien unter `items/<ID>/`.
- Eingabe: Claude_Harness-Backlog-Format (Version 1/2) oder eine einfache
  Markdown-Checkliste (`- [ ]`/`- [x]`; dort ist nur der Status bearbeitbar).
  Alte deutsche Prioritäten (`Dringend`, `Wichtig`, `Perspektivisch`) werden
  als `Urgent`, `Important`, `Prospective` gelesen.
- Ausgabe: Bearbeitungen ändern nur das betroffene Feld bzw. verschieben den
  Eintrag zwischen `TODO.md` und `archive.md`. Geschrieben wird atomar
  (temporäre Datei + Umbenennen); Zeilenenden (LF/CRLF) bleiben erhalten.
- Fehler: siehe `file_changed`, `entry_moved`. Nicht lesbare Quellen erscheinen
  mit `problem` in `GET /backlog`.

## CLI: `todo.sh`

- Zweck: Steuerung des Docker-Containers.
- Aufruf / Endpunkt: `./todo.sh <start|stop|restart|down|update|logs|status|open>`.
- Eingabe: Befehlsname.
- Ausgabe: siehe [README](../../README.md#quickstart-docker).
- Fehler: unbekannter Befehl → Hilfetext, Exit-Code 1.
