import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { SyncPreview } from "../../../../../../client/src/plugins/workspace/api";
import { SyncDialog } from "../../../../../../client/src/plugins/workspace/SyncDialog";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { fakeWorkspaceBackend, project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const mirrored = project("p1", "Viewer", 1, { mirror_enabled: true, mirror_folder: "/work/viewer" });
const entry = (fields: Record<string, unknown>, refs: Record<string, string[]> = {}) => ({ label: "TASK-001", kind: "task", fields, refs });

const preview = (extra: Partial<SyncPreview> = {}): SyncPreview => ({
	project: "p1",
	direction: "both",
	state: "conflicts",
	token: "tok-1",
	transfers: [
		{ key: "u9", kind: "task", label: "TASK-009", target: "files", action: "create" },
		{ key: "u8", kind: "story", label: "STORY-002", target: "database", action: "update" },
	],
	conflicts: [
		{ key: "u1", kind: "task", label: "TASK-001", conflict: "both_changed", database: entry({ status: "Open", title: "T" }), files: entry({ status: "Completed", title: "T" }), recommendation: "none", reason: "both_changed" },
		{ key: "u2", kind: "task", label: "TASK-002", conflict: "both_changed", database: entry({ priority: "Normal" }), files: entry({ priority: "Urgent" }), recommendation: "none", reason: "both_changed" },
		{ key: "u3", kind: "task", label: "TASK-003", conflict: "deleted_in_files", database: entry({ title: "Weg" }), files: null, recommendation: "none", reason: "" },
	],
	skipped: [],
	not_imported: [],
	...extra,
});

async function renderDialog(options: Parameters<typeof fakeWorkspaceBackend>[0] = {}, onClose = () => {}) {
	const backend = fakeWorkspaceBackend({ projects: [mirrored], syncPreview: preview(), ...options });
	await renderWorkspace(<SyncDialog project={mirrored} onClose={onClose} />, { backend });
	await screen.findByTestId(ids.syncConflict(options.syncPreview?.conflicts[0]?.key ?? "u1"));
	return backend;
}

const executeBody = (backend: ReturnType<typeof fakeWorkspaceBackend>) => backend.calls("POST", "core/sync/p1/execute")[0]!.body;

describe("SyncDialog explains a conflict", () => {
	const spec = (content: string) => ({ label: "STORY-086_spec_nsfw.md", kind: "document", fields: { kind: "spec", content }, refs: { item: ["STORY-086"] } });
	const renamed = {
		key: "d1",
		kind: "document",
		label: "STORY-086_spec_nsfw.md",
		conflict: "deleted_in_files",
		database: spec("# Spec\nzeile eins"),
		files: null,
		database_changed: false,
		files_changed: null,
		synced_at: "2026-10-22T13:42:00+00:00",
		renamed_to: { key: "d2", label: "STORY-086_spec_sensibel.md", similarity: 0.95 },
		recommendation: "files",
		reason: "renamed",
	} as const;

	it("shows origin, context, the rename partner and a recommendation that is not preselected", async () => {
		await renderDialog({ syncPreview: preview({ conflicts: [renamed] }) });
		const card = await screen.findByTestId(ids.syncConflict("d1"));

		expect(screen.getByTestId(ids.syncOrigin("d1")).textContent).toContain("Die Datenbank ist seit dem letzten Abgleich unverändert.");
		expect(screen.getByTestId(ids.syncOrigin("d1")).textContent).toContain("Letzter Abgleich dieses Eintrags");
		expect(screen.getByTestId(ids.syncContext("d1")).textContent).toBe("Spec zu STORY-086");
		expect(screen.getByTestId(ids.syncRename("d1")).textContent).toContain("STORY-086_spec_sensibel.md (95 % gleich)");
		expect(screen.getByTestId(ids.syncRecommended("d1", "files"))).toBeTruthy();
		expect(screen.queryByTestId(ids.syncRecommended("d1", "database"))).toBeNull();
		expect(card.textContent).toContain("Der Eintrag existiert unter neuem Namen weiter");
		expect((screen.getByTestId(ids.syncChoice("d1", "files")) as HTMLInputElement).checked).toBe(false);
		expect(screen.queryByTestId(ids.syncDifference("d1", "kind"))).toBeNull();
		expect(screen.queryByTestId(ids.syncDifference("d1", "item"))).toBeNull();
	});

	it("shows a text that exists on both sides as a line diff", async () => {
		const both = { ...renamed, key: "d3", conflict: "both_changed", database: spec("a\nb\nalt"), files: spec("a\nb\nneu"), renamed_to: null, recommendation: "none", reason: "both_changed" };
		await renderDialog({ syncPreview: preview({ conflicts: [both as never] }) });
		const diff = await screen.findByTestId(ids.syncDiff("d3", "content"));

		expect(diff.textContent).toContain("−alt");
		expect(diff.textContent).toContain("+neu");
		expect(screen.queryByTestId(ids.syncWhitespaceOnly("d3", "content"))).toBeNull();
	});

	it("says so and writes out the empty line when only whitespace differs", async () => {
		const both = { ...renamed, key: "d4", conflict: "both_changed", database: spec("a\n\nb"), files: spec("a\n\n\nb"), renamed_to: null, recommendation: "none", reason: "both_changed" };
		await renderDialog({ syncPreview: preview({ conflicts: [both as never] }) });
		const diff = await screen.findByTestId(ids.syncDiff("d4", "content"));

		expect(screen.getByTestId(ids.syncWhitespaceOnly("d4", "content"))).toBeTruthy();
		expect(diff.textContent).toContain("+⏎ leere Zeile");
	});
});

describe("SyncDialog", () => {
	it("shows the conflicts first with the fields that differ, then the transfers", async () => {
		await renderDialog();

		expect(screen.getByTestId(ids.syncDifference("u1", "status")).textContent).toContain("Open");
		expect(screen.getByTestId(ids.syncDifference("u1", "status")).textContent).toContain("Completed");
		expect(screen.queryByTestId(ids.syncDifference("u1", "title"))).toBeNull(); // gleiche Felder bleiben weg
		expect(screen.getByTestId(ids.syncConflict("u3")).textContent).toContain("in den Dateien gelöscht");
		expect(screen.getByTestId(ids.syncTransfers).textContent).toContain("in die Dateien · anlegen · TASK-009");
		expect(screen.getByTestId(ids.syncTransfers).textContent).toContain("in die Datenbank · ändern · STORY-002");
		expect(screen.getByTestId(ids.syncState).textContent).toBe("Konflikte warten");
	});

	it("decides a conflict by choice and sends the token with the decisions", async () => {
		const backend = await renderDialog();

		fireEvent.click(screen.getByTestId(ids.syncChoice("u1", "files")));
		fireEvent.click(screen.getByTestId(ids.syncChoice("u2", "database")));
		fireEvent.click(screen.getByTestId(ids.syncExecute));

		await waitFor(() => expect(backend.calls("POST", "core/sync/p1/execute")).toHaveLength(1));
		expect(executeBody(backend)).toEqual({
			token: "tok-1",
			direction: "both",
			decisions: [
				{ uid: "u1", choice: "files" },
				{ uid: "u2", choice: "database" },
			],
			delete_missing: false,
		});
	});

	it("decides all conflicts at once, but a deletion stays for the owner to choose", async () => {
		const backend = await renderDialog();

		fireEvent.click(screen.getByTestId(ids.syncAll("files")));
		fireEvent.click(screen.getByTestId(ids.syncExecute));

		await waitFor(() => expect(backend.calls("POST", "core/sync/p1/execute")).toHaveLength(1));
		expect(executeBody(backend)).toMatchObject({ decisions: [{ uid: "u1", choice: "files" }, { uid: "u2", choice: "files" }], delete_missing: false });
		expect(screen.getByTestId(ids.syncConflict("u3")).textContent).toContain("gelöscht");
	});

	it("sends delete_missing only when a deleting choice was made for one conflict", async () => {
		const backend = await renderDialog();

		fireEvent.click(screen.getByTestId(ids.syncChoice("u3", "files")));
		fireEvent.click(screen.getByTestId(ids.syncExecute));

		await waitFor(() => expect(backend.calls("POST", "core/sync/p1/execute")).toHaveLength(1));
		expect(executeBody(backend)).toMatchObject({ decisions: [{ uid: "u3", choice: "files" }], delete_missing: true });
	});

	it("leaves conflicts out that were not decided and shows the result", async () => {
		const backend = await renderDialog({
			syncResult: { project: "p1", state: "conflicts", to_database: 1, to_files: 2, created: ["TASK-004"], conflicts_left: [{ key: "u2", kind: "task", label: "TASK-002", conflict: "both_changed", database: null, files: null, recommendation: "none", reason: "both_changed" }] },
		});

		fireEvent.click(screen.getByTestId(ids.syncChoice("u1", "database")));
		fireEvent.click(screen.getByTestId(ids.syncExecute));

		const result = await screen.findByTestId(ids.syncResult);
		expect(result.textContent).toContain("1 in die Datenbank, 2 in die Dateien übertragen.");
		expect(result.textContent).toContain("Neu angelegt: TASK-004.");
		expect(result.textContent).toContain("1 Konflikt bleibt offen.");
		expect(executeBody(backend)).toMatchObject({ decisions: [{ uid: "u1", choice: "database" }] });
	});

	it("reloads the preview after a sync, so a decided conflict does not stay in the list", async () => {
		const backend = await renderDialog();
		const previews = () => backend.calls("GET", "core/sync/p1/preview").length;
		const before = previews();

		fireEvent.click(screen.getByTestId(ids.syncChoice("u1", "database")));
		fireEvent.click(screen.getByTestId(ids.syncExecute));

		await screen.findByTestId(ids.syncResult);
		await waitFor(() => expect(previews()).toBe(before + 1));
	});

	it("reloads the preview with the other direction", async () => {
		const backend = await renderDialog();

		fireEvent.change(screen.getByTestId(ids.syncDirection), { target: { value: "to_files" } });

		await waitFor(() => expect(backend.calls("GET", "core/sync/p1/preview").some((call) => call.query.get("direction") === "to_files")).toBe(true));
	});

	it("shows the message of the server when the sync is refused, and reloads the preview when it is stale", async () => {
		let stale = true;
		const backend = await renderDialog({
			respond: ({ method, path }) => {
				if (method === "POST" && path.endsWith("/execute") && stale) {
					stale = false;
					return Response.json({ code: "sync_preview_stale", message: "Die Vorschau ist veraltet", details: {} }, { status: 409 });
				}
				return undefined;
			},
		});
		const loads = () => backend.calls("GET", "core/sync/p1/preview").length;
		const before = loads();

		fireEvent.click(screen.getByTestId(ids.syncExecute));

		await waitFor(() => expect(screen.getByTestId(ids.syncError).textContent).toBe("Die Vorschau ist veraltet"));
		await waitFor(() => expect(loads()).toBeGreaterThan(before));
	});

	it("shows a format error of the folder with file and line", async () => {
		const backend = fakeWorkspaceBackend({
			projects: [mirrored],
			respond: ({ path }) =>
				path.endsWith("/preview")
					? Response.json({ code: "invalid_value", message: "TODO.md:33: Priorität `High` gibt es nicht", details: { file: "TODO.md", line: 33 } }, { status: 422 })
					: undefined,
		});
		await renderWorkspace(<SyncDialog project={mirrored} onClose={() => {}} />, { backend });

		await waitFor(() => expect(screen.getByTestId(ids.syncError).textContent).toBe("TODO.md:33: Priorität `High` gibt es nicht"));
		expect((screen.getByTestId(ids.syncExecute) as HTMLButtonElement).disabled).toBe(true);
	});

	it("says so when there is nothing to transfer, and closes", async () => {
		let closed = false;
		const backend = fakeWorkspaceBackend({ projects: [mirrored], syncPreview: preview({ state: "in_sync", conflicts: [], transfers: [] }) });
		await renderWorkspace(<SyncDialog project={mirrored} onClose={() => (closed = true)} />, { backend });

		await waitFor(() => expect(screen.getByTestId(ids.syncTransfers).textContent).toContain("Nichts zu übertragen."));
		fireEvent.click(screen.getByTestId(ids.syncClose));
		expect(closed).toBe(true);
	});

	it("tells how many new entries from the files this direction does not take over", async () => {
		const backend = fakeWorkspaceBackend({
			projects: [mirrored],
			syncPreview: preview({ conflicts: [], not_imported: [{ key: "n", kind: "task", label: null, target: "database", action: "create" }] }),
		});
		await renderWorkspace(<SyncDialog project={mirrored} onClose={() => {}} />, { backend });

		await waitFor(() => expect(screen.getByTestId(ids.syncTransfers).textContent).toContain("1 neue Einträge aus den Dateien"));
	});
});
