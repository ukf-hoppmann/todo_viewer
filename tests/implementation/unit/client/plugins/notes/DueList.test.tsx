import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DueCounter } from "../../../../../../client/src/plugins/notes/DueCounter";
import { notesTestIds as ids } from "../../../../../../client/src/plugins/notes/testIds";
import { fakeNotesBackend } from "../../../../../helpers/client/fakeNotesBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { dueNote } from "../../../../../helpers/client/notesFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true })];
const notice = { uid: "x1", kind: "item_completed", created_at: "2026-10-17T00:00:00Z", source: null, decisions: ["keep", "detach", "drop", "promote"] };
const due = {
	count: 4,
	notes: [
		dueNote("a", { reason: "review_expired", version: 2, path: ["Oben", "Unten"] }),
		dueNote("b", { reason: "trigger" }),
		dueNote("c", { reason: "notice", version: 5, notices: [notice] }),
		dueNote("d", { reason: "topic_due" }),
	],
};

afterEach(cleanup);

async function renderOpen() {
	const backend = fakeNotesBackend({ projects, due });
	await renderWorkspace(<DueCounter />, { backend });
	fireEvent.click(await screen.findByTestId(ids.dueCounter));
	await screen.findByTestId(ids.dueList);
	return backend;
}

describe("the due list behind the counter", () => {
	it("groups the notes by the reason in a fixed order", async () => {
		await renderOpen();

		const groups = screen.getAllByTestId(/^notes\.due-group\./).map((group) => group.getAttribute("data-testid"));
		expect(groups).toEqual([ids.dueGroup("trigger"), ids.dueGroup("notice"), ids.dueGroup("topic_due"), ids.dueGroup("review_expired")]);
		expect(screen.getByTestId(ids.dueGroup("trigger")).textContent).toContain("Auslöser");
		expect(screen.getByTestId(ids.dueGroup("notice")).textContent).toContain("Hinweis");
		expect(screen.getByTestId(ids.dueGroup("topic_due")).textContent).toContain("Termin");
		expect(screen.getByTestId(ids.dueGroup("review_expired")).textContent).toContain("Prüfung");
	});

	it("names the topic path of a note", async () => {
		await renderOpen();

		expect(screen.getByTestId(ids.dueItem("a")).textContent).toContain("Oben › Unten");
	});

	it.each([
		["keep", "keep", { version: 2 }],
		["snooze", "snooze", { version: 2 }],
		["done", "finish", { version: 2, status: "done" }],
		["dropped", "finish", { version: 2, status: "dropped" }],
	])("offers %s for a note due by review and sends it with the version", async (action, path, body) => {
		const backend = await renderOpen();

		fireEvent.click(screen.getByTestId(ids.dueAction(action, "a")));

		await waitFor(() => expect(backend.calls("POST", `notes/notes/a/${path}`)).toHaveLength(1));
		expect(backend.calls("POST", `notes/notes/a/${path}`)[0]!.body).toEqual(body);
	});

	it("offers the decisions of the notice instead, except promote that needs fields", async () => {
		const backend = await renderOpen();

		expect(screen.queryByTestId(ids.dueAction("done", "c"))).toBeNull();
		expect(screen.queryByTestId(ids.dueAction("promote", "c"))).toBeNull();
		fireEvent.click(screen.getByTestId(ids.dueAction("detach", "c")));

		await waitFor(() => expect(backend.calls("POST", "notes/notices/x1/decide")).toHaveLength(1));
		expect(backend.calls("POST", "notes/notices/x1/decide")[0]!.body).toEqual({ decision: "detach", version: 5 });
	});
});
