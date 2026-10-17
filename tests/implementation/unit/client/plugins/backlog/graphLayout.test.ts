import { describe, expect, it } from "vitest";
import { layoutGraph, NODE_HEIGHT } from "../../../../../../client/src/plugins/backlog/graphLayout";
import { dependencyGraph } from "../../../../../../client/src/plugins/backlog/graphModel";
import { item } from "../../../../../helpers/client/backlogFixtures";

describe("layoutGraph", () => {
	it("puts the items without dependencies in the left column and every dependent right of its dependencies", async () => {
		const graph = dependencyGraph([item("a"), item("b", { dependencies: ["a"] }), item("c", { dependencies: ["b", "a"] }), item("d")].concat([item("e", { dependencies: ["d"] })]));

		const positions = await layoutGraph(graph);

		expect(positions.size).toBe(5);
		const x = (uid: string) => positions.get(uid)!.x;
		expect(x("a")).toBe(0);
		expect(x("d")).toBe(0);
		expect(x("b")).toBeGreaterThan(x("a"));
		expect(x("c")).toBeGreaterThan(x("b"));
		expect(x("e")).toBeGreaterThan(x("d"));
	});

	it("stacks unrelated parts below each other from the same left edge", async () => {
		const graph = dependencyGraph([item("a"), item("b", { dependencies: ["a"] }), item("x"), item("y", { dependencies: ["x"] })]);

		const positions = await layoutGraph(graph);

		expect(positions.get("x")!.x).toBe(positions.get("a")!.x);
		expect(positions.get("x")!.y).toBeGreaterThanOrEqual(positions.get("a")!.y + NODE_HEIGHT);
		expect(positions.get("y")!.y).toBeGreaterThanOrEqual(positions.get("b")!.y + NODE_HEIGHT);
	});

	it("lays out an empty graph without positions", async () => {
		expect((await layoutGraph({ nodes: [], edges: [] })).size).toBe(0);
	});
});
