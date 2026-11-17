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

/** Where a dragged node lands relative to the node it is dropped on. */
export type DropZone = "before" | "after" | "inside";

/** A place in the tree: `parent` empty means under the root; `position` counts the siblings without the moved node. */
export interface Placement {
	parent: string | null;
	position: number;
}

/**
 * Where `sourceId` lands when it is dropped on `targetId` in `zone`, or `null` when the drop is not offered: the
 * root cannot be moved, a node cannot land on itself or in its own branch, nothing stands next to the root, and a
 * place the node already has changes nothing. "inside" appends to the children of the target.
 */
export function dropPlacement(rootId: string, nodes: readonly PlacedNode[], sourceId: string, targetId: string, zone: DropZone): Placement | null {
	const byId = new Map(nodes.map((node) => [node.uid, node]));
	const source = byId.get(sourceId);
	const target = byId.get(targetId);
	if (!source || sourceId === targetId || (!target && targetId !== rootId)) return null;
	const seen = new Set<string>();
	for (let current = target; current && !seen.has(current.uid); current = current.parent_uid ? byId.get(current.parent_uid) : undefined) {
		if (current.uid === sourceId) return null;
		seen.add(current.uid);
	}
	if (zone !== "inside" && !target) return null;
	const parent = zone === "inside" ? (target ? target.uid : null) : target!.parent_uid || null;
	const siblings = nodes.filter((node) => (node.parent_uid || null) === parent).sort((a, b) => a.position - b.position);
	const others = siblings.filter((node) => node.uid !== sourceId);
	const position = zone === "inside" ? others.length : others.findIndex((node) => node.uid === targetId) + (zone === "after" ? 1 : 0);
	if (siblings.findIndex((node) => node.uid === sourceId) === position) return null;
	return { parent, position };
}

/** The project whose tree the page shows: the marked one, else the only visible one, else none. */
export function shownProject<P>(visible: readonly P[], marked: P | undefined): P | undefined {
	return marked ?? (visible.length === 1 ? visible[0] : undefined);
}

/** The states a node can have, derived by the server from its items (spec `STORY-100`). */
export const NODE_STATES = ["idea", "planned", "in_progress", "done"] as const;

/** How a node is drawn: dashed and hollow (an idea), dimmed (finished), with ring and number (items count). */
export interface NodeLook {
	dashed: boolean;
	hollow: boolean;
	dimmed: boolean;
	counts: boolean;
}

export function nodeLook(state: string, total: number): NodeLook {
	return { dashed: state === "idea", hollow: state === "idea", dimmed: state === "done", counts: total > 0 };
}

/**
 * The nodes whose state is not hidden. A node whose parent is hidden stays in the list, but `visibleNodes` only
 * reaches nodes through their parents, so a hidden node takes its whole branch from the map.
 */
export function filterByState<T extends { state: string }>(nodes: readonly T[], hiddenStates: readonly string[]): T[] {
	return hiddenStates.length === 0 ? [...nodes] : nodes.filter((node) => !hiddenStates.includes(node.state));
}

/** Whether an item can be dropped on `targetId`: on a node of the tree, not on the root (the project). */
export function canDropItem(rootId: string, nodes: readonly PlacedNode[], targetId: string): boolean {
	return targetId !== rootId && nodes.some((node) => node.uid === targetId);
}

/** The marks a node can carry (`TASK-065`); no mark is `null`. They change neither counts nor state. */
export const NODE_MARKS = ["discarded", "later"] as const;

/** How a mark shows: a symbol, a struck-through title, and dimming. */
export interface MarkLook {
	icon: "discarded" | "later" | undefined;
	strike: boolean;
	dimmed: boolean;
}

export function markLook(mark: string | null | undefined): MarkLook {
	if (mark === "discarded") return { icon: "discarded", strike: true, dimmed: true };
	if (mark === "later") return { icon: "later", strike: false, dimmed: false };
	return { icon: undefined, strike: false, dimmed: false };
}

/**
 * The nodes whose mark is not hidden; a node without a mark always stays. Like `filterByState`, a hidden node takes
 * its branch from the map, but the mark belongs to that node alone.
 */
export function filterByMark<T extends { mark?: string | null }>(nodes: readonly T[], hiddenMarks: readonly string[]): T[] {
	return hiddenMarks.length === 0 ? [...nodes] : nodes.filter((node) => !node.mark || !hiddenMarks.includes(node.mark));
}
