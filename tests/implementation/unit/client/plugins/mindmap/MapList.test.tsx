import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { flushUiState } from "../../../../../../client/src/core/ui-state/uiState";
import { MapList } from "../../../../../../client/src/plugins/mindmap/MapList";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { node } from "../../../../../helpers/client/mindmapFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const marked = { workspace: { marked: "p1" } };
const maps = [
	{ uid: "f1", project_uid: "p1", name: "Ideen" },
	{ uid: "f2", project_uid: "p1", name: "Roadmap" },
	{ uid: "f3", project_uid: "p0", name: "Fremd" },
];

async function renderList(options: Parameters<typeof fakeMindmapBackend>[0] = {}) {
	const backend = fakeMindmapBackend({
		projects,
		documents: marked,
		maps,
		nodes: [node("a"), node("a1", "a"), node("x", null, 0, { tree_uid: "f1" })],
		...options,
	});
	await renderWorkspace(<MapList />, { backend });
	if (options.documents?.mindmap === undefined || (options.documents.mindmap as { view?: string }).view !== "all") await screen.findByTestId(ids.mapList);
	return backend;
}
const entries = () => [...document.querySelectorAll("[data-testid^='mindmap.map-entry.']")].map((entry) => entry.textContent);

describe("MapList: the maps of the shown project in the sidebar", () => {
	it("lists the project tree first, then the free maps of this project, each with its node count", async () => {
		await renderList();

		await screen.findByTestId(ids.mapEntry("f1"));
		expect(screen.getByTestId(ids.mapList).textContent).toContain("Maps in Viewer");
		expect(entries()).toEqual(["Viewer (Projektbaum)2", "Ideen1", "Roadmap0"]);
		expect(screen.getByTestId(ids.mapCount("t1")).textContent).toBe("2");
	});

	it("shows the project tree even before the project has a node", async () => {
		await renderList({ nodes: [], maps: [] });

		await screen.findByTestId(ids.mapEntry("p1"));
		expect(entries()).toEqual(["Viewer (Projektbaum)0"]);
	});

	it("marks the project tree as the chosen map at the start", async () => {
		await renderList();

		await screen.findByTestId(ids.mapEntry("f1"));
		expect(screen.getByTestId(ids.mapEntry("t1")).className).toContain("Mui-selected");
	});

	it("chooses a free map by a click and keeps the choice per project in the UI state of the server", async () => {
		const backend = await renderList();
		fireEvent.click(await screen.findByTestId(ids.mapEntry("f2")));

		await waitFor(() => expect(screen.getByTestId(ids.mapEntry("f2")).className).toContain("Mui-selected"));
		await flushUiState(backend.store);
		expect((backend.documents.get("mindmap") as { maps?: Record<string, string> }).maps).toEqual({ p1: "f2" });

		fireEvent.click(screen.getByTestId(ids.mapEntry("t1")));
		await waitFor(() => expect(screen.getByTestId(ids.mapEntry("t1")).className).toContain("Mui-selected"));
	});

	it("shows a stored choice, and ignores one whose map is gone", async () => {
		await renderList({ documents: { ...marked, mindmap: { maps: { p1: "f2" } } } });
		await screen.findByTestId(ids.mapEntry("f2"));
		await waitFor(() => expect(screen.getByTestId(ids.mapEntry("f2")).className).toContain("Mui-selected"));
		cleanup();

		await renderList({ documents: { ...marked, mindmap: { maps: { p1: "weg" } } } });
		await screen.findByTestId(ids.mapEntry("f2"));
		expect(screen.getByTestId(ids.mapEntry("t1")).className).toContain("Mui-selected");
	});

	it("offers no menu for the project tree: it can be neither renamed nor deleted", async () => {
		await renderList();

		await screen.findByTestId(ids.mapEntry("f1"));
		expect(screen.queryByTestId(ids.mapMenuButton("t1"))).toBeNull();
		expect(screen.getByTestId(ids.mapMenuButton("f1"))).toBeTruthy();
	});

	it("is not shown in the overall view", async () => {
		const backend = await renderList({ documents: { ...marked, mindmap: { view: "all" } } });
		await waitFor(() => expect(backend.calls("GET", "ui-state").length).toBeGreaterThan(0));
		await new Promise((resolve) => setTimeout(resolve, 50));
		expect(screen.queryByTestId(ids.mapList)).toBeNull();
		expect(backend.calls("GET", "mindmap/maps")).toHaveLength(0);
	});
});

describe("MapList: creating a map", () => {
	it("creates a free map by its name, lists it and chooses it", async () => {
		const backend = await renderList();
		fireEvent.click(await screen.findByTestId(ids.mapNew));
		fireEvent.change(await screen.findByTestId(ids.mapNameInput), { target: { value: "  Neu  " } });
		fireEvent.click(screen.getByText("Speichern"));

		await screen.findByTestId(ids.mapEntry("map1"));
		expect(backend.calls("POST", "mindmap/maps")[0]!.body).toEqual({ project: "p1", name: "Neu" });
		expect(entries().at(-1)).toBe("Neu0");
		await waitFor(() => expect(screen.getByTestId(ids.mapEntry("map1")).className).toContain("Mui-selected"));
	});

	it("keeps the dialog open and shows the reason when the server refuses the name", async () => {
		await renderList();
		fireEvent.click(await screen.findByTestId(ids.mapNew));
		fireEvent.change(await screen.findByTestId(ids.mapNameInput), { target: { value: "ideen" } });
		fireEvent.click(screen.getByText("Speichern"));

		expect((await screen.findByTestId(ids.mapNameError)).textContent).toContain("schon eine Map");
		expect(screen.getByTestId(ids.mapNameInput)).toBeTruthy();
	});

	it("does not send an empty name", async () => {
		const backend = await renderList();
		fireEvent.click(await screen.findByTestId(ids.mapNew));
		fireEvent.change(await screen.findByTestId(ids.mapNameInput), { target: { value: "   " } });
		fireEvent.click(screen.getByText("Speichern"));

		expect((await screen.findByTestId(ids.mapNameError)).textContent).toContain("nicht leer");
		expect(backend.calls("POST", "mindmap/maps")).toHaveLength(0);
	});
});

describe("MapList: renaming and deleting", () => {
	it("renames a free map from its menu with the version it was read in", async () => {
		const backend = await renderList();
		fireEvent.click(await screen.findByTestId(ids.mapMenuButton("f1")));
		fireEvent.click(await screen.findByTestId(ids.mapRename("f1")));
		const input = await screen.findByTestId(ids.mapNameInput);
		expect((input as HTMLInputElement).value).toBe("Ideen");
		fireEvent.change(input, { target: { value: "Plan" } });
		fireEvent.click(screen.getByText("Speichern"));

		await waitFor(() => expect(entries()).toContain("Plan1"));
		expect(backend.calls("PUT", "mindmap/maps/f1")[0]!.body).toEqual({ version: 1, name: "Plan" });
	});

	it("opens the menu with a right click on the entry", async () => {
		await renderList();
		fireEvent.contextMenu(await screen.findByTestId(ids.mapEntry("f1")));

		expect(await screen.findByTestId(ids.mapDelete("f1"))).toBeTruthy();
	});

	it("asks before deleting, names how many nodes go with the map, and puts it into the trash", async () => {
		const backend = await renderList();
		fireEvent.click(await screen.findByTestId(ids.mapMenuButton("f1")));
		fireEvent.click(await screen.findByTestId(ids.mapDelete("f1")));

		const dialog = await screen.findByTestId(sharedTestIds.confirmDialog);
		expect(dialog.textContent).toContain("Ideen");
		expect(dialog.textContent).toContain("1 Knoten");
		expect(backend.calls("DELETE", "mindmap/maps")).toHaveLength(0);

		fireEvent.click(screen.getByTestId(sharedTestIds.confirmDialogConfirm));
		await waitFor(() => expect(screen.queryByTestId(ids.mapEntry("f1"))).toBeNull());
		expect(backend.calls("DELETE", "mindmap/maps/f1")).toHaveLength(1);
		expect(entries()).toEqual(["Viewer (Projektbaum)2", "Roadmap0"]);
	});

	it("deletes nothing when the question is cancelled", async () => {
		const backend = await renderList();
		fireEvent.click(await screen.findByTestId(ids.mapMenuButton("f1")));
		fireEvent.click(await screen.findByTestId(ids.mapDelete("f1")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogCancel));

		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.confirmDialog)).toBeNull());
		expect(backend.calls("DELETE", "mindmap/maps")).toHaveLength(0);
		expect(screen.getByTestId(ids.mapEntry("f1"))).toBeTruthy();
	});

	it("falls back to the project tree when the shown map is deleted", async () => {
		const backend = await renderList({ documents: { ...marked, mindmap: { maps: { p1: "f1" } } } });
		fireEvent.click(await screen.findByTestId(ids.mapMenuButton("f1")));
		fireEvent.click(await screen.findByTestId(ids.mapDelete("f1")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogConfirm));

		await waitFor(() => expect(screen.getByTestId(ids.mapEntry("t1")).className).toContain("Mui-selected"));
		await flushUiState(backend.store);
		expect((backend.documents.get("mindmap") as { maps?: Record<string, string> }).maps).toEqual({});
	});
});
