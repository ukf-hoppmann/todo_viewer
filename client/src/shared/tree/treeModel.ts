/** One node of a tree for `TreeView`. */
export interface TreeNode {
	id: string;
	parentId: string | null;
	label: string;
	/** A short text next to the label, e.g. the label of the item (`STORY-012`). */
	badge?: string;
	/** A color for the status dot (any CSS color). */
	statusColor?: string;
	/** Drawn dashed and dimmed, e.g. an item that is not required for its parent. */
	dashed?: boolean;
	/** Done and total of the children, drawn as a `ProgressRing`. */
	progress?: { done: number; total: number };
	children: TreeNode[];
}

export type DropPosition = "before" | "after" | "inside";

/** A row of the visible tree: the node, how deep it stands, and whether it is open. */
export interface VisibleNode {
	node: TreeNode;
	depth: number;
	expanded: boolean;
}

export type FlatNode = Omit<TreeNode, "children">;

/**
 * Builds the tree from a flat list: every entry stands below its `parentId`; entries whose parent is not in
 * the list become roots. The order of the list is kept among siblings.
 */
export function buildTree(flat: readonly FlatNode[]): TreeNode[] {
	const nodes = new Map<string, TreeNode>(flat.map((entry) => [entry.id, { ...entry, children: [] }]));
	const roots: TreeNode[] = [];
	for (const entry of flat) {
		const node = nodes.get(entry.id)!;
		const parent = entry.parentId === null ? undefined : nodes.get(entry.parentId);
		(parent ? parent.children : roots).push(node);
	}
	return roots;
}

/** The rows that are visible with the given open nodes, depth first. */
export function flattenVisible(roots: readonly TreeNode[], expanded: ReadonlySet<string>): VisibleNode[] {
	const rows: VisibleNode[] = [];
	const walk = (nodes: readonly TreeNode[], depth: number) => {
		for (const node of nodes) {
			const open = node.children.length > 0 && expanded.has(node.id);
			rows.push({ node, depth, expanded: open });
			if (open) walk(node.children, depth + 1);
		}
	};
	walk(roots, 0);
	return rows;
}

/** Where a drop lands on a row: the upper quarter is before it, the lower quarter after it, the middle inside it. */
export function dropPosition(offsetY: number, height: number): DropPosition {
	if (height <= 0) return "inside";
	const ratio = offsetY / height;
	if (ratio < 0.25) return "before";
	if (ratio > 0.75) return "after";
	return "inside";
}

/** The ids of the ancestors of a node, nearest first. */
export function ancestorsOf(roots: readonly TreeNode[], id: string): string[] {
	const path: string[] = [];
	const find = (nodes: readonly TreeNode[]): boolean => {
		for (const node of nodes) {
			if (node.id === id) return true;
			path.push(node.id);
			if (find(node.children)) return true;
			path.pop();
		}
		return false;
	};
	return find(roots) ? path.reverse() : [];
}

/** True if `candidate` is `id` itself or stands below it (a node must not be dropped into its own subtree). */
export function isInSubtree(roots: readonly TreeNode[], id: string, candidate: string): boolean {
	return candidate === id || ancestorsOf(roots, candidate).includes(id);
}
