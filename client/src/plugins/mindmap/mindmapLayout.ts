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

/** How the map is arranged: the tree to the side, or around the root. */
export type LayoutMode = "side" | "round";

/** A side of a node an edge is attached to. */
export type Side = "left" | "right" | "top" | "bottom";

type Structure = ReadonlyArray<{ id: string; parentId: string | null }>;
type Point = { x: number; y: number };

// The round arrangement: the first level starts this far from the middle, every further level at least this far beyond its parent.
const ROUND_FIRST_RADIUS = 300;
const ROUND_LEVEL_STEP = 260;
const ROUND_PUSH = 10;
const ROUND_GAP = 8;

/**
 * The map around the root: the root in the middle, every subtree in an angular sector by its number of leaves, the siblings
 * clockwise in the order given, starting at the top. A node begins one step beyond its parent on the middle line of its
 * sector and moves outward only as far as needed to clear the nodes already placed, so a dense branch does not widen the
 * whole level. Nodes are placed level by level, so parents come before children. Returns the top-left corners by id.
 */
function layoutRound(nodes: Structure): Map<string, Point> {
	const positions = new Map<string, Point>();
	const root = nodes.find((node) => node.parentId === null) ?? nodes[0];
	const children = new Map<string, string[]>();
	for (const node of nodes) {
		if (node.parentId === null) continue;
		const list = children.get(node.parentId);
		if (list) list.push(node.id);
		else children.set(node.parentId, [node.id]);
	}
	const leaves = new Map<string, number>();
	const countLeaves = (id: string): number => {
		const own = children.get(id) ?? [];
		const count = own.length === 0 ? 1 : own.reduce((sum, child) => sum + countLeaves(child), 0);
		leaves.set(id, count);
		return count;
	};
	countLeaves(root.id);

	const angle = new Map<string, number>();
	const depth = new Map<string, number>();
	const parentOf = new Map(nodes.map((node) => [node.id, node.parentId]));
	const order: string[] = [];
	const assign = (id: string, from: number, to: number, level: number) => {
		angle.set(id, (from + to) / 2);
		depth.set(id, level);
		order.push(id);
		let start = from;
		for (const child of children.get(id) ?? []) {
			const span = ((to - from) * leaves.get(child)!) / leaves.get(id)!;
			assign(child, start, start + span, level + 1);
			start += span;
		}
	};
	assign(root.id, -Math.PI / 2, (3 * Math.PI) / 2, 0);
	order.sort((a, b) => depth.get(a)! - depth.get(b)! || angle.get(a)! - angle.get(b)!);

	// A grid of the placed rectangles keeps the check for a clash local.
	const cellWidth = NODE_WIDTH + ROUND_GAP;
	const cellHeight = NODE_HEIGHT + ROUND_GAP;
	const grid = new Map<string, Point[]>();
	const cellKey = (cx: number, cy: number) => `${cx},${cy}`;
	const clears = (point: Point) => {
		const cx = Math.floor(point.x / cellWidth);
		const cy = Math.floor(point.y / cellHeight);
		for (let dx = -1; dx <= 1; dx++) {
			for (let dy = -1; dy <= 1; dy++) {
				for (const other of grid.get(cellKey(cx + dx, cy + dy)) ?? []) {
					if (point.x < other.x + cellWidth && other.x < point.x + cellWidth && point.y < other.y + cellHeight && other.y < point.y + cellHeight) return false;
				}
			}
		}
		return true;
	};
	const place = (id: string, point: Point) => {
		positions.set(id, point);
		const key = cellKey(Math.floor(point.x / cellWidth), Math.floor(point.y / cellHeight));
		const list = grid.get(key);
		if (list) list.push(point);
		else grid.set(key, [point]);
	};

	const radius = new Map<string, number>([[root.id, 0]]);
	place(root.id, { x: -NODE_WIDTH / 2, y: -NODE_HEIGHT / 2 });
	for (const id of order) {
		if (id === root.id) continue;
		let r = radius.get(parentOf.get(id)!)! + (depth.get(id) === 1 ? ROUND_FIRST_RADIUS : ROUND_LEVEL_STEP);
		const direction = angle.get(id)!;
		for (;; r += ROUND_PUSH) {
			const point = { x: r * Math.cos(direction) - NODE_WIDTH / 2, y: r * Math.sin(direction) - NODE_HEIGHT / 2 };
			if (clears(point)) {
				place(id, point);
				radius.set(id, r);
				break;
			}
		}
	}
	return positions;
}

/**
 * The tree to the side (`mode` "side", the default) or around the root (`mode` "round"). To the side: the root at the left, every child right of its parent, siblings below each other in the order
 * given (parents before children). Returns the top-left corners by id.
 */
export async function layoutTree(nodes: Structure, mode: LayoutMode = "side"): Promise<Map<string, Point>> {
	const positions = new Map<string, Point>();
	if (nodes.length === 0) return positions;
	if (mode === "round") return layoutRound(nodes);
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

/**
 * The sides by which the edge from a parent to a child is attached, from the top-left corners of the two. The tree to the
 * side always leaves a parent on the right and reaches the child on the left. In the round arrangement a child that lies
 * more above or below than beside its parent is attached from the bottom to the top (or the reverse), else from the
 * side that faces it.
 */
export function edgeSides(mode: LayoutMode, parent: Point, child: Point): { source: Side; target: Side } {
	const dx = child.x - parent.x;
	const dy = child.y - parent.y;
	if (mode === "side" || Math.abs(dx) >= Math.abs(dy)) return dx < 0 ? { source: "left", target: "right" } : { source: "right", target: "left" };
	return dy < 0 ? { source: "top", target: "bottom" } : { source: "bottom", target: "top" };
}

/**
 * How the drop zones of a node read, from the top-left corners of the node and the root. "normal": the upper quarter places
 * before, the lower quarter after (the tree to the side, and the round arrangement right of the root, where earlier siblings
 * lie above). "flipped": left of the root earlier siblings lie below, so before and after trade places and the mark lies where
 * the node lands. "inside": above and below the root the siblings lie side by side, so only the middle (below the target) is offered.
 */
export type DropZones = "normal" | "flipped" | "inside";

export function dropZonesOf(mode: LayoutMode, node: Point, root: Point): DropZones {
	if (mode === "side") return "normal";
	const dx = node.x - root.x;
	const dy = node.y - root.y;
	if (Math.abs(dy) > Math.abs(dx)) return "inside";
	return dx < 0 ? "flipped" : "normal";
}
