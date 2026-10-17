import { describe, expect, it } from "vitest";
import { connectedComponents, dependencyGraph, focusNeighborhood, highlight, toggled } from "../../../../../../client/src/plugins/backlog/graphModel";
import { item } from "../../../../../helpers/client/backlogFixtures";

const items = [
	item("a"),
	item("b", { dependencies: ["a"] }),
	item("c", { dependencies: ["b", "a"] }),
	item("x"),
	item("y", { dependencies: ["x"] }),
	item("lonely"),
	item("hidden-dep", { dependencies: ["not-shown"] }),
];

describe("dependencyGraph", () => {
	it("keeps only items that take part in a dependency, with edges from the dependency to the dependent", () => {
		const graph = dependencyGraph(items);

		expect(graph.nodes.map((node) => node.uid)).toEqual(["a", "b", "c", "x", "y"]);
		expect(graph.edges).toEqual([
			{ from: "a", to: "b" },
			{ from: "b", to: "c" },
			{ from: "a", to: "c" },
			{ from: "x", to: "y" },
		]);
	});

	it("ignores dependencies on items that are not in the list", () => {
		const graph = dependencyGraph([item("a"), item("b", { dependencies: ["a", "gone"] })]);

		expect(graph.edges).toEqual([{ from: "a", to: "b" }]);
		expect(dependencyGraph([item("only", { dependencies: ["gone"] })]).nodes).toEqual([]);
	});
});

describe("connectedComponents", () => {
	it("splits the graph into its connected parts, in the order of the first node", () => {
		const parts = connectedComponents(dependencyGraph(items));

		expect(parts.map((part) => part.nodes.map((node) => node.uid))).toEqual([["a", "b", "c"], ["x", "y"]]);
		expect(parts[0]!.edges).toHaveLength(3);
		expect(parts[1]!.edges).toEqual([{ from: "x", to: "y" }]);
	});

	it("joins parts that a later edge connects", () => {
		const graph = dependencyGraph([item("a"), item("b"), item("c", { dependencies: ["a", "b"] })]);

		expect(connectedComponents(graph)).toHaveLength(1);
	});

	it("is empty for an empty graph", () => {
		expect(connectedComponents({ nodes: [], edges: [] })).toEqual([]);
	});
});

describe("focusNeighborhood", () => {
	const graph = dependencyGraph(items);

	it("holds the focus and its direct neighbors in both directions", () => {
		expect([...focusNeighborhood(graph, new Set(["b"]))].sort()).toEqual(["a", "b", "c"]);
		expect([...focusNeighborhood(graph, new Set(["y"]))].sort()).toEqual(["x", "y"]);
	});

	it("is empty when nothing is focused", () => {
		expect(focusNeighborhood(graph, new Set()).size).toBe(0);
	});
});

describe("toggled", () => {
	it("adds and removes a uid without changing the original", () => {
		const one = new Set(["a"]);

		expect([...toggled(one, "b")]).toEqual(["a", "b"]);
		expect([...toggled(one, "a")]).toEqual([]);
		expect([...one]).toEqual(["a"]);
	});
});

describe("highlight", () => {
	const graph = dependencyGraph(items);

	it("dims nothing without a focus and keeps all edges inactive", () => {
		const result = highlight(graph, null, new Set(), null);

		expect(result.focus.size).toBe(0);
		expect(graph.nodes.every((node) => !result.dimmed(node.uid))).toBe(true);
		expect(graph.edges.some((edge) => result.active(edge))).toBe(false);
	});

	it("focuses the selected node and dims everything but it and its neighbors", () => {
		const result = highlight(graph, "b", new Set(), null);

		expect(result.dimmed("a")).toBe(false);
		expect(result.dimmed("c")).toBe(false);
		expect(result.dimmed("x")).toBe(true);
		expect(result.active({ from: "a", to: "b" })).toBe(true);
		expect(result.active({ from: "x", to: "y" })).toBe(false);
	});

	it("adds the marked and the hovered nodes to the focus, and ignores a selection that is not in the graph", () => {
		const result = highlight(graph, "lonely", new Set(["x"]), "b");

		expect([...result.focus].sort()).toEqual(["b", "x"]);
		expect(result.dimmed("y")).toBe(false);
		expect(result.dimmed("a")).toBe(false);
		expect(highlight(graph, "lonely", new Set(["x"]), null).dimmed("a")).toBe(true);
	});
});
