/** What the tree logic needs of a node: where it hangs (`parent_uid` empty: under the root) and its place among its siblings. */
export interface PlacedNode {
	uid: string;
	parent_uid?: string | null;
	position: number;
}

/** What the user folded, by node id: only what differs from the default (`defaultOpen`). */
export type Fold = Readonly<Record<string, "open" | "closed">>;

/** A node the map draws. The root (the project) has no `node`. */
export interface ShownNode<T extends PlacedNode> {
	id: string;
	parentId: string | null;
	/** 0 for the root. */
	depth: number;
	node: T | undefined;
	hasChildren: boolean;
	open: boolean;
}

/** When nothing was chosen, the root and the first level are open: two levels below the root are visible. */
export function defaultOpen(depth: number): boolean {
	return depth < 2;
}

export function isOpen(fold: Fold, id: string, depth: number): boolean {
	const chosen = fold[id];
	return chosen ? chosen === "open" : defaultOpen(depth);
}

/** The fold after opening or closing `id`; a choice that equals the default is not stored. */
export function toggledFold(fold: Fold, id: string, depth: number): Fold {
	const next = !isOpen(fold, id, depth);
	const rest = Object.fromEntries(Object.entries(fold).filter(([key]) => key !== id));
	return next === defaultOpen(depth) ? rest : { ...rest, [id]: next ? "open" : "closed" };
}

/**
 * The nodes the map shows, parents before children and siblings by position: the root `rootId` (the project), then
 * every node whose ancestors are all open. Nodes whose parent is not part of the tree are left out.
 */
export function visibleNodes<T extends PlacedNode>(rootId: string, nodes: readonly T[], fold: Fold): ShownNode<T>[] {
	const children = new Map<string, T[]>();
	for (const node of nodes) {
		const parent = node.parent_uid || rootId;
		const list = children.get(parent);
		if (list) list.push(node);
		else children.set(parent, [node]);
	}
	for (const list of children.values()) list.sort((a, b) => a.position - b.position);

	const shown: ShownNode<T>[] = [];
	const visit = (id: string, parentId: string | null, depth: number, node: T | undefined) => {
		const below = children.get(id) ?? [];
		const open = isOpen(fold, id, depth);
		shown.push({ id, parentId, depth, node, hasChildren: below.length > 0, open });
		if (open) for (const child of below) visit(child.uid, id, depth + 1, child);
	};
	visit(rootId, null, 0, undefined);
	return shown;
}

/** The project whose tree the page shows: the marked one, else the only visible one, else none. */
export function shownProject<P>(visible: readonly P[], marked: P | undefined): P | undefined {
	return marked ?? (visible.length === 1 ? visible[0] : undefined);
}
