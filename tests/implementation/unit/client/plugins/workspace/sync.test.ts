import { describe, expect, it } from "vitest";
import type { SyncConflict, SyncStatus } from "../../../../../../client/src/plugins/workspace/api";
import { choiceDeletes, decisionsOf, differences, isDeletionConflict, needsAttention, syncView, withBulkChoice, choiceBlocked } from "../../../../../../client/src/plugins/workspace/sync";

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
