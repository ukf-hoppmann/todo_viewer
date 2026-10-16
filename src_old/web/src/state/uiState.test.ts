import { INITIAL_UI_STATE, mergeStored, scopeOf, snapshot, uiReducer } from "./uiState";

describe("uiState", () => {
  it("reads the old frontend's stored format and ignores garbage", () => {
    const state = mergeStored(INITIAL_UI_STATE, {
      hiddenProjects: ["A", 3],
      collapsed: ["P::EPIC-1"],
      markedProjects: ["A"],
      search: "x",
      selectedId: "P::TASK-1",
      currentView: "kanban",
      lang: "en",
      unknown: true,
    });
    expect(snapshot(state)).toEqual({
      hiddenProjects: ["A"],
      hiddenStatuses: [],
      hiddenPriorities: [],
      hiddenNoteStatuses: ["done", "dropped", "promoted"],
      collapsed: ["P::EPIC-1"],
      markedProjects: ["A"],
      search: "x",
      selectedId: "P::TASK-1",
      currentView: "kanban",
      lang: "en",
      defaultBackend: "markdown",
      selectedNote: null,
      notesHighlight: true,
      syncScopes: {},
    });
    expect(mergeStored(INITIAL_UI_STATE, { currentView: "nope", lang: "fr" })).toEqual(INITIAL_UI_STATE);
    expect(mergeStored(INITIAL_UI_STATE, { currentView: "trash" }).currentView).toBe("trash");
    expect(mergeStored(INITIAL_UI_STATE, "broken")).toBe(INITIAL_UI_STATE);
  });

  it("toggles hidden values and collapsed nodes", () => {
    const hidden = uiReducer(INITIAL_UI_STATE, { type: "toggleHidden", kind: "hiddenStatuses", value: "Rejected" });
    expect([...hidden.hiddenStatuses]).toEqual(["Rejected"]);
    expect([...uiReducer(hidden, { type: "toggleHidden", kind: "hiddenStatuses", value: "Rejected" }).hiddenStatuses]).toEqual([]);
    const shown = uiReducer({ ...INITIAL_UI_STATE, hiddenProjects: new Set(["A"]) }, { type: "showProject", project: "A" });
    expect(shown.hiddenProjects.size).toBe(0);
  });

  it("keeps the note status filter apart from the backlog filters, closed notes hidden by default", () => {
    expect([...INITIAL_UI_STATE.hiddenNoteStatuses]).toEqual(["done", "dropped", "promoted"]);
    const shown = uiReducer(INITIAL_UI_STATE, { type: "toggleHidden", kind: "hiddenNoteStatuses", value: "done" });
    expect([...shown.hiddenNoteStatuses]).toEqual(["dropped", "promoted"]);
    expect(shown.hiddenStatuses).toBe(INITIAL_UI_STATE.hiddenStatuses);
    expect([...mergeStored(INITIAL_UI_STATE, snapshot(shown)).hiddenNoteStatuses]).toEqual(["dropped", "promoted"]);
    const reset = uiReducer({ ...shown, hiddenNoteStatuses: new Set(["waiting"]) }, { type: "resetNoteStatuses" });
    expect(reset.hiddenNoteStatuses).toEqual(INITIAL_UI_STATE.hiddenNoteStatuses);
  });

  it("switches the extended marking of the notes tree, on by default, and keeps it", () => {
    expect(INITIAL_UI_STATE.notesHighlight).toBe(true);
    const plain = uiReducer(INITIAL_UI_STATE, { type: "notesHighlight", on: false });
    expect(plain.notesHighlight).toBe(false);
    expect(mergeStored(INITIAL_UI_STATE, snapshot(plain)).notesHighlight).toBe(false);
    expect(mergeStored(INITIAL_UI_STATE, { notesHighlight: "no" }).notesHighlight).toBe(true);
  });

  it("marks projects and collapses or expands a set of nodes at once", () => {
    const marked = uiReducer(INITIAL_UI_STATE, { type: "toggleMarked", project: "A" });
    expect([...marked.markedProjects]).toEqual(["A"]);
    expect(uiReducer(marked, { type: "toggleMarked", project: "A" }).markedProjects.size).toBe(0);

    const start = { ...INITIAL_UI_STATE, collapsed: new Set(["x"]) };
    const closed = uiReducer(start, { type: "setCollapsed", uids: ["a", "b"], collapsed: true });
    expect([...closed.collapsed]).toEqual(["x", "a", "b"]);
    expect([...uiReducer(closed, { type: "setCollapsed", uids: ["a", "b"], collapsed: false }).collapsed]).toEqual(["x"]);
  });

  it("keeps the backend new projects start with, and ignores anything else", () => {
    expect(INITIAL_UI_STATE.defaultBackend).toBe("markdown");
    expect(mergeStored(INITIAL_UI_STATE, { defaultBackend: "database" }).defaultBackend).toBe("database");
    expect(mergeStored(INITIAL_UI_STATE, { defaultBackend: "postgres" }).defaultBackend).toBe("markdown");
    expect(mergeStored({ ...INITIAL_UI_STATE, defaultBackend: "database" }, { defaultBackend: 3 }).defaultBackend).toBe("database");

    const chosen = uiReducer(INITIAL_UI_STATE, { type: "defaultBackend", backend: "database" });
    expect(chosen.defaultBackend).toBe("database");
    expect(snapshot(chosen).defaultBackend).toBe("database");
  });

  it("remembers the sync direction per project, both ways being the default", () => {
    expect(INITIAL_UI_STATE.syncScopes).toEqual({});
    expect(scopeOf(INITIAL_UI_STATE, "s1")).toBe("both");

    const one = uiReducer(INITIAL_UI_STATE, { type: "syncScope", sourceId: "s1", scope: "to_md" });
    expect(scopeOf(one, "s1")).toBe("to_md");
    expect(scopeOf(one, "s2")).toBe("both");  // other projects are not touched
    expect(snapshot(one).syncScopes).toEqual({ s1: "to_md" });
    expect(scopeOf(mergeStored(INITIAL_UI_STATE, snapshot(one)), "s1")).toBe("to_md");

    // Going back to the default drops the entry instead of storing it.
    expect(uiReducer(one, { type: "syncScope", sourceId: "s1", scope: "both" }).syncScopes).toEqual({});
  });

  it("ignores a stored sync direction that is not one of the three", () => {
    expect(mergeStored(INITIAL_UI_STATE, { syncScopes: { a: "sideways", b: "from_md", c: 3 } }).syncScopes).toEqual({ b: "from_md" });
    expect(mergeStored(INITIAL_UI_STATE, { syncScopes: "x" }).syncScopes).toEqual({});
    expect(mergeStored({ ...INITIAL_UI_STATE, syncScopes: { a: "to_md" } }, { syncScopes: null }).syncScopes).toEqual({ a: "to_md" });
  });

  it("remembers the Notes area and jumps to a note", () => {
    // A topic chosen by an older version is no longer part of the state.
    expect(snapshot(mergeStored(INITIAL_UI_STATE, { notesTopic: { project: "P", label: "TOPIC-001" } }))).not.toHaveProperty("notesTopic");

    const opened = uiReducer(INITIAL_UI_STATE, { type: "openNote", note: { project: "Q", label: "NOTE-004" } });
    expect(opened.currentView).toBe("notes");
    expect(snapshot(opened).selectedNote).toEqual({ project: "Q", label: "NOTE-004" });

    const restored = mergeStored(INITIAL_UI_STATE, snapshot(opened));
    expect(restored.selectedNote).toEqual({ project: "Q", label: "NOTE-004" });
    expect(mergeStored(INITIAL_UI_STATE, { selectedNote: { project: 1 } }).selectedNote).toBeNull();
    expect(uiReducer(opened, { type: "selectNote", note: null }).selectedNote).toBeNull();
  });
});
