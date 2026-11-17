import { describe, expect, it } from "vitest";
import { canDropItem, defaultOpen, dropPlacement, filterByMark, filterByState, focusPath, isOpen, markLook, nodeLook, parentForNewNode, shownProject, toggledFold, visibleNodes } from "../../../../../../client/src/plugins/mindmap/domain/tree";
import { node } from "../../../../../helpers/client/mindmapFixtures";

const nodes = [node("a"), node("b", null, 1), node("a1", "a"), node("a2", "a", 1), node("a11", "a1"), node("a111", "a11")];
const ids = (shown: ReturnType<typeof visibleNodes>) => shown.map((entry) => entry.id);

describe("visibleNodes", () => {
	it("shows the root and two levels below it when nothing was folded yet", () => {
		const shown = visibleNodes("p1", nodes, {});

		expect(ids(shown)).toEqual(["p1", "a", "a1", "a2", "b"]);
		expect(shown.map((entry) => entry.depth)).toEqual([0, 1, 2, 2, 1]);
		expect(shown.find((entry) => entry.id === "p1")).toMatchObject({ parentId: null, node: undefined, hasChildren: true, open: true });
		expect(shown.find((entry) => entry.id === "a1")).toMatchObject({ parentId: "a", hasChildren: true, open: false });
		expect(shown.find((entry) => entry.id === "a2")).toMatchObject({ hasChildren: false });
	});

	it("keeps the order of the siblings by their position, whatever the order of the list", () => {
		const shown = visibleNodes("p1", [node("y", null, 1), node("x", null, 0), node("x2", "x", 1), node("x1", "x", 0)], {});

		expect(ids(shown)).toEqual(["p1", "x", "x1", "x2", "y"]);
	});

	it("follows what the user opened and closed", () => {
		expect(ids(visibleNodes("p1", nodes, { a1: "open" }))).toEqual(["p1", "a", "a1", "a11", "a2", "b"]);
		expect(ids(visibleNodes("p1", nodes, { a: "closed" }))).toEqual(["p1", "a", "b"]);
		expect(ids(visibleNodes("p1", nodes, { p1: "closed" }))).toEqual(["p1"]);
	});

	it("shows only the root of a project without nodes", () => {
		expect(visibleNodes("p1", [], {})).toEqual([{ id: "p1", parentId: null, depth: 0, node: undefined, hasChildren: false, open: true }]);
	});

	it("leaves out nodes whose parent is not in the tree", () => {
		expect(ids(visibleNodes("p1", [node("a"), node("lost", "gone")], {}))).toEqual(["p1", "a"]);
	});
});

describe("fold", () => {
	it("is open by default down to the first level", () => {
		expect([0, 1, 2, 3].map(defaultOpen)).toEqual([true, true, false, false]);
		expect(isOpen({}, "x", 1)).toBe(true);
		expect(isOpen({ x: "closed" }, "x", 1)).toBe(false);
		expect(isOpen({ x: "open" }, "x", 5)).toBe(true);
	});

	it("stores only what differs from the default", () => {
		expect(toggledFold({}, "a", 1)).toEqual({ a: "closed" });
		expect(toggledFold({ a: "closed" }, "a", 1)).toEqual({});
		expect(toggledFold({ b: "open" }, "a1", 2)).toEqual({ b: "open", a1: "open" });
		expect(toggledFold({ a1: "open" }, "a1", 2)).toEqual({});
	});
});

describe("shownProject", () => {
	const p1 = { uid: "p1" };
	const p2 = { uid: "p2" };

	it("is the marked project, else the only visible one, else none", () => {
		expect(shownProject([p1, p2], p2)).toBe(p2);
		expect(shownProject([p1], undefined)).toBe(p1);
		expect(shownProject([p1, p2], undefined)).toBeUndefined();
		expect(shownProject([], undefined)).toBeUndefined();
	});
});

describe("dropPlacement", () => {
	// p1: a (a1 (a11 (a111)), a2), b
	it("hangs a node below the target, at the end of its children", () => {
		expect(dropPlacement("p1", nodes, "b", "a", "inside")).toEqual({ parent: "a", position: 2 });
		expect(dropPlacement("p1", nodes, "a2", "a11", "inside")).toEqual({ parent: "a11", position: 1 });
	});

	it("hangs a node below the root with an empty parent", () => {
		expect(dropPlacement("p1", nodes, "a11", "p1", "inside")).toEqual({ parent: null, position: 2 });
	});

	it("places a node before or after the target among the target's siblings, counted without the node itself", () => {
		expect(dropPlacement("p1", nodes, "b", "a1", "before")).toEqual({ parent: "a", position: 0 });
		expect(dropPlacement("p1", nodes, "b", "a1", "after")).toEqual({ parent: "a", position: 1 });
		expect(dropPlacement("p1", nodes, "a11", "b", "after")).toEqual({ parent: null, position: 2 });
		expect(dropPlacement("p1", nodes, "a", "b", "after")).toEqual({ parent: null, position: 1 });
		expect(dropPlacement("p1", nodes, "b", "a", "before")).toEqual({ parent: null, position: 0 });
	});

	it("offers nothing for the node itself, its own branch, the root as source and unknown nodes", () => {
		expect(dropPlacement("p1", nodes, "a", "a", "inside")).toBeNull();
		expect(dropPlacement("p1", nodes, "a", "a11", "inside")).toBeNull();
		expect(dropPlacement("p1", nodes, "a", "a111", "after")).toBeNull();
		expect(dropPlacement("p1", nodes, "p1", "a", "inside")).toBeNull();
		expect(dropPlacement("p1", nodes, "zz", "a", "inside")).toBeNull();
		expect(dropPlacement("p1", nodes, "a", "zz", "inside")).toBeNull();
	});

	it("offers no place next to the root", () => {
		expect(dropPlacement("p1", nodes, "a", "p1", "before")).toBeNull();
		expect(dropPlacement("p1", nodes, "a", "p1", "after")).toBeNull();
	});

	it("offers nothing where the node already stands", () => {
		expect(dropPlacement("p1", nodes, "a2", "a", "inside")).toBeNull();
		expect(dropPlacement("p1", nodes, "a1", "a2", "before")).toBeNull();
		expect(dropPlacement("p1", nodes, "a2", "a1", "after")).toBeNull();
		expect(dropPlacement("p1", nodes, "a1", "a", "inside")).toEqual({ parent: "a", position: 1 });
	});
});

describe("nodeLook", () => {
	it("draws an idea dashed and hollow, without ring and number while nothing counts", () => {
		expect(nodeLook("idea", 0)).toEqual({ dashed: true, hollow: true, dimmed: false, counts: false });
	});

	it("shows ring and number as soon as items count, also for an idea that only holds rejected items", () => {
		expect(nodeLook("idea", 2)).toEqual({ dashed: true, hollow: true, dimmed: false, counts: true });
		expect(nodeLook("planned", 3)).toEqual({ dashed: false, hollow: false, dimmed: false, counts: true });
		expect(nodeLook("in_progress", 3)).toEqual({ dashed: false, hollow: false, dimmed: false, counts: true });
	});

	it("dims a finished node and keeps its ring", () => {
		expect(nodeLook("done", 4)).toEqual({ dashed: false, hollow: false, dimmed: true, counts: true });
	});

	it("treats an unknown state like planned", () => {
		expect(nodeLook("other", 1)).toEqual({ dashed: false, hollow: false, dimmed: false, counts: true });
	});
});

describe("filterByState", () => {
	const stated = [
		{ ...node("a"), state: "in_progress" },
		{ ...node("a1", "a"), state: "done" },
		{ ...node("a2", "a", 1), state: "planned" },
		{ ...node("b", null, 1), state: "idea" },
	];

	it("keeps everything while no state is hidden", () => {
		expect(filterByState(stated, []).map((entry) => entry.uid)).toEqual(["a", "a1", "a2", "b"]);
	});

	it("drops the nodes of a hidden state; their branch disappears from the map with them", () => {
		const kept = filterByState(stated, ["done", "idea"]);

		expect(kept.map((entry) => entry.uid)).toEqual(["a", "a2"]);
		expect(visibleNodes("p1", filterByState(stated, ["in_progress"]), {}).map((entry) => entry.id)).toEqual(["p1", "b"]);
	});
});

describe("canDropItem", () => {
	const all = [node("a"), node("a1", "a")];

	it("offers every node of the tree", () => {
		expect(canDropItem("p1", all, "a")).toBe(true);
		expect(canDropItem("p1", all, "a1")).toBe(true);
	});

	it("does not offer the root (the project) or a node that is not there", () => {
		expect(canDropItem("p1", all, "p1")).toBe(false);
		expect(canDropItem("p1", all, "gone")).toBe(false);
	});
});

describe("markLook", () => {
	it("shows nothing for a node without a mark", () => {
		expect(markLook(null)).toEqual({ icon: undefined, strike: false, dimmed: false });
	});

	it("strikes a discarded node through and dims it", () => {
		expect(markLook("discarded")).toEqual({ icon: "discarded", strike: true, dimmed: true });
	});

	it("marks a node for later with its own symbol, without striking it through", () => {
		expect(markLook("later")).toEqual({ icon: "later", strike: false, dimmed: false });
	});

	it("treats an unknown mark like none", () => {
		expect(markLook("other")).toEqual({ icon: undefined, strike: false, dimmed: false });
	});
});

describe("filterByMark", () => {
	const marked = [
		{ ...node("a"), mark: "discarded" },
		{ ...node("a1", "a"), mark: null },
		{ ...node("b", null, 1), mark: "later" },
		{ ...node("c", null, 2), mark: null },
	];

	it("keeps everything while no mark is hidden", () => {
		expect(filterByMark(marked, []).map((entry) => entry.uid)).toEqual(["a", "a1", "b", "c"]);
	});

	it("drops the nodes of a hidden mark, never a node without a mark", () => {
		expect(filterByMark(marked, ["later"]).map((entry) => entry.uid)).toEqual(["a", "a1", "c"]);
		expect(filterByMark(marked, ["discarded", "later"]).map((entry) => entry.uid)).toEqual(["a1", "c"]);
	});

	it("takes the branch of a hidden node from the map; the mark itself stays on the node alone", () => {
		const kept = filterByMark(marked, ["discarded"]);

		expect(kept.find((entry) => entry.uid === "a1")?.mark).toBeNull();
		expect(visibleNodes("p1", kept, { a: "open" }).map((entry) => entry.id)).toEqual(["p1", "b", "c"]);
	});
});

describe("visibleNodes with a focus", () => {
	it("starts at the focus: it is the top of the view and the depth counts from there", () => {
		const shown = visibleNodes("p1", nodes, {}, "a");

		expect(ids(shown)).toEqual(["a", "a1", "a11", "a2"]);
		expect(shown.map((entry) => entry.depth)).toEqual([0, 1, 2, 1]);
		expect(shown[0]).toMatchObject({ parentId: null, hasChildren: true, open: true });
		expect(shown[0]!.node?.uid).toBe("a");
	});

	it("opens two levels below the focus, deeper than they were open before", () => {
		expect(ids(visibleNodes("p1", nodes, {}, "a1"))).toEqual(["a1", "a11", "a111"]);
	});

	it("still follows what the user folded", () => {
		expect(ids(visibleNodes("p1", nodes, { a1: "closed" }, "a"))).toEqual(["a", "a1", "a2"]);
		expect(ids(visibleNodes("p1", nodes, { a: "closed" }, "a"))).toEqual(["a"]);
	});

	it("shows the whole tree for the root, an unknown focus or one that is not in the list", () => {
		const whole = ["p1", "a", "a1", "a2", "b"];
		expect(ids(visibleNodes("p1", nodes, {}, "p1"))).toEqual(whole);
		expect(ids(visibleNodes("p1", nodes, {}, "nowhere"))).toEqual(whole);
		expect(ids(visibleNodes("p1", nodes, {}, undefined))).toEqual(whole);
	});

	it("shows a focus whose ancestors are not in the list", () => {
		const withoutA = nodes.filter((entry) => entry.uid !== "a");

		expect(ids(visibleNodes("p1", withoutA, {}, "a1"))).toEqual(["a1", "a11", "a111"]);
	});
});

describe("focusPath", () => {
	it("lists the ids from the root down to the focus", () => {
		expect(focusPath("p1", nodes, "a11")).toEqual(["p1", "a", "a1", "a11"]);
		expect(focusPath("p1", nodes, "b")).toEqual(["p1", "b"]);
	});

	it("is only the root for the root itself", () => {
		expect(focusPath("p1", nodes, "p1")).toEqual(["p1"]);
	});

	it("has no path for an unknown focus or one that is missing or empty", () => {
		expect(focusPath("p1", nodes, "nowhere")).toBeNull();
		expect(focusPath("p1", nodes, null)).toBeNull();
		expect(focusPath("p1", nodes, "")).toBeNull();
	});

	it("has no path when the chain does not reach the root, even in a cycle", () => {
		expect(focusPath("p1", [node("x", "y"), node("y", "x")], "x")).toBeNull();
	});
});

describe("parentForNewNode", () => {
	it("hangs a new node below the effective node of the item", () => {
		expect(parentForNewNode("a1", "p1")).toBe("a1");
	});

	it("hangs it below the root when the item has no node or hangs on the root", () => {
		expect(parentForNewNode(undefined, "p1")).toBeNull();
		expect(parentForNewNode(null, "p1")).toBeNull();
		expect(parentForNewNode("", "p1")).toBeNull();
		expect(parentForNewNode("p1", "p1")).toBeNull();
	});
});
