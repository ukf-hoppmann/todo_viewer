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
