import type { ItemRefOut, NodeItemOut, TreeNodeOut } from "../../../client/src/plugins/mindmap/api";

/**
 * A node of the project tree `p1`: `node("a")` hangs under the root, `node("b", "a", 1)` is the second child of `a`.
 * Without `extra` it counts nothing and is an idea, as the server answers for a node without items.
 */
export function node(uid: string, parent: string | null = null, position = 0, extra: Partial<TreeNodeOut> = {}): TreeNodeOut {
	return { uid, project_uid: "p1", label: `NODE-${uid}`, title: `Thema ${uid}`, text: null, tree_uid: "t1", parent_uid: parent, position, version: 1, documents: [], total: 0, done: 0, state: "idea", ...extra };
}

/** An item of the backlog as the mind map lists it. */
export function itemRef(uid: string, extra: Partial<ItemRefOut> = {}): ItemRefOut {
	return { uid, label: `TASK-${uid}`, type: "Task", title: `Aufgabe ${uid}`, status: "Open", ...extra };
}

/** An item in the detail of a node; `explicit`: assigned to that node itself, not inherited. */
export function nodeItem(uid: string, explicit = true, extra: Partial<ItemRefOut> = {}): NodeItemOut {
	return { ...itemRef(uid, extra), explicit };
}
