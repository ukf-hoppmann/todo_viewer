# STORY-061 — Server-Grundgerüst: Core mit Plugin-Host, HTTP, Ereignissen und SSE

## 2026-10-16 — Entscheidungen

### Decided

- Plugins aus einer festen Liste in der Composition Root, zunächst alle.
- Operationen werden einmal beschrieben; HTTP-Route und MCP-Tool werden daraus erzeugt.
- SSE ist der allgemeine Kanal vom Backend ins Frontend; die API ist der Weg vom Frontend ins Backend.
- Composition Root wie in my_story_game: dort werden die Operationen zusammengesteckt.
