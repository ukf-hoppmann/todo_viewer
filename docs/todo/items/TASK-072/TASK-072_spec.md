# TASK-072 — Spec: Prompts für Themenbaum und Claude_Harness

Zu `STORY-106`. Der Owner will den ersten Themenbaum nicht von Hand bauen und die Übergabe an Claude_Harness selbst
vornehmen (siehe `STORY-106_notes.md`). Diese Task schreibt die beiden Prompts und probiert den ersten aus; Code
ändert sie nicht.

## Prompt 1: Themenbaum erzeugen

Zielgruppe: eine Claude-Code-Sitzung im Checkout eines Projekts, die den Viewer über MCP erreicht (Tools
`workspace_…`, `backlog_…`, `mindmap_…`). Der Prompt beschreibt Auftrag, Ablauf und Regeln; die Werkzeugnamen
werden gegen `tools/list` des laufenden Servers geprüft, nicht aus dem Gedächtnis geschrieben.

Inhalt, den der Prompt festlegen muss:

1. **Auftrag:** Aus den Items des Projekts einen Themenbaum bauen und die Items zuordnen. Es läuft automatisch, ohne
   Rückfrage je Knoten; am Ende steht ein Bericht.
2. **Vorher lesen:** das Projekt bestimmen; den vorhandenen Baum lesen (`mindmap_get_tree`) — ist er nicht leer,
   wird erweitert, nichts doppelt angelegt; alle Items einschließlich der abgeschlossenen und abgelehnten lesen
   (`backlog_index_lines`, für Titel, Ziele und Zusammenhänge `backlog_get_item`; Epics und Stories genau, Tasks nur
   bei Unklarheit).
3. **Themen bilden:** Themen, keine technischen Schichten (also kein Knoten „Web-UI“ oder „Backend-API“ als
   Einordnung); Epics sind oft selbst Themen oder liefern deren Namen; gleiche Themen bündeln; so viele Ebenen wie
   nötig, so wenige wie möglich; Titel kurz, in der Sprache des Projekts.
4. **Anlegen:** `mindmap_create_node` von oben nach unten (Parent vor Kind).
5. **Zuordnen:** `mindmap_assign_item` für Epics und für Stories und Tasks ohne Epic. Ein eigens zugeordnetes Item
   zieht seine Kinder mit; Kinder werden nur zugeordnet, wenn sie woanders hingehören als ihr Parent.
6. **Prüfen:** `mindmap_get_tree` lesen; alles, was unter „Nicht zugeordnet“ bleibt, wird mit Grund im Bericht
   genannt.
7. **Verboten:** Items ändern, verschieben, schließen oder löschen; Knoten oder Items endgültig löschen;
   Memos anlegen.
8. **Bericht:** der Baum als eingerückte Liste mit Anzahl der Items je Knoten, die Liste der nicht zugeordneten
   Items, und was unklar war.

Erproben: einen frischen Viewer mit synthetischen Daten starten (`tests/helpers/server/`,
`tests/implementation/system/server/test_harness_flow.py` zeigen, wie ein Server mit Beispielprojekt läuft), den
Prompt einer Sitzung geben, das Ergebnis prüfen (Baum vorhanden, jedes Item unverändert und entweder zugeordnet oder
im Bericht genannt). Die Beobachtungen fließen in den Prompt ein.

## Prompt 2: Claude_Harness anpassen

Zielgruppe: eine Sitzung im Repository von Claude_Harness. Der Prompt nennt, was sich ändert, jeweils mit der
Stelle in Claude_Harness, die zu prüfen ist (Skill `todo`, `format.md`, `api.md`, Vorlagen, Hilfsskripte
`backlog.py`/`backlog_api.py`, Beispiele in den Skills, kopierte Fassung für Cloud-Sitzungen):

- Backlog-Dateiformat **Version 3**: Feld `Area` entfällt (nicht mehr Pflicht, wird nicht geschrieben); gelesen wird
  weiter Version 2 und 3, ein vorhandenes `Area` wird ignoriert; die Kennung heißt „backlog format version 3“; die
  Pflichtfelder und die Prüfung („every entry contains …“) ohne Area; Regel „Reuse existing areas …“ entfällt.
- API/MCP des Viewers: `create_item` und `update_item` ohne `area`; `backlog_list_areas` entfällt; die Index-Zeilen
  lauten `ID | Type | Status | Title | Parent | Notes`; `promote_memo` ohne `area`.
- Die Einordnung nach Themen läuft über die Knoten der Mindmap (Tools `mindmap_…`).

Die genauen Änderungen werden aus dem Stand nach `area-remove-server` abgelesen (techdocs `interfaces.md`), nicht aus
diesem Text.

## Ablage

Beide Prompts stehen (geschrieben am 2026-11-24) als `<ID>_spec_prompt-baum.md` und `<ID>_spec_prompt-harness.md` neben dieser Spec und werden
dem Owner am Ende der Sitzung vollständig im Text gegeben. Ein Prompt ist ein einziger Text, den der Owner kopiert.
