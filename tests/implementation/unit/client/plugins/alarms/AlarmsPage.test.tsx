import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import AlarmsPage from "../../../../../../client/src/plugins/alarms/pages/AlarmsPage";
import { alarmsTestIds as ids } from "../../../../../../client/src/plugins/alarms/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { alarm } from "../../../../../helpers/client/alarmsFixtures";
import { fakeAlarmsBackend } from "../../../../../helpers/client/fakeAlarmsBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const target = { uid: "s1", label: "STORY-001", title: "Eine Story", kind: "story", deleted: false };
const alarms = [
	alarm("wait", { at: "2026-10-22T07:00:00Z", target }),
	alarm("fired", { status: "Due", version: 3 }),
	alarm("snoozed", { status: "Snoozed", snoozed_until: "2026-10-25T07:00:00Z" }),
	alarm("done", { status: "Done" }),
	alarm("foreign", { target_text: "Misc:NOTE-003", at: "2026-10-23T07:00:00Z" }),
	alarm("other", { project_uid: "p0" }),
];

afterEach(cleanup);

async function renderPage(options: Parameters<typeof fakeAlarmsBackend>[0] = {}) {
	const backend = fakeAlarmsBackend({ projects, alarms, ...options });
	await renderWorkspace(<AlarmsPage />, { backend });
	return backend;
}

describe("AlarmsPage", () => {
	it("lists the alarms of the shown projects, fired ones first, with status, time and target", async () => {
		await renderPage();

		await screen.findByTestId(ids.row("fired"));
		const rows = screen.getAllByTestId(/^alarms\.row\./).map((row) => row.getAttribute("data-testid"));
		expect(rows).toEqual([ids.row("fired"), ids.row("other"), ids.row("wait"), ids.row("foreign"), ids.row("snoozed"), ids.row("done")]);
		expect(screen.getByTestId(ids.row("fired")).textContent).toContain("Gemeldet");
		expect(screen.getByTestId(ids.row("wait")).textContent).toContain("STORY-001 — Eine Story");
		expect(screen.getByTestId(ids.row("foreign")).textContent).toContain("Misc:NOTE-003");
		expect(screen.getByTestId(ids.row("snoozed")).textContent).toContain("Zurückgestellt");
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

	it("offers no actions for a finished alarm", async () => {
		await renderPage();
		await screen.findByTestId(ids.row("done"));

		expect(screen.queryByTestId(ids.action("finish", "done"))).toBeNull();
		expect(screen.getByTestId(ids.action("finish", "wait"))).toBeTruthy();
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

	it("sets a new alarm in the marked project", async () => {
		const backend = await renderPage({ documents: { workspace: { marked: "p1" } } });
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByText("Neuer Wecker"));
		fireEvent.change(await screen.findByTestId(ids.formField("text")), { target: { value: "Neu" } });
		fireEvent.change(screen.getByTestId(ids.formField("at")), { target: { value: "2026-10-30T09:00" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms")[0]!.body).toEqual({
			project: "p1",
			fields: { text: "Neu", at: new Date("2026-10-30T09:00").toISOString() },
		});
	});

	it("needs a time to save", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByText("Neuer Wecker"));
		fireEvent.change(await screen.findByTestId(ids.formField("text")), { target: { value: "Ohne Zeit" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		expect(await screen.findByText("Ein Zeitpunkt fehlt.")).toBeTruthy();
		expect(backend.calls("POST", "alarms/alarms")).toHaveLength(0);
	});

	it("edits an alarm and sends only what changed", async () => {
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

	it("changes the time of an alarm", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.row("wait"));

		fireEvent.click(screen.getByTestId(ids.action("edit", "wait")));
		fireEvent.change(await screen.findByTestId(ids.formField("at")), { target: { value: "2026-11-01T10:00" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("PUT", "alarms/alarms/wait")).toHaveLength(1));
		expect(backend.calls("PUT", "alarms/alarms/wait")[0]!.body).toEqual({ version: 1, fields: { at: new Date("2026-11-01T10:00").toISOString() } });
	});

	it("offers the current state when the alarm was changed meanwhile", async () => {
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
