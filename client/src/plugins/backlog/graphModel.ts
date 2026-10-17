import type { IndexItem } from "./api";

export interface GraphEdge {
	/** The dependency: it is needed first, the arrow starts here. */
	from: string;
	/** The item that depends on it. */
	to: string;
}

export interface DependencyGraph {
	nodes: IndexItem[];
	edges: GraphEdge[];
}

/** Only items that take part in at least one dependency between the given items; edges go from dependency to dependent. */
export function dependencyGraph(items: readonly IndexItem[]): DependencyGraph {
	const uids = new Set(items.map((item) => item.uid));
	const edges = items.flatMap((item) => item.dependencies.filter((dependency) => uids.has(dependency)).map((dependency) => ({ from: dependency, to: item.uid })));
	const connected = new Set(edges.flatMap((edge) => [edge.from, edge.to]));
	return { nodes: items.filter((item) => connected.has(item.uid)), edges };
}

/** The weakly connected subgraphs, in the order their first node appears. */
export function connectedComponents(graph: DependencyGraph): DependencyGraph[] {
	const root = new Map<string, string>(graph.nodes.map((node) => [node.uid, node.uid]));
	const find = (uid: string): string => {
		let current = uid;
		while (root.get(current) !== current) current = root.get(current)!;
		root.set(uid, current);
		return current;
	};
	for (const edge of graph.edges) root.set(find(edge.from), find(edge.to));

	const byRoot = new Map<string, DependencyGraph>();
	for (const node of graph.nodes) {
		const key = find(node.uid);
		if (!byRoot.has(key)) byRoot.set(key, { nodes: [], edges: [] });
		byRoot.get(key)!.nodes.push(node);
	}
	for (const edge of graph.edges) byRoot.get(find(edge.from))!.edges.push(edge);
	return [...byRoot.values()];
}

/** The focused nodes and their direct neighbors; empty when nothing is focused. */
export function focusNeighborhood(graph: DependencyGraph, focus: ReadonlySet<string>): Set<string> {
	const neighborhood = new Set(focus);
	for (const edge of graph.edges) {
		if (focus.has(edge.from)) neighborhood.add(edge.to);
		if (focus.has(edge.to)) neighborhood.add(edge.from);
	}
	return neighborhood;
}

/** The set with `uid` added, or removed if it was in it. */
export function toggled(set: ReadonlySet<string>, uid: string): ReadonlySet<string> {
	const next = new Set(set);
	if (!next.delete(uid)) next.add(uid);
	return next;
}

export interface Highlight {
	/** What is focused: the selected node, the marked ones and the hovered one (only those in the graph). */
	focus: Set<string>;
	/** Which nodes are drawn dimmed: all but the focus and its neighbors; none if nothing is focused. */
	dimmed: (uid: string) => boolean;
	/** An edge is active if it touches the focus. */
	active: (edge: GraphEdge) => boolean;
}

export function highlight(graph: DependencyGraph, selected: string | null, marked: ReadonlySet<string>, hovered: string | null): Highlight {
	const focus = new Set(marked);
	if (selected && graph.nodes.some((node) => node.uid === selected)) focus.add(selected);
	if (hovered) focus.add(hovered);
	const neighborhood = focusNeighborhood(graph, focus);
	return {
		focus,
		dimmed: (uid) => neighborhood.size > 0 && !neighborhood.has(uid),
		active: (edge) => focus.has(edge.from) || focus.has(edge.to),
	};
}
