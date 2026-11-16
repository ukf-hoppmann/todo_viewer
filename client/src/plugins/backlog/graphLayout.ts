import { loadElk } from "../../shared";
import { connectedComponents, type DependencyGraph } from "./graphModel";

export const NODE_WIDTH = 200;
export const NODE_HEIGHT = 50;

/** Vertical gap between unrelated subgraphs. */
const COMPONENT_GAP = 60;

/** ELK layered with thorough crossing minimization; every node without dependencies starts in the leftmost layer. */
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

/**
 * Left-to-right layered layout: dependencies stand left of the items that need them. Unrelated subgraphs are
 * stacked below each other, all starting at the same left edge. Returns the top-left corners by `uid`.
 */
export async function layoutGraph(graph: DependencyGraph): Promise<Map<string, { x: number; y: number }>> {
	const elk = await loadElk();
	const laidOut = await Promise.all(
		connectedComponents(graph).map((component) =>
			elk.layout({
				id: "root",
				layoutOptions: LAYOUT_OPTIONS,
				children: component.nodes.map((node) => ({ id: node.uid, width: NODE_WIDTH, height: NODE_HEIGHT })),
				edges: component.edges.map((edge, index) => ({ id: `e${index}`, sources: [edge.from], targets: [edge.to] })),
			}),
		),
	);

	const positions = new Map<string, { x: number; y: number }>();
	let top = 0;
	for (const result of laidOut) {
		let bottom = 0;
		for (const child of result.children ?? []) {
			positions.set(child.id, { x: child.x ?? 0, y: top + (child.y ?? 0) });
			bottom = Math.max(bottom, (child.y ?? 0) + NODE_HEIGHT);
		}
		top += bottom + COMPONENT_GAP;
	}
	return positions;
}
