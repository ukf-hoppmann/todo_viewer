import { describe, expect, it } from "vitest";
import { ancestorsOf, buildTree, dropPosition, flattenVisible, guideLines, isInSubtree } from "../../../../../../client/src/shared/tree/treeModel";

const flat = [
	{ id: "e1", parentId: null, label: "Epic" },
	{ id: "s1", parentId: "e1", label: "Story 1" },
	{ id: "t1", parentId: "s1", label: "Task" },
	{ id: "s2", parentId: "e1", label: "Story 2" },
	{ id: "lost", parentId: "gone", label: "Parent not in the list" },
];

describe("buildTree", () => {
	it("nests entries below their parent in the order of the list; unknown parents make roots", () => {
		const roots = buildTree(flat);

		expect(roots.map((n) => n.id)).toEqual(["e1", "lost"]);
		expect(roots[0]!.children.map((n) => n.id)).toEqual(["s1", "s2"]);
		expect(roots[0]!.children[0]!.children.map((n) => n.id)).toEqual(["t1"]);
	});

	it("keeps the other fields and does not change the input", () => {
		const input = [{ id: "a", parentId: null, label: "A", badge: "X", progress: { done: 1, total: 2 } }];

		const [node] = buildTree(input);

		expect(node).toMatchObject({ badge: "X", progress: { done: 1, total: 2 }, children: [] });
		expect(input[0]).not.toHaveProperty("children");
	});
});

describe("flattenVisible", () => {
	const roots = buildTree(flat);

	it("shows only the roots when nothing is open", () => {
		expect(flattenVisible(roots, new Set()).map((r) => r.node.id)).toEqual(["e1", "lost"]);
	});

	it("shows the children of open nodes with their depth, depth first", () => {
		const rows = flattenVisible(roots, new Set(["e1", "s1"]));

		expect(rows.map((r) => [r.node.id, r.depth, r.expanded])).toEqual([
			["e1", 0, true],
			["s1", 1, true],
			["t1", 2, false],
			["s2", 1, false],
			["lost", 0, false],
		]);
	});

	it("ignores an open mark on a node without children", () => {
		expect(flattenVisible(roots, new Set(["lost"]))[1]).toMatchObject({ expanded: false });
	});
});

describe("guideLines", () => {
	it("gives each row one line per level above it, dashed below a dashed node", () => {
		const tree = buildTree([
			{ id: "e", parentId: null, label: "E" },
			{ id: "s1", parentId: "e", label: "S1", dashed: true },
			{ id: "t1", parentId: "s1", label: "T1" },
			{ id: "s2", parentId: "e", label: "S2" },
			{ id: "t2", parentId: "s2", label: "T2" },
		]);
		const rows = flattenVisible(tree, new Set(["e", "s1", "s2"]));

		expect(rows.map((row) => row.node.id)).toEqual(["e", "s1", "t1", "s2", "t2"]);
		expect(guideLines(rows)).toEqual([[], [true], [true, false], [false], [false, false]]);
	});
});

describe("dropPosition", () => {
	it.each([
		[0, "before"],
		[9, "before"],
		[10, "inside"],
		[20, "inside"],
		[31, "after"],
		[40, "after"],
	])("offset %i of 40 is %s", (offset, expected) => {
		expect(dropPosition(offset, 40)).toBe(expected);
	});

	it("is inside for a row without height", () => {
		expect(dropPosition(0, 0)).toBe("inside");
	});
});

describe("ancestorsOf and isInSubtree", () => {
	const roots = buildTree(flat);

	it("lists the ancestors nearest first, none for a root or an unknown id", () => {
		expect(ancestorsOf(roots, "t1")).toEqual(["s1", "e1"]);
		expect(ancestorsOf(roots, "e1")).toEqual([]);
		expect(ancestorsOf(roots, "ghost")).toEqual([]);
	});

	it("knows a node is in its own subtree and in the subtrees of its ancestors only", () => {
		expect(isInSubtree(roots, "e1", "t1")).toBe(true);
		expect(isInSubtree(roots, "s1", "s1")).toBe(true);
		expect(isInSubtree(roots, "s1", "s2")).toBe(false);
		expect(isInSubtree(roots, "t1", "e1")).toBe(false);
	});
});
