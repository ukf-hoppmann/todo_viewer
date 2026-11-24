import type { DocumentOut, IndexItem, ItemOut } from "../../../client/src/plugins/backlog/api";

/** An item of the index with plain defaults (project `p1`, type Task, status Open, priority Normal). */
export function item(uid: string, extra: Partial<IndexItem> = {}): IndexItem {
	return {
		uid,
		project_uid: "p1",
		label: uid.toUpperCase(),
		type: "Task",
		title: `Titel ${uid}`,
		status: "Open",
		priority: "Normal",
		parent_uid: null,
		required_for_parent: null,
		dependencies: [],
		progress: null,
		version: 1,
		...extra,
	};
}

/** The detail of an item with plain defaults. */
export function detail(uid: string, extra: Partial<ItemOut> = {}): ItemOut {
	return {
		uid,
		project_uid: "p1",
		label: uid.toUpperCase(),
		type: "Task",
		title: `Titel ${uid}`,
		status: "Open",
		priority: "Normal",
		parent: null,
		required_for_parent: null,
		goal: null,
		completion_criteria: null,
		summary: null,
		resolution: null,
		created: "2026-10-16",
		notes: [],
		spec: [],
		children: [],
		dependencies: [],
		progress: null,
		version: 1,
		deleted: false,
		...extra,
	};
}

/** A document with plain defaults (notes, version 1). */
export function document(name: string, content: string, extra: Partial<DocumentOut> = {}): DocumentOut {
	return { name, kind: name.includes("_notes") ? "notes" : "spec", content, version: 1, updated_at: "2026-10-16T12:00:00Z", ...extra };
}
