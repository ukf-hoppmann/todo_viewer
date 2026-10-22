import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DocumentsSection } from "../../../../../../client/src/plugins/backlog/DocumentsSection";
import { NotesPeek } from "../../../../../../client/src/plugins/backlog/NotesPeek";
import { backlogTestIds as ids } from "../../../../../../client/src/plugins/backlog/testIds";
import { detail } from "../../../../../helpers/client/backlogFixtures";
import { fakeWorkspaceBackend } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const HEAD = "- Goal/Status: läuft\n- Next step: weiter";
const entries = [
	{ position: 1, day: "2026-10-01", topic: "Erstes", text: "## 2026-10-01 — Erstes\n\n### Discussed\n\n- eins\n" },
	{ position: 2, day: "2026-10-02", topic: "Zweites", text: "## 2026-10-02 — Zweites\n\n### Discussed\n\n- zwei\n" },
];

async function renderHead(state: string, content = HEAD, notes = ["T_notes.md"]) {
	const item = detail("t1", { label: "TASK-001", notes, notes_state: notes.length ? state : null });
	const backend = fakeWorkspaceBackend({ notesStates: { t1: { state, content } }, notesEntries: { t1: entries } });
	await renderWorkspace(<DocumentsSection item={item} />, { backend });
	return backend;
}

describe("NotesHead in the item detail", () => {
	it("shows the head above the documents and keeps the log folded", async () => {
		await renderHead("current");

		await waitFor(() => expect(screen.getByTestId(ids.notesHeadContent).textContent).toContain("Goal/Status: läuft"));
		expect(screen.queryByTestId(ids.notesHeadWarning)).toBeNull();
		expect(screen.queryByTestId(ids.notesLogEntry(1))).toBeNull();
	});

	it("shows the log entries after a click on the log, newest first, and hides them again", async () => {
		const backend = await renderHead("current");

		expect(backend.calls("GET", "notes/entries")).toHaveLength(0);
		fireEvent.click(screen.getByTestId(ids.notesLogToggle));

		await waitFor(() => expect(screen.getByTestId(ids.notesLogEntry(2))).toBeTruthy());
		const shown = [screen.getByTestId(ids.notesLogEntry(2)), screen.getByTestId(ids.notesLogEntry(1))];
		expect(shown[0]!.compareDocumentPosition(shown[1]!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
		expect(shown[1]!.textContent).toContain("2026-10-01 — Erstes");
		fireEvent.click(screen.getByTestId(ids.notesLogToggle));
		expect(screen.queryByTestId(ids.notesLogEntry(1))).toBeNull();
	});

	it("marks a stale head with a warning symbol and a tooltip text", async () => {
		await renderHead("stale");

		const warning = await screen.findByTestId(ids.notesHeadWarning);
		expect(warning.getAttribute("aria-label")).toContain("nicht aktuell");
	});

	it("marks a missing head and says that none is recorded", async () => {
		await renderHead("missing", "");

		expect((await screen.findByTestId(ids.notesHeadWarning)).getAttribute("aria-label")).toContain("noch keinen Stand");
		expect(screen.getByTestId(ids.notesHeadContent).textContent).toContain("Noch kein Stand eingetragen.");
	});

	it("shows nothing for an item without notes and asks for nothing", async () => {
		const backend = await renderHead("current", HEAD, []);

		expect(screen.queryByTestId(ids.notesHead)).toBeNull();
		expect(backend.calls("GET", "notes/state")).toHaveLength(0);
	});
});

describe("NotesPeek in the list", () => {
	it("is a symbol that turns to the warning state for a stale head", async () => {
		const backend = fakeWorkspaceBackend({ notesStates: { t1: { state: "stale", content: HEAD } } });
		await renderWorkspace(<NotesPeek uid="t1" state="stale" />, { backend });

		expect(screen.getByTestId(ids.notesPeek("t1")).getAttribute("data-state")).toBe("stale");
		expect(backend.calls("GET", "notes/state")).toHaveLength(0);
	});

	it("loads the head on the first look and shows it as the tooltip", async () => {
		const backend = fakeWorkspaceBackend({ notesStates: { t1: { state: "current", content: HEAD } } });
		await renderWorkspace(<NotesPeek uid="t1" state="current" />, { backend });

		fireEvent.mouseOver(screen.getByTestId(ids.notesPeek("t1")));

		await waitFor(() => expect(screen.getByTestId(ids.notesPeekText).textContent).toContain("Next step: weiter"));
		expect(backend.calls("GET", "notes/state")).toHaveLength(1);
	});
});
