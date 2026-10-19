import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { coreTestIds } from "../../../../../../client/src/core";
import AlarmsPage from "../../../../../../client/src/plugins/alarms/pages/AlarmsPage";
import { useShownElement } from "../../../../../../client/src/plugins/workspace/shownElement";
import { alarmsTestIds as ids } from "../../../../../../client/src/plugins/alarms/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { alarm, target } from "../../../../../helpers/client/alarmsFixtures";
import { fakeAlarmsBackend } from "../../../../../helpers/client/fakeAlarmsBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const story = target("s1", { label: "STORY-001", title: "Eine Story" });
const note = target("n1", { label: "NOTE-001", title: "Eine Note", kind: "note", open: false });
const alarms = [
	alarm("wait", { at: "2026-10-22T07:00:00Z", targets: [story] }),
	alarm("fired", { status: "Due", version: 3 }),
	alarm("snoozed", { status: "Snoozed", snoozed_until: "2026-10-25T07:00:00Z" }),
	alarm("done", { status: "Done", version: 2, done_at: "2026-10-18T09:00:00Z", purge_at: "2026-10-19T09:00:00Z" }),
	alarm("foreign", { target_text: "Misc:NOTE-003", at: "2026-10-23T07:00:00Z" }),
	alarm("other", { project_uid: "p0" }),
	alarm("multi", { text: "Sachen nachfragen", at: "2026-10-24T07:00:00Z", targets: [story, note] }),
	alarm("about", { text: "", at: "2026-10-24T08:00:00Z", targets: [story] }),
];

beforeEach(() => {
	vi.useFakeTimers({ toFake: ["Date"] });
	vi.setSystemTime(new Date(2026, 9, 18, 12, 0));
});

afterEach(() => {
	cleanup();
	vi.useRealTimers();
});

/** The detail views of a test plugin (`workspace.element-detail`): show which element they got. */
function StoryView() {
	const { uid } = useShownElement();
	return <p data-testid="test.story-view">{`Story ${uid}`}</p>;
}

function NoteView() {
	const { uid } = useShownElement();
	return <p data-testid="test.note-view">{`Note ${uid}`}</p>;
}

async function renderPage(options: Parameters<typeof fakeAlarmsBackend>[0] = {}) {
	const backend = fakeAlarmsBackend({ projects, alarms, ...options });
	await renderWorkspace(<AlarmsPage />, {
		backend,
		widgets: [
			{ ownerId: "backlog", slot: "workspace.element-detail", name: "story", component: StoryView },
			{ ownerId: "notes", slot: "workspace.element-detail", name: "note", component: NoteView },
		],
	});
	return backend;
}

const rowsOf = (key: string) => within(screen.getByTestId(ids.group(key))).queryAllByTestId(/^alarms\.row\./).map((row) => row.getAttribute("data-testid"));

const series = alarm("series", { status: "Due", at: "2026-10-18T09:00:00Z", repeat: "weekly", series_from: "2026-09-20T09:00:00Z", missed: 3 });

describe("AlarmsPage: series alarms", () => {
	it("marks a series alarm with its repetition and the count of missed terms, others with nothing", async () => {
		await renderPage({ alarms: [...alarms, series] });
		await screen.findByTestId(ids.row("series"));

		expect(screen.getByTestId(ids.repeat("series")).getAttribute("aria-label")).toBe("Wiederholung: Wöchentlich");
		expect(screen.getByTestId(ids.missed("series")).textContent).toBe("3 verpasst");
		expect(screen.queryByTestId(ids.repeat("wait"))).toBeNull();
		expect(screen.queryByTestId(ids.missed("wait"))).toBeNull();
	});

	it("shows no counter when nothing was missed", async () => {
		await renderPage({ alarms: [alarm("daily", { repeat: "daily", series_from: "2026-10-18T09:00:00Z" })] });
		await screen.findByTestId(ids.row("daily"));

		expect(screen.getByTestId(ids.repeat("daily"))).toBeTruthy();
		expect(screen.queryByTestId(ids.missed("daily"))).toBeNull();
	});

	it("offers finish but never undo, and names repetition and missed terms in the detail bar", async () => {
		await renderPage({ alarms: [...alarms, series] });
		await screen.findByTestId(ids.row("series"));

		expect(screen.getByTestId(ids.action("finish", "series"))).toBeTruthy();
		expect(screen.queryByTestId(ids.action("reopen", "series"))).toBeNull();
		fireEvent.click(screen.getByTestId(ids.row("series")));
		const detail = await screen.findByTestId(ids.detail);
		expect(detail.textContent).toContain("Wöchentlich");
		expect(detail.textContent).toContain("3 verpasst");
	});

	it("sets a series alarm and sends the repetition only when there is one", async () => {
		const backend = await renderPage({ documents: { workspace: { marked: "p1" } } });
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByText("Neuer Wecker"));
		fireEvent.change(await screen.findByTestId(ids.formField("text")), { target: { value: "Montag" } });
		fireEvent.change(screen.getByTestId(ids.formField("at")), { target: { value: "2026-10-30T09:00" } });
		expect((screen.getByTestId(ids.formField("repeat")) as HTMLSelectElement).value).toBe("none");
		fireEvent.change(screen.getByTestId(ids.formField("repeat")), { target: { value: "weekly" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms")[0]!.body).toEqual({
			project: "p1",
			fields: { text: "Montag", at: new Date("2026-10-30T09:00").toISOString(), targets: [], repeat: "weekly" },
		});
	});

	it("shows the repetition when editing and switches it off", async () => {
		const backend = await renderPage({ alarms: [series] });
		await screen.findByTestId(ids.row("series"));

		fireEvent.click(screen.getByTestId(ids.action("edit", "series")));
		const field = (await screen.findByTestId(ids.formField("repeat"))) as HTMLSelectElement;
		expect(field.value).toBe("weekly");
		fireEvent.change(field, { target: { value: "none" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("PUT", "alarms/alarms/series")).toHaveLength(1));
		expect(backend.calls("PUT", "alarms/alarms/series")[0]!.body).toEqual({ version: 1, fields: { repeat: "none" } });
	});
});

describe("AlarmsPage: the list", () => {
	it("groups the reminders of the shown projects by time, finished ones last", async () => {
		await renderPage();
		await screen.findByTestId(ids.row("fired"));

		expect(rowsOf("due")).toEqual([ids.row("fired")]);
		expect(rowsOf("later")).toEqual([ids.row("other"), ids.row("wait"), ids.row("foreign"), ids.row("multi"), ids.row("about"), ids.row("snoozed")]);
		expect(rowsOf("done")).toEqual([ids.row("done")]);
		expect(screen.queryByTestId(ids.group("today"))).toBeNull();
	});

	it("shows the heading without label and the elements as chips, closed ones greyed out", async () => {
		await renderPage();
		await screen.findByTestId(ids.row("multi"));

		expect(screen.getByTestId(ids.row("multi")).textContent).not.toContain("MULTI");
		expect(screen.getByTestId(ids.text("multi")).textContent).toBe("Sachen nachfragen");
		expect(screen.getByTestId(ids.text("about")).textContent).toBe("Eine Story");
		expect(screen.getByTestId(ids.targetChip("multi", "s1")).getAttribute("data-open")).toBe("true");
		expect(screen.getByTestId(ids.targetChip("multi", "n1")).getAttribute("data-open")).toBe("false");
		expect(screen.getByTestId(ids.row("done")).textContent).toContain("verschwindet");
	});

	it("shows only the projects that are switched on", async () => {
		await renderPage({ documents: { workspace: { hidden: ["p0"] } } });

		await screen.findByTestId(ids.row("wait"));
		expect(screen.queryByTestId(ids.row("other"))).toBeNull();
	});

	it("says so when there are none", async () => {
		await renderPage({ alarms: [] });

		expect((await screen.findByTestId(ids.empty)).textContent).toContain("Keine Wecker");
	});

	it("expands and collapses the full heading of a row without opening its detail", async () => {
		await renderPage();
		const toggle = await screen.findByTestId(ids.action("expand", "wait"));
		expect(toggle.getAttribute("aria-expanded")).toBe("false");

		fireEvent.click(toggle);
		expect(screen.getByTestId(ids.action("expand", "wait")).getAttribute("aria-expanded")).toBe("true");
		expect(screen.queryByTestId(ids.detail)).toBeNull();
	});
});

describe("AlarmsPage: the detail of a reminder", () => {
	it("shows the reminder bar and the one element it reminds of", async () => {
		await renderPage();
		fireEvent.click(await screen.findByTestId(ids.row("wait")));

		const detail = await screen.findByTestId(ids.detail);
		expect(within(detail).getByTestId(sharedTestIds.detailTitle).textContent).toBe("Wecker wait");
		expect(within(detail).getByTestId("test.story-view").textContent).toBe("Story s1");
		expect(within(detail).queryByTestId(ids.targetCard("s1"))).toBeNull();
		expect(screen.getByTestId(coreTestIds.detail).contains(detail)).toBe(true);
		expect(screen.getByTestId(ids.row("wait")).getAttribute("aria-selected")).toBe("true");
	});

	it("opens the reminder chosen elsewhere (UI state `alarms.selected`, e.g. from the bell)", async () => {
		await renderPage({ documents: { alarms: { selected: "wait" } } });

		const detail = await screen.findByTestId(ids.detail);
		expect(within(detail).getByTestId(sharedTestIds.detailTitle).textContent).toBe("Wecker wait");
	});

	it("names only the time when the element itself is the heading", async () => {
		await renderPage();
		fireEvent.click(await screen.findByTestId(ids.row("about")));

		const detail = await screen.findByTestId(ids.detail);
		expect(within(detail).getByTestId(sharedTestIds.detailTitle).textContent).toMatch(/^⏰ /);
		expect(within(detail).getByTestId("test.story-view")).toBeTruthy();
	});

	it("switches between several elements with cards, the first open", async () => {
		await renderPage();
		fireEvent.click(await screen.findByTestId(ids.row("multi")));

		const detail = await screen.findByTestId(ids.detail);
		expect(within(detail).getByTestId(ids.targetCard("s1")).getAttribute("aria-pressed")).toBe("true");
		expect(within(detail).getByTestId(ids.targetCard("n1")).getAttribute("data-open")).toBe("false");
		expect(within(detail).getByTestId("test.story-view")).toBeTruthy();

		fireEvent.click(within(detail).getByTestId(ids.targetCard("n1")));
		expect((await within(detail).findByTestId("test.note-view")).textContent).toBe("Note n1");
		expect(within(detail).queryByTestId("test.story-view")).toBeNull();
	});

	it("shows a free reminder as the bar alone and an element in the trash as a hint", async () => {
		await renderPage({ alarms: [...alarms, alarm("gone", { targets: [target("x", { deleted: true, open: false })] })] });
		fireEvent.click(await screen.findByTestId(ids.row("fired")));
		const free = await screen.findByTestId(ids.detail);
		expect(within(free).getByTestId(sharedTestIds.detailTitle).textContent).toBe("Wecker fired");
		expect(within(free).queryByTestId("test.story-view")).toBeNull();

		fireEvent.click(screen.getByTestId(ids.row("gone")));
		await waitFor(() => expect(screen.getByTestId(ids.detail).textContent).toContain("liegt im Papierkorb"));
	});

	it("closes the detail with its close button and with a second click on the row", async () => {
		await renderPage();
		fireEvent.click(await screen.findByTestId(ids.row("wait")));
		fireEvent.click(within(await screen.findByTestId(ids.detail)).getByTestId(sharedTestIds.detailAction("close")));
		await waitFor(() => expect(screen.queryByTestId(ids.detail)).toBeNull());

		fireEvent.click(screen.getByTestId(ids.row("wait")));
		await screen.findByTestId(ids.detail);
		fireEvent.click(screen.getByTestId(ids.row("wait")));
		await waitFor(() => expect(screen.queryByTestId(ids.detail)).toBeNull());
	});

	it("finishes and snoozes from the bar of the detail, with the version", async () => {
		const backend = await renderPage();
		fireEvent.click(await screen.findByTestId(ids.row("wait")));
		const detail = await screen.findByTestId(ids.detail);

		fireEvent.click(within(detail).getByTestId(sharedTestIds.detailAction("snooze")));
		fireEvent.click(within(detail).getByTestId(sharedTestIds.detailAction("finish")));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms/wait/finish")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms/wait/snooze")[0]!.body).toEqual({ version: 1 });
	});
});

describe("AlarmsPage: actions", () => {
	it("does not open the detail when an action of the row is clicked", async () => {
		const backend = await renderPage();
		fireEvent.click(await screen.findByTestId(ids.action("snooze", "wait")));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms/wait/snooze")).toHaveLength(1));
		expect(screen.queryByTestId(ids.detail)).toBeNull();
	});

	it("shows the actions of a row as icons named by their tooltip", async () => {
		await renderPage();
		await screen.findByTestId(ids.row("wait"));

		expect(screen.getByTestId(ids.action("edit", "wait")).getAttribute("aria-label")).toBe("Bearbeiten");
		expect(screen.getByTestId(ids.action("snooze", "wait")).getAttribute("aria-label")).toBe("Zurückstellen");
		expect(screen.getByTestId(ids.action("finish", "wait")).getAttribute("aria-label")).toBe("Erledigt");
		expect(screen.getByTestId(ids.action("finish", "wait")).textContent).toBe("");
	});

	it("offers only undo for a finished reminder and sends it with the version", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.row("done"));

		expect(screen.queryByTestId(ids.action("finish", "done"))).toBeNull();
		fireEvent.click(screen.getByTestId(ids.action("reopen", "done")));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms/done/reopen")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms/done/reopen")[0]!.body).toEqual({ version: 2 });
	});

	it.each([
		["snooze", "snooze"],
		["finish", "finish"],
	])("sends %s with the version", async (action, path) => {
		const backend = await renderPage();
		await screen.findByTestId(ids.row("fired"));

		fireEvent.click(screen.getByTestId(ids.action(action, "fired")));

		await waitFor(() => expect(backend.calls("POST", `alarms/alarms/fired/${path}`)).toHaveLength(1));
		expect(backend.calls("POST", `alarms/alarms/fired/${path}`)[0]!.body).toEqual({ version: 3 });
	});

	it("shows the message of the server when an action is refused", async () => {
		await renderPage({
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/finish") ? Response.json({ code: "alarm_done", message: "ALARM ist schon erledigt", details: {} }, { status: 400 }) : undefined,
		});
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByTestId(ids.action("finish", "wait")));

		expect(await screen.findByText("ALARM ist schon erledigt")).toBeTruthy();
	});
});

describe("AlarmsPage: the form", () => {
	it("sets a new reminder in the marked project", async () => {
		const backend = await renderPage({ documents: { workspace: { marked: "p1" } } });
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByText("Neuer Wecker"));
		fireEvent.change(await screen.findByTestId(ids.formField("text")), { target: { value: "Neu" } });
		fireEvent.change(screen.getByTestId(ids.formField("at")), { target: { value: "2026-10-30T09:00" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms")[0]!.body).toEqual({
			project: "p1",
			fields: { text: "Neu", at: new Date("2026-10-30T09:00").toISOString(), targets: [] },
		});
	});

	it("needs a time, and a text when no element is chosen", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByText("Neuer Wecker"));
		fireEvent.change(await screen.findByTestId(ids.formField("text")), { target: { value: "Ohne Zeit" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		expect(await screen.findByText("Ein Zeitpunkt fehlt.")).toBeTruthy();

		fireEvent.change(screen.getByTestId(ids.formField("text")), { target: { value: " " } });
		fireEvent.change(screen.getByTestId(ids.formField("at")), { target: { value: "2026-10-30T09:00" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		expect(await screen.findByText("Ein Text oder mindestens ein Element fehlt.")).toBeTruthy();
		expect(backend.calls("POST", "alarms/alarms")).toHaveLength(0);
	});

	it("edits a reminder and sends only what changed", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByTestId(ids.action("edit", "wait")));
		const dialog = await screen.findByTestId(ids.formDialog);
		expect((within(dialog).getByTestId(ids.formField("text")) as HTMLInputElement).value).toBe("Wecker wait");
		fireEvent.change(within(dialog).getByTestId(ids.formField("text")), { target: { value: "Anders" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("PUT", "alarms/alarms/wait")).toHaveLength(1));
		expect(backend.calls("PUT", "alarms/alarms/wait")[0]!.body).toEqual({ version: 1, fields: { text: "Anders" } });
	});

	it("changes the time of a reminder", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByTestId(ids.action("edit", "wait")));
		fireEvent.change(await screen.findByTestId(ids.formField("at")), { target: { value: "2026-11-01T10:00" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("PUT", "alarms/alarms/wait")).toHaveLength(1));
		expect(backend.calls("PUT", "alarms/alarms/wait")[0]!.body).toEqual({ version: 1, fields: { at: new Date("2026-11-01T10:00").toISOString() } });
	});

	it("offers the current state when the reminder was changed meanwhile", async () => {
		await renderPage({
			respond: ({ method, path }) =>
				method === "PUT" && path === "alarms/alarms/wait" ? Response.json({ code: "version_conflict", message: "Version", details: {} }, { status: 409 }) : undefined,
		});
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByTestId(ids.action("edit", "wait")));
		fireEvent.change(await screen.findByTestId(ids.formField("text")), { target: { value: "Anders" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		expect(await screen.findByTestId(sharedTestIds.editFormConflict)).toBeTruthy();
	});
});
