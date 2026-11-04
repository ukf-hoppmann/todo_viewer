/** One node of a tree for `TreeView`. */
export interface TreeNode {
	id: string;
	parentId: string | null;
	label: string;
	/** A short text next to the label, e.g. the label of the item (`STORY-012`). */
	badge?: string;
	/** A color for the badge (any CSS color), e.g. the priority of the item; without it the badge is dimmed. */
	badgeColor?: string;
	/** A color for the status dot (any CSS color). */
	statusColor?: string;
	/** Its guide line is dashed, the label dimmed and the status dot hollow, e.g. an item that is not required for its parent. */
	dashed?: boolean;
	/** Done and total of the children, drawn as a `ProgressRing`. */
	progress?: { done: number; total: number };
	/** A number at the right of the row, e.g. the open notes below a topic. */
	count?: number;
	/** A small word before the label, e.g. `Topic` or `Note`; `tagColor` colors it. */
	tag?: string;
	tagColor?: string;
	/** Shades the row as part of the area of a topic of this level (1 or 2): a tint, and at level 1 or 2 a colored left edge. */
	area?: 1 | 2;
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

/**
 * The guide lines left of each row: one per level above it (index 0 = the line of the first level), each `true` when
 * dashed. A line belongs to the node at that level whose subtree contains the row, so the children of a dashed node
 * continue its dashed line.
 */
export function guideLines(rows: readonly VisibleNode[]): boolean[][] {
	const dashedAt: boolean[] = [];
	return rows.map(({ node, depth }) => {
		dashedAt[depth] = node.dashed === true;
		return dashedAt.slice(1, depth + 1);
	});
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

/** The ids of the ancestors of an entry, nearest first, following `parentOf` (a guard stops cycles). */
export function ancestorChain(parentOf: (id: string) => string | null | undefined, id: string): string[] {
	const chain: string[] = [];
	for (let current = parentOf(id); current && !chain.includes(current); current = parentOf(current)) chain.push(current);
	return chain;
}
