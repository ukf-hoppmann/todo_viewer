import type { Entity } from "../../../shared";

/** What the plan logic needs of a node of the branch. */
export interface PlanNode {
	uid: string;
	label: string;
	parent_uid?: string | null;
	position: number;
	title: string;
	text?: string | null;
}

/** What becomes of a node: nothing, a backlog item or a memo. Nothing is derived from level or depth. */
export type ChoiceKind = "skip" | "item" | "memo";

/** The input of the dialog for one node. `parent` and `dependsOn` name a node of the plan or an existing item (by uid). */
export interface NodeChoice {
	kind: ChoiceKind;
	type: string;
	title: string;
	goal: string;
	criteria: string;
	parent: string | null;
	dependsOn: string[];
}

/** The choices by node uid; a node without an entry is `emptyChoice`. */
export type Choices = Readonly<Record<string, NodeChoice>>;

/** The wire form of an entry of the plan (`TransferEntryIn` of the server). */
export interface PlanEntry {
	node: string;
	kind: "item" | "memo";
	type?: string;
	title?: string;
	goal?: string;
	completion_criteria?: string;
	memo?: { summary?: string; body?: string };
	parent?: string;
	depends_on?: string[];
}

/** No relation, nothing chosen; title and goal are the suggestion taken from the node. */
export function emptyChoice(node: Pick<PlanNode, "title" | "text">): NodeChoice {
	return { kind: "skip", type: "", title: node.title, goal: node.text ?? "", criteria: "", parent: null, dependsOn: [] };
}

/** A row of the dialog: the node and how deep it stands below the root of the branch. */
export interface BranchRow<T extends PlanNode> {
	node: T;
	depth: number;
}

/** The branch below `rootUid` for display: the root first, parents before children, siblings by position. */
export function branchRows<T extends PlanNode>(nodes: readonly T[], rootUid: string): BranchRow<T>[] {
	const children = new Map<string, T[]>();
	for (const node of nodes) {
		const list = children.get(node.parent_uid ?? "");
		if (list) list.push(node);
		else children.set(node.parent_uid ?? "", [node]);
	}
	for (const list of children.values()) list.sort((a, b) => a.position - b.position);
	const root = nodes.find((node) => node.uid === rootUid);
	if (!root) return [];
	const rows: BranchRow<T>[] = [];
	const visit = (node: T, depth: number) => {
		rows.push({ node, depth });
		for (const child of children.get(node.uid) ?? []) visit(child, depth + 1);
	};
	visit(root, 0);
	return rows;
}

const filled = (value: string) => (value.trim() === "" ? undefined : value);

/** The entries of the plan in the order of the branch: only nodes that become an item or a memo. */
export function buildEntries(nodes: readonly PlanNode[], choices: Choices): PlanEntry[] {
	const entries: PlanEntry[] = [];
	const items = new Set(nodes.filter((node) => choices[node.uid]?.kind === "item").map((node) => node.uid));
	const inPlan = new Set(nodes.map((node) => node.uid));
	// A node that does not become an item cannot be the target of a relation; the relation is left out.
	const valid = (ref: string) => !inPlan.has(ref) || items.has(ref);
	for (const node of nodes) {
		const choice = choices[node.uid];
		if (!choice || choice.kind === "skip") continue;
		if (choice.kind === "memo") {
			const summary = filled(choice.title);
			const body = filled(choice.goal);
			entries.push({ node: node.uid, kind: "memo", memo: { ...(summary ? { summary } : {}), ...(body ? { body } : {}) } });
			continue;
		}
		const entry: PlanEntry = { node: node.uid, kind: "item" };
		if (choice.type) entry.type = choice.type;
		const title = filled(choice.title);
		const goal = filled(choice.goal);
		const criteria = filled(choice.criteria);
		if (title) entry.title = title;
		if (goal) entry.goal = goal;
		if (criteria) entry.completion_criteria = criteria;
		if (choice.parent && valid(choice.parent)) entry.parent = choice.parent;
		const depends = choice.dependsOn.filter(valid);
		if (depends.length > 0) entry.depends_on = depends;
		entries.push(entry);
	}
	return entries;
}

/** What a node may be related to: the other nodes that become an item in the plan, then the existing items. */
export function relationTargets(
	nodes: readonly PlanNode[],
	choices: Choices,
	self: string,
	existing: ReadonlyArray<{ uid: string; label: string; title: string }>,
): Entity[] {
	const planned = nodes
		.filter((node) => node.uid !== self && choices[node.uid]?.kind === "item")
		.map((node) => ({ id: node.uid, label: node.label, title: choices[node.uid]!.title || node.title }));
	return [...planned, ...existing.map((item) => ({ id: item.uid, label: item.label, title: item.title }))];
}
