import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ItemDetail } from "../../../../../../client/src/plugins/backlog/ItemDetail";
import { CreateEpic } from "../../../../../../client/src/plugins/backlog/CreateForms";
import { backlogTestIds as ids } from "../../../../../../client/src/plugins/backlog/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { detail, item } from "../../../../../helpers/client/backlogFixtures";
import { fakeWorkspaceBackend } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const summary = (uid: string) => ({ uid, label: uid.toUpperCase(), type: "Epic", title: `Titel ${uid}`, status: "Completed", required_for_parent: null, deleted: false });

async function renderDetail(options: Parameters<typeof fakeWorkspaceBackend>[0] = {}, uid = "t1") {
	const backend = fakeWorkspaceBackend({
		details: { t1: detail("t1", { version: 4 }), ...options?.details },
		backlog: [item("t1"), item("t2"), item("e1", { type: "Epic" })],
		areas: { p1: ["Client", "Server"] },
		projects: [{ uid: "p1", name: "Viewer", position: 0, version: 1, builtin: false, mirror_folder: null, mirror_enabled: false, auto_sync: false, sync_direction: "both", created_at: "2026-10-16T10:00:00Z" }],
		...options,
	});
	await renderWorkspace(<ItemDetail uid={uid} onSelect={() => {}} />, { backend });
	await screen.findByTestId(ids.detail);
	return backend;
}

const putBody = (backend: ReturnType<typeof fakeWorkspaceBackend>) => backend.calls("PUT", "backlog/items/t1")[0]!.body;
const choose = async (field: string, option: string) => {
	fireEvent.mouseDown(within(screen.getByTestId(sharedTestIds.inlineField(field))).getByRole("combobox"));
	fireEvent.click(await screen.findByRole("option", { name: option }));
};

describe("ItemDetail: inline fields", () => {
	it("changes the status with the version and without a resolution", async () => {
		const backend = await renderDetail();

		await choose("status", "In Arbeit");

		await waitFor(() => expect(backend.calls("PUT", "backlog/items/t1")).toHaveLength(1));
		expect(putBody(backend)).toEqual({ version: 4, fields: { status: "In progress" } });
	});

	it("asks for a resolution when the status is closed, suggests one and sends it", async () => {
		const backend = await renderDetail();

		await choose("status", "Abgeschlossen");
		const input = (await screen.findByTestId(ids.resolutionInput)) as HTMLInputElement | HTMLTextAreaElement;
		expect(input.value).toMatch(/^Confirmed by the project owner on \d{4}-\d{2}-\d{2}\.$/);
		fireEvent.change(input, { target: { value: "Von Hand bestätigt." } });
		fireEvent.click(screen.getByTestId(ids.resolutionConfirm));

		await waitFor(() => expect(backend.calls("PUT", "backlog/items/t1")).toHaveLength(1));
		expect(putBody(backend)).toEqual({ version: 4, fields: { status: "Completed" }, resolution: "Von Hand bestätigt." });
		expect(screen.queryByTestId(ids.resolutionDialog)).toBeNull();
	});

	it("sends nothing when the resolution dialog is cancelled", async () => {
		const backend = await renderDetail();

		await choose("status", "Abgelehnt");
		fireEvent.click(await screen.findByText("Abbrechen"));

		expect(backend.calls("PUT", "backlog/items/t1")).toHaveLength(0);
	});

	it("changes the priority", async () => {
		const backend = await renderDetail();

		await choose("priority", "Dringend");

		await waitFor(() => expect(putBody(backend)).toEqual({ version: 4, fields: { priority: "Urgent" } }));
	});

	it("chooses an area of the project or creates a new one", async () => {
		const backend = await renderDetail();

		await choose("area", "Server");
		await waitFor(() => expect(backend.calls("PUT", "backlog/items/t1")).toHaveLength(1));
		await choose("area", "＋ Neuer Bereich …");
		fireEvent.change(await screen.findByTestId(ids.resolutionInput), { target: { value: "Neuer Bereich" } });
		fireEvent.click(screen.getByTestId(ids.resolutionConfirm));

		await waitFor(() => expect(backend.calls("PUT", "backlog/items/t1")).toHaveLength(2));
		expect(backend.calls("PUT", "backlog/items/t1").map((call) => call.body)).toEqual([
			{ version: 4, fields: { area: "Server" } },
			{ version: 4, fields: { area: "Neuer Bereich" } },
		]);
	});

	it("shows 'required for parent' only below a parent and changes it", async () => {
		const withParent = await renderDetail({ details: { t1: detail("t1", { version: 4, parent: summary("e1"), required_for_parent: true }) } });

		await choose("required", "Nein");

		await waitFor(() => expect(putBody(withParent)).toEqual({ version: 4, fields: { required_for_parent: false } }));
		cleanup();
		await renderDetail();
		expect(screen.queryByTestId(sharedTestIds.inlineField("required"))).toBeNull();
	});

	it("sets the dependencies from the items of the project", async () => {
		const backend = await renderDetail();

		fireEvent.mouseDown(within(screen.getByTestId(sharedTestIds.inlineField("dependencies"))).getByRole("combobox"));
		fireEvent.click(await screen.findByRole("option", { name: "T2 — Titel t2" }));

		await waitFor(() => expect(putBody(backend)).toEqual({ version: 4, fields: { dependencies: ["t2"] } }));
	});

	it("shows the message of the server when a field cannot be saved", async () => {
		await renderDetail({
			respond: ({ method, path }) =>
				method === "PUT" && path === "backlog/items/t1"
					? Response.json({ code: "epic_without_required_child", message: "Epic T1 braucht ein Pflichtkind.", details: {} }, { status: 400 })
					: undefined,
		});

		await choose("status", "In Arbeit");

		await waitFor(() => expect(screen.getByTestId(sharedTestIds.inlineFieldError("status")).textContent).toBe("Epic T1 braucht ein Pflichtkind."));
	});
});

describe("ItemDetail: form, children, type, trash", () => {
	it("edits the item in the form and sends all fields with the version", async () => {
		const backend = await renderDetail({ details: { t1: detail("t1", { version: 4, goal: "Ziel", completion_criteria: "Krit", area: "Server" }) } });

		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("edit")));
		const title = await screen.findByTestId(ids.formField("title"));
		fireEvent.change(title, { target: { value: "Neuer Titel" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("PUT", "backlog/items/t1")).toHaveLength(1));
		expect(putBody(backend)).toMatchObject({
			version: 4,
			fields: { title: "Neuer Titel", area: "Server", priority: "Normal", goal: "Ziel", completion_criteria: "Krit", dependencies: [] },
		});
		await waitFor(() => expect(screen.queryByTestId(ids.formDialog)).toBeNull());
	});

	it("offers to load the current state after a version conflict", async () => {
		await renderDetail({
			details: { t1: detail("t1", { version: 4, goal: "Ziel", completion_criteria: "Krit", area: "Server" }) },
			respond: ({ method }) =>
				method === "PUT" ? Response.json({ code: "version_conflict", message: "geändert", details: {} }, { status: 409 }) : undefined,
		});

		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("edit")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.editFormSave));

		expect(await screen.findByTestId(sharedTestIds.editFormConflict)).toBeTruthy();
		expect(screen.getByTestId(ids.formDialog)).toBeTruthy();
	});

	it("creates a child below the item: a story below an epic, with the parent and 'required'", async () => {
		const backend = await renderDetail({ details: { e1: detail("e1", { type: "Epic" }) } }, "e1");

		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("child")));
		expect((await screen.findByTestId(ids.formDialog)).textContent).toContain("Story anlegen");
		fireEvent.change(screen.getByTestId(ids.formField("title")), { target: { value: "Kind" } });
		fireEvent.change(screen.getByTestId(ids.formField("area")), { target: { value: "Server" } });
		fireEvent.change(screen.getByTestId(ids.formField("goal")), { target: { value: "Ziel" } });
		fireEvent.change(screen.getByTestId(ids.formField("completion_criteria")), { target: { value: "Krit" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.requests.filter((call) => call.path === "backlog/items" && call.method === "POST")).toHaveLength(1));
		expect(backend.requests.find((call) => call.path === "backlog/items" && call.method === "POST")!.body).toMatchObject({
			project: "p1",
			type: "Story",
			fields: { title: "Kind", area: "Server", parent: "e1", required_for_parent: true },
		});
	});

	it("offers no child for a task", async () => {
		await renderDetail();

		expect((screen.getByTestId(sharedTestIds.detailAction("child")) as HTMLButtonElement).disabled).toBe(true);
	});

	it("reopens the closed ancestors after a yes and creates the item once more", async () => {
		let attempts = 0;
		const backend = await renderDetail({
			details: { e1: detail("e1", { type: "Epic" }) },
			respond: ({ method, path }) => {
				if (method === "POST" && path === "backlog/items" && attempts++ === 0) {
					return Response.json(
						{ code: "parent_closed", message: "zu", details: { ancestors: [{ uid: "e0", label: "EPIC-000" }, { uid: "e1", label: "EPIC-001" }] } },
						{ status: 400 },
					);
				}
				return undefined;
			},
		}, "e1");

		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("child")));
		for (const [field, value] of [["title", "K"], ["area", "S"], ["goal", "Z"], ["completion_criteria", "C"]] as const) {
			fireEvent.change(await screen.findByTestId(ids.formField(field)), { target: { value } });
		}
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		const dialog = await screen.findByTestId(sharedTestIds.confirmDialog);
		expect(dialog.textContent).toContain("EPIC-000, EPIC-001");
		fireEvent.click(screen.getByTestId(sharedTestIds.confirmDialogConfirm));

		const creates = () => backend.requests.filter((call) => call.method === "POST" && call.path === "backlog/items");
		await waitFor(() => expect(creates()).toHaveLength(2));
		expect(backend.calls("POST", "backlog/items/e1/reopen")).toHaveLength(1);
	});

	it("keeps the item as it is when the reopening is declined", async () => {
		const backend = await renderDetail({
			details: { e1: detail("e1", { type: "Epic" }) },
			respond: ({ method, path }) =>
				method === "POST" && path === "backlog/items"
					? Response.json({ code: "parent_closed", message: "Parent geschlossen", details: { ancestors: [{ uid: "e1", label: "EPIC-001" }] } }, { status: 400 })
					: undefined,
		}, "e1");

		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("child")));
		for (const [field, value] of [["title", "K"], ["area", "S"], ["goal", "Z"], ["completion_criteria", "C"]] as const) {
			fireEvent.change(await screen.findByTestId(ids.formField(field)), { target: { value } });
		}
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogCancel));

		await waitFor(() => expect(screen.getByTestId(sharedTestIds.editFormError).textContent).toBe("Parent geschlossen"));
		expect(backend.calls("POST", "reopen")).toHaveLength(0);
	});

	it("changes the type and tells the old and the new label", async () => {
		const backend = await renderDetail({
			respond: ({ method, path }) =>
				method === "POST" && path === "backlog/items/t1/retype"
					? Response.json({
							item: detail("t1", { label: "STORY-007", type: "Story" }),
							old_label: "T1",
							new_label: "STORY-007",
							notices: [{ code: "external_references_may_remain", message: "x", details: { old_label: "T1", new_label: "STORY-007" } }],
						})
					: undefined,
		});

		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("retype")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.choiceDialogOption("Story")));

		const notice = await screen.findByTestId(ids.retypeNotice);
		expect(notice.textContent).toContain("T1 heißt jetzt STORY-007");
		expect(notice.textContent).toContain("außerhalb des Backlogs");
		expect(backend.calls("POST", "retype")[0]!.body).toEqual({ version: 4, type: "Story" });
	});

	it("moves the item to the trash, and asks first when it has children", async () => {
		const backend = await renderDetail({ elements: [{ uid: "t1", project_uid: "p1", kind: "task", label: "T1", title: "Titel t1", version: 4, deleted: false }], children: { t1: 2 } });

		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("delete")));
		expect((await screen.findByTestId(sharedTestIds.confirmDialog)).textContent).toContain("2 Kinder");
		fireEvent.click(screen.getByTestId(sharedTestIds.confirmDialogConfirm));

		await waitFor(() => expect(backend.calls("DELETE", "workspace/elements/t1")).toHaveLength(2));
		expect(backend.calls("DELETE", "workspace/elements/t1")[1]!.query.get("cascade")).toBe("true");
	});
});

describe("create forms for the '＋ New' dialog", () => {
	it("creates an epic in the project the dialog hands over", async () => {
		const backend = fakeWorkspaceBackend({ areas: { p1: [] } });
		const { useCreateDialog } = await import("../../../../../../client/src/plugins/workspace/createDialog");
		const { CreateDialogState } = await import("../../../../../../client/src/plugins/workspace/createDialog");
		let closed = false;
		await renderWorkspace(
			<CreateDialogState.Provider value={{ close: () => (closed = true), projectUid: "p1" }}>
				<CreateEpic />
			</CreateDialogState.Provider>,
			{ backend },
		);
		void useCreateDialog;

		for (const [field, value] of [["title", "Neues Epic"], ["area", "Server"], ["goal", "Z"], ["completion_criteria", "C"]] as const) {
			fireEvent.change(await screen.findByTestId(ids.formField(field)), { target: { value } });
		}
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "backlog/items")).toHaveLength(1));
		expect(backend.calls("POST", "backlog/items")[0]!.body).toMatchObject({ project: "p1", type: "Epic", fields: { title: "Neues Epic" } });
		await waitFor(() => expect(closed).toBe(true));
		expect(screen.queryByTestId(ids.formField("parent"))).toBeNull(); // ein Epic hat keinen Parent
	});
});
