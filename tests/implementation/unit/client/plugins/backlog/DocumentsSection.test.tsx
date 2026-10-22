import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DocumentsSection } from "../../../../../../client/src/plugins/backlog/DocumentsSection";
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

		expect(screen.getByTestId(sharedTestIds.document("TASK-001_notes.md"))).toBeTruthy();
		expect(screen.getByTestId(sharedTestIds.document("TASK-001_spec.md"))).toBeTruthy();
	});

	it("says so when there are none, and offers no adding for an item in the trash", async () => {
		await renderSection({ ...withDocs, notes: [], spec: [], deleted: true });

		expect(screen.getByTestId(sharedTestIds.documents).textContent).toContain("Noch keine Notizen oder Specs.");
		expect(screen.queryByTestId(sharedTestIds.documentsAddEntry)).toBeNull();
	});

	it("opens a document as formatted text", async () => {
		await renderSection();

		fireEvent.click(screen.getByTestId(sharedTestIds.document("TASK-001_spec.md")));

		const dialog = await screen.findByTestId(sharedTestIds.documentDialog);
		await waitFor(() => expect(dialog.querySelector("strong")?.textContent).toBe("Text"));
	});

	it("offers large view, edit and close as icons in the title bar of the document", async () => {
		await renderSection();

		fireEvent.click(screen.getByTestId(sharedTestIds.document("TASK-001_spec.md")));

		expect((await screen.findByTestId(sharedTestIds.documentLarge)).getAttribute("aria-label")).toBe("Großansicht");
		expect(screen.getByTestId(sharedTestIds.documentEdit).getAttribute("aria-label")).toBe("Bearbeiten");
		fireEvent.click(screen.getByTestId(sharedTestIds.documentClose));
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.documentDialog)).toBeNull());
	});

	it("edits a document with the preview and saves it in the version it was loaded", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(sharedTestIds.document("TASK-001_spec.md")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.documentEdit));
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

		fireEvent.click(screen.getByTestId(sharedTestIds.document("TASK-001_spec.md")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.documentEdit));
		fireEvent.change(await screen.findByRole("textbox", { name: "TASK-001_spec.md" }), { target: { value: "# Meins\n" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.markdownSave));
		expect(await screen.findByTestId(sharedTestIds.markdownConflict)).toBeTruthy();
		fireEvent.click(screen.getByTestId(sharedTestIds.markdownSaveAnyway));

		await waitFor(() => expect(backend.calls("PUT", "documents/TASK-001_spec.md")).toHaveLength(2));
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.markdownEditor)).toBeNull());
	});

	it("appends a notes entry: topic and one bullet per line", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(sharedTestIds.documentsAddEntry));
		fireEvent.change(await screen.findByTestId(sharedTestIds.entryField("topic")), { target: { value: "Sync" } });
		fireEvent.change(screen.getByTestId(sharedTestIds.entryField("discussed")), { target: { value: "Eins\n\n Zwei " } });
		fireEvent.change(screen.getByTestId(sharedTestIds.entryField("decided")), { target: { value: "Ja" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.entrySave));

		await waitFor(() => expect(backend.calls("POST", "backlog/items/t1/notes")).toHaveLength(1));
		expect(backend.calls("POST", "backlog/items/t1/notes")[0]!.body).toEqual({ topic: "Sync", discussed: ["Eins", "Zwei"], decided: ["Ja"], open: [] });
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.entryDialog)).toBeNull());
	});

	it("asks for a summary with the first entry when the item has none", async () => {
		const backend = await renderSection(detail("t1", { label: "TASK-001", summary: null }));

		fireEvent.click(screen.getByTestId(sharedTestIds.documentsAddEntry));
		fireEvent.change(await screen.findByTestId(sharedTestIds.entryField("topic")), { target: { value: "Start" } });
		fireEvent.change(screen.getByTestId(sharedTestIds.entryField("discussed")), { target: { value: "Eins" } });
		fireEvent.change(screen.getByTestId(sharedTestIds.entryField("summary")), { target: { value: "Kurzfassung" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.entrySave));

		await waitFor(() => expect(backend.calls("POST", "notes")).toHaveLength(1));
		expect(backend.calls("POST", "notes")[0]!.body).toMatchObject({ summary: "Kurzfassung" });
	});

	it("does not ask for a summary when the item has one", async () => {
		await renderSection();

		fireEvent.click(screen.getByTestId(sharedTestIds.documentsAddEntry));

		await screen.findByTestId(sharedTestIds.entryField("topic"));
		expect(screen.queryByTestId(sharedTestIds.entryField("summary"))).toBeNull();
	});

	it("shows the message of the server when an entry is refused", async () => {
		await renderSection(withDocs, {
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/notes")
					? Response.json({ code: "value_required", message: "Ein Notiz-Eintrag braucht ein Thema", details: {} }, { status: 400 })
					: undefined,
		});

		fireEvent.click(screen.getByTestId(sharedTestIds.documentsAddEntry));
		fireEvent.click(await screen.findByTestId(sharedTestIds.entrySave));

		await waitFor(() => expect(screen.getByTestId(sharedTestIds.documentError).textContent).toBe("Ein Notiz-Eintrag braucht ein Thema"));
		expect(screen.getByTestId(sharedTestIds.entryDialog)).toBeTruthy();
	});

	it("creates a spec with a name that follows the label, and opens it", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(sharedTestIds.documentsAddSpec));
		const name = (await screen.findByTestId(sharedTestIds.specName)) as HTMLInputElement;
		expect(name.value).toBe("TASK-001_spec.md");
		fireEvent.change(name, { target: { value: "TASK-001_spec_Teil.md" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.specSave));

		await waitFor(() => expect(backend.calls("PUT", "documents/TASK-001_spec_Teil.md")).toHaveLength(1));
		expect(backend.calls("PUT", "documents/TASK-001_spec_Teil.md")[0]!.body).toEqual({ content: "# TASK-001 — Ein Task\n" });
	});

	it("deletes a document after asking, in the version that is shown, and closes it", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(sharedTestIds.document("TASK-001_spec.md")));
		const trash = await screen.findByTestId(sharedTestIds.documentDelete);
		expect(trash.getAttribute("aria-label")).toBe("In den Papierkorb legen");
		fireEvent.click(trash);
		expect(backend.calls("DELETE", "documents/TASK-001_spec.md")).toHaveLength(0);
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogConfirm));

		await waitFor(() => expect(backend.calls("DELETE", "documents/TASK-001_spec.md")).toHaveLength(1));
		expect(backend.calls("DELETE", "documents/TASK-001_spec.md")[0]!.query.get("version")).toBe("3");
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.documentDialog)).toBeNull());
	});

	it("deletes nothing when the question is cancelled", async () => {
		const backend = await renderSection();

		fireEvent.click(screen.getByTestId(sharedTestIds.document("TASK-001_spec.md")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.documentDelete));
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogCancel));

		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.confirmDialog)).toBeNull());
		expect(backend.calls("DELETE", "documents/")).toHaveLength(0);
		expect(screen.getByTestId(sharedTestIds.documentDialog)).toBeTruthy();
	});

	it("tells the notes apart in the question: the summary goes with them", async () => {
		await renderSection();

		fireEvent.click(screen.getByTestId(sharedTestIds.document("TASK-001_notes.md")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.documentDelete));

		expect((await screen.findByTestId(sharedTestIds.confirmDialog)).textContent).toContain("Kurzfassung");
	});

	it("shows the message of the server when deleting is refused and keeps the document open", async () => {
		await renderSection(withDocs, {
			respond: ({ method }) =>
				method === "DELETE" ? Response.json({ code: "version_conflict", message: "Das Dokument wurde inzwischen geändert", details: {} }, { status: 409 }) : undefined,
		});

		fireEvent.click(screen.getByTestId(sharedTestIds.document("TASK-001_spec.md")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.documentDelete));
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogConfirm));

		await waitFor(() => expect(screen.getByTestId(sharedTestIds.documentError).textContent).toBe("Das Dokument wurde inzwischen geändert"));
		expect(screen.getByTestId(sharedTestIds.documentDialog)).toBeTruthy();
	});

	it("offers no deleting for an item in the trash", async () => {
		await renderSection({ ...withDocs, deleted: true });

		fireEvent.click(screen.getByTestId(sharedTestIds.document("TASK-001_spec.md")));

		await screen.findByTestId(sharedTestIds.documentLarge);
		expect(screen.queryByTestId(sharedTestIds.documentDelete)).toBeNull();
	});
});
