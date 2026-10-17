import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { AlarmCounter } from "../../../../../../client/src/plugins/alarms/AlarmCounter";
import { CreateAlarm } from "../../../../../../client/src/plugins/alarms/CreateForms";
import { SetAlarm } from "../../../../../../client/src/plugins/alarms/SetAlarm";
import { alarmsTestIds as ids } from "../../../../../../client/src/plugins/alarms/testIds";
import { DetailSections } from "../../../../../../client/src/plugins/workspace/detailSections";
import { NewButton } from "../../../../../../client/src/plugins/workspace/NewButton";
import { workspaceTestIds } from "../../../../../../client/src/plugins/workspace/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { alarm } from "../../../../../helpers/client/alarmsFixtures";
import { fakeAlarmsBackend } from "../../../../../helpers/client/fakeAlarmsBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const target = { uid: "e1", label: "STORY-001", title: "Eine Story", kind: "story", deleted: false };

afterEach(cleanup);

describe("AlarmCounter", () => {
	it("shows nothing while no alarm has fired", async () => {
		await renderWorkspace(<AlarmCounter />, { backend: fakeAlarmsBackend({ projects, alarms: [alarm("a")] }) });

		await waitFor(() => expect(screen.queryByTestId(ids.counter)).toBeNull());
	});

	it("shows how many have fired and lists them with done and snooze", async () => {
		const backend = fakeAlarmsBackend({
			projects,
			alarms: [alarm("a", { status: "Due", version: 4, target }), alarm("b", { status: "Due" }), alarm("c")],
		});
		await renderWorkspace(<AlarmCounter />, { backend });

		const counter = await screen.findByTestId(ids.counter);
		expect(counter.textContent).toBe("⏰2");
		expect(counter.getAttribute("aria-label")).toBe("2 Wecker haben sich gemeldet");
		fireEvent.click(counter);
		expect((await screen.findByTestId(ids.dueItem("a"))).textContent).toContain("STORY-001");
		fireEvent.click(screen.getByTestId(ids.action("finish", "a")));
		fireEvent.click(screen.getByTestId(ids.action("snooze", "b")));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms/a/finish")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms/a/finish")[0]!.body).toEqual({ version: 4 });
		await waitFor(() => expect(backend.calls("POST", "alarms/alarms/b/snooze")).toHaveLength(1));
	});
});

describe("SetAlarm in the detail panel of an element", () => {
	const widgets = [{ ownerId: "alarms", slot: "workspace.detail-sections", name: "set-alarm", component: SetAlarm }];
	const renderPanel = async (alarms = [alarm("mine", { target }), alarm("done", { target, status: "Done" }), alarm("other")]) => {
		const backend = fakeAlarmsBackend({ projects, alarms });
		await renderWorkspace(<DetailSections uid="e1" label="STORY-001" projectUid="p1" />, { backend, widgets });
		return backend;
	};

	it("lists the open alarms bound to the element", async () => {
		await renderPanel();

		expect((await screen.findByTestId(ids.elementAlarm("mine"))).textContent).toContain("ALARM — Wecker mine".replace("ALARM", "MINE"));
		expect(screen.queryByTestId(ids.elementAlarm("done"))).toBeNull();
		expect(screen.queryByTestId(ids.elementAlarm("other"))).toBeNull();
	});

	it("sets an alarm for the element", async () => {
		const backend = await renderPanel([]);

		fireEvent.click(await screen.findByTestId(ids.setAlarmButton));
		const dialog = await screen.findByTestId(ids.formDialog);
		expect(dialog.textContent).toContain("Wecker für STORY-001");
		fireEvent.change(screen.getByTestId(ids.formField("text")), { target: { value: "Nachfragen" } });
		fireEvent.change(screen.getByTestId(ids.formField("at")), { target: { value: "2026-10-30T09:00" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms")[0]!.body).toEqual({
			project: "p1",
			fields: { text: "Nachfragen", at: new Date("2026-10-30T09:00").toISOString(), target: "e1" },
		});
	});

	it("renders nothing when no plugin hangs a widget into the slot", async () => {
		await renderWorkspace(<DetailSections uid="e1" label="STORY-001" projectUid="p1" />, { backend: fakeAlarmsBackend({ projects }) });

		expect(screen.queryByTestId("workspace.detail-sections")).toBeNull();
	});
});

describe("the form in the dialog '＋ New'", () => {
	it("sets an alarm in the built-in project by default", async () => {
		const backend = fakeAlarmsBackend({ projects });
		await renderWorkspace(<NewButton />, { backend, createTypes: [{ ownerId: "alarms", name: "alarm", title: "Neuer Wecker", form: CreateAlarm }] });
		await waitFor(() => expect(screen.getByTestId(workspaceTestIds.newButton)).toBeTruthy());

		fireEvent.click(screen.getByTestId(workspaceTestIds.newButton));
		fireEvent.click(await screen.findByTestId(workspaceTestIds.newMenuItem("alarm")));
		await waitFor(() => expect(screen.getByTestId(ids.formField("text"))).toBeTruthy());
		fireEvent.change(screen.getByTestId(ids.formField("text")), { target: { value: "Aus dem Menü" } });
		fireEvent.change(screen.getByTestId(ids.formField("at")), { target: { value: "2026-10-30T09:00" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms")[0]!.body).toMatchObject({ project: "p0", fields: { text: "Aus dem Menü" } });
	});
});
