import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { NoteDetail } from "../../../../../../client/src/plugins/notes/NoteDetail";
import { notesTestIds as ids } from "../../../../../../client/src/plugins/notes/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeNotesBackend } from "../../../../../helpers/client/fakeNotesBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { note, noteDetail, notesDocument, topic } from "../../../../../helpers/client/notesFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const action = (id: string) => screen.getByTestId(sharedTestIds.detailAction(id));

afterEach(cleanup);

async function renderDetail(detail = noteDetail("n1"), options: Parameters<typeof fakeNotesBackend>[0] = {}) {
	const backend = fakeNotesBackend({
		projects,
		topics: [topic("t1"), topic("t2")],
		notes: [note("n1", { topic_uid: "t1" })],
		noteDetails: { [detail.uid]: detail },
		elements: [{ uid: "n1", project_uid: "p1", kind: "note", label: "N1", title: "Note n1", deleted: false, version: 1 }],
		...options,
	});
	await renderWorkspace(<NoteDetail uid={detail.uid} />, { backend });
	await screen.findByTestId(ids.detail);
	return backend;
}

describe("NoteDetail", () => {
	it("shows status, topic path, review date and text", async () => {
		await renderDetail(
			noteDetail("n1", { status: "due", body: "Ein **langer** Text", path: [{ uid: "t1", label: "T1", name: "Oben" }, { uid: "t2", label: "T2", name: "Unten" }], review_at: "2026-11-15T12:00:00Z" }),
		);

		expect(screen.getByTestId(sharedTestIds.detailTitle).textContent).toBe("N1 — Note n1");
		expect(screen.getByTestId(ids.detailStatus).textContent).toBe("Fällig");
		expect(screen.getByTestId(ids.detailPath).textContent).toBe("Oben › Unten");
		expect(screen.getByTestId(ids.detailReview).textContent).toBe("2026-11-15");
		expect(screen.getByTestId(ids.detailBody).querySelector("strong")?.textContent).toBe("langer");
	});

	it("says there is no topic and no text when so", async () => {
		await renderDetail();

		expect(screen.getByTestId(ids.detailPath).textContent).toBe("Ohne Topic");
		expect(screen.queryByTestId(ids.detailBody)).toBeNull();
	});

	it.each([
		["done", "finish", { version: 1, status: "done" }],
		["dropped", "finish", { version: 1, status: "dropped" }],
		["keep", "keep", { version: 1 }],
	])("%s sends %s with the version", async (id, path, body) => {
		const backend = await renderDetail();

		fireEvent.click(action(id));

		await waitFor(() => expect(backend.calls("POST", `notes/notes/n1/${path}`)).toHaveLength(1));
		expect(backend.calls("POST", `notes/notes/n1/${path}`)[0]!.body).toEqual(body);
	});

	it("snoozes until a chosen date, or for the interval without one", async () => {
		const backend = await renderDetail();

		fireEvent.click(action("snooze"));
		fireEvent.change(await screen.findByTestId(ids.snoozeDate), { target: { value: "2027-01-02" } });
		fireEvent.click(screen.getByTestId(ids.snoozeConfirm));
		await waitFor(() => expect(backend.calls("POST", "notes/notes/n1/snooze")).toHaveLength(1));
		expect(backend.calls("POST", "notes/notes/n1/snooze")[0]!.body).toEqual({ version: 1, review_at: "2027-01-02" });

		await waitFor(() => expect(screen.queryByTestId(ids.snoozeDialog)).toBeNull());
		fireEvent.click(action("snooze"));
		await screen.findByTestId(ids.snoozeDate);
		fireEvent.click(screen.getByTestId(ids.snoozeConfirm));
		await waitFor(() => expect(backend.calls("POST", "notes/notes/n1/snooze")).toHaveLength(2));
		expect(backend.calls("POST", "notes/notes/n1/snooze")[1]!.body).toEqual({ version: 1 });
	});

	it("edits the note and sends only what changed", async () => {
		const backend = await renderDetail(noteDetail("n1", { body: "alt" }));

		fireEvent.click(action("edit"));
		fireEvent.change(await screen.findByTestId(ids.formField("summary")), { target: { value: "Neue Kurzfassung" } });
		fireEvent.change(screen.getByTestId(ids.formField("review_at")), { target: { value: "2027-02-03" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("PUT", "notes/notes/n1")).toHaveLength(1));
		expect(backend.calls("PUT", "notes/notes/n1")[0]!.body).toEqual({ version: 1, fields: { summary: "Neue Kurzfassung", review_at: "2027-02-03" } });
	});

	it("offers the current state when the note was changed meanwhile", async () => {
		await renderDetail(noteDetail("n1"), {
			respond: ({ method, path }) =>
				method === "PUT" && path === "notes/notes/n1" ? Response.json({ code: "version_conflict", message: "Version", details: {} }, { status: 409 }) : undefined,
		});

		fireEvent.click(action("edit"));
		fireEvent.change(await screen.findByTestId(ids.formField("summary")), { target: { value: "Anders" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		expect(await screen.findByTestId(sharedTestIds.editFormConflict)).toBeTruthy();
	});

	it("puts the note into the trash", async () => {
		const backend = await renderDetail();

		fireEvent.click(action("delete"));

		await waitFor(() => expect(backend.calls("DELETE", "workspace/elements/n1")).toHaveLength(1));
	});

	it("offers only restore, large view and delete for an archived note, and restores it", async () => {
		const backend = await renderDetail(noteDetail("n1", { status: "done", stored_status: "done", archived: true }));

		expect(screen.queryByTestId(sharedTestIds.detailAction("edit"))).toBeNull();
		expect(screen.queryByTestId(sharedTestIds.detailAction("done"))).toBeNull();
		fireEvent.click(action("restore"));

		await waitFor(() => expect(backend.calls("POST", "notes/notes/n1/restore")).toHaveLength(1));
		expect(backend.calls("POST", "notes/notes/n1/restore")[0]!.body).toEqual({ version: 1 });
	});

	it("marks a note that is archived because of its topic", async () => {
		await renderDetail(noteDetail("n1", { stored_status: "waiting", archived: true }));

		expect(screen.getByText("mit dem Topic archiviert")).toBeTruthy();
	});

	it("shows a note in the trash without actions", async () => {
		await renderDetail(noteDetail("n1", { deleted: true }));

		expect(screen.queryAllByRole("button", { name: "Bearbeiten" })).toHaveLength(0);
		expect(screen.getByText("im Papierkorb")).toBeTruthy();
	});

	it("shows the message of the server when an action is refused", async () => {
		await renderDetail(noteDetail("n1"), {
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/keep") ? Response.json({ code: "note_archived", message: "N1 liegt im Archiv", details: {} }, { status: 400 }) : undefined,
		});

		fireEvent.click(action("keep"));

		await waitFor(() => expect(screen.getByTestId(ids.detailError).textContent).toContain("N1 liegt im Archiv"));
	});

	it("opens the text in the large view", async () => {
		await renderDetail(noteDetail("n1", { body: "# Überschrift\n\nText" }));

		fireEvent.click(action("large"));

		expect(await screen.findByTestId(sharedTestIds.largeView)).toBeTruthy();
	});
});

describe("NoteDetail: documents", () => {
	const detail = noteDetail("n1", { documents: ["N1_notes.md", "N1_spec.md"] });
	const documents = { "N1_notes.md": notesDocument("N1_notes.md", "# N1 — Note n1\n\n## 2026-10-16 — Start\n"), "N1_spec.md": notesDocument("N1_spec.md", "Spec") };

	it("lists the documents and shows one", async () => {
		await renderDetail(detail, { noteDocuments: documents });

		expect(screen.getByTestId(sharedTestIds.document("N1_spec.md"))).toBeTruthy();
		fireEvent.click(screen.getByTestId(sharedTestIds.document("N1_notes.md")));
		const dialog = await screen.findByTestId(sharedTestIds.documentDialog);
		await waitFor(() => expect(dialog.textContent).toContain("Start"));
	});

	it("edits a document in its version", async () => {
		const backend = await renderDetail(detail, { noteDocuments: documents });

		fireEvent.click(screen.getByTestId(sharedTestIds.document("N1_spec.md")));
		await screen.findByText("Spec");
		fireEvent.click(screen.getByTestId(sharedTestIds.documentEdit));
		const editor = await screen.findByRole("textbox", { name: "N1_spec.md" });
		fireEvent.change(editor, { target: { value: "Spec neu" } });
		fireEvent.click(screen.getByText("Speichern"));

		await waitFor(() => expect(backend.calls("PUT", "notes/notes/n1/documents/N1_spec.md")).toHaveLength(1));
		expect(backend.calls("PUT", "notes/notes/n1/documents/N1_spec.md")[0]!.body).toEqual({ content: "Spec neu", version: 1 });
	});

	it("appends an entry to the notes", async () => {
		const backend = await renderDetail(detail, { noteDocuments: documents });

		fireEvent.click(screen.getByTestId(sharedTestIds.documentsAddEntry));
		fireEvent.change(await screen.findByTestId(sharedTestIds.entryField("topic")), { target: { value: "Treffen" } });
		fireEvent.change(screen.getByTestId(sharedTestIds.entryField("discussed")), { target: { value: "a\n\nb" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.entrySave));

		await waitFor(() => expect(backend.calls("POST", "notes/notes/n1/entries")).toHaveLength(1));
		expect(backend.calls("POST", "notes/notes/n1/entries")[0]!.body).toEqual({ topic: "Treffen", discussed: ["a", "b"], decided: [], open: [] });
	});

	it("creates a spec with the name of the label", async () => {
		const backend = await renderDetail(noteDetail("n1"), { noteDocuments: {} });

		fireEvent.click(screen.getByTestId(sharedTestIds.documentsAddSpec));
		expect((await screen.findByTestId(sharedTestIds.specName) as HTMLInputElement).value).toBe("N1_spec.md");
		fireEvent.click(screen.getByTestId(sharedTestIds.specSave));

		await waitFor(() => expect(backend.calls("PUT", "notes/notes/n1/documents/N1_spec.md")).toHaveLength(1));
		expect(backend.calls("PUT", "notes/notes/n1/documents/N1_spec.md")[0]!.body).toEqual({ content: "# N1 — Note n1\n" });
	});

	it("cannot add documents to an archived note", async () => {
		await renderDetail(noteDetail("n1", { archived: true, status: "done", stored_status: "done" }));

		expect(screen.queryByTestId(sharedTestIds.documentsAddEntry)).toBeNull();
	});
});
