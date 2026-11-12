import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoDetail } from "../../../../../../client/src/plugins/memos/MemoDetail";
import { memosTestIds as ids } from "../../../../../../client/src/plugins/memos/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeMemosBackend } from "../../../../../helpers/client/fakeMemosBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { memoDetail } from "../../../../../helpers/client/memosFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const elements = [
	{ uid: "i1", project_uid: "p1", kind: "task", label: "TASK-001", title: "Ein Task", deleted: false, version: 1 },
	{ uid: "o1", project_uid: "p1", kind: "memo", label: "MEMO-002", title: "Andere Memo", deleted: false, version: 1 },
];
const target = { uid: "i1", label: "TASK-001", title: "Ein Task", kind: "task", deleted: false };
const hint = (uid: string, kind: string, decisions: string[]) => ({ uid, kind, created_at: "2026-10-17T00:00:00Z", source: target, decisions });
const section = (id: string) => screen.getByTestId(sharedTestIds.detailSection(id));

afterEach(cleanup);

async function renderDetail(detail = memoDetail("n1"), options: Parameters<typeof fakeMemosBackend>[0] = {}) {
	const backend = fakeMemosBackend({ projects, memoDetails: { [detail.uid]: detail }, elements, ...options });
	await renderWorkspace(<MemoDetail uid={detail.uid} />, { backend });
	await screen.findByTestId(ids.detail);
	return backend;
}

describe("MemoDetail: triggers", () => {
	const triggers = [
		{ uid: "t1", kind: "event", status: "Completed", target, fired_at: null, already_met: false, arrived: false },
		{ uid: "t2", kind: "event", status: "In progress", target, fired_at: "2026-10-17T00:00:00Z", already_met: true, arrived: true },
		{ uid: "t3", kind: "topic_date", status: null, target: null, fired_at: null, already_met: false, arrived: true },
	];

	it("lists the triggers and marks those that arrived", async () => {
		await renderDetail(memoDetail("n1", { triggers, status: "due", reason: "trigger" }));

		expect(screen.getByTestId(ids.trigger("t1")).textContent).toContain("TASK-001 — Ein Task erreicht „Abgeschlossen“");
		expect(screen.getByTestId(ids.trigger("t1")).getAttribute("data-arrived")).toBe("false");
		expect(screen.getByTestId(ids.trigger("t2")).textContent).toContain("schon erreicht");
		expect(screen.getByTestId(ids.trigger("t3")).textContent).toContain("Der Termin des Topics ist erreicht");
		expect(screen.getByTestId(ids.detailReason).textContent).toBe("ein Auslöser ist eingetreten");
	});

	it("says there are none", async () => {
		await renderDetail();
		fireEvent.click(screen.getByTestId(sharedTestIds.detailSectionToggle("triggers")));

		expect(within(section("triggers")).getByText(/Keine Auslöser/)).toBeTruthy();
	});

	it("removes a trigger", async () => {
		const backend = await renderDetail(memoDetail("n1", { triggers }));

		fireEvent.click(screen.getByTestId(ids.triggerRemove("t1")));

		await waitFor(() => expect(backend.calls("DELETE", "memos/triggers/t1")).toHaveLength(1));
	});

	it("adds an event trigger for an item found by search", async () => {
		const backend = await renderDetail(memoDetail("n1"));
		fireEvent.click(screen.getByTestId(sharedTestIds.detailSectionToggle("triggers")));

		fireEvent.click(await screen.findByTestId(ids.addTrigger));
		const dialog = await screen.findByTestId(ids.triggerDialog);
		const picker = within(dialog).getByRole("combobox", { name: "Item" });
		fireEvent.change(picker, { target: { value: "task" } });
		fireEvent.click(await screen.findByRole("option", { name: /TASK-001/ }));
		fireEvent.click(screen.getByTestId(ids.triggerSave));

		await waitFor(() => expect(backend.calls("POST", "memos/memos/n1/triggers")).toHaveLength(1));
		expect(backend.calls("POST", "memos/memos/n1/triggers")[0]!.body).toEqual({ kind: "event", target: "i1", status: "Completed" });
	});

	it("needs a topic for the date trigger and then sends it without a target", async () => {
		const backend = await renderDetail(memoDetail("n1", { path: [{ uid: "t", label: "TOPIC-001", name: "Thema" }] }));
		fireEvent.click(screen.getByTestId(sharedTestIds.detailSectionToggle("triggers")));

		fireEvent.click(await screen.findByTestId(ids.addTrigger));
		await screen.findByTestId(ids.triggerDialog);
		fireEvent.mouseDown(within(screen.getByTestId(ids.triggerDialog)).getAllByRole("combobox")[0]!);
		fireEvent.click(await screen.findByRole("option", { name: /Termin des Topics/ }));
		fireEvent.click(screen.getByTestId(ids.triggerSave));

		await waitFor(() => expect(backend.calls("POST", "memos/memos/n1/triggers")).toHaveLength(1));
		expect(backend.calls("POST", "memos/memos/n1/triggers")[0]!.body).toEqual({ kind: "topic_date" });
	});

	it("shows the message of the server when a trigger is refused", async () => {
		await renderDetail(memoDetail("n1", { path: [{ uid: "t", label: "T", name: "Thema" }] }), {
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/triggers") ? Response.json({ code: "trigger_needs_topic_date", message: "Das Topic braucht einen Termin", details: {} }, { status: 400 }) : undefined,
		});
		fireEvent.click(screen.getByTestId(sharedTestIds.detailSectionToggle("triggers")));
		fireEvent.click(await screen.findByTestId(ids.addTrigger));
		await screen.findByTestId(ids.triggerDialog);
		fireEvent.mouseDown(within(screen.getByTestId(ids.triggerDialog)).getAllByRole("combobox")[0]!);
		fireEvent.click(await screen.findByRole("option", { name: /Termin des Topics/ }));
		fireEvent.click(screen.getByTestId(ids.triggerSave));

		expect(await screen.findByText("Das Topic braucht einen Termin")).toBeTruthy();
	});

	it("cannot add or remove triggers of a memo in the archive", async () => {
		await renderDetail(memoDetail("n1", { triggers, archived: true, status: "done", stored_status: "done" }));

		expect(screen.queryByTestId(ids.addTrigger)).toBeNull();
		expect(screen.queryByTestId(ids.triggerRemove("t1"))).toBeNull();
	});
});

describe("MemoDetail: hints", () => {
	const hints = [hint("x1", "item_completed", ["keep", "detach", "drop", "promote"])];

	it("shows what happened and one button per decision", async () => {
		await renderDetail(memoDetail("n1", { hints, status: "due", reason: "hint" }));

		const shown = screen.getByTestId(ids.hint("x1"));
		expect(shown.textContent).toContain("Das verknüpfte Item TASK-001 — Ein Task ist abgeschlossen.");
		for (const decision of ["keep", "detach", "drop", "promote"]) expect(within(shown).getByTestId(ids.hintDecision("x1", decision))).toBeTruthy();
		expect(screen.getByTestId(ids.detailReason).textContent).toBe("ein Hinweis wartet auf eine Entscheidung");
	});

	it("says there are none", async () => {
		await renderDetail();
		fireEvent.click(screen.getByTestId(sharedTestIds.detailSectionToggle("hints")));

		expect(await screen.findByText("Keine offenen Hinweise.")).toBeTruthy();
	});

	it.each(["keep", "detach", "drop"])("sends the decision %s with the version of the memo", async (decision) => {
		const backend = await renderDetail(memoDetail("n1", { hints, version: 4 }));

		fireEvent.click(screen.getByTestId(ids.hintDecision("x1", decision)));

		await waitFor(() => expect(backend.calls("POST", "memos/hints/x1/decide")).toHaveLength(1));
		expect(backend.calls("POST", "memos/hints/x1/decide")[0]!.body).toEqual({ decision, version: 4 });
	});

	it("promotes through the dialog and decides the hint with the fields", async () => {
		const backend = await renderDetail(memoDetail("n1", { hints, version: 4 }));

		fireEvent.click(screen.getByTestId(ids.hintDecision("x1", "promote")));
		await screen.findByTestId(ids.promoteDialog);
		fireEvent.change(screen.getByTestId(ids.promoteField("area")), { target: { value: "Server" } });
		fireEvent.change(screen.getByTestId(ids.promoteField("goal")), { target: { value: "Ziel" } });
		fireEvent.change(screen.getByTestId(ids.promoteField("completion_criteria")), { target: { value: "Kriterien" } });
		fireEvent.click(screen.getByTestId(ids.promoteConfirm));

		await waitFor(() => expect(backend.calls("POST", "memos/hints/x1/decide")).toHaveLength(1));
		expect(backend.calls("POST", "memos/hints/x1/decide")[0]!.body).toEqual({
			decision: "promote",
			version: 4,
			type: "Task",
			fields: { area: "Server", goal: "Ziel", completion_criteria: "Kriterien" },
		});
	});

	it("shows the message of the server when a decision fails", async () => {
		await renderDetail(memoDetail("n1", { hints }), {
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/decide") ? Response.json({ code: "memo_archived", message: "N1 liegt im Archiv", details: {} }, { status: 400 }) : undefined,
		});

		fireEvent.click(screen.getByTestId(ids.hintDecision("x1", "keep")));

		expect(await screen.findByText("N1 liegt im Archiv")).toBeTruthy();
	});
});

describe("MemoDetail: promote", () => {
	const open = async (options: Parameters<typeof fakeMemosBackend>[0] = {}) => {
		const backend = await renderDetail(memoDetail("n1", { summary: "Meine Idee", version: 3 }), options);
		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("promote")));
		await screen.findByTestId(ids.promoteDialog);
		return backend;
	};
	const fill = () => {
		fireEvent.change(screen.getByTestId(ids.promoteField("area")), { target: { value: "Server" } });
		fireEvent.change(screen.getByTestId(ids.promoteField("goal")), { target: { value: "Ziel" } });
		fireEvent.change(screen.getByTestId(ids.promoteField("completion_criteria")), { target: { value: "Kriterien" } });
	};

	it("shows the summary as the placeholder of the title and sends the fields with the type", async () => {
		const backend = await open();
		expect((screen.getByTestId(ids.promoteField("title")) as HTMLInputElement).placeholder).toBe("Meine Idee");

		fireEvent.mouseDown(within(screen.getByTestId(ids.promoteDialog)).getAllByRole("combobox")[0]!);
		fireEvent.click(await screen.findByRole("option", { name: "Story" }));
		fireEvent.change(screen.getByTestId(ids.promoteField("title")), { target: { value: "Besserer Titel" } });
		fill();
		fireEvent.click(screen.getByTestId(ids.promoteConfirm));

		await waitFor(() => expect(backend.calls("POST", "memos/memos/n1/promote")).toHaveLength(1));
		expect(backend.calls("POST", "memos/memos/n1/promote")[0]!.body).toEqual({
			version: 3,
			type: "Story",
			fields: { area: "Server", goal: "Ziel", completion_criteria: "Kriterien", title: "Besserer Titel" },
		});
		await waitFor(() => expect(screen.queryByTestId(ids.promoteDialog)).toBeNull());
	});

	it("shows what the backlog refuses and keeps the dialog", async () => {
		await open({
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/promote") ? Response.json({ code: "value_required", message: "Pflichtfeld fehlt", details: {} }, { status: 422 }) : undefined,
		});
		fill();

		fireEvent.click(screen.getByTestId(ids.promoteConfirm));

		await waitFor(() => expect(screen.getByTestId(ids.promoteError).textContent).toBe("Pflichtfeld fehlt"));
		expect(screen.getByTestId(ids.promoteDialog)).toBeTruthy();
	});
});
