import type { NodeOut } from "../../../client/src/plugins/mindmap/api";

/** A node of the project tree `p1`: `node("a")` hangs under the root, `node("b", "a", 1)` is the second child of `a`. */
export function node(uid: string, parent: string | null = null, position = 0, extra: Partial<NodeOut> = {}): NodeOut {
	return { uid, project_uid: "p1", label: `NODE-${uid}`, title: `Thema ${uid}`, text: null, tree_uid: "t1", parent_uid: parent, position, version: 1, documents: [], ...extra };
}
