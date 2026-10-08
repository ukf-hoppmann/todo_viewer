import { INITIAL_UI_STATE, mergeStored, snapshot, uiReducer } from "./uiState";

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
      collapsed: ["P::EPIC-1"],
      markedProjects: ["A"],
      search: "x",
      selectedId: "P::TASK-1",
      currentView: "kanban",
      lang: "en",
      defaultBackend: "markdown",
      notesProject: null,
      notesTopic: null,
      selectedNote: null,
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

  it("remembers the Notes area and jumps to a note", () => {
    const scoped = uiReducer(INITIAL_UI_STATE, { type: "notesScope", project: "P", topic: { project: "P", label: "TOPIC-001" } });
    expect(snapshot(scoped)).toMatchObject({ notesProject: "P", notesTopic: { project: "P", label: "TOPIC-001" } });

    const opened = uiReducer(scoped, { type: "openNote", note: { project: "Q", label: "NOTE-004" } });
    expect(opened.currentView).toBe("notes");
    expect(snapshot(opened).selectedNote).toEqual({ project: "Q", label: "NOTE-004" });

    const restored = mergeStored(INITIAL_UI_STATE, snapshot(opened));
    expect(restored.selectedNote).toEqual({ project: "Q", label: "NOTE-004" });
    expect(mergeStored(INITIAL_UI_STATE, { selectedNote: { project: 1 } }).selectedNote).toBeNull();
    expect(uiReducer(opened, { type: "selectNote", note: null }).selectedNote).toBeNull();
  });
});
