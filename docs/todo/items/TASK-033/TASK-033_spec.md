# TASK-033 — Spec: Konflikte beim Sync entscheiden: Datenbank, Datei oder aufschieben

## Arbeitsweise
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story. **Diese Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition`, `claude-harness:testing`, `claude-harness:techdocs`, `claude-harness:worktree`. Neues Verhalten: Test zuerst; er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Arbeit, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- **Datenbank-Backup zuerst (Vorgabe des Besitzers):** Bevor ein Schritt die echte Datenbank oder ihr Schema berührt, liegt ein frisches Backup in `configs/backups/` (bis TASK-031 fertig ist: von Hand mit der SQLite-Backup-Funktion `Connection.backup`, danach Integritätsprüfung und Zeilenzahlen vergleichen). Migrationen und Sync-Läufe werden zuerst an einer Kopie von `configs/todo.db` geprüft, nie zuerst an der echten Datenbank.
- Backlog: beim Start `In progress`, bei erfüllten Abschlusskriterien `Awaiting confirmation`.
- Weicht der Code von dieser Spec ab oder trifft die Arbeit auf einen Punkt unter „Stoppen und fragen“: nicht raten, anhalten und fragen.

## Ziel
Der Sync-Lauf nimmt je Konflikt eine Entscheidung entgegen und überträgt nur, was entschieden oder konfliktfrei ist.

## Schon vorhanden
- TASK-032: Stand je Eintrag, Klassifikation, Konfliktliste in der Vorschau, `conflicts` im Status.
- `application/services/sync.py` (`SyncService.run`, Token, `delete_missing`), `api/v2/routers.py` (`POST /sources/{id}/sync`).

## Festgelegt (Vorschlag, im Plan zu bestätigen)
- Request: `POST /sources/{id}/sync` erhält `resolutions` (Liste aus Art, Label, optional Name, Wahl `database`, `markdown` oder `defer`). Fehlt eine Entscheidung, gilt `defer`; der Lauf bricht dann nicht ab.
- Das Token deckt die Konfliktliste mit ab; ändert sich eine Seite seit der Vorschau, antwortet der Server wie bisher mit 409 `sync_stale`.
- Antwort: `resolved` (was übertragen wurde), `deferred` (offen geblieben), `kept` und `deleted` wie bisher.
- Aufgeschobene Einträge: Inhalt beider Seiten und gespeicherter Stand bleiben unverändert.
- Die Vorschau liefert je Konflikt beide Fassungen (Item: alle Felder als Werte; Dokument: Text beider Seiten), damit STORY-058 sie vergleichen kann.
- Der Stand je Eintrag wird am Ende des Laufs nur für wirklich übertragene Einträge geschrieben; bricht ein Lauf mitten drin ab, gelten die übrigen nicht als synchron.
- Läuft der Sync in die Datenbank, liegt vorher ein Backup (TASK-031).

## Dateien
`domain/sync.py`, `application/services/sync.py`, `api/v2/schemas.py`, `routers.py`, OpenAPI (`backend/scripts/export_openapi.py`), Tests `backend/tests/{unit,integration,api_v2}`, `docs/techdocs/interfaces.md`.

## Nicht anfassen
Die UI (STORY-058), Notes (STORY-047), das Schema des gespeicherten Stands (TASK-032).

## Tests (zuerst)
Jede Wahl (`database`, `markdown`, `defer`); Mischfall mit Konflikten und konfliktfreien Einträgen; Konflikt ohne Entscheidung wird aufgeschoben; aufgeschobener Eintrag erscheint im nächsten Lauf wieder; beide Seiten von Hand gleich gemacht → kein Konflikt; Token ungültig nach Änderung; Abbruch mitten im Lauf lässt keinen falschen Stand zurück.

## Stoppen und fragen
Wenn die Schreibreihenfolge (Dokumente vor/nach Backlog je Richtung) mit Entscheidungen je Eintrag nicht mehr stimmig ist.

## Abnahme
Tests und `scripts/check.sh` grün; OpenAPI neu erzeugt; Technikdoku aktuell.
