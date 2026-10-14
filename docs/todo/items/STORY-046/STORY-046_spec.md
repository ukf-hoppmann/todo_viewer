# STORY-046 — Spec: Doku und Release

## Was und warum
Die Doku beschreibt den Stand nach der Umsetzung (Skill `claude-harness:techdocs`), das Release hält ihn fest (Skill `claude-harness:semver`).

## Inhalte
- **Techdocs:** `architecture.md` (Modell, Schichten, Auslöser-Auswertung ohne Takt), `interfaces.md` (API für Topics, Notes, Links, Index, Zähler, Fällig-Liste, Fehlercodes), `configuration.md` (`notes.review_days`, `notes.max_topic_depth`), `operations.md` (Zeitzone, Backup der Notes mit der Datenbank, Verhalten bei nicht erreichbaren Projekten).
- **README:** Bedienung des Bereichs Notes und des Ausrufezeichens.
- **Harness-Prompt:** `docs/notes-harness-prompt.md` ist teilweise überholt (Tiefe 2, „feuert beim frühesten", keine Notizen und Specs an Notes, Markdown-Spiegel „optional") und muss vor der Weitergabe an den Harness angepasst werden.
- **Release:** neue Minor-Version, Tag, Tagesbericht.

## Abnahme
- Die Doku beschreibt Modell, API, Auslöser und Bedienung und widerspricht dem Code nicht.
- Das Release ist getaggt und `docs/VERSION` stimmt.
