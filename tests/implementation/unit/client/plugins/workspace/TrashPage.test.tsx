import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds } from "../../../../../../client/src/core";
import TrashPage from "../../../../../../client/src/plugins/workspace/pages/TrashPage";
import type { TrashedElement } from "../../../../../../client/src/plugins/workspace/api";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { fakeWorkspaceBackend, project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const entry = (uid: string, label: string, title: string, projectUid = "p0"): TrashedElement => ({
	uid,
	project_uid: projectUid,
	kind: "task",
	label,
	title,
	deleted_at: "2026-10-16T12:00:00Z",
});

const trash = [entry("a", "TASK-001", "Sync reparieren"), entry("b", "STORY-001", "Anderes", "p1"), entry("c", "TASK-002", "Noch eins")];
const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];

afterEach(cleanup);

async function renderTrash(options: Parameters<typeof fakeWorkspaceBackend>[0] = {}) {
	const backend = fakeWorkspaceBackend({ projects, trash, ...options });
	await renderWorkspace(<TrashPage />, { backend });
	await screen.findByTestId(ids.trashRow("a"));
	return backend;
}

describe("TrashPage", () => {
	it("lists the deleted elements of the shown projects with label, title and project", async () => {
		await renderTrash();

		expect(screen.getByTestId(ids.trashRow("a")).textContent).toContain("TASK-001");
		expect(screen.getByTestId(ids.trashRow("a")).textContent).toContain("Sync reparieren");
		expect(screen.getByTestId(ids.trashRow("b")).textContent).toContain("Viewer");
		expect(screen.getByTestId(ids.trash).textContent).toContain("3 Elemente");
	});

	it("shows only the projects that are switched on and filters by the search text", async () => {
		await renderTrash({ documents: { workspace: { hidden: ["p1"], search: "sync" } } });

		await waitFor(() => expect(screen.queryByTestId(ids.trashRow("c"))).toBeNull());
		expect(screen.queryByTestId(ids.trashRow("b"))).toBeNull();
		expect(screen.getByTestId(ids.trashRow("a"))).toBeTruthy();
	});

	it("shows the element of a clicked row in the detail column and closes it on a second click", async () => {
		await renderTrash();

		fireEvent.click(screen.getByTestId(ids.trashRow("a")));

		const detail = await screen.findByTestId(coreTestIds.detail);
		expect(detail.querySelector(`[data-testid="${ids.elementDetailPlain}"]`)?.textContent).toContain("TASK-001 — Sync reparieren");
		expect(screen.getByTestId(ids.trashRow("a")).getAttribute("aria-selected")).toBe("true");

		fireEvent.click(screen.getByTestId(ids.trashRow("a")));
		expect(screen.queryByTestId(coreTestIds.detail)).toBeNull();
	});

	it("does not open the detail when the checkbox or a button of the row is used", async () => {
		await renderTrash();

		fireEvent.click(screen.getByTestId(ids.trashSelect("a")));
		fireEvent.click(screen.getByTestId(ids.trashPurge("b")));

		expect(screen.queryByTestId(coreTestIds.detail)).toBeNull();
	});

	it("says so when the trash is empty", async () => {
		const backend = fakeWorkspaceBackend({ projects, trash: [] });
		await renderWorkspace(<TrashPage />, { backend });

		expect((await screen.findByTestId(ids.trash)).textContent).toContain("Der Papierkorb ist leer.");
	});

	it("restores one element", async () => {
		const backend = await renderTrash();

		fireEvent.click(screen.getByTestId(ids.trashRestore("a")));

		await waitFor(() => expect(screen.queryByTestId(ids.trashRow("a"))).toBeNull());
		expect(backend.calls("POST", "trash/restore")[0]!.body).toEqual({ uids: ["a"] });
	});

	it("restores the chosen elements together, and chooses all", async () => {
		const backend = await renderTrash();

		fireEvent.click(screen.getByTestId(ids.trashSelect("a")));
		fireEvent.click(screen.getByTestId(ids.trashSelect("b")));
		fireEvent.click(screen.getByTestId(ids.trashRestoreSelected));

		await waitFor(() => expect(screen.queryByTestId(ids.trashRow("b"))).toBeNull());
		expect(backend.calls("POST", "trash/restore")[0]!.body).toEqual({ uids: ["a", "b"] });
		fireEvent.click(screen.getByTestId(ids.trashSelectAll));
		expect((screen.getByTestId(ids.trashSelect("c")) as HTMLInputElement).checked).toBe(true);
	});

	it("shows the plugin's refusal when a restore is not allowed and keeps the element", async () => {
		await renderTrash({ restoreRefused: { a: "Das Elternelement liegt im Papierkorb" } });

		fireEvent.click(screen.getByTestId(ids.trashRestore("a")));

		await waitFor(() => expect(screen.getByTestId(ids.trashError).textContent).toBe("Das Elternelement liegt im Papierkorb"));
		expect(screen.getByTestId(ids.trashRow("a"))).toBeTruthy();
	});

	it("asks before it deletes for good, and deletes only after the confirmation", async () => {
		const backend = await renderTrash();

		fireEvent.click(screen.getByTestId(ids.trashPurge("a")));
		expect((await screen.findByTestId("shared.confirm-dialog")).textContent).toContain("1 Element wird");
		fireEvent.click(screen.getByTestId("shared.confirm-dialog-cancel"));
		expect(backend.calls("POST", "trash/purge")).toHaveLength(0);

		fireEvent.click(screen.getByTestId(ids.trashPurge("a")));
		fireEvent.click(await screen.findByTestId("shared.confirm-dialog-confirm"));

		await waitFor(() => expect(screen.queryByTestId(ids.trashRow("a"))).toBeNull());
		expect(backend.calls("POST", "trash/purge")[0]!.body).toEqual({ uids: ["a"] });
	});

	it("deletes the chosen elements for good in one request", async () => {
		const backend = await renderTrash();

		fireEvent.click(screen.getByTestId(ids.trashSelectAll));
		fireEvent.click(screen.getByTestId(ids.trashPurgeSelected));
		fireEvent.click(await screen.findByTestId("shared.confirm-dialog-confirm"));

		await waitFor(() => expect(backend.calls("POST", "trash/purge")).toHaveLength(1));
		expect(backend.calls("POST", "trash/purge")[0]!.body).toEqual({ uids: ["a", "b", "c"] });
	});
});
