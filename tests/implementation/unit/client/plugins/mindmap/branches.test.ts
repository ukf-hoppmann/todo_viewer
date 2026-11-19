import { describe, expect, it } from "vitest";
import { branchOf, standingIn, targetReason } from "../../../../../../client/src/plugins/mindmap/domain/branches";

const nodes = [
	{ uid: "a", title: "A", parent_uid: null },
	{ uid: "b", title: "B", parent_uid: "a" },
	{ uid: "c", title: "C", parent_uid: "b" },
	{ uid: "d", title: "D", parent_uid: null },
];

describe("branch logic", () => {
	it("lists a node and its descendants, parents first", () => {
		expect(branchOf(nodes, "a")).toEqual(["a", "b", "c"]);
		expect(branchOf(nodes, "c")).toEqual(["c"]);
	});

	it("finds the nodes of a branch that already stand in a tree", () => {
		expect(standingIn(["a", "b", "c"], [{ uid: "c", title: "C" }, { uid: "z", title: "Z" }])).toEqual(["c"]);
		expect(standingIn(["a"], [])).toEqual([]);
	});

	it("refuses to transfer into the own tree but lets a move go below its root", () => {
		expect(targetReason("transfer", "t1", ["a"], { tree_uid: "t1" }, [])).toEqual({ kind: "sameTree" });
		expect(targetReason("move", "t1", ["a"], { tree_uid: "t1" }, [])).toBeUndefined();
	});

	it("refuses a target that holds part of the branch and names the titles", () => {
		const target = [{ uid: "b", title: "Bee" }];
		expect(targetReason("move", "t1", ["a", "b", "c"], { tree_uid: "t2" }, target)).toEqual({ kind: "standing", nodes: ["Bee"] });
		expect(targetReason("transfer", "t1", ["a"], { tree_uid: "t2" }, target)).toBeUndefined();
	});

	it("offers a target whose tree is still loading", () => {
		expect(targetReason("move", "t1", ["a"], { tree_uid: "t2" }, undefined)).toBeUndefined();
	});
});
