import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DocumentsSection } from "../../../../../../client/src/plugins/backlog/DocumentsSection";
import { backlogTestIds as ids } from "../../../../../../client/src/plugins/backlog/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { detail, document } from "../../../../../helpers/client/backlogFixtures";
import { fakeWorkspaceBackend } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const withDocs = detail("t1", { label: "TASK-001", title: "Ein Task", summary: "Kurz", notes: ["TASK-001_notes.md"], spec: ["TASK-001_spec.md"] });

async function renderSection(item = withDocs, options: Parameters<typeof fakeWorkspaceBackend>[0] = {}) {
	const backend = fakeWorkspaceBackend({
		itemDocuments: {
			"TASK-001_notes.md": document("TASK-001_notes.md", "# TASK-001 — Ein Task\n\n## 2026-10-16 — Thema\n"),
			"TASK-001_spec.md": document("TASK-001_spec.md", "# Spec\n\nEin **Text**.", { version: 3 }),
		},
		...options,
	});
	await renderWorkspace(<DocumentsSection item={item} />, { backend });
	return backend;
}

describe("DocumentsSection", () => {
	it("lists the notes and specs of the item by name", async () => {
		await renderSection();

		expect(screen.getByTestId(ids.document("TASK-001_notes.md"))).toBeTruthy();
		expect(screen.getByTestId(ids.document("TASK-001_spec.md"))).toBeTruthy();
	});

	it("says so when there are none, and offers no adding for an item in the trash", async () => {
		await renderSection({ ...withDocs, notes: [], spec: [], deleted: true });

		expect(screen.getByTestId(ids.documents).textContent).toContain("Noch keine Notizen oder Specs.");
		expect(screen.queryByTestId(ids.addNote)).toBeNull();
	});

	it("opens a document as formatted text", async () => {
		await renderSection();

		fireEvent.click(screen.getByTestId(ids.document("TASK-001_spec.md")));

		const dialog = await screen.findByTestId(ids.documentDialog);
		await waitFor(() => expect(dialog.querySelector("strong")?.textContent).toBe("Text"));
	});

	it("edits a document with the preview and saves it in the version it was loaded", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(ids.document("TASK-001_spec.md")));
		fireEvent.click(await screen.findByTestId(ids.documentEdit));
		fireEvent.change(await screen.findByRole("textbox", { name: "TASK-001_spec.md" }), { target: { value: "# Neu\n" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.markdownSave));

		await waitFor(() => expect(backend.calls("PUT", "documents/TASK-001_spec.md")).toHaveLength(1));
		expect(backend.calls("PUT", "documents/TASK-001_spec.md")[0]!.body).toEqual({ content: "# Neu\n", version: 3 });
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.markdownEditor)).toBeNull());
	});

	it("shows a conflict and saves anyway on the current version", async () => {
		let attempts = 0;
		const backend = await renderSection(withDocs, {
			respond: ({ method, path }) =>
				method === "PUT" && path.endsWith("TASK-001_spec.md") && attempts++ === 0
					? Response.json({ code: "version_conflict", message: "geändert", details: {} }, { status: 409 })
					: undefined,
			itemDocuments: { "TASK-001_spec.md": document("TASK-001_spec.md", "# Spec", { version: 3 }), "TASK-001_notes.md": document("TASK-001_notes.md", "# N") },
		});

		fireEvent.click(screen.getByTestId(ids.document("TASK-001_spec.md")));
		fireEvent.click(await screen.findByTestId(ids.documentEdit));
		fireEvent.change(await screen.findByRole("textbox", { name: "TASK-001_spec.md" }), { target: { value: "# Meins\n" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.markdownSave));
		expect(await screen.findByTestId(sharedTestIds.markdownConflict)).toBeTruthy();
		fireEvent.click(screen.getByTestId(sharedTestIds.markdownSaveAnyway));

		await waitFor(() => expect(backend.calls("PUT", "documents/TASK-001_spec.md")).toHaveLength(2));
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.markdownEditor)).toBeNull());
	});

	it("appends a notes entry: topic and one bullet per line", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(ids.addNote));
		fireEvent.change(await screen.findByTestId(ids.noteField("topic")), { target: { value: "Sync" } });
		fireEvent.change(screen.getByTestId(ids.noteField("discussed")), { target: { value: "Eins\n\n Zwei " } });
		fireEvent.change(screen.getByTestId(ids.noteField("decided")), { target: { value: "Ja" } });
		fireEvent.click(screen.getByTestId(ids.noteSave));

		await waitFor(() => expect(backend.calls("POST", "backlog/items/t1/notes")).toHaveLength(1));
		expect(backend.calls("POST", "backlog/items/t1/notes")[0]!.body).toEqual({ topic: "Sync", discussed: ["Eins", "Zwei"], decided: ["Ja"], open: [] });
		await waitFor(() => expect(screen.queryByTestId(ids.noteDialog)).toBeNull());
	});

	it("asks for a summary with the first entry when the item has none", async () => {
		const backend = await renderSection(detail("t1", { label: "TASK-001", summary: null }));

		fireEvent.click(screen.getByTestId(ids.addNote));
		fireEvent.change(await screen.findByTestId(ids.noteField("topic")), { target: { value: "Start" } });
		fireEvent.change(screen.getByTestId(ids.noteField("discussed")), { target: { value: "Eins" } });
		fireEvent.change(screen.getByTestId(ids.noteField("summary")), { target: { value: "Kurzfassung" } });
		fireEvent.click(screen.getByTestId(ids.noteSave));

		await waitFor(() => expect(backend.calls("POST", "notes")).toHaveLength(1));
		expect(backend.calls("POST", "notes")[0]!.body).toMatchObject({ summary: "Kurzfassung" });
	});

	it("does not ask for a summary when the item has one", async () => {
		await renderSection();

		fireEvent.click(screen.getByTestId(ids.addNote));

		await screen.findByTestId(ids.noteField("topic"));
		expect(screen.queryByTestId(ids.noteField("summary"))).toBeNull();
	});

	it("shows the message of the server when an entry is refused", async () => {
		await renderSection(withDocs, {
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/notes")
					? Response.json({ code: "value_required", message: "Ein Notiz-Eintrag braucht ein Thema", details: {} }, { status: 400 })
					: undefined,
		});

		fireEvent.click(screen.getByTestId(ids.addNote));
		fireEvent.click(await screen.findByTestId(ids.noteSave));

		await waitFor(() => expect(screen.getByTestId(ids.documentError).textContent).toBe("Ein Notiz-Eintrag braucht ein Thema"));
		expect(screen.getByTestId(ids.noteDialog)).toBeTruthy();
	});

	it("creates a spec with a name that follows the label, and opens it", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(ids.addSpec));
		const name = (await screen.findByTestId(ids.specName)) as HTMLInputElement;
		expect(name.value).toBe("TASK-001_spec.md");
		fireEvent.change(name, { target: { value: "TASK-001_spec_Teil.md" } });
		fireEvent.click(screen.getByTestId(ids.specSave));

		await waitFor(() => expect(backend.calls("PUT", "documents/TASK-001_spec_Teil.md")).toHaveLength(1));
		expect(backend.calls("PUT", "documents/TASK-001_spec_Teil.md")[0]!.body).toEqual({ content: "# TASK-001 — Ein Task\n" });
	});
});
