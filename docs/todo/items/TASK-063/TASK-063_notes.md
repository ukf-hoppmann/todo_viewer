# TASK-063 — Mindmap: Äste zwischen Bäumen umhängen und übertragen

## State

- Goal/Status: Vom Projekteigner am 2026-11-19 bestätigt (`Completed`); auf `main`, Release v0.11.0.
- Next step: Keiner; der Eintrag ist abgeschlossen.
- Open:
  - Keine
- Decided:
  - Umhängen (aus A weg, in B drin; auch innerhalb eines Baums) und Übertragen (derselbe Ast in A und B; nur zwischen Bäumen), beides nur innerhalb eines Projekts, nichts wird kopiert (2026-11-19)
  - Bedienung: Kontextmenü „Umhängen nach …“ / „Übertragen nach …“ und Ziehen auf einen Eintrag der Map-Liste; Ziel ist die Wurzel der Ziel-Map (2026-11-19)
  - Beides auch über API und MCP, damit die KI Äste verschieben kann (2026-11-19)
  - Verbotene Ziele werden abgelehnt, mit Meldung der Knoten; in der Oberfläche ausgegraut mit Grund; kein Zusammenführen (2026-11-19)
  - Inhalt eines übertragenen Knotens gemeinsam, Struktur darunter je Baum eigen; Zahl und Zustand je Baum berechnet (2026-11-19)
  - Übertragene Äste: Symbol beim Überfahren, schaltbarer Rand, Baumauswahl beim Sprung (2026-11-19)
  - „Hier entfernen“ und „Knoten löschen“ getrennt; letzte Platzierung weg heißt Papierkorb (2026-11-19)
  - Backend „wiederherstellen und umziehen“ für Knoten im Papierkorb, auch API und MCP (2026-11-19)
  - Vorsichtige Annahmen der Umsetzung: Heimatlos gewordene Unterknoten rücken in ihrer Platzierung unter den Parent des entfernten Asts; ein Unterknoten im Papierkorb blockiert ein Ziel ebenfalls; der Papierkorb von `workspace` kaskadiert nur über ausschließlich dort stehende Unterknoten (2026-11-19)
- References: Spec `TASK-063_spec.md`; Story-Spec `STORY-102_spec.md`; Konzept `EPIC-008_spec.md`; Ideensammlung `TASK-064`; Folge-Tasks `TASK-066`, `TASK-067`

State confirmed after entry 2026-11-19 — Umsetzung (ad3560aa1c24)


## 2026-11-19 — Übernahme der Entscheidungen aus STORY-102

### Discussed

- Bedienung: A Kontextmenü, B Ziehen auf die Map-Liste, C Zielknoten im Dialog. Der Owner wählte A und B zusammen; die Gesamtansicht als dritter Weg entfällt, weil sie nur Projektbäume zeigt und der Code das Verschieben nur innerhalb eines Projekts erlaubt.
- Projektgrenze: Äste wandern nicht zwischen Projekten (Empfehlung angenommen, weil Übergreifendes nach „Allgemein“ gehört). Der Owner fordert API und MCP, weil er viel an die KI auslagern will; sein Wort „kopieren“ meint das Übertragen.
- Struktur: Je Baum eigen (Empfehlung) oder gemeinsam. Gemeinsam hätte beim Herausziehen eines Unterknotens aus dem Ast offene Folgen für die anderen Bäume. Eine Doppelzählung unter einer Wurzel kann nach den Regeln nicht entstehen; das Kriterium bleibt als Test.
- Markierung: Symbol mit Baumzahl nur beim Überfahren, dazu ein Schalter, der alle übertragenen Äste mit einem Rand einfärbt (Owner, damit die Karte ruhig bleibt und man sie trotzdem gezielt sehen kann). Sprung zu einem Knoten in mehreren Bäumen: Auswahl des Baums statt einer festen Regel.
- Entfernen: Nur „Löschen“, wenn der Knoten in einem Baum steht; Rückfrage mit den Bäumen bei einem geteilten Knoten; „Hier entfernen“ ohne Rückfrage; getrennte Namen in API und MCP. Das Wiederherstellen von „Hier entfernen“ liegt in `TASK-066`.
- Verbotene Fälle: Ablehnen (Empfehlung) oder Zusammenführen; Zusammenführen wäre bequem, die Struktur entspräche aber nicht mehr der Quelle.
- Papierkorb: Der Owner will Knoten von dort an eine neue Stelle ziehen. Das Backend (wiederherstellen und umziehen) gehört hierher, die Oberfläche in `TASK-067`.

### Decided

- A und B; C entfällt vorerst.
- Nur innerhalb eines Projekts; API und MCP für Umhängen und Übertragen.
- Struktur je Baum eigen, Inhalt gemeinsam.
- Symbol beim Überfahren plus schaltbarer Rand; Sprung per Baumauswahl.
- Getrenntes „Hier entfernen“ und „Knoten löschen“; Rückfrage bei geteilten Knoten; letzte Platzierung weg heißt Papierkorb.
- Ablehnen statt Zusammenführen; Wurzel einer Map nicht bewegbar; Knoten im Papierkorb nicht bewegbar.
- Backend „wiederherstellen und umziehen“ in einem Schritt.

### Open

- Keine

## 2026-11-19 — Umsetzung

### Discussed

- Wie ein Knoten „heimatlos“ wird: Ein Knoten ist es, wenn er nach dem Schnitt in keinem Baum außerhalb des Papierkorbs mehr steht. Die Rechnung läuft über alle Bäume zugleich (`plan_cuts`), weil beim Löschen eines Knotens, der in mehreren Bäumen steht, dessen Äste in jedem Baum geschnitten werden und ein Unterknoten nur bleibt, wenn er außerhalb aller Schnitte noch steht.
- Die Platzierung eines heimatlosen Knotens bleibt (wie bisher beim Löschen), damit er zurückkommen kann. Ist sein Parent-Platz im selben Baum aber weg (der Parent bleibt anderswo und verlässt nur diesen Baum), hinge die Platzierung ins Leere: Option 1 an der Wurzel, Option 2 unter den nächsten verbleibenden Vorfahren (der Parent des entfernten Asts). Gewählt 2, weil der Knoten beim Wiederherstellen dort steht, wo der Ast vorher stand. Das Merken der entfernten Platzierung selbst ist `TASK-066`.
- Papierkorb von `workspace`: seine Kaskade (`children`) folgte bisher allen Platzierungen; für Knoten in mehreren Bäumen wäre das falsch. Die Liste der Unterknoten nimmt jetzt nur Knoten, die ausschließlich unter dem Parent stehen. Für geteilte Knoten sind `delete_node` und `remove_node_from_map` der richtige Weg (eigene Operationen, getrennt in API und MCP, wie gefordert); `workspace_delete_element` bleibt allgemein und für Knoten in einem Baum unverändert.
- Neue Unterknoten: Sie entstehen in jedem Baum, in dem der Parent steht, auch in einer Map im Papierkorb (sonst fehlte der Knoten nach dem Wiederherstellen der Map).
- Ziel: Ein Unterknoten im Papierkorb, der schon im Ziel steht, blockiert ebenfalls (höchstens eine Platzierung je Knoten und Baum); die Meldung nennt ihn.
- „Wurzel einer Map als Quelle“: eine Wurzel ist kein Knoten; abgelehnt wird die Map-Uid als `ref` (`mindmap_root_fixed`).
- `get_node` ohne `tree` für einen Knoten in mehreren Bäumen: bisher Fehler, jetzt Lesen im Projektbaum (sonst erste freie Map); Schreiben verlangt weiter die Angabe.
- Wiederherstellen und umziehen: erst die Platzierung im Baum setzen, dann über `workspace` wiederherstellen (der Schutz „Parent im Papierkorb“ gilt sonst gerade für den Fall, um den es geht). Die Platzierungen in anderen Bäumen prüft die Operation vorher mit demselben Schutz; steht dort der Parent im Papierkorb, bricht sie ab (`mindmap_parent_in_trash`), bevor etwas geändert ist.
- Oberfläche: Menü per Rechtsklick und Knopf in der Aktionsleiste (Rechtsklick allein wäre schlecht auffindbar); beim Ziehen trägt der Knoten zusätzlich einen eigenen Medientyp, den die Map-Liste annimmt. Die Karte selbst nimmt weiter nur Knoten an.

### Decided

- Umgesetzt wie in der Spec; Server `application/branches.py`, `domain/branches.py`; Operationen `move_node_to_map`, `transfer_node_to_map`, `remove_node_from_map`, `delete_node`, `restore_and_move_node`, `list_node_trees`; `tree_count` je Knoten im Baum; Oberfläche `BranchDialog`, `NodeMenus`, Markierung, Schalter „Übertragene Äste einrahmen“, Baumauswahl bei „Gehe hin“.
- Die Projekt-Uid als `target` nennt den Projektbaum, auch wenn er noch keinen Knoten hat.
- Nicht Teil: entfernte Platzierungen wieder einsetzen (`TASK-066`), Papierkorb-Ansicht und Ziehen daraus (`TASK-067`). Die Oberfläche für „wiederherstellen und umziehen“ gehört zu `TASK-067`.

### Open

- Keine.
