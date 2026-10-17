import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CreateNote, CreateTopic } from "../../../../../../client/src/plugins/notes/CreateForms";
import { DueCounter } from "../../../../../../client/src/plugins/notes/DueCounter";
import { NotesSettings } from "../../../../../../client/src/plugins/notes/NotesSettings";
import { NewButton } from "../../../../../../client/src/plugins/workspace/NewButton";
import { workspaceTestIds } from "../../../../../../client/src/plugins/workspace/testIds";
import { notesTestIds as ids } from "../../../../../../client/src/plugins/notes/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeNotesBackend } from "../../../../../helpers/client/fakeNotesBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { dueNote } from "../../../../../helpers/client/notesFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];

afterEach(() => {
	cleanup();
	document.title = "";
});

describe("DueCounter", () => {
	const due = { count: 2, notes: [dueNote("n1", { label: "NOTE-001", summary: "Eins", reason: "trigger" }), dueNote("n2", { label: "NOTE-002", summary: "Zwei" })] };

	it("shows nothing when no note is due", async () => {
		await renderWorkspace(<DueCounter />, { backend: fakeNotesBackend({ projects }) });

		await waitFor(() => expect(screen.queryByTestId(ids.dueCounter)).toBeNull());
	});

	it("shows the number, puts it into the tab title, and lists the due notes on a click", async () => {
		document.title = "ToDo-Viewer";
		await renderWorkspace(<DueCounter />, { backend: fakeNotesBackend({ projects, due }) });

		const counter = await screen.findByTestId(ids.dueCounter);
		expect(counter.textContent).toBe("!2");
		expect(counter.getAttribute("aria-label")).toBe("2 fällige Notes");
		expect(document.title).toBe("(2) ToDo-Viewer");

		fireEvent.click(counter);
		const list = await screen.findByTestId(ids.dueList);
		expect(list.textContent).toContain("NOTE-001 — Eins");
		expect(list.textContent).toContain("NOTE-002 — Zwei");
	});

	it("remembers the chosen note as the selected one", async () => {
		const backend = fakeNotesBackend({ projects, due });
		await renderWorkspace(<DueCounter />, { backend });

		fireEvent.click(await screen.findByTestId(ids.dueCounter));
		fireEvent.click(await screen.findByTestId(ids.dueItem("n2")));

		await waitFor(async () => {
			const { flushUiState } = await import("../../../../../../client/src/core/ui-state/uiState");
			await flushUiState(backend.store);
			expect((backend.documents.get("notes") as { selected?: string }).selected).toBe("n2");
		});
	});
});

describe("NotesSettings", () => {
	it("shows the settings and saves the changed values", async () => {
		const backend = fakeNotesBackend({ projects, settings: { max_topic_depth: 3, review_days: 30 } });
		await renderWorkspace(<NotesSettings />, { backend });

		const days = (await screen.findByTestId(ids.settingsField("review_days"))) as HTMLInputElement;
		expect(days.value).toBe("30");
		expect((screen.getByTestId(ids.settingsField("max_topic_depth")) as HTMLInputElement).value).toBe("3");
		fireEvent.change(days, { target: { value: "14" } });
		fireEvent.change(screen.getByTestId(ids.settingsField("max_topic_depth")), { target: { value: "5" } });
		fireEvent.click(screen.getByTestId(ids.settingsSave));

		await waitFor(() => expect(backend.calls("PUT", "notes/settings")).toHaveLength(1));
		expect(backend.calls("PUT", "notes/settings")[0]!.body).toEqual({ review_days: 14, max_topic_depth: 5 });
		expect(await screen.findByText("Gespeichert.")).toBeTruthy();
	});

	it("shows the message of the server when the values are refused", async () => {
		await renderWorkspace(<NotesSettings />, {
			backend: fakeNotesBackend({
				projects,
				respond: ({ method, path }) =>
					method === "PUT" && path === "notes/settings" ? Response.json({ code: "invalid_input", message: "review_days muss zwischen 1 und 3650 liegen", details: {} }, { status: 422 }) : undefined,
			}),
		});

		fireEvent.click(await screen.findByTestId(ids.settingsSave));

		expect(await screen.findByText("review_days muss zwischen 1 und 3650 liegen")).toBeTruthy();
	});
});

describe("create forms of the dialog '＋ New'", () => {
	const types = [
		{ ownerId: "notes", name: "note", title: "Neue Note", form: CreateNote },
		{ ownerId: "notes", name: "topic", title: "Neues Topic", form: CreateTopic },
	];

	it("creates a note in the marked project", async () => {
		const backend = fakeNotesBackend({ projects, documents: { workspace: { marked: "p1" } } });
		await renderWorkspace(<NewButton />, { backend, createTypes: types });

		fireEvent.click(screen.getByTestId(workspaceTestIds.newButton));
		fireEvent.click(await screen.findByTestId(workspaceTestIds.newMenuItem("note")));
		fireEvent.change(await screen.findByTestId(ids.formField("summary")), { target: { value: "Aus dem Menü" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "notes/notes")).toHaveLength(1));
		expect(backend.calls("POST", "notes/notes")[0]!.body).toEqual({ project: "p1", fields: { summary: "Aus dem Menü" } });
		await waitFor(() => expect(screen.queryByTestId(workspaceTestIds.newDialog)).toBeNull());
	});

	it("creates a topic in the built-in project by default", async () => {
		const backend = fakeNotesBackend({ projects });
		await renderWorkspace(<NewButton />, { backend, createTypes: types });
		await waitFor(() => expect(screen.getByTestId(workspaceTestIds.newButton)).toBeTruthy());

		fireEvent.click(screen.getByTestId(workspaceTestIds.newButton));
		fireEvent.click(await screen.findByTestId(workspaceTestIds.newMenuItem("topic")));
		await waitFor(() => expect(screen.getByTestId(ids.topicField("name"))).toBeTruthy());
		fireEvent.change(screen.getByTestId(ids.topicField("name")), { target: { value: "Ideen" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "notes/topics")).toHaveLength(1));
		expect(backend.calls("POST", "notes/topics")[0]!.body).toEqual({ project: "p0", name: "Ideen", parent: null, due_at: null });
	});
});
