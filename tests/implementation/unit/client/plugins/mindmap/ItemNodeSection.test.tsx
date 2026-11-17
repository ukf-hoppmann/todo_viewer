import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ItemDetail } from "../../../../../../client/src/plugins/backlog/ItemDetail";
import { ItemNodeSection } from "../../../../../../client/src/plugins/mindmap/ItemNodeSection";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { detail } from "../../../../../helpers/client/backlogFixtures";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { itemRef, node, nodeItem } from "../../../../../helpers/client/mindmapFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

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
