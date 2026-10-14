# STORY-058 — Spec: Konflikte im Sync mit Diff-Ansicht entscheiden

## Was und warum
Konflikte des Abgleichs (STORY-057) soll der Besitzer nicht blind auflösen. Die UI zeigt beide Fassungen und die Unterschiede; pro Konflikt: Datenbank, Datei oder aufschieben.

## Festgelegt
- Teil des vorhandenen Sync-Dialogs (`components/SyncDialog.tsx`), kein zweiter Dialog. STORY-047 nutzt denselben Dialog für Notes.
- Items: feldweise nebeneinander, geänderte Felder hervorgehoben. Dokumente und lange Texte: Textvergleich. Kein Bearbeiten im Dialog und kein Zusammenführen innerhalb eines Eintrags; wer Teile übernehmen will, schiebt auf, ändert von Hand und gleicht erneut ab.
- Die Entscheidungen gehören zur Bestätigung des Syncs (kein eigener Speicher in der UI); „Aufschieben“ ist vorbelegt.
- Nur API v2, Typen aus `schema.d.ts`, Texte über `i18n/messages.ts`, Beleg per Screenshot (`preview_start`).

## Offen
- Diff-Bibliothek: kleine Abhängigkeit (z. B. `diff`) oder eigene Zeilenvergleichsfunktion in `web/src/domain/`. Vor dem Aufnehmen einer neuen npm-Abhängigkeit den Besitzer fragen.

## Betroffene Stellen
`web/src/components/SyncDialog.tsx`, neue Komponenten für Konfliktliste und Vergleich, `web/src/domain/sync.ts` (+ Test), `api/queries.ts`, `i18n/messages.ts`, `components/sync.test.tsx`.

## Abnahme
Siehe Abschlusskriterien. Manuell: Projekt mit Konflikt (Item und Dokument), alle drei Entscheidungen einmal durchspielen, Screenshot.
