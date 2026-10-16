# STORY-071 — Backlog anzeigen: Baum, Filter, Suche, Detail (Plugin backlog)

## 2026-10-16 — Entscheidungen

### Decided

- Kanban fällt weg; Baum bleibt.
- Prioritäten: genau Urgent, Important, Normal, Prospective, relational erzwungen; die UI zeigt Dringend, Wichtig, Normal, Perspektivisch.

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Zuschnitt.** `STORY-071` baut das Plugin `backlog` mit dem Datenmodell und allem Lesenden: Server (Tabellen, Fortschritt, `list_items`, `get_item`) und Client (Hauptroute mit Baum, Filter, Detailpanel). Schreibende Operationen (Anlegen, Bearbeiten, Verschieben, Typwechsel) gehören zu `STORY-072`. Die Tests legen Items deshalb über das Repository des Plugins an (`ItemRepository.insert`, das `STORY-072` weiter benutzt).
- **Elementtypen.** `backlog` meldet `epic`, `story`, `task` mit den Präfixen `EPIC`, `STORY`, `TASK` im Register an; Label und `uid` kommen vom Register, `backlog_items.uid` ist Fremdschlüssel auf `workspace_elements.uid`. Titel stehen in beiden (Frage 25). Es meldet dem Papierkorb Kinder (über `parent_uid`), Regel (kein Wiederherstellen unter einem Parent im Papierkorb) und Aufräumen (Zeilen und Abhängigkeiten) an.
- **Fortschritt** (reine Funktion, Vorlage `src_old/web/src/domain/model.ts`): je Item erledigt/gesamt über alle Nachkommen; optionale (`required_for_parent = false`) und abgelehnte Kinder zählen samt Unterbaum nicht; unabhängig von den Filtern. Der Index liefert ihn je Item, je Projekt rechnet ihn der Client aus den Wurzeln.
- **`list_items(projects, statuses, priorities, query)`** liefert die flache Liste mit `uid`, Label, Typ, Status, Priorität, Bereich, Titel, `parent_uid`, `required_for_parent`, `progress`, Version; der Client baut den Baum (`buildTree` aus `shared`). **`get_item(ref, project?)`**: `ref` ist `uid` oder Label (dann mit Projekt; auch frühere Labels lösen auf) und liefert alle Felder, Kinder (auch gelöschte, markiert) und Abhängigkeiten.
- **Hauptroute.** Statt „Backlog“ mit Unterseite „Baum“ (es gibt nur noch eine Ansicht, der Graph kommt mit `STORY-074` als eigener Zugang) ist `backlog/main` eine Seite mit Baum links und Detailpanel rechts; die Filter Status und Priorität sind Seitenleisten-Abschnitte mit `when: ["backlog/main"]`. Standardmäßig sind die offenen Status sichtbar (`Open`, `In progress`, `Awaiting confirmation`); abgeschlossene und abgelehnte sind ausgeblendet, zählen aber im Fortschritt (Frage 27). Gemerkt werden im UI-Zustand (`backlog`): ausgeblendete Status und Prioritäten, zugeklappte Items, gewähltes Item.
- Prioritäten- und Statusnamen kommen übersetzt aus den Texten des Plugins (DE: Dringend, Wichtig, Normal, Perspektivisch). Kein Kanban.

### Decided

1. **Server Domain und Migration**: Wertelisten, `Item`, Fortschritt; Migration v1 mit festen Nachschlagetabellen (Typen, Status, Prioritäten), Bereichen, Items, Abhängigkeiten. Tests zuerst (Fortschritt, Filter).
2. **Repository** auf SQLite (Anlegen, Lesen, Filtern) und Papierkorb-Anmeldung; Tests gegen echte SQLite.
3. **Operationen** `list_items`, `get_item` (HTTP + MCP); Integrationstests.
4. **Client**: API, Baum mit Fortschrittsringen und gestrichelten optionalen Kindern, Filter-Abschnitte, Zuklappen, Detailpanel mit allen Feldern und Kindern; UI-Tests.
5. **Integration**: `check-next.sh`, `check.sh`, Techdoku.

### Open

- Frage 27 in `STORY-060`.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant: Server `viewer/plugins/backlog/`, Client `client/src/plugins/backlog/`. Beschreibung in `docs/techdocs/neubau-server.md` und `neubau-client.md`. Abweichungen: Frage 27 (Standard der Filter; eine Seite statt Hauptroute mit Unterseite).
- Der gemeinsame Baum kann jetzt Knoten gestrichelt zeichnen (`TreeNode.dashed`, Test in `TreeView.test.tsx`).
- Die Filter wirken im Browser (nicht über die Parameter von `list_items`), damit Fortschritt und Zuklappen unabhängig von ihnen bleiben; die Parameter der Operation bleiben für API und MCP.

### Decided

- Abschlusskriterien geprüft: (1) feste Tabellen für Typen, Status, Prioritäten (`Urgent`, `Important`, `Normal`, `Prospective`) und Bereiche; ein erfundener Wert scheitert an der Datenbank (`test_the_value_lists_are_enforced_by_the_database`); (2) Baum je Projekt mit Fortschrittsring, optionale Kinder gestrichelt, abgelehnte zählen nicht (`test_model.py`, `test_items.py`, `BacklogPage.test.tsx`); (3) Filter Status und Priorität in der Seitenleiste, Suche und Projekte aus `workspace` (`BacklogPage.test.tsx`); (4) Detailpanel mit allen Feldern und Kindern, gelöschte markiert (`ItemDetail.test.tsx`); (5) `list_items` und `get_item` über API und MCP; (6) Tests grün.
- `scripts/check-next.sh` und `scripts/check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Frage 27 in `STORY-060` (Annahme gilt).
- Nicht geprüft: das Anzeigen im echten Browser mit Daten aus dem Spiegel (kommt mit `STORY-075`); Anlegen und Bearbeiten von Items (`STORY-072`).
