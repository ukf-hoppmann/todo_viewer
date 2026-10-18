# STORY-039 — Spec: API für Topics, Notes und Links

## Was und warum
Die API ist die Hauptanwendung für Notes (EPIC-005). Claude und andere LLMs arbeiten nur darüber. Sie hält sich an die bestehenden Konventionen von API v2: Versionstoken gegen gleichzeitige Änderungen, Fehler als `{code, message, details}`, TypeScript-Typen aus dem OpenAPI-Schema, Router ohne Geschäftslogik, Services in `application/services/`.

## Operationen (Vorschlag, Pfade unter `/api/v2`)
- **Topics:** anlegen, lesen, umbenennen, Termin setzen oder entfernen, verschieben (Tiefe wird geprüft), löschen.
- **Notes:** anlegen, lesen, ändern (Kurzfassung, Langtext, Topic, Prüf-Datum, Auslöser-Modus), Auslöser setzen und entfernen, löschen. **Projekt wechseln** erzeugt eine neue Note und löscht die alte; die Antwort nennt das neue Label.
- **Links:** setzen und lösen; Abfrage in beide Richtungen („Notes zu Item X", „Links einer Note").
- **Dokumente einer Note:** lesen und schreiben wie bei Items (Notizen, Specs, Spec mit Thema), mit Versionstoken.
- **Index (schlank):** je Topic und Note nur Label, Status, Fälligkeit (mit Grund) und Kurzfassung, je Topic zusätzlich der Pfad. Filter: Projekt, Topic, Status, fällig, verlinktes Item. Ohne Langtexte.
- **Zähler:** eigene billige Abfrage der fälligen Notes, global über alle Projekte (speist das Ausrufezeichen).
- **Fällig-Liste global:** alle fälligen Notes projektübergreifend mit Grund und möglichen Aktionen (speist das Modal).

## Regeln
- Adressiert wird mit Projekt plus Label, `uid` erscheint nie.
- Rechte erzwingt die API nicht (wie beim Backlog); sie weiß nicht, wer aufruft. Das regelt der Harness.
- Fehlercodes sind stabil, z. B. `topic_depth_exceeded`, `note_not_found`, `link_target_not_found`, `version_conflict`; die Namen werden in der Umsetzung festgelegt und in den Techdocs aufgelistet.
- Zeitpunkte kommen als ISO-Zeitstempel mit Zeitzone; „morgen früh" löst der Aufrufer auf.

## Betroffene Dateien
`api/v2/routers.py`, `api/v2/schemas.py`, `api/errors.py`, `application/services/notes.py` (neu), `application/container.py`, `bootstrap.py`, `web/src/api/openapi.json` und `schema.d.ts` (generiert), `backend/tests/api_v2/`.

## Abnahme
- Alle Operationen sind per API-Test abgedeckt, inklusive Versionskonflikt.
- Der Index liefert nie Langtexte und lässt sich nach allen genannten Filtern einschränken.
- Der Zähler ändert sich, wenn eine Note fällig wird oder aufgelöst wird.
- Der OpenAPI-Test (`test_openapi.py`) bleibt grün.
