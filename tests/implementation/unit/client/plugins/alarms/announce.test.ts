import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { alarmsApi } from "../../../../../../client/src/plugins/alarms/api";
import { canNotify, onAlarmsDue } from "../../../../../../client/src/plugins/alarms/announce";
import { banners } from "../../../../../../client/src/core";
import { alarm } from "../../../../../helpers/client/alarmsFixtures";
import { fakeAlarmsBackend } from "../../../../../helpers/client/fakeAlarmsBackend";

const fired = [alarm("a1", { status: "Due", text: "Anrufen", version: 2, target: { uid: "s", label: "STORY-001", title: "T", kind: "story", deleted: false } }), alarm("a2", { status: "Due" })];

function context(backend: ReturnType<typeof fakeAlarmsBackend>) {
	return { dispatch: backend.store.dispatch as never, api: alarmsApi as never };
}

async function bannersShown(count: number) {
	await vi.waitFor(() => expect(banners.getSnapshot()).toHaveLength(count));
	return banners.getSnapshot();
}

beforeEach(() => banners.clear());
afterEach(() => {
	banners.clear();
	vi.unstubAllGlobals();
});

describe("onAlarmsDue", () => {
	it("shows a banner for each alarm that fired, with the text and the target", async () => {
		const backend = fakeAlarmsBackend({ alarms: [...fired, alarm("quiet")] });

		onAlarmsDue({ uids: ["a1", "a2"] }, context(backend));

		const shown = await bannersShown(2);
		expect(shown.map((entry) => entry.request.message)).toEqual(["Anrufen (STORY-001)", "Wecker a2"]);
		expect(shown[0]!.request.severity).toBe("warning");
	});

	it("shows only the alarms the event names", async () => {
		const backend = fakeAlarmsBackend({ alarms: fired });

		onAlarmsDue({ uids: ["a2"] }, context(backend));

		expect((await bannersShown(1))[0]!.request.message).toBe("Wecker a2");
	});

	it("does nothing without alarms in the event", async () => {
		const backend = fakeAlarmsBackend({ alarms: fired });

		onAlarmsDue({ uids: [] }, context(backend));
		onAlarmsDue(undefined, context(backend));

		await new Promise((resolve) => setTimeout(resolve, 20));
		expect(banners.getSnapshot()).toHaveLength(0);
		expect(backend.calls("GET", "alarms/alarms")).toHaveLength(0);
	});

	it("finishes and snoozes with the version from the banner", async () => {
		const backend = fakeAlarmsBackend({ alarms: fired });
		onAlarmsDue({ uids: ["a1"] }, context(backend));
		const [banner] = await bannersShown(1);

		await banner!.request.actions![0]!.onClick(banner!.handle);
		await banner!.request.actions![1]!.onClick(banner!.handle);

		await vi.waitFor(() => expect(backend.calls("POST", "alarms/alarms/a1/finish")).toHaveLength(1));
		expect(backend.calls("POST", "alarms/alarms/a1/finish")[0]!.body).toEqual({ version: 2 });
		await vi.waitFor(() => expect(backend.calls("POST", "alarms/alarms/a1/snooze")).toHaveLength(1));
	});

	it("shows a browser notification when the user allowed them", async () => {
		const made: Array<{ title: string; options: { body: string; tag: string } }> = [];
		class FakeNotification {
			static permission = "granted";
			constructor(title: string, options: { body: string; tag: string }) {
				made.push({ title, options });
			}
		}
		vi.stubGlobal("Notification", FakeNotification);
		const backend = fakeAlarmsBackend({ alarms: fired });

		onAlarmsDue({ uids: ["a1"] }, context(backend));

		await vi.waitFor(() => expect(made).toHaveLength(1));
		expect(made[0]!.options).toEqual({ body: "Anrufen (STORY-001)", tag: "a1" });
	});

	it("shows no notification without permission", async () => {
		class FakeNotification {
			static permission = "default";
			constructor() {
				throw new Error("must not be created");
			}
		}
		vi.stubGlobal("Notification", FakeNotification);
		const backend = fakeAlarmsBackend({ alarms: fired });

		onAlarmsDue({ uids: ["a1"] }, context(backend));

		await bannersShown(1);
		expect(canNotify()).toBe(false);
	});
});
