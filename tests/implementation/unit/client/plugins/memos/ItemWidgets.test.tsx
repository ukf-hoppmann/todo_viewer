import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ItemDetail } from "../../../../../../client/src/plugins/backlog/ItemDetail";
import { DemoteAction, ItemHints } from "../../../../../../client/src/plugins/memos/ItemWidgets";
import { memosTestIds as ids } from "../../../../../../client/src/plugins/memos/testIds";
import { detail } from "../../../../../helpers/client/backlogFixtures";
import { fakeMemosBackend } from "../../../../../helpers/client/fakeMemosBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const widgets = [
	{ ownerId: "memos", slot: "backlog.item-detail", name: "hints", component: ItemHints },
	{ ownerId: "memos", slot: "backlog.item-detail", name: "demote", component: DemoteAction },
];
const source = { uid: "n1", label: "MEMO-001", title: "Eine Memo", kind: "memo", deleted: false };
const dropped = { uid: "x1", kind: "memo_dropped", created_at: "2026-10-17T00:00:00Z", source, decisions: ["acknowledge"] };

afterEach(cleanup);

async function renderItem(item = detail("t1", { status: "Open", version: 7 }), options: Parameters<typeof fakeMemosBackend>[0] = {}) {
	const backend = fakeMemosBackend({ projects, details: { [item.uid]: item }, ...options });
	await renderWorkspace(<ItemDetail uid={item.uid} onSelect={() => {}} />, { backend, widgets });
	await screen.findByTestId("backlog.detail");
	return backend;
}

describe("the widgets of memos in the detail of an item", () => {
	it("offers the way back to a memo for an open item and does it with the version of the item", async () => {
		const backend = await renderItem();

		fireEvent.click(await screen.findByTestId(ids.demoteButton));

		await waitFor(() => expect(backend.calls("POST", "memos/items/t1/demote")).toHaveLength(1));
		expect(backend.calls("POST", "memos/items/t1/demote")[0]!.body).toEqual({ version: 7 });
		expect((await screen.findByTestId(ids.demoteDone)).textContent).toBe("Zurückgestuft zum Memo MEMO-009.");
	});

	it.each(["In progress", "Completed"])("offers nothing for an item with the status %s", async (status) => {
		await renderItem(detail("t1", { status }));

		await waitFor(() => expect(screen.getByTestId("backlog.detail")).toBeTruthy());
		expect(screen.queryByTestId(ids.demote)).toBeNull();
	});

	it("offers nothing for an item in the trash", async () => {
		await renderItem(detail("t1", { status: "Open", deleted: true }));

		await waitFor(() => expect(screen.getByTestId("backlog.detail")).toBeTruthy());
		expect(screen.queryByTestId(ids.demote)).toBeNull();
	});

	it("shows what the backlog refuses", async () => {
		await renderItem(detail("t1", { status: "Open" }), {
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/demote") ? Response.json({ code: "demote_has_children", message: "TASK hat Kinder", details: {} }, { status: 400 }) : undefined,
		});

		fireEvent.click(await screen.findByTestId(ids.demoteButton));

		expect(await screen.findByText("TASK hat Kinder")).toBeTruthy();
	});

	it("lists the hints of the item and acknowledges one", async () => {
		const backend = await renderItem(detail("t1"), { itemHints: { t1: [dropped] } });

		const shown = await screen.findByTestId(ids.itemHint("x1"));
		expect(shown.textContent).toContain("Das verweisende Memo MEMO-001 — Eine Memo wurde verworfen.");
		fireEvent.click(screen.getByTestId(ids.hintDecision("x1", "acknowledge")));

		await waitFor(() => expect(backend.calls("POST", "memos/hints/x1/decide")).toHaveLength(1));
		expect(backend.calls("POST", "memos/hints/x1/decide")[0]!.body).toEqual({ decision: "acknowledge" });
	});

	it("shows no hint section when there is none", async () => {
		await renderItem();

		await waitFor(() => expect(screen.getByTestId("backlog.detail")).toBeTruthy());
		expect(screen.queryByTestId(ids.itemHints)).toBeNull();
	});
});
