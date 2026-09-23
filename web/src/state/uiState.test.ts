import { INITIAL_UI_STATE, mergeStored, snapshot, uiReducer } from "./uiState";

describe("uiState", () => {
  it("reads the old frontend's stored format and ignores garbage", () => {
    const state = mergeStored(INITIAL_UI_STATE, {
      hiddenProjects: ["A", 3],
      collapsed: ["P::EPIC-1"],
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
      search: "x",
      selectedId: "P::TASK-1",
      currentView: "kanban",
      lang: "en",
    });
    expect(mergeStored(INITIAL_UI_STATE, { currentView: "nope", lang: "fr" })).toEqual(INITIAL_UI_STATE);
    expect(mergeStored(INITIAL_UI_STATE, "broken")).toBe(INITIAL_UI_STATE);
  });

  it("toggles hidden values and collapsed nodes", () => {
    const hidden = uiReducer(INITIAL_UI_STATE, { type: "toggleHidden", kind: "hiddenStatuses", value: "Rejected" });
    expect([...hidden.hiddenStatuses]).toEqual(["Rejected"]);
    expect([...uiReducer(hidden, { type: "toggleHidden", kind: "hiddenStatuses", value: "Rejected" }).hiddenStatuses]).toEqual([]);
    const shown = uiReducer({ ...INITIAL_UI_STATE, hiddenProjects: new Set(["A"]) }, { type: "showProject", project: "A" });
    expect(shown.hiddenProjects.size).toBe(0);
  });
});
