import { toItems } from "./model";
import { parentCandidates, promoteDraft, promoteRequest } from "./conversion";

const apiItem = (id: string, over: Record<string, unknown> = {}) => ({
  key: `s/${id}`,
  source_id: "s",
  id,
  version: `v-${id}`,
  archived: false,
  project: "P",
  type: "Task",
  title: `Title ${id}`,
  status: "Open",
  parent: null,
  required_for_parent: null,
  dependencies: [],
  created: null,
  area: null,
  priority: null,
  goal: null,
  completion_criteria: null,
  summary: null,
  resolution: null,
  documents: [],
  deleted: null,
  extra_fields: {},
  archive_supported: true,
  ...over,
});

describe("promoteDraft", () => {
  it("takes title and summary from the note's summary and the goal from its long text", () => {
    expect(promoteDraft({ summary: "Check the sync", body: "Look at both directions." })).toMatchObject({
      item_type: "Story",
      title: "Check the sync",
      summary: "Check the sync",
      goal: "Look at both directions.",
      area: "",
      completion_criteria: "",
      priority: "Normal",
      parent: "",
      required_for_parent: "",
    });
  });

  it("falls back to the summary for the goal when there is no long text", () => {
    expect(promoteDraft({ summary: "Check the sync", body: null }).goal).toBe("Check the sync");
  });
});

describe("promoteRequest", () => {
  const draft = { ...promoteDraft({ summary: "S", body: null }), area: " Core ", completion_criteria: " Done. ", title: " A title " };

  it("sends the version and the trimmed fields, and leaves out parent and flag when there is no parent", () => {
    expect(promoteRequest(draft, "v1")).toEqual({
      version: "v1",
      item_type: "Story",
      area: "Core",
      goal: "S",
      completion_criteria: "Done.",
      title: "A title",
      summary: "S",
      priority: "Normal",
    });
  });

  it("adds the parent and whether it is required for it", () => {
    expect(promoteRequest({ ...draft, parent: "EPIC-001", required_for_parent: "Yes" }, "v1")).toMatchObject({ parent: "EPIC-001", required_for_parent: "Yes" });
  });

  it("leaves out an empty title and summary so that the server takes them from the note", () => {
    const request = promoteRequest({ ...draft, title: " ", summary: "" }, "v1");
    expect(request).not.toHaveProperty("title");
    expect(request).not.toHaveProperty("summary");
  });
});

describe("parentCandidates", () => {
  const items = toItems([
    apiItem("EPIC-001", { type: "Epic" }),
    apiItem("EPIC-002", { type: "Epic", status: "Completed" }),
    apiItem("STORY-001", { type: "Story", parent: "EPIC-001" }),
    apiItem("TASK-001", { parent: "STORY-001" }),
    apiItem("EPIC-001", { type: "Epic", project: "Q", key: "t/EPIC-001", source_id: "t" }),
  ]);

  it("offers the open items of the project that can be a parent of the type", () => {
    expect(parentCandidates(items, "P", "Task").map((i) => i.id)).toEqual(["EPIC-001", "STORY-001"]);
    expect(parentCandidates(items, "P", "Story").map((i) => i.id)).toEqual(["EPIC-001"]);
  });

  it("offers nothing for an epic", () => {
    expect(parentCandidates(items, "P", "Epic")).toEqual([]);
  });
});
