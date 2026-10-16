# `TASK-035` — Markdown-Format Version 2

Grundlage: `EPIC-007_spec.md`, Abschnitt 10.

## Ziel

Ein Format, das eine LLM ohne API sicher schreiben kann und das der Sync
eindeutig zuordnet. Es wird hier festgelegt; der Harness folgt nach dem
Umstieg (`STORY-084`).

## Festlegungen

- **Ordner eines Projekts:** `TODO.md`, `archive.md`, `items/<LABEL>/`
  (`<LABEL>_notes.md`, `<LABEL>_spec.md`, `<LABEL>_spec_<thema>.md`),
  `notes/` (`<NOTE-LABEL>.md`, `<NOTE-LABEL>_notes.md`, `…_spec.md`,
  `topics.md`), `alarms.md`.
- **Backlog-Einträge:** Syntax wie Version 1 (Feldnamen englisch), dazu als
  erste Feldzeile `- Uid: <uuid>.` Felder `Notes`/`Spec` entfallen (die
  Dokumente stehen in `items/<LABEL>/` und werden über den Ordner gefunden).
  Kopfzeile `TODO.md`: `Format: backlog format version 2`.
- **Neue Einträge aus der Cloud:** ohne `Uid`, Label als Platzhalter
  `NEW-<kurzname>` (`[a-z0-9-]+`), z. B. `` `NEW-login-dialog` ``. Verweise
  (`Parent`, `Dependencies`, Links) dürfen Platzhalter nennen. Dokumente eines
  neuen Eintrags liegen in `items/NEW-<kurzname>/`. Der Import vergibt Label
  und `Uid`, schreibt Verweise um und benennt Ordner um.
- **Notes:** Kopf wie heute (`Summary`, `Status`, `Topic`, `Review`, `Mode`,
  `Created`, `Updated`, `Archived`, `Deleted`, `Links`, Auslöser) plus
  `Uid:`. Neue Notes in `notes/new-<kurzname>.md` ohne `Uid` und Label.
- **Topics:** `notes/topics.md`, eine Zeile je Topic mit Label, `Uid`, Name,
  Parent, Termin, Erstellt, Gelöscht. Neue Topics mit Platzhalter
  `NEW-<kurzname>`.
- **Wecker:** `alarms.md`, ein Eintrag je Wecker im Listenformat wie
  Backlog-Einträge: Label `ALARM-NNN`, `Uid`, `At` (ISO 8601 UTC mit `Z`),
  `Text`, `Target` (Verweis oder `None`), `Status` (`Pending`, `Due`,
  `Done`, `Snoozed`), `Created`, `Deleted`.
- **Verweise über Projekte:** `<projekt>:<LABEL>` wie heute.
- **`counters.md` entfällt**; Labels vergibt nur die DB.
- **Prioritäten:** nur `Urgent`, `Important`, `Normal`, `Prospective`.
  Status und Typen wie Version 1.
- **Zeiten:** UTC mit `Z`; Daten (`Created`, `Deleted`) als `YYYY-MM-DD`.
- **Prüfregeln** (je Regel ein Fehlercode, Datei und Zeile): unbekanntes
  Feld, fehlendes Pflichtfeld, unbekannter Wert (Priorität, Status, Typ),
  doppelte `Uid`, doppeltes Label, unbekannter Verweis, Zyklus in Parent
  oder Dependencies, Platzhalter mit ungültigem Namen, Merge-Marker.

## Nicht im Umfang

Der Codec selbst (`STORY-075`, `STORY-079`, `STORY-080`); Änderungen am Harness.

## Akzeptanz

Abschlusskriterien des Items. Die Beispiele unter
`tests/fixtures/mirror-v2/` dienen später als Golden Files der Codecs.
