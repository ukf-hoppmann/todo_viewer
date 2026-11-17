import { loadElk } from "../../shared";

export const NODE_WIDTH = 190;
export const NODE_HEIGHT = 36;

/** ELK layered to the right: one level per column; the order of the nodes given is the order from top to bottom. */
const LAYOUT_OPTIONS: Record<string, string> = {
	"elk.algorithm": "layered",
	"elk.direction": "RIGHT",
	"elk.padding": "[top=0,left=0,bottom=0,right=0]",
	"elk.layered.spacing.nodeNodeBetweenLayers": "70",
	"elk.spacing.nodeNode": "12",
	"elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
	"elk.layered.crossingMinimization.forceNodeModelOrder": "true",
	"elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
};

/**
 * The tree to the side: the root at the left, every child right of its parent, siblings below each other in the order
 * given (parents before children). Returns the top-left corners by id.
 */
export async function layoutTree(nodes: ReadonlyArray<{ id: string; parentId: string | null }>): Promise<Map<string, { x: number; y: number }>> {
	const positions = new Map<string, { x: number; y: number }>();
	if (nodes.length === 0) return positions;
	const elk = await loadElk();
	const result = await elk.layout({
		id: "tree",
		layoutOptions: LAYOUT_OPTIONS,
		children: nodes.map((node) => ({ id: node.id, width: NODE_WIDTH, height: NODE_HEIGHT })),
		edges: nodes.filter((node) => node.parentId !== null).map((node) => ({ id: `${node.parentId}->${node.id}`, sources: [node.parentId!], targets: [node.id] })),
	});
	for (const child of result.children ?? []) positions.set(child.id, { x: child.x ?? 0, y: child.y ?? 0 });
	return positions;
}
