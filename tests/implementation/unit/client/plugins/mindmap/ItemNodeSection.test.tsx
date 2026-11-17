import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ItemDetail } from "../../../../../../client/src/plugins/backlog/ItemDetail";
import { ItemNodeSection } from "../../../../../../client/src/plugins/mindmap/ItemNodeSection";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { detail } from "../../../../../helpers/client/backlogFixtures";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { itemRef, node, nodeItem } from "../../../../../helpers/client/mindmapFixtures";
import { locationTestId, renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const widgets = [{ ownerId: "mindmap", slot: "backlog.item-detail", name: "node", component: ItemNodeSection }];
const nodes = [node("a"), node("b", null, 1), node("a1", "a")];

async function renderItem(options: Parameters<typeof fakeMindmapBackend>[0] = {}, item = detail("t1", { status: "Open", version: 3 })) {
	const backend = fakeMindmapBackend({ projects, nodes, details: { [item.uid]: item }, ...options });
	await renderWorkspace(<ItemDetail uid={item.uid} onSelect={() => {}} />, { backend, widgets });
	await screen.findByTestId("backlog.detail");
	return backend;
}
const select = () => screen.getByTestId(ids.itemNodeSelect) as HTMLInputElement;
const choose = async (title: string) => {
	fireEvent.mouseDown(screen.getByRole("combobox", { name: "Knoten" }));
	fireEvent.click(await screen.findByRole("option", { name: title }));
};

describe("the node of an item in its detail", () => {
	it("says that an item without a node is not assigned", async () => {
		await renderItem({ unassigned: [itemRef("t1")] });

		expect((await screen.findByTestId(ids.itemNode)).textContent).toContain("Nicht zugeordnet");
		expect(screen.queryByTestId(ids.itemNodeRelease)).toBeNull();
	});

	it("shows the own node of an item and offers to release it", async () => {
		const backend = await renderItem({ items: { a: [nodeItem("t1", true)] } });

		await waitFor(() => expect(select().value).toBe("a"));
		fireEvent.click(screen.getByTestId(ids.itemNodeRelease));

		await waitFor(() => expect(select().value).toBe(""));
		expect(backend.calls("DELETE", "mindmap/items/t1/node")).toHaveLength(1);
	});

	it("shows the node an item inherits, marked as inherited, without an action to release it", async () => {
		await renderItem({ items: { a1: [nodeItem("t1", false)] } });

		await waitFor(() => expect(select().value).toBe("a1"));
		expect(screen.getByTestId(ids.itemNode).textContent).toContain("geerbt");
		expect(screen.queryByTestId(ids.itemNodeRelease)).toBeNull();
	});

	it("assigns the item to the chosen node; the nodes of the project are offered by their depth", async () => {
		const backend = await renderItem({ unassigned: [itemRef("t1")] });
		await screen.findByTestId(ids.itemNode);

		fireEvent.mouseDown(screen.getByRole("combobox", { name: "Knoten" }));
		const options = await screen.findAllByRole("option");
		expect(options.map((option) => option.textContent?.trim())).toEqual(["Thema a", "Thema a1", "Thema b"]);
		fireEvent.click(screen.getByRole("option", { name: "Thema b" }));

		await waitFor(() => expect(select().value).toBe("b"));
		expect(backend.calls("POST", "mindmap/nodes/b/items")[0]!.body).toEqual({ item: "t1", replace: true });
	});

	it("moves an item that hangs on another node to the chosen one", async () => {
		const backend = await renderItem({ items: { a: [nodeItem("t1", true)] } });
		await waitFor(() => expect(select().value).toBe("a"));

		await choose("Thema b");

		await waitFor(() => expect(select().value).toBe("b"));
		expect(backend.calls("POST", "mindmap/nodes/b/items")[0]!.body).toEqual({ item: "t1", replace: true });
	});

	it("shows the message of the server when the assignment fails", async () => {
		await renderItem({
			unassigned: [itemRef("t1")],
			respond: ({ method, path }) => (method === "POST" && path === "mindmap/nodes/b/items" ? Response.json({ code: "mindmap_other_project", message: "Item und Knoten stehen in verschiedenen Projekten", details: {} }, { status: 400 }) : undefined),
		});
		await screen.findByTestId(ids.itemNode);

		await choose("Thema b");

		expect((await screen.findByTestId(ids.itemNodeError)).textContent).toContain("verschiedenen Projekten");
	});

	it("offers nothing for an item in the trash", async () => {
		await renderItem({}, detail("t1", { deleted: true }));

		expect(screen.queryByTestId(ids.itemNode)).toBeNull();
	});
});

describe("the actions on an item: go there, create, anchor", () => {
	const location = () => screen.getByTestId(locationTestId).textContent;

	it("goes to the effective node of the item, also an inherited one", async () => {
		await renderItem({ items: { a1: [nodeItem("t1", false)] } });
		await waitFor(() => expect(select().value).toBe("a1"));

		fireEvent.click(screen.getByTestId(ids.itemNodeGoto));

		await waitFor(() => expect(location()).toBe("/mindmap/main?focus=a1"));
	});

	it("goes to the whole map when the item has no node", async () => {
		await renderItem({ unassigned: [itemRef("t1")] });
		await screen.findByTestId(ids.itemNode);

		fireEvent.click(screen.getByTestId(ids.itemNodeGoto));

		await waitFor(() => expect(location()).toBe("/mindmap/main"));
	});

	it("shows a hidden project of the item and marks it before it goes there", async () => {
		const backend = await renderItem({ items: { a: [nodeItem("t1", true)] }, documents: { workspace: { hidden: ["p1"], marked: "p0" } } });
		await waitFor(() => expect(select().value).toBe("a"));

		fireEvent.click(screen.getByTestId(ids.itemNodeGoto));

		await waitFor(() => expect(location()).toBe("/mindmap/main?focus=a"));
		const { flushUiState } = await import("../../../../../../client/src/core/ui-state/uiState");
		await waitFor(async () => {
			await flushUiState(backend.store);
			expect(backend.documents.get("workspace")).toMatchObject({ hidden: [], marked: "p1" });
		});
	});

	it("leaves the project selection alone when the project is visible and marked", async () => {
		const backend = await renderItem({ items: { a: [nodeItem("t1", true)] }, documents: { workspace: { hidden: ["p0"], marked: "p1" } } });
		await waitFor(() => expect(select().value).toBe("a"));

		fireEvent.click(screen.getByTestId(ids.itemNodeGoto));

		await waitFor(() => expect(location()).toBe("/mindmap/main?focus=a"));
		const { flushUiState } = await import("../../../../../../client/src/core/ui-state/uiState");
		await flushUiState(backend.store);
		expect(backend.documents.get("workspace")).toEqual({ hidden: ["p0"], marked: "p1" });
	});

	it("creates a node with the title of the item below its node and hangs the item on it", async () => {
		const backend = await renderItem({ items: { a: [nodeItem("t1", true)] } });
		await waitFor(() => expect(select().value).toBe("a"));

		fireEvent.click(screen.getByTestId(ids.itemNodeCreate));

		await waitFor(() => expect(select().value).toBe("new1"));
		expect(backend.calls("POST", "mindmap/nodes")[0]!.body).toEqual({ project: "p1", title: "Titel t1", parent: "a" });
		expect(backend.calls("POST", "mindmap/nodes/new1/items")[0]!.body).toEqual({ item: "t1", replace: true });
		expect(screen.queryByTestId(ids.itemNodeError)).toBeNull();
	});

	it("creates the node under the root when the item has none", async () => {
		const backend = await renderItem({ unassigned: [itemRef("t1")] });
		await screen.findByTestId(ids.itemNode);

		fireEvent.click(screen.getByTestId(ids.itemNodeCreate));

		await waitFor(() => expect(select().value).toBe("new1"));
		expect(backend.calls("POST", "mindmap/nodes")[0]!.body).toEqual({ project: "p1", title: "Titel t1" });
	});

	it("shows the message when creating the node fails and assigns nothing", async () => {
		const backend = await renderItem({
			unassigned: [itemRef("t1")],
			respond: ({ method, path }) => (method === "POST" && path === "mindmap/nodes" ? Response.json({ code: "mindmap_failed", message: "Der Knoten konnte nicht angelegt werden", details: {} }, { status: 400 }) : undefined),
		});
		await screen.findByTestId(ids.itemNode);

		fireEvent.click(screen.getByTestId(ids.itemNodeCreate));

		expect((await screen.findByTestId(ids.itemNodeError)).textContent).toContain("nicht angelegt");
		expect(backend.calls("POST", "mindmap/nodes/new1/items")).toHaveLength(0);
	});

	it("keeps the new node and shows the message when hanging the item on it fails", async () => {
		const backend = await renderItem({
			unassigned: [itemRef("t1")],
			respond: ({ method, path }) => (method === "POST" && path === "mindmap/nodes/new1/items" ? Response.json({ code: "mindmap_other_project", message: "Item und Knoten stehen in verschiedenen Projekten", details: {} }, { status: 400 }) : undefined),
		});
		await screen.findByTestId(ids.itemNode);

		fireEvent.click(screen.getByTestId(ids.itemNodeCreate));

		expect((await screen.findByTestId(ids.itemNodeError)).textContent).toContain("verschiedenen Projekten");
		expect(backend.calls("POST", "mindmap/nodes").filter((call) => call.path === "mindmap/nodes")).toHaveLength(1);
		expect(select().value).toBe("");
	});

	it("offers the anchor only for an item on a node of its own, and opens the map there", async () => {
		await renderItem({ items: { a: [nodeItem("t1", true)] } });

		fireEvent.click(await screen.findByTestId(ids.itemNodeAnchor));

		await waitFor(() => expect(location()).toBe("/mindmap/main?focus=a"));
	});

	it("shows a hidden project of the item for the anchor as well", async () => {
		const backend = await renderItem({ items: { a: [nodeItem("t1", true)] }, documents: { workspace: { hidden: ["p1"] } } });

		fireEvent.click(await screen.findByTestId(ids.itemNodeAnchor));

		await waitFor(() => expect(location()).toBe("/mindmap/main?focus=a"));
		const { flushUiState } = await import("../../../../../../client/src/core/ui-state/uiState");
		await waitFor(async () => {
			await flushUiState(backend.store);
			expect(backend.documents.get("workspace")).toMatchObject({ hidden: [], marked: "p1" });
		});
	});

	it("offers no anchor for an item without a node or one that only inherits its node", async () => {
		await renderItem({ items: { a1: [nodeItem("t1", false)] } });
		await waitFor(() => expect(select().value).toBe("a1"));
		expect(screen.queryByTestId(ids.itemNodeAnchor)).toBeNull();
		expect(screen.getByTestId(ids.itemNodeGoto)).toBeTruthy();
		expect(screen.getByTestId(ids.itemNodeCreate)).toBeTruthy();

		cleanup();
		await renderItem({ unassigned: [itemRef("t1")] });
		await screen.findByTestId(ids.itemNode);
		expect(screen.queryByTestId(ids.itemNodeAnchor)).toBeNull();
	});

	it("offers none of the actions for an item in the trash", async () => {
		await renderItem({}, detail("t1", { deleted: true }));

		expect(screen.queryByTestId(ids.itemNodeGoto)).toBeNull();
		expect(screen.queryByTestId(ids.itemNodeCreate)).toBeNull();
		expect(screen.queryByTestId(ids.itemNodeAnchor)).toBeNull();
	});
});
