# NEW-branch-transfer-ui — Spec: Ast überführen (Oberfläche)

Zu `STORY-103`. Der Server liefert `preview_branch_transfer` und `transfer_branch` (Task „Server: einen Ast mit
Vorschau ins Backlog überführen“); dort stehen Plan, Problemcodes und Ergebnis. Die Dialoge für einzelne Knoten
(Task „Oberfläche: im Detail eines Knotens …“) liefern die Eingabefelder, die hier wiederverwendet werden.

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/client.md`. Tests und Befehle: `tests/README.md`; Client-Tests unter `tests/implementation/unit/client/…` (Vitest, Testing Library), Hilfen unter `tests/helpers/client/`. Am Ende laufen `cd client && npx tsc -b && npm run lint` und alle Client-Tests grün.

## Umfang

- Einstieg: Menü eines Knotens (`client/src/plugins/mindmap/NodeMenus.tsx`), Eintrag „Ast überführen“; Dialog in
  einer neuen Datei im Plugin `mindmap` (Vorbild: `BranchDialog.tsx`).
- Der Dialog zeigt den Ast als Baum (vorhandene Hilfen: `domain/branches.ts`, `domain/tree.ts`, der gemeinsame
  `TreeView` in `client/src/shared/tree/`). Je Knoten: Wahl „nichts / Item / Memo“, bei Item der Typ, Titel, Ziel,
  Abschlusskriterien; Beziehung: „Kind von“ (Auswahl unter den Knoten des Plans und den Items des Projekts),
  „hängt ab von“ (Mehrfachauswahl). Keine Voreinstellung nach Ebene oder Tiefe.
- Die Vorschau ruft bei jeder Änderung (entprellt) `preview_branch_transfer` auf; Probleme zeigt der Dialog am
  Knoten, mit der Meldung des Servers (Codes über Übersetzungen).
- „Überführen“ ruft `transfer_branch`; das Ergebnis zeigt der Dialog je Knoten (Label des neuen Items oder Fehler)
  und bleibt offen, bis der Mensch schließt.
- Knoten, die bereits Items haben, sind erlaubt; der Dialog zeigt ihren Zustand am Knoten.
- Ablage der Eingabe im Zustand des Dialogs; nichts wird persistiert.
- Testkennungen, Übersetzungen, API-Mutationen/-Abfragen in `api.ts` wie bei den übrigen Teilen.

## Tests

`tests/implementation/unit/client/plugins/mindmap/`: Plan aus den Wahlen bauen (reine Funktion in `domain/`), Dialog
mit Fake-Server (Vorschau meldet Problem → Knopf gesperrt; ohne Problem → Aufruf mit richtigem Plan; Teilfehler im
Ergebnis).
