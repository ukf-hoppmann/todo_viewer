import type { ApiItem } from "../api/client";
import {
  buildTrees,
  collapsibleUids,
  defaultResolution,
  dependencyGraph,
  filterItems,
  filterOptions,
  groupByStatus,
  itemProgress,
  needsResolution,
  projectProgress,
  sortByKeyOrder,
  statusOptions,
  toItems,
} from "./model";

function apiItem(id: string, overrides: Partial<ApiItem> = {}): ApiItem {
  return {
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
    notes: [],
    spec: [],
    extra_fields: {},
    archive_supported: true,
    ...overrides,
  };
}

const noFilters = { hiddenProjects: new Set<string>(), hiddenStatuses: new Set<string>(), hiddenPriorities: new Set<string>(), search: "" };

describe("model", () => {
  const items = toItems([
    apiItem("EPIC-1", { type: "Epic", status: "In progress" }),
    apiItem("STORY-1", { parent: "EPIC-1", status: "Completed", priority: "Urgent" }),
    apiItem("TASK-1", { parent: "STORY-1", dependencies: ["TASK-2"], priority: "Custom" }),
    apiItem("TASK-2", { parent: "STORY-1", required_for_parent: false, status: "Completed" }),
    apiItem("X-1", { project: "Other", title: "Findme" }),
  ]);

  it("links parents and dependencies within a project", () => {
    expect(items[2]).toMatchObject({ uid: "P::TASK-1", parentUid: "P::STORY-1", dependencyUids: ["P::TASK-2"] });
  });

  it("sorts known keys first", () => {
    expect(sortByKeyOrder(["Zeta", "Completed", "Open", "Alpha"], ["Open", "Completed"])).toEqual(["Open", "Completed", "Alpha", "Zeta"]);
  });

  it("filters by hidden values and search; items without priority survive priority filters", () => {
    expect(filterItems(items, { ...noFilters, hiddenPriorities: new Set(["Urgent", "Custom"]) }).map((i) => i.id))
      .toEqual(["EPIC-1", "TASK-2", "X-1"]);
    expect(filterItems(items, { ...noFilters, search: "findme" }).map((i) => i.id)).toEqual(["X-1"]);
    expect(filterItems(items, { ...noFilters, search: "task-2" }).map((i) => i.id)).toEqual(["TASK-2"]);
  });

  it("offers filter values in key order", () => {
    expect(filterOptions(items, [])).toEqual({
      projects: ["Other", "P"],
      statuses: ["Open", "In progress", "Completed"],
      priorities: ["Urgent", "Custom"],
    });
  });

  it("builds trees; hidden parents promote children to roots; optional children are marked", () => {
    const [other, p] = buildTrees(items.filter((i) => i.id !== "EPIC-1"), items);
    expect(other?.project).toBe("Other");
    expect(p?.roots.map((n) => n.item.id)).toEqual(["STORY-1"]);
    expect(p?.roots[0]?.children.map((n) => [n.item.id, n.optional])).toEqual([["TASK-1", false], ["TASK-2", true]]);
  });

  it("counts progress over all items, skipping optional and rejected ones", () => {
    expect(projectProgress(items, "P")).toEqual({ done: 1, total: 3 });
    const withRejected = toItems([apiItem("A-1", { status: "Completed" }), apiItem("A-2", { status: "Rejected" }), apiItem("A-3")]);
    expect(projectProgress(withRejected, "P")).toEqual({ done: 1, total: 2 });
  });

  it("counts item progress over required, non-rejected descendants", () => {
    const progress = itemProgress(items);
    expect(progress.get("P::EPIC-1")).toEqual({ done: 1, total: 2 });
    expect(progress.get("P::STORY-1")).toEqual({ done: 0, total: 1 });
    expect(progress.has("P::TASK-1")).toBe(false);
    const withRejected = toItems([
      apiItem("E-1", { type: "Epic" }),
      apiItem("S-1", { parent: "E-1", status: "Rejected" }),
      apiItem("T-1", { parent: "S-1", status: "Completed" }),
    ]);
    expect(itemProgress(withRejected).has("P::E-1")).toBe(false);
  });

  it("groups by status in key order", () => {
    expect(groupByStatus(items).map((g) => [g.status, g.items.length])).toEqual([["Open", 2], ["In progress", 1], ["Completed", 2]]);
  });

  it("keeps only connected items in the dependency graph", () => {
    expect(dependencyGraph(items)).toMatchObject({ edges: [{ from: "P::TASK-2", to: "P::TASK-1" }] });
    expect(dependencyGraph(items).nodes.map((n) => n.id)).toEqual(["TASK-1", "TASK-2"]);
  });

  it("knows the editing rules", () => {
    const [odd] = toItems([apiItem("X-1", { status: "Blocked", archive_supported: false })]);
    expect(statusOptions(odd!)).toEqual(["Open", "In progress", "Awaiting confirmation", "Completed", "Rejected", "Blocked"]);
    expect(needsResolution(items[0]!, "Rejected")).toBe(true);
    expect(needsResolution(odd!, "Completed")).toBe(false);
    expect(defaultResolution("Completed", new Date("2026-09-23T10:00:00Z"))).toBe("Confirmed by the project owner on 2026-09-23.");
  });
});

describe("collapsibleUids", () => {
  const all = toItems([
    apiItem("EPIC-1", { type: "Epic" }),
    apiItem("EPIC-2", { type: "Epic" }),
    apiItem("STORY-1", { type: "Story", parent: "EPIC-1" }),
    apiItem("TASK-1", { parent: "STORY-1" }),
    apiItem("EPIC-1", { type: "Epic", project: "Q", key: "t/EPIC-1", source_id: "t" }),
    apiItem("STORY-1", { type: "Story", project: "Q", key: "t/STORY-1", source_id: "t", parent: "EPIC-1" }),
  ]);

  it("returns items of the type that have children, in all projects when none is given", () => {
    expect(collapsibleUids(all, "Epic", new Set())).toEqual(["P::EPIC-1", "Q::EPIC-1"]);
    expect(collapsibleUids(all, "Story", new Set())).toEqual(["P::STORY-1"]);
  });

  it("limits the result to the given projects", () => {
    expect(collapsibleUids(all, "Epic", new Set(["Q"]))).toEqual(["Q::EPIC-1"]);
  });
});
