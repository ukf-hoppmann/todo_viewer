# STORY-066 — Client-Grundgerüst: ezf-ui-Core ohne Login, Layout, SSE, UI-Zustand

## 2026-10-16 — Entscheidungen

### Decided

- Stack bleibt: React/Vite/TypeScript; im Frontend Redux Toolkit wie in ezf-ui.
- Der Frontend-Core wird aus ezf-ui kopiert; das Login fliegt raus.
- Layout ähnlich ezf-ui: Kopfzeile und Seitenleiste mit austauschbaren Elementen; die Seitenleiste bleibt.
- SSE als Rückkanal; Polling entfällt.
