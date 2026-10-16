import { describe, expect, it } from "vitest";
import type { DependencyGraph, Item } from "../domain/model";
import { connectedComponents, focusNeighborhood, layoutGraph } from "./graphLayout";

function graph(edges: [string, string][]): DependencyGraph {
  const uids = [...new Set(edges.flat())];
  return { nodes: uids.map((uid) => ({ uid }) as Item), edges: edges.map(([from, to]) => ({ from, to })) };
}

describe("layoutGraph", () => {
  it("places dependencies left of their dependents", async () => {
    const pos = await layoutGraph(graph([["a", "b"], ["b", "c"]]));
    expect(pos.get("a")!.x).toBeLessThan(pos.get("b")!.x);
    expect(pos.get("b")!.x).toBeLessThan(pos.get("c")!.x);
  });

  it("orders a layer so that edges do not cross", async () => {
    // Given in crossing order: a1 -> b2 and a2 -> b1.
    const g = graph([["a1", "b2"], ["a2", "b1"], ["a1", "c"], ["b2", "c"], ["a2", "d"], ["b1", "d"]]);
    const pos = await layoutGraph(g);
    const y = (uid: string) => pos.get(uid)!.y;
    const crossings = g.edges.filter((e) => ["a1", "a2"].includes(e.from) && ["b1", "b2"].includes(e.to));
    const [e1, e2] = crossings as [(typeof crossings)[0], (typeof crossings)[0]];
    expect(Math.sign(y(e1.from) - y(e2.from))).toBe(Math.sign(y(e1.to) - y(e2.to)));
  });

  it("starts every root at the left edge", async () => {
    // "r" only feeds the last layer; it still belongs to the first one.
    const pos = await layoutGraph(graph([["a", "b"], ["b", "c"], ["r", "c"]]));
    expect(pos.get("r")!.x).toBe(pos.get("a")!.x);
  });

  it("stacks unrelated subgraphs below each other at the same left edge", async () => {
    const pos = await layoutGraph(graph([["a", "b"], ["b", "c"], ["x", "y"]]));
    expect(pos.get("x")!.x).toBe(pos.get("a")!.x);
    const firstBottom = Math.max(...["a", "b", "c"].map((u) => pos.get(u)!.y));
    expect(pos.get("x")!.y).toBeGreaterThan(firstBottom);
  });

  it("returns a position for every node", async () => {
    const g = graph([["a", "b"], ["x", "y"]]);
    const pos = await layoutGraph(g);
    expect([...pos.keys()].sort()).toEqual(["a", "b", "x", "y"]);
  });
});

describe("connectedComponents", () => {
  it("splits unrelated subgraphs and keeps their edges", () => {
    const parts = connectedComponents(graph([["a", "b"], ["x", "y"], ["c", "b"]]));
    expect(parts.map((p) => p.nodes.map((n) => n.uid).sort())).toEqual([["a", "b", "c"], ["x", "y"]]);
    expect(parts.map((p) => p.edges.length)).toEqual([2, 1]);
  });
});

describe("focusNeighborhood", () => {
  const g = graph([["a", "b"], ["b", "c"], ["x", "c"], ["y", "z"]]);

  it("is empty without focus", () => {
    expect(focusNeighborhood(g, new Set()).size).toBe(0);
  });

  it("contains the focus and its direct dependencies and dependents", () => {
    expect([...focusNeighborhood(g, new Set(["b"]))].sort()).toEqual(["a", "b", "c"]);
  });

  it("unites the neighborhoods of several focused nodes", () => {
    expect([...focusNeighborhood(g, new Set(["a", "y"]))].sort()).toEqual(["a", "b", "y", "z"]);
  });
});
