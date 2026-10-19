import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { flushUiState } from "../../../../../../client/src/core/ui-state/uiState";
import { AlarmAttention } from "../../../../../../client/src/plugins/alarms/AlarmAttention";
import { CreateAlarm } from "../../../../../../client/src/plugins/alarms/CreateForms";
import { SetAlarm } from "../../../../../../client/src/plugins/alarms/SetAlarm";
import { alarmsTestIds as ids } from "../../../../../../client/src/plugins/alarms/testIds";
import { DetailSections } from "../../../../../../client/src/plugins/workspace/detailSections";
import { NewButton } from "../../../../../../client/src/plugins/workspace/NewButton";
import { ProjectsSection } from "../../../../../../client/src/plugins/workspace/ProjectsSection";
import { workspaceTestIds } from "../../../../../../client/src/plugins/workspace/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { alarm, target as element } from "../../../../../helpers/client/alarmsFixtures";
import { fakeAlarmsBackend } from "../../../../../helpers/client/fakeAlarmsBackend";
import { expectPersisted, project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const target = element("e1", { label: "STORY-001", title: "Eine Story" });

afterEach(cleanup);

describe("AlarmAttention in the bell of the projects section", () => {
	const widgets = [{ ownerId: "alarms", slot: "workspace.attention-sources", name: "due", component: AlarmAttention }];

	it("reports nothing while no alarm has fired", async () => {
		await renderWorkspace(<ProjectsSection />, { backend: fakeAlarmsBackend({ projects, alarms: [alarm("a")] }), widgets });

		await screen.findByTestId(workspaceTestIds.project("p1"));
		await waitFor(() => expect(screen.queryByTestId(workspaceTestIds.attentionBell)).toBeNull());
	});

	it("lists the fired ones, the latest first, with done and snooze", async () => {
		const backend = fakeAlarmsBackend({
			projects,
			alarms: [
				alarm("a", { status: "Due", version: 4, at: "2026-10-18T09:00:00Z", targets: [target] }),
				alarm("b", { status: "Due", at: "2026-10-18T07:00:00Z" }),
				alarm("c"),
			],
		});
		await renderWorkspace(<ProjectsSection />, { backend, widgets });

		fireEvent.click(await screen.findByTestId(workspaceTestIds.attentionBell));
		const first = await screen.findByTestId(workspaceTestIds.attentionItem("alarms:a"));
		expect(first.textContent).toContain("STORY-001");
		fireEvent.click(screen.getByTestId(ids.action("finish", "a")));
		fireEvent.click(screen.getByTestId(workspaceTestIds.attentionToggle("alarms:b")));
		fireEvent.click(screen.getByTestId(ids.action("snooze", "b")));

		await waitFor(() => expect(backend.calls("POST", "alarms/alarms/a/finish")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms/a/finish")[0]!.body).toEqual({ version: 4 });
		await waitFor(() => expect(backend.calls("POST", "alarms/alarms/b/snooze")).toHaveLength(1));
	});

	it("opens a fired alarm in the alarms view", async () => {
		const backend = fakeAlarmsBackend({ projects, alarms: [alarm("a", { status: "Due" })] });
		await renderWorkspace(<ProjectsSection />, { backend, widgets });

		fireEvent.click(await screen.findByTestId(workspaceTestIds.attentionBell));
		fireEvent.click(await screen.findByTestId(workspaceTestIds.attentionOpen("alarms:a")));

		await expectPersisted(backend, flushUiState, waitFor, { selected: "a" }, "alarms");
	});
});

describe("SetAlarm in the detail panel of an element", () => {
	const widgets = [{ ownerId: "alarms", slot: "workspace.detail-sections", name: "set-alarm", component: SetAlarm }];
	const renderPanel = async (alarms = [alarm("mine", { targets: [target] }), alarm("done", { targets: [target], status: "Done" }), alarm("other")]) => {
		const backend = fakeAlarmsBackend({ projects, alarms });
		await renderWorkspace(<DetailSections uid="e1" label="STORY-001" projectUid="p1" />, { backend, widgets });
		return backend;
	};

	it("lists the waiting reminders of the element", async () => {
		await renderPanel();

		expect((await screen.findByTestId(ids.elementAlarm("mine"))).textContent).toContain("Wecker mine");
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
			fields: { text: "Nachfragen", at: new Date("2026-10-30T09:00").toISOString(), targets: ["e1"] },
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
