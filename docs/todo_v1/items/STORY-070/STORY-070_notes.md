# STORY-070 — Papierkorb für alle Elementtypen

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- Der Papierkorb ist ein Dienst des Plugins `workspace`; ob ein Element im Papierkorb liegt, steht in `workspace_elements.deleted_at` (eine Wahrheit für alle Typen). Die besitzenden Plugins melden dem Dienst je Elementtyp drei Ports an (beim Bau, über `context.required["workspace"].trash.register(kind, …)`; `requires` stellt sicher, dass `workspace` vorher gebaut ist): `children(tx, uid)` (`ChildrenProvider`: `uid`s aller direkten Kinder, gelöschte eingeschlossen), `restore_guard(tx, element)` (`RestoreGuard`: wirft einen `DomainError`, wenn das Wiederherstellen gegen eine Regel des Plugins verstößt) und `purger(tx, uid)` (`Purger`: entfernt Plugin-Daten und Dokumente des Elements). Ein Typ ohne Anmeldung hat keine Kinder, keine Regel und keine eigenen Daten.
- Die Darstellung (Titel, Typ-Badge) liefert das Register selbst (`title`, `label`, `kind`, Frage 25), ein `ChildrenProvider` muss sie nicht mehr liefern.
- **Kaskade.** `delete_element(uid, version, cascade)` legt das Element und alle noch aktiven Nachkommen mit demselben Löschzeitpunkt in den Papierkorb. Hat es Nachkommen und ist `cascade` nicht gesetzt, ändert sich nichts und die Antwort nennt `has_children` und die Zahl. Wiederherstellen holt mit dem Element die Nachkommen zurück, die denselben Löschzeitpunkt haben (also mit ihm gelöscht wurden), nicht die vorher einzeln gelöschten.
- **Sammelaktionen.** Wiederherstellen und endgültig Löschen nehmen eine Liste von `uid`s (`restore_elements`, `purge_elements`) und wenden die Vorfahren-Regel auf dem Server an: ein gewähltes Element, das Nachkomme eines anderen gewählten ist, wird übergangen (Frage 26: die Spec nennt Einzel-Operationen `restore_element`/`purge_element`; eine Liste mit einem Element ist der Einzelfall). Alles in einer Transaktion: scheitert eins (Regel des Plugins, Version), ändert sich nichts.
- Endgültig Löschen nur für Elemente im Papierkorb, Nachkommen zuerst; die Verknüpfungen gehen über den Fremdschlüssel mit. Kein MCP-Tool (`mcp=False`).
- Wiederherstellen eines Elements in einem entfernten Projekt wird abgewiesen (`project_in_trash`).
- Ereignis `workspace.element.changed` (öffentlich): `{change: "deleted"|"restored"|"purged", uids}`.
- Client: Hauptroute „Papierkorb“ im Plugin `workspace` (Liste der gelöschten Elemente der sichtbaren Projekte, gefiltert nach dem Suchtext, mit Checkboxen, Sammelaktionen und Bestätigung vor dem endgültigen Löschen) und der Hook `useDeleteElement` für Plugins (fragt bei Kindern nach). Das gestrichelte und durchgestrichene Darstellen gelöschter Kinder im Detailpanel gehört zum Detailpanel des Backlogs (`STORY-071`).

### Decided

1. **Domain/Ports**: Port-Typen, Fehler, Auflösen der Nachkommen; Tests zuerst (Kaskade, Vorfahren-Regel, Restore-Regel).
2. **Dienst `TrashService`** und Speicher (`list_deleted`); Ereignis.
3. **Operationen** `delete_element`, `list_trash`, `restore_elements`, `purge_elements` (HTTP; MCP außer endgültigem Löschen); Integrationstests mit dem Test-Plugin mit Eltern/Kind-Beziehung.
4. **Client**: API, Hauptroute „Papierkorb“, Hook `useDeleteElement`; UI-Tests.
5. **Integration**: `check-next.sh`, `check.sh`, Techdoku.

### Open

- Frage 26 in `STORY-060`.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant im Plugin `workspace`: Dienst `TrashService`, Operationen, Hauptroute und Hook. Beschreibung in `docs/techdocs/neubau-server.md` und `neubau-client.md`. Abweichung von der Spec: Frage 26 (`restore_elements`/`purge_elements` mit Liste).
- Das Test-Plugin `kinds-test` hat dafür eine Eltern/Kind-Tabelle und meldet Kinder, Regel („Elternelement nicht im Papierkorb“) und Aufräumen an; es ist die Vorlage für die Fach-Plugins.

### Decided

- Abschlusskriterien geprüft: (1) Löschen mit Kindern fragt nach und legt alle in den Papierkorb (`test_trash.py`, `useDeleteElement.test.tsx`); (2) die Ansicht zeigt Elemente aller Plugins der sichtbaren Projekte mit Löschdatum, nach Suche gefiltert (`TrashPage.test.tsx`); (3) Wiederherstellen und endgültig Löschen einzeln und gesammelt, gewählte Nachkommen gewählter Elemente werden übergangen (`test_a_chosen_descendant_of_a_chosen_element_is_skipped`); (4) kein endgültiges Löschen über MCP (`purge_elements` hat `mcp=False`, im Test geprüft); (5) alle Tests grün.
- `scripts/check-next.sh` und `scripts/check.sh` grün.
- Status: `Awaiting confirmation`.

### Open

- Frage 26 in `STORY-060` (Annahme gilt).
- Nicht geprüft: die Zusammenarbeit mit echten Fach-Plugins (Backlog, Notes); sie melden ihre Ports mit ihren Items an. Die Darstellung gelöschter Kinder im Detailpanel kommt mit `STORY-071`. „Nur der Projektinhaber darf endgültig löschen“ ist durch den Ausschluss aus MCP umgesetzt (die Weboberfläche ist die einzige Schnittstelle dafür); eine Anmeldung gibt es im Neubau nicht.
