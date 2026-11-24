import { describe, expect, it } from "vitest";
import type { SyncConflict, SyncStatus } from "../../../../../../client/src/plugins/workspace/api";
import { choiceDeletes, decisionsOf, differences, documentContext, entryName, isDeletionConflict, lineDiff, needsAttention, onlyWhitespaceDiffers, originKey, syncView, visibleWhitespace, withBulkChoice, choiceBlocked } from "../../../../../../client/src/plugins/workspace/sync";

const status = (state: SyncStatus["state"], extra: Partial<SyncStatus> = {}): SyncStatus => ({ project: "p", state, conflicts: 0, to_database: 0, to_files: 0, files: [], reason: null, last_sync: null, ...extra });
const on = { mirror_enabled: true };

function conflict(key: string, kind: string, database: unknown, files: unknown): SyncConflict {
	return { key, kind: "task", label: key.toUpperCase(), conflict: kind, database, files } as SyncConflict;
}
const entry = (fields: Record<string, unknown>, refs: Record<string, string[]> = {}) => ({ label: "X", kind: "task", fields, refs });

describe("syncView", () => {
	it("is off without a mirror, loading without a status, in sync, or needs the owner", () => {
		expect(syncView({ mirror_enabled: false }, status("conflicts"))).toEqual({ kind: "off" });
		expect(syncView(on, undefined)).toEqual({ kind: "loading" });
		expect(syncView(on, status("in_sync"))).toEqual({ kind: "in_sync" });
		expect(syncView(on, status("mirror_changed", { to_database: 2 }))).toEqual({ kind: "needs_you", changes: true, conflicts: 0 });
		expect(syncView(on, status("conflicts", { conflicts: 3 }))).toEqual({ kind: "needs_you", changes: false, conflicts: 3 });
		expect(syncView(on, status("paused", { reason: "missing" }))).toEqual({ kind: "paused", reason: "missing" });
	});

	it("asks for attention for waiting changes, conflicts and a pause, not for the rest", () => {
		expect(needsAttention(syncView(on, status("primary_changed", { to_files: 1 })))).toBe(true);
		expect(needsAttention(syncView(on, status("paused")))).toBe(true);
		expect(needsAttention(syncView(on, status("in_sync")))).toBe(false);
		expect(needsAttention(syncView({ mirror_enabled: false }, undefined))).toBe(false);
	});
});

describe("deletions", () => {
	const missingInFiles = conflict("a", "deleted_in_files", entry({}), null);
	const missingInDatabase = conflict("b", "deleted_in_database", null, entry({}));
	const changed = conflict("c", "both_changed", entry({ status: "Open" }), entry({ status: "Completed" }));

	it("knows which conflicts are about a deletion and which choice deletes", () => {
		expect([missingInFiles, missingInDatabase, changed].map(isDeletionConflict)).toEqual([true, true, false]);
		expect([choiceDeletes(missingInFiles, "files"), choiceDeletes(missingInFiles, "database"), choiceDeletes(missingInFiles, "defer")]).toEqual([true, false, false]);
		expect([choiceDeletes(missingInDatabase, "database"), choiceDeletes(missingInDatabase, "files")]).toEqual([true, false]);
		expect(choiceDeletes(changed, "files")).toBe(false);
	});

	it("leaves the choices that delete out of a bulk choice but sets the harmless ones", () => {
		const all = [missingInFiles, missingInDatabase, changed];

		expect(withBulkChoice(all, {}, "files")).toEqual({ b: "files", c: "files" });
		expect(withBulkChoice(all, {}, "database")).toEqual({ a: "database", c: "database" });
		expect(withBulkChoice(all, { a: "files" }, "database")).toEqual({ a: "database", c: "database" });
		expect(withBulkChoice(all, { a: "files" }, "files")).toEqual({ a: "files", b: "files", c: "files" });
	});
});

describe("decisionsOf", () => {
	const missing = conflict("a", "deleted_in_files", entry({}), null);
	const changed = conflict("c", "both_changed", entry({}), entry({}));

	it("sends the decisions that are not deferred and flags a deletion only if one was chosen", () => {
		expect(decisionsOf([missing, changed], { c: "database", a: "database" })).toEqual({
			decisions: [
				{ uid: "a", choice: "database" },
				{ uid: "c", choice: "database" },
			],
			deleteMissing: false,
		});
		expect(decisionsOf([missing, changed], { a: "files", c: "defer" })).toEqual({ decisions: [{ uid: "a", choice: "files" }], deleteMissing: true });
		expect(decisionsOf([missing, changed], {})).toEqual({ decisions: [], deleteMissing: false });
	});
});

describe("differences", () => {
	it("lists only the fields and references that differ", () => {
		const rows = differences(
			conflict(
				"c",
				"both_changed",
				entry({ title: "T", status: "Open", summary: null }, { dependencies: ["TASK-001"] }),
				entry({ title: "T", status: "Completed", summary: null }, { dependencies: ["TASK-001", "TASK-002"] }),
			),
		);

		expect(rows).toEqual([
			{ name: "status", database: "Open", files: "Completed" },
			{ name: "dependencies", database: "TASK-001", files: "TASK-001, TASK-002" },
		]);
	});

	it("shows every field when one side is missing, with a dash for the missing side", () => {
		const rows = differences(conflict("a", "deleted_in_files", entry({ title: "T", required_for_parent: true }), null));

		expect(rows).toEqual([
			{ name: "title", database: "T", files: "—" },
			{ name: "required_for_parent", database: "Yes", files: "—" },
		]);
	});
});

describe("choices against the direction", () => {
	it("blocks the side that would be written against the direction", () => {
		expect(choiceBlocked("to_files", "files")).toBe(true);
		expect(choiceBlocked("to_files", "database")).toBe(false);
		expect(choiceBlocked("to_database", "database")).toBe(true);
		expect(choiceBlocked("both", "files")).toBe(false);
		expect(choiceBlocked("to_files", "defer")).toBe(false);
	});
});

describe("originKey", () => {
	const make = (kind: string, extra: Partial<SyncConflict>) => ({ ...conflict("a", kind, entry({}), null), ...extra }) as SyncConflict;

	it("names the origin of a deletion by whether the other side changed since the last sync", () => {
		expect(originKey(make("deleted_in_files", { database_changed: false }))).toBe("deleted_in_files_unchanged");
		expect(originKey(make("deleted_in_files", { database_changed: true }))).toBe("deleted_in_files_changed");
		expect(originKey(make("deleted_in_database", { files_changed: false }))).toBe("deleted_in_database_unchanged");
		expect(originKey(make("deleted_in_database", { files_changed: true }))).toBe("deleted_in_database_changed");
	});

	it("falls back to the kind of the conflict when the server could not tell", () => {
		expect(originKey(make("deleted_in_files", {}))).toBe("deleted_in_files");
		expect(originKey(make("both_changed", { database_changed: true, files_changed: true }))).toBe("both_changed");
		expect(originKey(make("both_created", {}))).toBe("both_created");
	});
});

describe("documentContext", () => {
	it("reads the document kind and the item from either side of a document conflict", () => {
		const doc = { ...conflict("d", "deleted_in_files", entry({ kind: "spec" }, { item: ["STORY-086"] }), null), kind: "document" } as SyncConflict;
		expect(documentContext(doc)).toEqual({ kind: "spec", item: "STORY-086" });
	});

	it("is none for entries that are not documents", () => {
		expect(documentContext(conflict("a", "both_changed", entry({ title: "T" }), entry({ title: "T" })))).toBeNull();
	});
});

describe("onlyWhitespaceDiffers", () => {
	it("is true for empty lines, indentation, trailing spaces, and line endings, false for content or equal texts", () => {
		expect(onlyWhitespaceDiffers("a\n\nb", "a\n\n\nb")).toBe(true);
		expect(onlyWhitespaceDiffers("a\nb", "a  \r\n  b")).toBe(true);
		expect(onlyWhitespaceDiffers("a\nb", "a\nc")).toBe(false);
		expect(onlyWhitespaceDiffers("a", "a")).toBe(false);
	});
});

describe("visibleWhitespace", () => {
	it("makes tabs, trailing spaces, and a carriage return visible and reports an empty line as null", () => {
		expect(visibleWhitespace("")).toBeNull();
		expect(visibleWhitespace("a  ")).toBe("a··");
		expect(visibleWhitespace("a\tb")).toBe("a→   b");
		expect(visibleWhitespace("a \r")).toBe("a·␍");
		expect(visibleWhitespace("  a")).toBe("  a");
	});
});

describe("lineDiff", () => {
	it("marks removed and added lines and collapses long unchanged runs", () => {
		const before = ["a", "b", "c", "d", "e", "f", "g", "h", "old"].join("\n");
		const after = ["a", "b", "c", "d", "e", "f", "g", "h", "new"].join("\n");
		expect(lineDiff(before, after, 2)).toEqual([
			{ op: "skip", count: 6 },
			{ op: "same", text: "g" },
			{ op: "same", text: "h" },
			{ op: "del", text: "old" },
			{ op: "add", text: "new" },
		]);
	});

	it("shows everything when nothing is shared and gives up on texts too long to compare", () => {
		expect(lineDiff("x", "y")).toEqual([
			{ op: "del", text: "x" },
			{ op: "add", text: "y" },
		]);
		const long = Array.from({ length: 1200 }, (_, i) => `a${i}`).join("\n");
		expect(lineDiff(long, long.replace("a5", "z"))).toBeNull();
	});
});

describe("Mindmap-Einträge im Abgleich", () => {
	const tree = (fields: Record<string, unknown>, refs: Record<string, string[]> = {}) => ({ label: null, kind: "mindmap.tree", fields, refs });
	const treeConflict = (database: unknown, files: unknown) => ({ key: "t1", kind: "mindmap.tree", label: null, conflict: "both_changed", database, files }) as SyncConflict;

	it("zeigt die Ordnung eines Baums als eingerückte Liste statt als Zahlen und Labels", () => {
		const before = tree({ tree_kind: "free", name: "Ideen", depths: [0, 1, 1, 0], removed: [] }, { nodes: ["NODE-001", "NODE-002", "NODE-003", "NODE-004"] });
		const after = tree({ tree_kind: "free", name: "Ideen", depths: [0, 1, 0, 1], removed: [] }, { nodes: ["NODE-001", "NODE-002", "NODE-004", "NODE-003"] });

		expect(differences(treeConflict(before, after))).toEqual([
			{ name: "order", database: "NODE-001\n  NODE-002\n  NODE-003\nNODE-004", files: "NODE-001\n  NODE-002\nNODE-004\n  NODE-003" },
		]);
	});

	it("schreibt entfernte Platzierungen als Zeilen und zeigt gleiche Bäume nicht", () => {
		const removedFields = [{ position: 2, has_parent: true }, { position: 0, has_parent: false }];
		const refs = { nodes: ["NODE-001"], removed_nodes: ["NODE-005", "NODE-006"], removed_groups: ["NODE-004", "NODE-006"], removed_parents: ["NODE-001"] };
		const same = tree({ tree_kind: "project", depths: [0], removed: removedFields }, refs);
		const other = tree({ tree_kind: "project", depths: [0], removed: [] }, { nodes: ["NODE-001"] });

		expect(differences(treeConflict(same, structuredClone(same)))).toEqual([]);
		const rows = differences(treeConflict(same, other));
		expect(rows).toHaveLength(1);
		expect(rows[0]).toMatchObject({ name: "removed", files: "—" });
		expect(rows[0]!.database.split("\n")).toEqual(["NODE-005 · NODE-004 · NODE-001 · 2", "NODE-006 · NODE-006 · — · 0"]);
	});

	it("benennt Knoten, Maps und Bäume lesbar", () => {
		const node = { kind: "mindmap.node", label: "NODE-001", database: { fields: { title: "Idee" } }, files: null };
		expect(entryName(node)).toEqual({ key: "node", params: { label: "NODE-001", title: "Idee" } });
		const free = { kind: "mindmap.tree", label: null, database: null, files: tree({ tree_kind: "free", name: "Ideen" }) };
		expect(entryName(free)).toEqual({ key: "freeMap", params: { name: "Ideen" } });
		expect(entryName({ kind: "mindmap.tree", label: null, database: tree({ tree_kind: "project" }), files: null })).toEqual({ key: "projectTree", params: {} });
		expect(entryName({ kind: "mindmap.tree", label: null })).toEqual({ key: "tree", params: {} });
		expect(entryName({ kind: "task", label: "TASK-001" })).toBeNull();
	});

	it("liest bei einer Notiz zu einem Knoten das Label des Knotens statt eines Items", () => {
		const doc = { ...conflict("d", "both_changed", entry({ kind: "notes" }, { node: ["NODE-007"] }), null), kind: "mindmap.document" } as SyncConflict;
		expect(documentContext(doc)).toEqual({ kind: "notes", item: null, node: "NODE-007" });
	});
});
