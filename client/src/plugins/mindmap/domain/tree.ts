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
 * every node whose ancestors are all open. Nodes whose parent is not part of the tree are left out. With a `focusId`
 * the view starts at that node instead: it becomes the top (depth 0, no parent) and the depth counts from there; a
 * focus that is the root, unknown or not in `nodes` shows the whole tree.
 */
export function visibleNodes<T extends PlacedNode>(rootId: string, nodes: readonly T[], fold: Fold, focusId?: string | null): ShownNode<T>[] {
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
	const focus = focusId && focusId !== rootId ? nodes.find((node) => node.uid === focusId) : undefined;
	if (focus) visit(focus.uid, null, 0, focus);
	else visit(rootId, null, 0, undefined);
	return shown;
}

/**
 * The ids from the root `rootId` down to `focusId`, the root first; `null` when there is no such focus: it is empty,
 * unknown, or its chain of parents does not reach the root. The path of the root is the root alone.
 */
export function focusPath(rootId: string, nodes: readonly PlacedNode[], focusId: string | null | undefined): string[] | null {
	if (!focusId) return null;
	if (focusId === rootId) return [rootId];
	const byId = new Map(nodes.map((node) => [node.uid, node]));
	const path: string[] = [];
	const seen = new Set<string>();
	for (let current = byId.get(focusId); current; current = current.parent_uid ? byId.get(current.parent_uid) : undefined) {
		if (seen.has(current.uid)) return null;
		seen.add(current.uid);
		path.unshift(current.uid);
		if (!current.parent_uid || current.parent_uid === rootId) return [rootId, ...path];
	}
	return null;
}

/** The parent for a node created for an item: its effective node, or `null` (under the root) without one or on the root. */
export function parentForNewNode(effectiveNodeUid: string | null | undefined, rootId: string): string | null {
	return !effectiveNodeUid || effectiveNodeUid === rootId ? null : effectiveNodeUid;
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

/** The views of the map: one project (`single`), or all chosen projects under a common root (`all`). */
export type ViewMode = "single" | "all";

/** The id of the common root of the overall view: it belongs to no project and is no record. */
export const COMBINED_ROOT = "mindmap:all";

/**
 * The state of a project node (or the common root) over the states of what hangs below it, by the rule of the node
 * state: only ideas (or nothing) is an idea, only planned is planned, only done is done, anything else is in progress.
 * Ideas count nothing and are left out.
 */
export function combinedState(states: readonly string[]): string {
	const counted = states.filter((state) => state !== "idea");
	if (counted.length === 0) return "idea";
	if (counted.every((state) => state === "planned")) return "planned";
	if (counted.every((state) => state === "done")) return "done";
	return "in_progress";
}

/** What a node of the overall view needs besides its place: the counts and the state. */
export interface CountedNode extends PlacedNode {
	total: number;
	done: number;
	state: string;
}

/**
 * The nodes of the overall view: for every project a node of its own (made by `makeProject` from the project and its
 * place, counts and state), directly under the common root, with the top nodes of its tree hung below it. `trees[i]`
 * holds the nodes of `projects[i]`. A project counts the sum of its top nodes, which already hold their sub-nodes, so
 * every item counts once; items without a node are no node and do not count. The given nodes stay unchanged.
 */
export function combinedTree<P extends { uid: string }, T extends CountedNode>(
	projects: readonly P[],
	trees: ReadonlyArray<readonly T[]>,
	makeProject: (project: P, own: { position: number; total: number; done: number; state: string }) => T,
): T[] {
	return projects.flatMap((project, position) => {
		const nodes = trees[position] ?? [];
		const top = nodes.filter((entry) => !entry.parent_uid);
		const own = {
			position,
			total: top.reduce((sum, entry) => sum + entry.total, 0),
			done: top.reduce((sum, entry) => sum + entry.done, 0),
			state: combinedState(top.map((entry) => entry.state)),
		};
		return [makeProject(project, own), ...nodes.map((entry) => (entry.parent_uid ? entry : { ...entry, parent_uid: project.uid }))];
	});
}

/** A line between two nodes: `count` dependencies of items in `to_node` on items in `from_node`. */
export interface NodeLink {
	from_node: string;
	to_node: string;
	count: number;
}

/**
 * The lines as the map draws them. A line whose end is not shown (folded away, filtered out, outside the focus) ends at
 * the nearest shown ancestor of that end instead (`parentOf`: node → parent). A line without a shown ancestor at one of
 * its ends is dropped; so is one that now runs from a node to itself. Lines with the same ends are summed again. Sorted
 * by (from, to).
 */
export function liftLinks(links: readonly NodeLink[], shownIds: ReadonlySet<string>, parentOf: ReadonlyMap<string, string | null | undefined>): NodeLink[] {
	const lift = (id: string): string | null => {
		const seen = new Set<string>();
		let current: string | null | undefined = id;
		while (current && !shownIds.has(current)) {
			if (seen.has(current)) return null;
			seen.add(current);
			current = parentOf.get(current);
		}
		return current || null;
	};
	const sums = new Map<string, NodeLink>();
	for (const link of links) {
		const from = lift(link.from_node);
		const to = lift(link.to_node);
		if (!from || !to || from === to) continue;
		const key = `${from}\u0000${to}`;
		const known = sums.get(key);
		if (known) known.count += link.count;
		else sums.set(key, { from_node: from, to_node: to, count: link.count });
	}
	return [...sums.values()].sort((a, b) => a.from_node.localeCompare(b.from_node) || a.to_node.localeCompare(b.to_node));
}
