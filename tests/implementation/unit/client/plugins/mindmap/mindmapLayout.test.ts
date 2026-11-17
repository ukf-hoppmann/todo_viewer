import { describe, expect, it } from "vitest";
import { layoutTree, NODE_HEIGHT } from "../../../../../../client/src/plugins/mindmap/mindmapLayout";

const tree = [
	{ id: "root", parentId: null },
	{ id: "a", parentId: "root" },
	{ id: "a1", parentId: "a" },
	{ id: "a2", parentId: "a" },
	{ id: "a3", parentId: "a" },
	{ id: "b", parentId: "root" },
	{ id: "b1", parentId: "b" },
	{ id: "c", parentId: "root" },
];

describe("layoutTree", () => {
	it("puts every child right of its parent and one level in one column", async () => {
		const positions = await layoutTree(tree);

		expect(positions.size).toBe(tree.length);
		const x = (id: string) => positions.get(id)!.x;
		expect(x("a")).toBeGreaterThan(x("root"));
		expect(x("a1")).toBeGreaterThan(x("a"));
		expect(x("b")).toBe(x("a"));
		expect(x("c")).toBe(x("a"));
		expect(x("b1")).toBe(x("a1"));
	});

	it("keeps the siblings in their order from top to bottom without overlap", async () => {
		const positions = await layoutTree(tree);

		const y = (id: string) => positions.get(id)!.y;
		expect(y("b")).toBeGreaterThanOrEqual(y("a") + NODE_HEIGHT);
		expect(y("c")).toBeGreaterThanOrEqual(y("b") + NODE_HEIGHT);
		expect(y("a2")).toBeGreaterThanOrEqual(y("a1") + NODE_HEIGHT);
		expect(y("a3")).toBeGreaterThanOrEqual(y("a2") + NODE_HEIGHT);
		expect(y("b1")).toBeGreaterThanOrEqual(y("a3") + NODE_HEIGHT);
	});

	it("lays out a single root and an empty list", async () => {
		expect((await layoutTree([{ id: "root", parentId: null }])).get("root")).toEqual({ x: 0, y: 0 });
		expect((await layoutTree([])).size).toBe(0);
	});
});
