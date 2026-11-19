import type { MapOut } from "../api";

/** What the branch logic needs of a node. */
export interface BranchNode {
	uid: string;
	title: string;
	parent_uid?: string | null;
}

/** The media type a dragged node carries (JSON `DraggedNode`), so the map list can take it. */
export const NODE_MIME = "application/x-mindmap-node";

/** The branch to hang over or transfer: a node with its sub-nodes in the tree `tree_uid`. A drag onto the map list carries it as JSON. */
export interface BranchSource {
	uid: string;
	version: number;
	title: string;
	project_uid: string;
	tree_uid: string;
}

/** The node and all its descendants in one tree, parents before children. */
export function branchOf(nodes: readonly BranchNode[], uid: string): string[] {
	const found = [uid];
	for (let index = 0; index < found.length; index += 1) {
		for (const node of nodes) if (node.parent_uid === found[index] && !found.includes(node.uid)) found.push(node.uid);
	}
	return found;
}

/** The nodes of the branch that already stand in the target tree. */
export function standingIn(branch: readonly string[], target: readonly BranchNode[]): string[] {
	const there = new Set(target.map((node) => node.uid));
	return branch.filter((uid) => there.has(uid));
}

export type BranchAction = "move" | "transfer";

/** Why a map is no target, or nothing when it is one. `nodes` are the titles that block it. */
export type TargetReason = { kind: "sameTree" } | { kind: "standing"; nodes: string[] };

/**
 * Whether a branch may go to `target`. Transferring into the tree it comes from is refused; moving there only moves
 * the branch below the root. A target that already holds the branch or part of it is refused with those nodes' titles.
 * `targetNodes` is `undefined` while the target tree is still loading: only the first rule can apply then.
 */
export function targetReason(
	action: BranchAction,
	sourceTree: string,
	branch: readonly string[],
	target: Pick<MapOut, "tree_uid">,
	targetNodes: readonly BranchNode[] | undefined,
): TargetReason | undefined {
	if (target.tree_uid === sourceTree) return action === "transfer" ? { kind: "sameTree" } : undefined;
	if (!targetNodes) return undefined;
	const standing = standingIn(branch, targetNodes);
	if (standing.length === 0) return undefined;
	return { kind: "standing", nodes: standing.map((uid) => targetNodes.find((node) => node.uid === uid)!.title) };
}

/** Whether the map is the tree a node stands in. */
export function isTreeOf(map: Pick<MapOut, "tree_uid">, treeUid: string): boolean {
	return map.tree_uid === treeUid;
}
