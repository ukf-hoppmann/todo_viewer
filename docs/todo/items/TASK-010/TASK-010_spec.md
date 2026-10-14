# TASK-010 — Spec: Hinweis-Modell: speichern, fällig machen, entscheiden

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-041), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Das Fundament für STORY-041. Erzeugt werden die Hinweise erst in TASK-011 und TASK-012; hier entstehen Modell, Speicher, Entscheidungen, Fälligkeit und Routen.

## Schon vorhanden
- `NoteRepository`/`DatabaseNoteRepository`, Contract-Suite `backend/tests/contract/test_note_repository.py`, Migrationen in `infrastructure/database/migrations.py` (vorwärts, mit Test „leere Datenbank auf aktuellen Stand“).
- `evaluate(note, triggers, topic_due, now)` in `domain/notes.py` entscheidet über fällig und den Grund (`NoteReason`: `trigger`, `review_expired`, `topic_due`).
- `NoteService.due_all()`/`due_count()` aus TASK-009.

## Festgelegtes Modell
Tabelle `note_notices`, Domain-Typ `Notice` in `domain/notes.py` (oder neu `domain/notices.py`):
- `id`, `side` (`note` | `item`), `project` und `label` des **Betroffenen** (bei `note` die Note, bei `item` das Item), `cause`, `counterpart` (`LinkTarget` der anderen Seite: bei `side=note` das Item; bei `side=item` die Note), `created_at`, `decided_at` (leer = offen), `decision`.
- `cause` (`NoticeCause`): Seite Note: `item_completed`, `item_rejected`, `item_deleted`, `item_retyped`, `project_unreachable`; Seite Item: `note_dropped`, `note_promoted`.
- `decision` (`NoticeDecision`): Seite Note: `keep`, `detach`, `drop`, `promote`; Seite Item: `acknowledge`.
- Doppelte offene Hinweise gleicher Ursache auf dieselbe Gegenseite werden nicht noch einmal angelegt.

## Zu tun
1. Port `NoteRepository` um `add_notice`, `notices_of(project, label, side, open_only)`, `decide_notice(notice_id, decision, at)` erweitern; Adapter, Migration (neue Version, vorwärts) und Contract-Tests dazu. Löschen/Purge einer Note entfernt ihre Hinweise mit.
2. Domain: `NoteReason.NOTICE = "notice"`. `evaluate` bekommt einen Parameter `open_notices: int`; ist er > 0 und die Note nicht abgeschlossen, ist sie fällig. Hat die Note mehrere Gründe, gilt die Reihenfolge `trigger`, `notice`, `topic_due`, `review_expired` (der erste zutreffende wird als Grund genannt). Reine Funktion, mit festem Clock getestet.
3. Service: `NoteService.decide(project, label, notice_id, decision, version)`:
   - `keep`: Link bleibt, Hinweis erledigt, `review_at` neu (wie `keep`).
   - `detach`: den Link zur Gegenseite entfernen (Link der Rolle `reference`; trigger-Links gehen mit dem Auslöser), Hinweis erledigt.
   - `drop`: `finish(..., dropped)`; Hinweis erledigt.
   - `promote`: hier **nicht** umsetzen; Entscheidung wird in TASK-013 angeschlossen. Bis dahin Fehler `decision_not_available`.
   - Seite Item: nur `acknowledge`.
   - Entscheidung auf einen schon entschiedenen Hinweis → Fehler `notice_already_decided`.
4. `due_all()`/`due_count()` (TASK-009) zählen offene Hinweise mit (Note fällig mit Grund `notice`); `actions` für diesen Grund: `keep`, `detach`, `drop`, `promote`.
5. Routen (`tags=["notices"]`): `GET /api/v2/notices?project&label&side&open=true` (Liste), `POST /api/v2/notices/{notice_id}/decision` Body `{decision, version?}` → aktualisierte Note bzw. Hinweis. `NoteOut` (TASK-005) bekommt `open_notices` (Liste).
6. OpenAPI neu erzeugen.

## Dateien
`domain/notes.py` oder `domain/notices.py`, `application/ports.py`, `application/services/notes.py`, `infrastructure/database/schema.py`, `migrations.py`, `notes.py`, `api/v2/notes_routers.py`, `api/v2/schemas.py`, Tests: `tests/unit/domain/`, `tests/contract/test_note_repository.py`, `tests/api_v2/test_notices.py` (neu), Migrationstest.

## Nicht anfassen
Wo Hinweise **entstehen** (TASK-011, TASK-012), Beförderung (STORY-042), die UI.

## Tests (zuerst)
Contract: anlegen, Duplikat, lesen offen/alle, entscheiden, mit Note löschen. Domain: Note mit offenem Hinweis ist fällig mit Grund `notice`, ohne nicht; abgeschlossene Note nie. Service/API: jede Entscheidung mit ihrem Endzustand; zweite Entscheidung abgelehnt; Zähler steigt mit Hinweis und fällt nach der Entscheidung; Migration einer leeren Datenbank.

## Stoppen und fragen
Wenn `evaluate` bereits einen Parameter für Hinweise kennt, die Migrationsnummer belegt ist oder `detach` für Links anderer Rollen nötig scheint.

## Abnahme
Entscheidungen und Fälligkeit per Test; Zähler berücksichtigt Hinweise; `scripts/check.sh` grün.
