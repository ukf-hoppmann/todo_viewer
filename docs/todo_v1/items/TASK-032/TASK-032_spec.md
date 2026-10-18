# TASK-032 — Spec: Stand je Eintrag speichern und Änderungsseite erkennen

## Arbeitsweise
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story. **Diese Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition`, `claude-harness:testing`, `claude-harness:techdocs`, `claude-harness:worktree`. Neues Verhalten: Test zuerst; er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Arbeit, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- **Datenbank-Backup zuerst (Vorgabe des Besitzers):** Bevor ein Schritt die echte Datenbank oder ihr Schema berührt, liegt ein frisches Backup in `configs/backups/` (bis TASK-031 fertig ist: von Hand mit der SQLite-Backup-Funktion `Connection.backup`, danach Integritätsprüfung und Zeilenzahlen vergleichen). Migrationen und Sync-Läufe werden zuerst an einer Kopie von `configs/todo.db` geprüft, nie zuerst an der echten Datenbank.
- Backlog: beim Start `In progress`, bei erfüllten Abschlusskriterien `Awaiting confirmation`.
- Weicht der Code von dieser Spec ab oder trifft die Arbeit auf einen Punkt unter „Stoppen und fragen“: nicht raten, anhalten und fragen.

## Ziel
Pro Eintrag den Stand des letzten Syncs speichern und daraus ableiten, welche Seite den Eintrag geändert hat.

## Schon vorhanden
- `domain/sync.py` (`fingerprint`, `classify`, `plan_sync`, `SyncPreview`), `domain/source.py` (`SyncBaseline`), `application/services/sync.py`, `syncstatus.py`, `Source.baseline` (zwei Fingerabdrücke in `projects`).
- TASK-031: Backup vor Migration und Sync.

## Festgelegt
- Eintragsschlüssel: (Art, Label, Name). Art `item` oder `document`; Papierkorb-Items sind Items mit `deleted`; Name nur bei Dokumenten. STORY-047 ergänzt weitere Arten.
- Gespeichert wird die Version beider Seiten, die nach dem Sync übereinstimmen (`Item.version`, `content_version`). Nur Versionen, kein Inhalt. Eine Tabelle, Schlüssel inkl. Projekt-ID, versionierte Migration (nächste Nummer in `migrations.py`), Port in `application/ports.py` mit Contract-Test, Datenbank-Adapter in `infrastructure/database/`.
- Geschrieben wird der Stand nur am Ende eines erfolgreichen Syncs (`confirm`), und nur für Einträge, die danach auf beiden Seiten gleich sind. Aufgeschobene Konflikte und absichtlich stehen gelassene Einträge (`kept`) bekommen keinen neuen Stand.
- Die Klassifikation ist eine reine Funktion in `domain/sync.py`. Seiten heißen `database` und `markdown`, unabhängig von der Primärquelle. Ergebnisse: unverändert, nur Datenbank geändert, nur Markdown geändert, beide geändert, nur in der Datenbank neu, nur in Markdown neu, auf beiden Seiten neu mit verschiedenem Inhalt, in der Datenbank gelöscht, in Markdown gelöscht (Stand vorhanden, Eintrag fehlt auf einer Seite). Konflikt = beide geändert, auf beiden Seiten neu mit verschiedenem Inhalt oder gelöscht auf einer Seite (Besitzer, 2026-10-14: Löschungen sind Konflikte).
- Ohne gespeicherten Stand (vor dem ersten Sync nach der Migration): nur auf einer Seite vorhanden = dort neu; auf beiden Seiten vorhanden und verschieden = Konflikt.
- `Source.baseline` und `classify` bleiben für den Gesamtstatus erhalten; `SyncStatusService` ergänzt die Zahl der Konflikte (`conflicts`).
- `SyncPreview` erhält je Eintrag die Änderungsseite; API-Schema und generierte TS-Typen ändern sich.

## Festgelegt: Richtung
- Beidseitiger Abgleich (Variante A, STORY-057): `direction` beeinflusst die Klassifikation nicht, sie schränkt nur ein, welche Richtungen ein Lauf ausführt.

## Festgelegt: Hash
- Gespeichert wird die Version (Hash), nicht der Inhalt (Besitzer, 2026-10-14: Konflikte liegen zur Entscheidung bereit, kein automatischer Merge). Ein späterer automatischer Merge bräuchte den Inhalt und damit eine weitere Migration.

## Dateien
`domain/sync.py`, `domain/source.py`, `application/ports.py`, `application/services/sync.py`, `syncstatus.py`, `application/container.py`, `bootstrap.py`, `infrastructure/database/schema.py`, `migrations.py`, neues Modul für den Speicher, `api/v2/schemas.py`, `routers.py`, Tests `backend/tests/{unit/domain,unit/application,contract,integration,api_v2}`, `docs/techdocs/{architecture,interfaces,operations}.md`.

## Nicht anfassen
Markdown-Adapter, Notes (STORY-047), UI (STORY-058), die Entscheidung der Konflikte (TASK-033).

## Tests (zuerst)
Reine Funktion: jeder Fall der Klassifikation, mit und ohne gespeicherten Stand. Contract-Test des Speichers. Integration: Sync, Änderung auf einer Seite, Vorschau zeigt die richtige Seite; Änderung auf beiden Seiten und gleiche neue ID auf beiden Seiten → Konflikt. Migration an einer Kopie von `configs/todo.db`. Status nennt `conflicts`.

## Stoppen und fragen
Wenn die Version eines Items auf beiden Backends nicht gleich berechnet wird; wenn die Migration an der Kopie der echten Datenbank Daten verändert.

## Abnahme
Tests und `scripts/check.sh` grün; Migration an der Kopie der echten Datenbank fehlerfrei; Technikdoku aktuell.
