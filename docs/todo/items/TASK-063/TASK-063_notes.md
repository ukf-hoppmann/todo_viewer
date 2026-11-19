# TASK-063 — Mindmap: Äste zwischen Bäumen umhängen und übertragen

## State

- Goal/Status: Geplant; Entscheidungen aus der Besprechung von `STORY-102` übernommen.
- Next step: Nach `TASK-062` beginnen; Plan beim Start vorstellen.
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
- References: Spec `TASK-063_spec.md`; Story-Spec `STORY-102_spec.md`; Konzept `EPIC-008_spec.md`; Ideensammlung `TASK-064`; Folge-Tasks `TASK-066`, `NEW-papierkorb-ansicht`

State confirmed after entry 2026-11-19 — Übernahme der Entscheidungen aus STORY-102 (c54de6080214)

## 2026-11-19 — Übernahme der Entscheidungen aus STORY-102

### Discussed

- Bedienung: A Kontextmenü, B Ziehen auf die Map-Liste, C Zielknoten im Dialog. Der Owner wählte A und B zusammen; die Gesamtansicht als dritter Weg entfällt, weil sie nur Projektbäume zeigt und der Code das Verschieben nur innerhalb eines Projekts erlaubt.
- Projektgrenze: Äste wandern nicht zwischen Projekten (Empfehlung angenommen, weil Übergreifendes nach „Allgemein“ gehört). Der Owner fordert API und MCP, weil er viel an die KI auslagern will; sein Wort „kopieren“ meint das Übertragen.
- Struktur: Je Baum eigen (Empfehlung) oder gemeinsam. Gemeinsam hätte beim Herausziehen eines Unterknotens aus dem Ast offene Folgen für die anderen Bäume. Eine Doppelzählung unter einer Wurzel kann nach den Regeln nicht entstehen; das Kriterium bleibt als Test.
- Markierung: Symbol mit Baumzahl nur beim Überfahren, dazu ein Schalter, der alle übertragenen Äste mit einem Rand einfärbt (Owner, damit die Karte ruhig bleibt und man sie trotzdem gezielt sehen kann). Sprung zu einem Knoten in mehreren Bäumen: Auswahl des Baums statt einer festen Regel.
- Entfernen: Nur „Löschen“, wenn der Knoten in einem Baum steht; Rückfrage mit den Bäumen bei einem geteilten Knoten; „Hier entfernen“ ohne Rückfrage; getrennte Namen in API und MCP. Das Wiederherstellen von „Hier entfernen“ liegt in `TASK-066`.
- Verbotene Fälle: Ablehnen (Empfehlung) oder Zusammenführen; Zusammenführen wäre bequem, die Struktur entspräche aber nicht mehr der Quelle.
- Papierkorb: Der Owner will Knoten von dort an eine neue Stelle ziehen. Das Backend (wiederherstellen und umziehen) gehört hierher, die Oberfläche in `NEW-papierkorb-ansicht`.

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
