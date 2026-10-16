import type { ELK } from "elkjs/lib/elk.bundled.js";
import type { DependencyGraph, Uid } from "../domain/model";

export const NODE_WIDTH = 200;
export const NODE_HEIGHT = 50;

// ELK is large; load it only when the graph view is first used.
let elkPromise: Promise<ELK> | null = null;
function loadElk(): Promise<ELK> {
  elkPromise ??= import("elkjs/lib/elk.bundled.js").then(({ default: ElkConstructor }) => new ElkConstructor());
  return elkPromise;
}

/** Vertical gap between unrelated subgraphs. */
const COMPONENT_GAP = 60;

/** ELK layered with thorough crossing minimization; every root starts in the leftmost layer. */
const LAYOUT_OPTIONS: Record<string, string> = {
  "elk.algorithm": "layered",
  "elk.direction": "RIGHT",
  "elk.padding": "[top=0,left=0,bottom=0,right=0]",
  "elk.layered.spacing.nodeNodeBetweenLayers": "120",
  "elk.spacing.nodeNode": "30",
  "elk.layered.layering.strategy": "LONGEST_PATH_SOURCE",
  "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
  "elk.layered.crossingMinimization.greedySwitch.type": "TWO_SIDED",
  "elk.layered.thoroughness": "50",
  "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
};

/** Weakly connected subgraphs, in the order their first node appears. */
export function connectedComponents(graph: DependencyGraph): DependencyGraph[] {
  const root = new Map<Uid, Uid>(graph.nodes.map((n) => [n.uid, n.uid]));
  const find = (uid: Uid): Uid => {
    let r = uid;
    while (root.get(r) !== r) r = root.get(r)!;
    root.set(uid, r);
    return r;
  };
  for (const e of graph.edges) root.set(find(e.from), find(e.to));

  const byRoot = new Map<Uid, DependencyGraph>();
  for (const n of graph.nodes) {
    const r = find(n.uid);
    if (!byRoot.has(r)) byRoot.set(r, { nodes: [], edges: [] });
    byRoot.get(r)!.nodes.push(n);
  }
  for (const e of graph.edges) byRoot.get(find(e.from))!.edges.push(e);
  return [...byRoot.values()];
}

/**
 * Left-to-right layered layout: dependencies left of the items that need them. Unrelated subgraphs
 * are stacked below each other, all starting at the same left edge. Returns top-left corners.
 */
export async function layoutGraph(graph: DependencyGraph): Promise<Map<Uid, { x: number; y: number }>> {
  const elk = await loadElk();
  const laidOut = await Promise.all(
    connectedComponents(graph).map((component) =>
      elk.layout({
        id: "root",
        layoutOptions: LAYOUT_OPTIONS,
        children: component.nodes.map((n) => ({ id: n.uid, width: NODE_WIDTH, height: NODE_HEIGHT })),
        edges: component.edges.map((e, i) => ({ id: `e${i}`, sources: [e.from], targets: [e.to] })),
      }),
    ),
  );

  const positions = new Map<Uid, { x: number; y: number }>();
  let top = 0;
  for (const result of laidOut) {
    let bottom = 0;
    for (const c of result.children ?? []) {
      positions.set(c.id, { x: c.x ?? 0, y: top + (c.y ?? 0) });
      bottom = Math.max(bottom, (c.y ?? 0) + NODE_HEIGHT);
    }
    top += bottom + COMPONENT_GAP;
  }
  return positions;
}

/** The focused nodes and their direct neighbors; empty when nothing is focused. */
export function focusNeighborhood(graph: DependencyGraph, focus: ReadonlySet<Uid>): Set<Uid> {
  const set = new Set<Uid>(focus);
  for (const e of graph.edges) {
    if (focus.has(e.from)) set.add(e.to);
    if (focus.has(e.to)) set.add(e.from);
  }
  return set;
}
