import { describe, expect, it } from "vitest";
import { item } from "../../../../../helpers/client/backlogFixtures";
import { collapsibleIds, filterItems, groupByProject, placementOf, projectProgress, toFlatNodes } from "../../../../../../client/src/plugins/backlog/model";

const none = { hiddenStatuses: new Set<string>(), hiddenPriorities: new Set<string>(), search: "" };

describe("filterItems", () => {
	const items = [item("a"), item("b", { status: "Completed", priority: "Urgent" }), item("c", { title: "Sync reparieren" })];

	it("lets everything through without filters", () => {
		expect(filterItems(items, none)).toHaveLength(3);
	});

	it("hides statuses and priorities that are switched off", () => {
		expect(filterItems(items, { ...none, hiddenStatuses: new Set(["Completed"]) }).map((i) => i.uid)).toEqual(["a", "c"]);
		expect(filterItems(items, { ...none, hiddenPriorities: new Set(["Urgent"]) }).map((i) => i.uid)).toEqual(["a", "c"]);
	});

	it("searches title and label without regard to case", () => {
		expect(filterItems(items, { ...none, search: " SYNC " }).map((i) => i.uid)).toEqual(["c"]);
		expect(filterItems(items, { ...none, search: "b" }).map((i) => i.uid)).toEqual(["b"]);
	});
});

describe("projectProgress", () => {
	it("does not count optional or rejected items", () => {
		const items = [item("a", { status: "Completed" }), item("b"), item("c", { required_for_parent: false, status: "Completed" }), item("d", { status: "Rejected" })];

		expect(projectProgress(items)).toEqual({ done: 1, total: 2 });
		expect(projectProgress([])).toEqual({ done: 0, total: 0 });
	});
});

describe("groupByProject", () => {
	it("keeps the order of the projects and leaves out projects without items", () => {
		const projects = [{ uid: "p0" }, { uid: "p1" }, { uid: "p2" }];

		const groups = groupByProject(projects, [item("a", { project_uid: "p2" }), item("b", { project_uid: "p1" }), item("c", { project_uid: "p2" })]);

		expect(groups.map((g) => [g.project.uid, g.items.map((i) => i.uid)])).toEqual([
			["p1", ["b"]],
			["p2", ["a", "c"]],
		]);
	});
});

describe("toFlatNodes", () => {
	it("makes nodes with badge, color, progress and a dashed mark for optional children only", () => {
		const nodes = toFlatNodes([
			item("e", { type: "Epic", progress: { done: 1, total: 2 }, status: "In progress" }),
			item("s", { parent_uid: "e", required_for_parent: false }),
			item("t", { required_for_parent: false }),
		]);

		expect(nodes[0]).toMatchObject({ id: "e", parentId: null, badge: "E", label: "Titel e", progress: { done: 1, total: 2 }, dashed: false });
		expect(nodes[0]!.statusColor).toBe("#d59a3a");
		expect(nodes[1]!.dashed).toBe(true);
		expect(nodes[2]!.dashed).toBe(false); // ein Root ist nie optional
	});
});

describe("collapsibleIds", () => {
	const items = [
		item("e1", { type: "Epic" }),
		item("e2", { type: "Epic", project_uid: "p2" }),
		item("e3", { type: "Epic" }),
		item("s1", { type: "Story", parent_uid: "e1" }),
		item("s2", { type: "Story", parent_uid: "e2", project_uid: "p2" }),
	];

	it("names the items of the type with children, limited to the projects (all if empty)", () => {
		expect(collapsibleIds(items, "Epic", new Set())).toEqual(["e1", "e2"]);
		expect(collapsibleIds(items, "Epic", new Set(["p2"]))).toEqual(["e2"]);
		expect(collapsibleIds(items, "Story", new Set())).toEqual([]);
	});
});

describe("placementOf", () => {
	const items = [
		item("e1", { type: "Epic" }),
		item("e2", { type: "Epic" }),
		item("s1", { type: "Story", parent_uid: "e1" }),
		item("s2", { type: "Story", parent_uid: "e1" }),
		item("s3", { type: "Story", parent_uid: "e1" }),
		item("t1", { parent_uid: "s1" }),
		item("loose"),
		item("other", { project_uid: "p2" }),
	];

	it("drops into an item at the end of its children", () => {
		expect(placementOf(items, "loose", "e1", "inside")).toEqual({ parent: "e1", position: 3 });
		expect(placementOf(items, "t1", "s2", "inside")).toEqual({ parent: "s2", position: 0 });
	});

	it("drops before and after a sibling, counted without the dragged item", () => {
		expect(placementOf(items, "s3", "s1", "before")).toEqual({ parent: "e1", position: 0 });
		expect(placementOf(items, "s3", "s1", "after")).toEqual({ parent: "e1", position: 1 });
		expect(placementOf(items, "s1", "s3", "after")).toEqual({ parent: "e1", position: 2 });
		expect(placementOf(items, "s1", "s2", "before")).toEqual({ parent: "e1", position: 0 });
	});

	it("drops next to a root and makes the item a root", () => {
		expect(placementOf(items, "s1", "loose", "after")).toEqual({ parent: null, position: 3 });
	});

	it("refuses an epic below another item, a child below a task, and a drop on itself", () => {
		expect(placementOf(items, "e2", "e1", "inside")).toBeNull();
		expect(placementOf(items, "e2", "s1", "before")).toBeNull();
		expect(placementOf(items, "loose", "t1", "inside")).toBeNull();
		expect(placementOf(items, "e1", "e1", "inside")).toBeNull();
		expect(placementOf(items, "ghost", "e1", "inside")).toBeNull();
	});

	it("lets an epic move among the roots", () => {
		expect(placementOf(items, "e2", "e1", "before")).toEqual({ parent: null, position: 0 });
	});
});
