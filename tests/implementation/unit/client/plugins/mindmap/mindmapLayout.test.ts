import { describe, expect, it } from "vitest";
import { layoutTree, NODE_HEIGHT, NODE_WIDTH } from "../../../../../../client/src/plugins/mindmap/mindmapLayout";

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

type Structure = Array<{ id: string; parentId: string | null }>;

/** A fixed map of 300 nodes: eight branches (wide, deep and mixed), depth up to 6. No randomness: the same map every run. */
function bigMap(): Structure {
	let seed = 7;
	const next = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
	const nodes: Structure = [{ id: "root", parentId: null }];
	const depth = new Map<string, number>([["root", 0]]);
	const add = (parentId: string, d: number) => {
		const id = `n${nodes.length}`;
		nodes.push({ id, parentId });
		depth.set(id, d);
		return id;
	};
	const kinds = ["wide", "deep", "mixed", "wide", "mixed", "deep", "mixed", "wide"];
	const frontier = kinds.map((kind, i) => ({ id: add("root", 1), kind, depth: 1, i }));
	while (nodes.length < 300 && frontier.length > 0) {
		const at = Math.floor(next() * frontier.length);
		const entry = frontier[at];
		frontier.splice(at, 1);
		if (entry.depth >= 6) continue;
		const children = entry.kind === "wide" ? 3 + Math.floor(next() * 5) : entry.kind === "deep" ? 1 + Math.floor(next() * 2) : 1 + Math.floor(next() * 4);
		for (let k = 0; k < children && nodes.length < 300; k++) {
			frontier.push({ id: add(entry.id, entry.depth + 1), kind: entry.kind === "wide" && entry.depth >= 2 ? "mixed" : entry.kind, depth: entry.depth + 1, i: 0 });
		}
	}
	return nodes;
}

describe("layoutTree, round", () => {
	it("keeps the tree to the side unchanged when the mode is `side` or missing", async () => {
		expect([...(await layoutTree(tree, "side")).entries()]).toEqual([...(await layoutTree(tree)).entries()]);
	});

	it("puts the root in the middle and every node in the result", async () => {
		const positions = await layoutTree(tree, "round");

		expect(positions.size).toBe(tree.length);
		expect(positions.get("root")).toEqual({ x: -NODE_WIDTH / 2, y: -NODE_HEIGHT / 2 });
	});

	it("lets no rectangle overlap another in a map of 300 nodes", async () => {
		const map = bigMap();
		const positions = await layoutTree(map, "round");

		expect(map).toHaveLength(300);
		expect(positions.size).toBe(300);
		const boxes = [...positions.entries()];
		const clashes: string[] = [];
		for (let a = 0; a < boxes.length; a++) {
			for (let b = a + 1; b < boxes.length; b++) {
				const [idA, p] = boxes[a];
				const [idB, q] = boxes[b];
				if (p.x < q.x + NODE_WIDTH && q.x < p.x + NODE_WIDTH && p.y < q.y + NODE_HEIGHT && q.y < p.y + NODE_HEIGHT) clashes.push(`${idA}/${idB}`);
			}
		}
		expect(clashes).toEqual([]);
	});

	it("places the siblings clockwise in the order given, starting at the top", async () => {
		const positions = await layoutTree(tree, "round");

		const angle = (id: string) => {
			const p = positions.get(id)!;
			const degrees = (Math.atan2(p.y + NODE_HEIGHT / 2, p.x + NODE_WIDTH / 2) * 180) / Math.PI;
			return (degrees + 90 + 360) % 360;
		};
		expect(angle("a")).toBeLessThan(angle("b"));
		expect(angle("b")).toBeLessThan(angle("c"));
		expect(angle("a1")).toBeLessThan(angle("a2"));
		expect(angle("a2")).toBeLessThan(angle("a3"));
	});

	it("spreads the map around the root: nodes lie left and right of it and above and below it", async () => {
		const positions = await layoutTree(bigMap(), "round");

		const centres = [...positions.entries()].filter(([id]) => id !== "root").map(([, p]) => ({ x: p.x + NODE_WIDTH / 2, y: p.y + NODE_HEIGHT / 2 }));
		expect(centres.some((c) => c.x < 0)).toBe(true);
		expect(centres.some((c) => c.x > 0)).toBe(true);
		expect(centres.some((c) => c.y < 0)).toBe(true);
		expect(centres.some((c) => c.y > 0)).toBe(true);
	});

	it("places a child farther from the middle than its parent", async () => {
		const positions = await layoutTree(tree, "round");

		const distance = (id: string) => {
			const p = positions.get(id)!;
			return Math.hypot(p.x + NODE_WIDTH / 2, p.y + NODE_HEIGHT / 2);
		};
		for (const { id, parentId } of tree) if (parentId) expect(distance(id)).toBeGreaterThan(distance(parentId));
	});

	it("lays out a single root and an empty list", async () => {
		expect((await layoutTree([{ id: "root", parentId: null }], "round")).get("root")).toEqual({ x: -NODE_WIDTH / 2, y: -NODE_HEIGHT / 2 });
		expect((await layoutTree([], "round")).size).toBe(0);
	});
});
