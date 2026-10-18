import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { StatusFilter } from "../../../../../../client/src/plugins/notes/Filters";
import NotesPage from "../../../../../../client/src/plugins/notes/pages/NotesPage";
import { notesTestIds as ids } from "../../../../../../client/src/plugins/notes/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeNotesBackend } from "../../../../../helpers/client/fakeNotesBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { note, noteDetail, topic } from "../../../../../helpers/client/notesFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const topics = [
	topic("t1", { open_notes: 2, due_notes: 1 }),
	topic("t2", { parent_uid: "t1", open_notes: 1 }),
	topic("t3"),
	topic("old", { archived: true }),
];
const notes = [
	note("n1", { topic_uid: "t1" }),
	note("n2", { topic_uid: "t1", status: "due" }),
	note("n3", { topic_uid: "t2", status: "snoozed" }),
	note("n4", { status: "done", archived: true, topic_uid: "t3" }),
	note("n5"),
	note("n6", { topic_uid: "old" }),
	note("other", { project_uid: "p0", summary: "Allgemeines" }),
];

const node = (uid: string) => screen.getByTestId(sharedTestIds.treeNode(uid));
const dragData = { dataTransfer: { setData: () => {}, getData: () => "", effectAllowed: "" } };

afterEach(cleanup);

async function renderPage(options: Parameters<typeof fakeNotesBackend>[0] = {}) {
	const backend = fakeNotesBackend({ projects, topics, notes, noteDetails: { n1: noteDetail("n1") }, ...options });
	await renderWorkspace(
		<>
			<StatusFilter />
			<NotesPage />
		</>,
		{ backend },
	);
	return backend;
}

describe("NotesPage: tree", () => {
	it("shows a tree per project with topics, their note counts and the notes", async () => {
		await renderPage();

		await screen.findByTestId(sharedTestIds.treeNode("t1"));
		const viewer = screen.getByTestId(ids.project("p1"));
		expect(within(viewer).getByTestId(sharedTestIds.treeNode("t1")).textContent).toContain("Topic t1");
		// n1, n2 and n3 are open and below t1 (n3 in the sub-topic); n4 is done and hidden by the default filter
		expect(screen.getByTestId(sharedTestIds.treeCount("t1")).textContent).toBe("3");
		expect(screen.getByTestId(sharedTestIds.treeCount("t2")).textContent).toBe("1");
		expect(screen.getByTestId(sharedTestIds.treeTag("n1")).textContent).toBe("Note");
		expect(screen.getByTestId(sharedTestIds.treeTag("t1")).textContent).toBe("Topic");
		expect(screen.getByTestId(ids.project("p0"))).toBeTruthy();
		expect(screen.getByTestId(sharedTestIds.treeNode("n5"))).toBeTruthy(); // without topic: directly at the project
	});

	it("shows due notes before the others of the same topic", async () => {
		await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("n1"));

		const order = screen.getAllByRole("treeitem").map((row) => row.getAttribute("data-testid"));
		expect(order.indexOf(sharedTestIds.treeNode("n2"))).toBeLessThan(order.indexOf(sharedTestIds.treeNode("n1")));
	});

	it("hides finished notes and archived topics by default and shows them when asked", async () => {
		await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("n1"));
		expect(screen.queryByTestId(sharedTestIds.treeNode("n4"))).toBeNull();
		expect(screen.queryByTestId(sharedTestIds.treeNode("old"))).toBeNull();

		fireEvent.click(screen.getByTestId(sharedTestIds.filterOption("done")));
		await waitFor(() => expect(screen.getByTestId(sharedTestIds.treeNode("n4"))).toBeTruthy());
		fireEvent.click(screen.getByTestId(sharedTestIds.filterOption("archived-topics")));
		await waitFor(() => expect(screen.getByTestId(sharedTestIds.treeNode("old"))).toBeTruthy());
		expect(node("old").getAttribute("data-dashed")).toBe("true");
	});

	it("marks the areas of the topics, and drops the marking with the checkbox", async () => {
		await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("t1"));
		expect([node("t1"), node("t2"), node("n1"), node("n5")].map((row) => row.getAttribute("data-area"))).toEqual(["1", "2", "1", null]);

		fireEvent.click(screen.getByTestId(ids.marking));

		await waitFor(() => expect(node("t1").getAttribute("data-area")).toBeNull());
	});

	it("filters by the search text and keeps the topics on the way", async () => {
		await renderPage({ documents: { workspace: { search: "n3" } } });

		await screen.findByTestId(sharedTestIds.treeNode("n3"));
		expect(screen.getByTestId(sharedTestIds.treeNode("t1"))).toBeTruthy();
		expect(screen.getByTestId(sharedTestIds.treeNode("t2"))).toBeTruthy();
		expect(screen.queryByTestId(sharedTestIds.treeNode("n1"))).toBeNull();
		expect(screen.queryByTestId(sharedTestIds.treeNode("t3"))).toBeNull();
	});

	it("says so when nothing is shown", async () => {
		await renderPage({ notes: [], topics: [] });

		expect((await screen.findByTestId(ids.empty)).textContent).toContain("Keine Notes");
	});

	it("folds all topics and remembers a folded topic in the UI state", async () => {
		const backend = await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("n3"));

		fireEvent.click(screen.getByTestId(sharedTestIds.treeToggle("t1")));
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.treeNode("n3"))).toBeNull());
		await waitFor(async () => {
			const { flushUiState } = await import("../../../../../../client/src/core/ui-state/uiState");
			await flushUiState(backend.store);
			expect((backend.documents.get("notes") as { collapsed?: string[] }).collapsed).toEqual(["t1"]);
		});

		fireEvent.click(screen.getByTestId(ids.collapse));
		await waitFor(() => expect(screen.getByTestId(ids.collapse).textContent).toBe("Topics aufklappen"));
		fireEvent.click(screen.getByTestId(ids.collapse));
		await waitFor(() => expect(screen.getByTestId(sharedTestIds.treeNode("n3"))).toBeTruthy());
	});

	it("shows the detail of the selected note", async () => {
		await renderPage();
		expect(screen.queryByTestId(ids.detail)).toBeNull();

		fireEvent.click(await screen.findByTestId(sharedTestIds.treeNode("n1")));

		await waitFor(() => expect(screen.getByTestId(sharedTestIds.detailTitle).textContent).toBe("N1 — Note n1"));
	});
});

describe("NotesPage: actions on topics and creating", () => {
	it("offers the actions of a topic in its row", async () => {
		await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("t1"));

		for (const action of ["note", "subtopic", "edit", "move", "archive", "delete"]) {
			expect(screen.getByTestId(ids.topicAction(action, "t1"))).toBeTruthy();
		}
	});

	it("creates a note in the topic with the form of the dialog", async () => {
		const backend = await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("t1"));

		fireEvent.click(screen.getByTestId(ids.topicAction("note", "t1")));
		fireEvent.change(await screen.findByTestId(ids.formField("summary")), { target: { value: "Neue Idee" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "notes/notes")).toHaveLength(1));
		expect(backend.calls("POST", "notes/notes")[0]!.body).toEqual({ project: "p1", fields: { summary: "Neue Idee", topic: "t1" } });
	});

	it("creates a note without topic and a topic at the project", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.project("p1"));

		fireEvent.click(screen.getByTestId(ids.newNote("p1")));
		fireEvent.change(await screen.findByTestId(ids.formField("summary")), { target: { value: "Lose Idee" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		await waitFor(() => expect(backend.calls("POST", "notes/notes")[0]!.body).toEqual({ project: "p1", fields: { summary: "Lose Idee" } }));

		await waitFor(() => expect(screen.queryByTestId(ids.formDialog)).toBeNull());
		fireEvent.click(screen.getByTestId(ids.newTopic("p1")));
		fireEvent.change(await screen.findByTestId(ids.topicField("name")), { target: { value: "Neu" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		await waitFor(() => expect(backend.calls("POST", "notes/topics")).toHaveLength(1));
		expect(backend.calls("POST", "notes/topics")[0]!.body).toEqual({ project: "p1", name: "Neu", parent: null, due_at: null });
	});

	it("creates a sub-topic and renames a topic with a due date", async () => {
		const backend = await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("t3"));

		fireEvent.click(screen.getByTestId(ids.topicAction("subtopic", "t3")));
		fireEvent.change(await screen.findByTestId(ids.topicField("name")), { target: { value: "Unter" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		await waitFor(() => expect(backend.calls("POST", "notes/topics")[0]!.body).toMatchObject({ name: "Unter", parent: "t3" }));

		await waitFor(() => expect(screen.queryByTestId(ids.topicField("name"))).toBeNull());
		fireEvent.click(screen.getByTestId(ids.topicAction("edit", "t3")));
		fireEvent.change(await screen.findByTestId(ids.topicField("name")), { target: { value: "Umbenannt" } });
		fireEvent.change(screen.getByTestId(ids.topicField("due_at")), { target: { value: "2026-12-01" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		await waitFor(() => expect(backend.calls("PUT", "notes/topics/t3")).toHaveLength(1));
		expect(backend.calls("PUT", "notes/topics/t3")[0]!.body).toEqual({ version: 1, fields: { name: "Umbenannt", due_at: "2026-12-01" } });
	});

	it("moves a topic with the dialog", async () => {
		const backend = await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("t3"));

		fireEvent.click(screen.getByTestId(ids.topicAction("move", "t3")));
		const dialog = await screen.findByTestId(ids.moveDialog);
		fireEvent.mouseDown(within(dialog).getByRole("combobox"));
		fireEvent.click(await screen.findByRole("option", { name: /Topic t1/ }));
		fireEvent.click(screen.getByTestId(ids.moveSave));

		await waitFor(() => expect(backend.calls("POST", "notes/topics/t3/move")).toHaveLength(1));
		expect(backend.calls("POST", "notes/topics/t3/move")[0]!.body).toEqual({ version: 1, parent: "t1" });
	});
});

describe("NotesPage: delete and archive a topic", () => {
	it("deletes an empty topic after one click on OK", async () => {
		const backend = await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("t3"));

		fireEvent.click(screen.getByTestId(ids.topicAction("delete", "t3")));
		await waitFor(() => expect(screen.getByTestId(ids.choiceConfirm).hasAttribute("disabled")).toBe(false));
		fireEvent.click(screen.getByTestId(ids.choiceConfirm));

		await waitFor(() => expect(backend.calls("POST", "notes/topics/t3/delete")).toHaveLength(1));
		expect(backend.calls("POST", "notes/topics/t3/delete")[0]!.body).toEqual({ version: 1 });
	});

	it("shows the numbers of a topic with content and sends the choice in one request", async () => {
		const backend = await renderPage({ contents: { t1: { topics: 1, active: 3, archived: 2 } } });
		await screen.findByTestId(sharedTestIds.treeNode("t1"));

		fireEvent.click(screen.getByTestId(ids.topicAction("delete", "t1")));
		expect((await screen.findByTestId(ids.choiceCounts)).textContent).toBe("Das Topic enthält 3 aktive und 2 archivierte Notes sowie 1 Unter-Topics.");
		fireEvent.click(screen.getByTestId(ids.choiceKeepArchived));
		fireEvent.click(screen.getByTestId(ids.choiceMove));
		const dialog = screen.getByTestId(ids.choiceDialog);
		fireEvent.mouseDown(within(dialog).getByRole("combobox"));
		fireEvent.click(await screen.findByRole("option", { name: /Topic t3/ }));
		fireEvent.click(screen.getByTestId(ids.choiceConfirm));

		await waitFor(() => expect(backend.calls("POST", "notes/topics/t1/delete")).toHaveLength(1));
		expect(backend.calls("POST", "notes/topics/t1/delete")[0]!.body).toEqual({ version: 1, keep_archived: true, active_notes: "move", move_to: "t3" });
	});

	it("deletes everything with the topic when nothing is chosen, and changes nothing on cancel", async () => {
		const backend = await renderPage({ contents: { t1: { topics: 0, active: 1, archived: 0 } } });
		await screen.findByTestId(sharedTestIds.treeNode("t1"));

		fireEvent.click(screen.getByTestId(ids.topicAction("delete", "t1")));
		await screen.findByTestId(ids.choiceCounts);
		fireEvent.click(screen.getByText("Abbrechen"));
		await waitFor(() => expect(screen.queryByTestId(ids.choiceDialog)).toBeNull());
		expect(backend.calls("POST", "notes/topics/t1/delete")).toHaveLength(0);

		fireEvent.click(screen.getByTestId(ids.topicAction("delete", "t1")));
		await screen.findByTestId(ids.choiceCounts);
		fireEvent.click(screen.getByTestId(ids.choiceConfirm));
		await waitFor(() => expect(backend.calls("POST", "notes/topics/t1/delete")).toHaveLength(1));
		expect(backend.calls("POST", "notes/topics/t1/delete")[0]!.body).toEqual({ version: 1, keep_archived: false, active_notes: "delete" });
	});

	it("archives with the active notes by default and reactivates an archived topic", async () => {
		const backend = await renderPage({ contents: { t1: { topics: 1, active: 3, archived: 0 } }, documents: { notes: { showArchivedTopics: true } } });
		await screen.findByTestId(sharedTestIds.treeNode("t1"));

		fireEvent.click(screen.getByTestId(ids.topicAction("archive", "t1")));
		await screen.findByTestId(ids.choiceCounts);
		fireEvent.click(screen.getByTestId(ids.choiceConfirm));
		await waitFor(() => expect(backend.calls("POST", "notes/topics/t1/archive")).toHaveLength(1));
		expect(backend.calls("POST", "notes/topics/t1/archive")[0]!.body).toEqual({ version: 1, keep_archived: false, active_notes: "archive" });

		fireEvent.click(await screen.findByTestId(ids.topicAction("reactivate", "old")));
		await waitFor(() => expect(backend.calls("POST", "notes/topics/old/reactivate")).toHaveLength(1));
		expect(backend.calls("POST", "notes/topics/old/reactivate")[0]!.body).toEqual({ version: 1 });
	});

	it("shows the message of the server when the request is refused", async () => {
		await renderPage({
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/delete") ? Response.json({ code: "topic_system", message: "Das Topic lässt sich nicht löschen", details: {} }, { status: 400 }) : undefined,
		});
		await screen.findByTestId(sharedTestIds.treeNode("t3"));

		fireEvent.click(screen.getByTestId(ids.topicAction("delete", "t3")));
		await waitFor(() => expect(screen.getByTestId(ids.choiceConfirm).hasAttribute("disabled")).toBe(false));
		fireEvent.click(screen.getByTestId(ids.choiceConfirm));

		await waitFor(() => expect(screen.getByText("Das Topic lässt sich nicht löschen")).toBeTruthy());
	});
});

describe("NotesPage: drag and drop", () => {
	const dragEvent = (type: "dragOver" | "drop", target: HTMLElement, offsetY: number) => {
		// jsdom has no DragEvent: build the event by hand so that it carries the pointer position.
		const event = new Event(type.toLowerCase(), { bubbles: true, cancelable: true });
		Object.defineProperty(event, "clientY", { value: offsetY });
		Object.defineProperty(event, "dataTransfer", { value: { setData: () => {}, getData: () => dragged, effectAllowed: "", dropEffect: "" } });
		target.getBoundingClientRect = () => ({ top: 0, height: 40, bottom: 40, left: 0, right: 100, width: 100, x: 0, y: 0, toJSON: () => ({}) });
		fireEvent(target, event);
	};
	let dragged = "";
	const start = (uid: string) => {
		dragged = uid;
		fireEvent.dragStart(node(uid), dragData);
	};

	it("moves a note into a topic", async () => {
		const backend = await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("n5"));

		start("n5");
		dragEvent("drop", node("t3"), 20);

		await waitFor(() => expect(backend.calls("PUT", "notes/notes/n5")).toHaveLength(1));
		expect(backend.calls("PUT", "notes/notes/n5")[0]!.body).toEqual({ version: 1, fields: { topic: "t3" } });
	});

	it("moves a topic below another one", async () => {
		const backend = await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("t3"));

		start("t3");
		dragEvent("drop", node("t1"), 20);

		await waitFor(() => expect(backend.calls("POST", "notes/topics/t3/move")).toHaveLength(1));
		expect(backend.calls("POST", "notes/topics/t3/move")[0]!.body).toEqual({ version: 1, parent: "t1" });
	});

	it("takes a note out of its topic when dropped on the name of the project", async () => {
		const backend = await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("n1"));

		dragged = "n1";
		dragEvent("drop", screen.getByTestId(ids.projectDrop("p1")), 0);

		await waitFor(() => expect(backend.calls("PUT", "notes/notes/n1")).toHaveLength(1));
		expect(backend.calls("PUT", "notes/notes/n1")[0]!.body).toEqual({ version: 1, fields: { topic: null } });
	});

	it("does not accept a drop that changes nothing or loops", async () => {
		const backend = await renderPage();
		await screen.findByTestId(sharedTestIds.treeNode("n1"));

		start("n1");
		dragEvent("drop", node("t1"), 20);
		start("t1");
		dragEvent("drop", node("t2"), 20);

		expect(backend.requests.filter((entry) => entry.method !== "GET" && !entry.path.startsWith("core/"))).toHaveLength(0);
	});

	it("shows the message of the server when a move is refused", async () => {
		await renderPage({
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/move") ? Response.json({ code: "topic_too_deep", message: "Das Topic läge auf Ebene 4", details: {} }, { status: 400 }) : undefined,
		});
		await screen.findByTestId(sharedTestIds.treeNode("t3"));

		start("t3");
		dragEvent("drop", node("t2"), 20);

		await waitFor(() => expect(screen.getByTestId(ids.error).textContent).toContain("Das Topic läge auf Ebene 4"));
	});
});
