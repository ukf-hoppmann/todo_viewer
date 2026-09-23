import { Graph, layout } from "@dagrejs/dagre";
import type { DependencyGraph, Uid } from "../domain/model";

export const NODE_WIDTH = 200;
export const NODE_HEIGHT = 50;

/** Left-to-right layered layout: dependencies left of the items that need them. */
export function layoutGraph(graph: DependencyGraph): Map<Uid, { x: number; y: number }> {
  const g = new Graph();
  g.setGraph({ rankdir: "LR", ranksep: 120, nodesep: 30 });
  g.setDefaultEdgeLabel(() => ({}));
  for (const node of graph.nodes) g.setNode(node.uid, { width: NODE_WIDTH, height: NODE_HEIGHT });
  for (const edge of graph.edges) g.setEdge(edge.from, edge.to);
  layout(g);

  // dagre returns centers; React Flow positions the top-left corner.
  return new Map(
    graph.nodes.map((n) => {
      const { x, y } = g.node(n.uid);
      return [n.uid, { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 }];
    }),
  );
}
