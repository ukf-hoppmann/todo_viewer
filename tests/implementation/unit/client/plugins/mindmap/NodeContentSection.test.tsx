import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { NodeContentSection } from "../../../../../../client/src/plugins/mindmap/NodeContentSection";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import type { ElementOut } from "../../../../../../client/src/plugins/workspace/api";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { itemRef, node, nodeItem } from "../../../../../helpers/client/mindmapFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const element = (uid: string, kind: string, label: string, title: string, projectUid = "p1"): ElementOut => ({ uid, project_uid: projectUid, kind, label, title, version: 1, deleted: false });
const elements = [
	element("t1", "task", "TASK-001", "Erste Aufgabe"),
	element("t2", "story", "STORY-002", "Zweite Geschichte"),
	element("t9", "task", "TASK-009", "Anderes Projekt", "p0"),
	element("m1", "memo", "MEMO-001", "Eine Notiz"),
	element("m2", "memo", "MEMO-002", "Noch eine Notiz"),
];

async function renderSection(options: Parameters<typeof fakeMindmapBackend>[0] = {}) {
	const backend = fakeMindmapBackend({
		projects: [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)],
		nodes: [node("a"), node("b", null, 1)],
		elements,
		...options,
	});
	await renderWorkspace(<NodeContentSection node={node("a")} />, { backend });
	return backend;
}
const pick = async (name: string, text: string, option: string) => {
	fireEvent.change(screen.getByRole("combobox", { name }), { target: { value: text } });
	fireEvent.click(await screen.findByRole("option", { name: option }));
};

describe("NodeContentSection: what the node holds", () => {
	it("lists the items of the node and the memos linked to it; only own items can be unassigned", async () => {
		await renderSection({
			items: { a: [nodeItem("t1", true), nodeItem("t2", false, { status: "In progress" })] },
			memos: { a: [{ uid: "m1", label: "MEMO-001", title: "Eine Notiz" }] },
		});

		const own = await screen.findByTestId(ids.contentItem("t1"));
		expect(own.textContent).toContain("TASK-t1");
		expect(within(own).getByTestId(ids.unassign("t1"))).toBeTruthy();
		const inherited = screen.getByTestId(ids.contentItem("t2"));
		expect(inherited.textContent).toContain("In progress");
		expect(inherited.textContent).toContain("geerbt");
		expect(within(inherited).queryByTestId(ids.unassign("t2"))).toBeNull();
		expect(screen.getByTestId(ids.contentMemo("m1")).textContent).toContain("MEMO-001");
	});

	it("says so when the node holds nothing", async () => {
		await renderSection();

		expect((await screen.findByTestId(ids.content)).textContent).toContain("Keine Items");
		expect(screen.getByTestId(ids.content).textContent).toContain("Keine Memos");
	});

	it("asks for the content by the status filter of the backlog", async () => {
		const backend = await renderSection({ items: { a: [nodeItem("t1")] } });
		await screen.findByTestId(ids.contentItem("t1"));

		expect(backend.calls("GET", "mindmap/nodes/a/content")[0]!.query.get("statuses")).toBe("Open,In progress,Awaiting confirmation");
	});
});

describe("NodeContentSection: the switch for the sub-nodes", () => {
	it("asks for the items of the sub-nodes only when the switch is on, and keeps it", async () => {
		const backend = await renderSection({ items: { a: [nodeItem("t1")] } });
		await screen.findByTestId(ids.contentItem("t1"));
		expect(backend.calls("GET", "mindmap/nodes/a/content")[0]!.query.has("include_subnodes")).toBe(false);
		expect((screen.getByTestId(ids.includeSubnodes) as HTMLInputElement).checked).toBe(false);

		fireEvent.click(screen.getByTestId(ids.includeSubnodes));

		await waitFor(() => expect(backend.calls("GET", "mindmap/nodes/a/content").at(-1)!.query.get("include_subnodes")).toBe("true"));
		await waitFor(() => expect((backend.documents.get("mindmap") as { includeSubnodes?: boolean }).includeSubnodes).toBe(true));
	});
});

describe("NodeContentSection: assigning and releasing items", () => {
	it("assigns a found item of the project and lists it", async () => {
		const backend = await renderSection({ unassigned: [itemRef("t1", { label: "TASK-001", title: "Erste Aufgabe" })] });
		await screen.findByTestId(ids.content);

		await pick("Item zuordnen", "erste", "TASK-001 — Erste Aufgabe");
		fireEvent.click(screen.getByTestId(ids.assignAdd));

		await screen.findByTestId(ids.contentItem("t1"));
		expect(backend.calls("POST", "mindmap/nodes/a/items")[0]!.body).toEqual({ item: "t1" });
	});

	it("offers only items of the project of the node, no memos", async () => {
		await renderSection();
		await screen.findByTestId(ids.content);

		fireEvent.change(screen.getByRole("combobox", { name: "Item zuordnen" }), { target: { value: "-0" } });

		await screen.findByRole("option", { name: "STORY-002 — Zweite Geschichte" });
		expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual(["TASK-001 — Erste Aufgabe", "STORY-002 — Zweite Geschichte"]);
	});

	it("asks before it takes an item from another node, and then replaces", async () => {
		const backend = await renderSection({ items: { b: [nodeItem("t1", true, { label: "TASK-001", title: "Erste Aufgabe" })] } });
		await screen.findByTestId(ids.content);

		await pick("Item zuordnen", "erste", "TASK-001 — Erste Aufgabe");
		fireEvent.click(screen.getByTestId(ids.assignAdd));
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogConfirm));

		await screen.findByTestId(ids.contentItem("t1"));
		expect(backend.calls("POST", "mindmap/nodes/a/items").map((call) => call.body)).toEqual([{ item: "t1" }, { item: "t1", replace: true }]);
	});

	it("leaves the item where it is when the replacement is declined", async () => {
		const backend = await renderSection({ items: { b: [nodeItem("t1", true, { label: "TASK-001", title: "Erste Aufgabe" })] } });
		await screen.findByTestId(ids.content);

		await pick("Item zuordnen", "erste", "TASK-001 — Erste Aufgabe");
		fireEvent.click(screen.getByTestId(ids.assignAdd));
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogCancel));

		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.confirmDialog)).toBeNull());
		expect(backend.calls("POST", "mindmap/nodes/a/items")).toHaveLength(1);
		expect(screen.queryByTestId(ids.contentItem("t1"))).toBeNull();
	});

	it("releases an own item", async () => {
		const backend = await renderSection({ items: { a: [nodeItem("t1", true)] } });

		fireEvent.click(await screen.findByTestId(ids.unassign("t1")));

		await waitFor(() => expect(screen.queryByTestId(ids.contentItem("t1"))).toBeNull());
		expect(backend.calls("DELETE", "mindmap/items/t1/node")).toHaveLength(1);
	});

	it("shows the message of the server when the assignment fails otherwise", async () => {
		await renderSection({
			respond: ({ method, path }) => (method === "POST" && path === "mindmap/nodes/a/items" ? Response.json({ code: "mindmap_item_deleted", message: "Das Item liegt im Papierkorb", details: {} }, { status: 400 }) : undefined),
		});
		await screen.findByTestId(ids.content);

		await pick("Item zuordnen", "erste", "TASK-001 — Erste Aufgabe");
		fireEvent.click(screen.getByTestId(ids.assignAdd));

		expect((await screen.findByTestId(ids.contentError)).textContent).toContain("Papierkorb");
	});
});

describe("NodeContentSection: linking memos", () => {
	it("links a memo and lists it", async () => {
		const backend = await renderSection();
		await screen.findByTestId(ids.content);

		await pick("Memo verlinken", "noch", "MEMO-002 — Noch eine Notiz");
		fireEvent.click(screen.getByTestId(ids.memoAdd));

		await screen.findByTestId(ids.contentMemo("m2"));
		expect(backend.calls("POST", "mindmap/nodes/a/memos")[0]!.body).toEqual({ memo: "m2" });
	});

	it("unlinks a memo", async () => {
		const backend = await renderSection({ memos: { a: [{ uid: "m1", label: "MEMO-001", title: "Eine Notiz" }] } });

		fireEvent.click(await screen.findByTestId(ids.unlink("m1")));

		await waitFor(() => expect(screen.queryByTestId(ids.contentMemo("m1"))).toBeNull());
		expect(backend.calls("DELETE", "mindmap/nodes/a/memos/m1")).toHaveLength(1);
	});
});
