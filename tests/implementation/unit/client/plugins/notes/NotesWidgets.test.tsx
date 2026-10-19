import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CreateNote, CreateTopic } from "../../../../../../client/src/plugins/notes/CreateForms";
import { NotesAttention } from "../../../../../../client/src/plugins/notes/NotesAttention";
import { NotesSettings } from "../../../../../../client/src/plugins/notes/NotesSettings";
import { NewButton } from "../../../../../../client/src/plugins/workspace/NewButton";
import { ProjectsSection } from "../../../../../../client/src/plugins/workspace/ProjectsSection";
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

describe("NotesAttention in the bell of the projects section", () => {
	const due = {
		count: 2,
		notes: [
			dueNote("n1", { label: "NOTE-001", summary: "Eins", reason: "trigger", due_since: "2026-10-18T07:00:00Z" }),
			dueNote("n2", { label: "NOTE-002", summary: "Zwei", review_at: "2026-10-18T09:00:00Z", due_since: "2026-10-18T09:00:00Z" }),
		],
	};
	const widgets = [{ ownerId: "notes", slot: "workspace.attention-sources", name: "due", component: NotesAttention }];

	it("reports nothing when no note is due", async () => {
		await renderWorkspace(<ProjectsSection />, { backend: fakeNotesBackend({ projects }), widgets });

		await screen.findByTestId(workspaceTestIds.project("p1"));
		await waitFor(() => expect(screen.queryByTestId(workspaceTestIds.attentionBell)).toBeNull());
	});

	it("counts the due notes, puts the number into the tab title, and lists them the latest first", async () => {
		document.title = "ToDo-Viewer";
		await renderWorkspace(<ProjectsSection />, { backend: fakeNotesBackend({ projects, due }), widgets });

		const bell = await screen.findByTestId(workspaceTestIds.attentionBell);
		expect(bell.getAttribute("aria-label")).toBe("2 fällig");
		await waitFor(() => expect(document.title).toBe("(2) ToDo-Viewer"));

		fireEvent.click(bell);
		const items = (await screen.findByTestId(workspaceTestIds.attentionList)).querySelectorAll("[data-testid^='workspace.attention-item.']");
		expect([...items].map((item) => item.textContent?.slice(0, 15))).toEqual(["NOTE-002 — Zwei", "NOTE-001 — Eins"]);
	});

	it("remembers the chosen note as the selected one", async () => {
		const backend = fakeNotesBackend({ projects, due });
		await renderWorkspace(<ProjectsSection />, { backend, widgets });

		fireEvent.click(await screen.findByTestId(workspaceTestIds.attentionBell));
		fireEvent.click(await screen.findByTestId(workspaceTestIds.attentionOpen("notes:n2")));

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
