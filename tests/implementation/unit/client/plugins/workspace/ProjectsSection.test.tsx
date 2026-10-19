import { cleanup, createEvent, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { flushUiState } from "../../../../../../client/src/core/ui-state/uiState";
import { ProjectsSection } from "../../../../../../client/src/plugins/workspace/ProjectsSection";
import { SYNC_AUTO_CLASS } from "../../../../../../client/src/plugins/workspace/SyncIndicator";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { expectPersisted, fakeWorkspaceBackend, project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const three = () => [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1), project("p2", "Notizen", 2)];

afterEach(cleanup);

async function renderSection(options: Parameters<typeof fakeWorkspaceBackend>[0] = { projects: three() }) {
	const backend = fakeWorkspaceBackend(options);
	await renderWorkspace(<ProjectsSection />, { backend });
	await screen.findByTestId(ids.project("p0"));
	return backend;
}

/** Marks the project by a click on its name and opens its card with the pencil in the header. */
async function editProject(uid: string) {
	fireEvent.click(screen.getByTestId(ids.projectName(uid)));
	await waitFor(() => expect(screen.getByTestId(ids.project(uid)).getAttribute("data-marked")).toBe("true"));
	fireEvent.click(screen.getByTestId(ids.projectEditMarked));
	await screen.findByTestId(ids.projectCard);
}

describe("ProjectsSection", () => {
	it("lists the projects in the order of the server, all visible, none marked", async () => {
		await renderSection();

		const items = within(screen.getByTestId(ids.projectList)).getAllByRole("listitem");
		expect(items.map((item) => item.textContent)).toEqual(["Allgemein", "Viewer", "Notizen"]);
		for (const uid of ["p0", "p1", "p2"]) {
			expect((screen.getByTestId(ids.projectVisible(uid)) as HTMLInputElement).checked).toBe(true);
			expect(screen.getByTestId(ids.project(uid)).getAttribute("data-marked")).toBe("false");
		}
	});

	it("hides a project with the checkbox and keeps that in the UI state of the server", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(ids.projectVisible("p1")));
	
		await expectPersisted(backend, flushUiState, waitFor, { hidden: ["p1"] });
		await waitFor(() => expect((screen.getByTestId(ids.projectVisible("p1")) as HTMLInputElement).checked).toBe(false));
	});

	it("restores the hidden and the marked project from the UI state", async () => {
		await renderSection({ projects: three(), documents: { workspace: { hidden: ["p2"], marked: "p1" } } });

		await waitFor(() => expect(screen.getByTestId(ids.project("p1")).getAttribute("data-marked")).toBe("true"));
		expect((screen.getByTestId(ids.projectVisible("p2")) as HTMLInputElement).checked).toBe(false);
		expect((screen.getByTestId(ids.projectVisible("p0")) as HTMLInputElement).checked).toBe(true);
	});

	it("marks a project by a click and unmarks it by a second click", async () => {
		const backend = await renderSection();

		fireEvent.click(within(screen.getByTestId(ids.project("p1"))).getByRole("button", { name: "Viewer" }));
		await waitFor(() => expect(screen.getByTestId(ids.project("p1")).getAttribute("data-marked")).toBe("true"));
			await expectPersisted(backend, flushUiState, waitFor, { marked: "p1" });

		fireEvent.click(within(screen.getByTestId(ids.project("p1"))).getByRole("button", { name: "Viewer" }));
		await waitFor(() => expect(screen.getByTestId(ids.project("p1")).getAttribute("data-marked")).toBe("false"));
	});

	it("moves a project to the place of another by dragging", async () => {
		const backend = await renderSection();
		const dataTransfer = { setData: () => {}, getData: () => "p2" };
		const drag = (type: string, uid: string) => {
			const event = createEvent(type as never, screen.getByTestId(ids.project(uid)), { bubbles: true, cancelable: true } as never);
			Object.defineProperty(event, "dataTransfer", { value: dataTransfer });
			fireEvent(screen.getByTestId(ids.project(uid)), event);
		};

		drag("dragstart", "p2");
		drag("dragover", "p1");
		drag("drop", "p1");

		await waitFor(() => expect(backend.calls("POST", "/move")).toHaveLength(1));
		expect(backend.calls("POST", "/move")[0]).toMatchObject({ path: "workspace/projects/p2/move", body: { version: 1, position: 1 } });
		await waitFor(() =>
			expect(within(screen.getByTestId(ids.projectList)).getAllByRole("listitem").map((item) => item.textContent)).toEqual(["Allgemein", "Notizen", "Viewer"]),
		);
	});

	it("creates a project in the card and lists it", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(ids.projectAdd));
		fireEvent.change(screen.getByTestId(ids.cardName), { target: { value: "Neu" } });
		fireEvent.click(screen.getByTestId(ids.cardSave));

		await waitFor(() => expect(screen.getByTestId(ids.project("p3")).textContent).toBe("Neu"));
		expect(screen.queryByTestId(ids.projectCard)).toBeNull();
		expect(backend.calls("POST", "workspace/projects")[0]!.body).toMatchObject({ name: "Neu", mirror_enabled: false });
	});

	it("shows the server's message when the name is taken and keeps the card open", async () => {
		await renderSection();

		fireEvent.click(screen.getByTestId(ids.projectAdd));
		fireEvent.change(screen.getByTestId(ids.cardName), { target: { value: "Viewer" } });
		fireEvent.click(screen.getByTestId(ids.cardSave));

		await waitFor(() => expect(screen.getByTestId(ids.cardError).textContent).toBe("Der Name ist schon vergeben"));
		expect(screen.getByTestId(ids.projectCard)).toBeTruthy();
	});

	it("edits a project: name, folder and mirror, sent with the version", async () => {
		const backend = await renderSection();

		await editProject("p1");
		fireEvent.change(screen.getByTestId(ids.cardName), { target: { value: "Viewer 2" } });
		fireEvent.change(screen.getByTestId(ids.cardFolder), { target: { value: "/work/viewer" } });
		fireEvent.click(screen.getByTestId(ids.cardMirrorEnabled));
		fireEvent.click(screen.getByTestId(ids.cardSave));

		await waitFor(() => expect(screen.getByTestId(ids.project("p1")).textContent).toBe("Viewer 2"));
		expect(backend.calls("PUT", "workspace/projects/p1")[0]!.body).toMatchObject({
			version: 1,
			name: "Viewer 2",
			mirror_folder: "/work/viewer",
			mirror_enabled: true,
			auto_sync: false,
		});
	});

	it("offers the pencil in the header only while a project is marked, with a hint otherwise", async () => {
		await renderSection();

		const pencil = screen.getByTestId(ids.projectEditMarked) as HTMLButtonElement;
		expect(pencil.disabled).toBe(true);
		expect(screen.getByTestId(ids.projectEditHint).getAttribute("aria-label")).toBe("Erst ein Projekt auswählen");
		expect(screen.queryByTestId("workspace.project-edit.p1")).toBeNull();

		await editProject("p1");
		expect((screen.getByTestId(ids.cardName) as HTMLInputElement).value).toBe("Viewer");
	});

	it("opens the card of a project by a double click on its name", async () => {
		await renderSection();

		fireEvent.doubleClick(screen.getByTestId(ids.projectName("p2")));

		expect(((await screen.findByTestId(ids.cardName)) as HTMLInputElement).value).toBe("Notizen");
	});

	it("opens the sync of a project directly from its warning, and keeps the auto-sync sign for hovering", async () => {
		const mirrored = project("p1", "Viewer", 1, { mirror_enabled: true, mirror_folder: "/work/viewer", auto_sync: true });
		await renderSection({
			projects: [project("p0", "Allgemein", 0, { builtin: true }), mirrored],
			syncStatus: { p1: { project: "p1", state: "conflicts", conflicts: 1, to_database: 0, to_files: 0, files: [], reason: null, last_sync: null } },
		});

		const warning = await screen.findByTestId(ids.syncAttention("p1"));
		expect(screen.getByTestId(ids.syncAuto("p1")).classList.contains(SYNC_AUTO_CLASS)).toBe(true);
		fireEvent.click(warning);

		expect(await screen.findByTestId(ids.syncDialog)).toBeTruthy();
	});

	it("does not offer to rename or remove the built-in project", async () => {
		await renderSection();

		await editProject("p0");

		expect((screen.getByTestId(ids.cardName) as HTMLInputElement).disabled).toBe(true);
		expect(screen.queryByTestId(ids.cardRemove)).toBeNull();
	});

	it("removes an empty project at once", async () => {
		await renderSection();

		await editProject("p2");
		fireEvent.click(screen.getByTestId(ids.cardRemove));

		await waitFor(() => expect(screen.queryByTestId(ids.project("p2"))).toBeNull());
	});

	it("asks before it removes a project with content, then removes it with confirmation", async () => {
		const backend = await renderSection({ projects: three(), elementsInProjects: { p1: 2 } });

		await editProject("p1");
		fireEvent.click(screen.getByTestId(ids.cardRemove));
		const dialog = await screen.findByTestId("shared.confirm-dialog");
		expect(dialog.textContent).toContain("2 Elemente");
		fireEvent.click(screen.getByTestId("shared.confirm-dialog-confirm"));

		await waitFor(() => expect(screen.queryByTestId(ids.project("p1"))).toBeNull());
		expect(backend.calls("DELETE", "workspace/projects/p1").map((call) => call.query.get("confirm"))).toEqual([null, "true"]);
	});

	it("picks the mirror folder in the folder browser", async () => {
		await renderSection({
			projects: three(),
			folders: {
				"": { path: "/home/me", parent: "/home", has_mirror: false, folders: [{ name: "work", has_mirror: false }] },
				"/home/me/work": { path: "/home/me/work", parent: "/home/me", has_mirror: true, folders: [] },
			},
		});

		await editProject("p1");
		fireEvent.click(screen.getByTestId(ids.cardBrowse));
		fireEvent.click(await screen.findByTestId(ids.folder("work")));
		await waitFor(() => expect(screen.getByTestId(ids.folderBrowser).textContent).toContain("/home/me/work"));
		fireEvent.click(screen.getByTestId(ids.folderChoose));

		await waitFor(() => expect((screen.getByTestId(ids.cardFolder) as HTMLInputElement).value).toBe("/home/me/work"));
		expect(screen.queryByTestId(ids.folderBrowser)).toBeNull();
	});
});
