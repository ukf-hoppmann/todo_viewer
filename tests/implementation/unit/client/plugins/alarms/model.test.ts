import { describe, expect, it } from "vitest";
import { fromInputValue, notificationBody, sortAlarms, toInputValue, waitingFor } from "../../../../../../client/src/plugins/alarms/model";
import { alarm } from "../../../../../helpers/client/alarmsFixtures";

describe("sortAlarms", () => {
	it("puts fired alarms first, then waiting, snoozed and done ones, each by time", () => {
		const list = [
			alarm("done", { status: "Done" }),
			alarm("later", { at: "2026-10-22T07:00:00Z" }),
			alarm("snoozed", { status: "Snoozed", at: "2026-10-01T07:00:00Z", snoozed_until: "2026-10-25T07:00:00Z" }),
			alarm("soon", { at: "2026-10-21T07:00:00Z" }),
			alarm("due", { status: "Due" }),
		];

		expect(sortAlarms(list).map((entry) => entry.uid)).toEqual(["due", "soon", "later", "snoozed", "done"]);
	});

	it("does not change the list it is given and breaks ties by label", () => {
		const list = [alarm("b"), alarm("a")];

		expect(sortAlarms(list).map((entry) => entry.uid)).toEqual(["a", "b"]);
		expect(list.map((entry) => entry.uid)).toEqual(["b", "a"]);
	});
});

describe("waitingFor", () => {
	it("is the time, or the snoozed time of a snoozed alarm", () => {
		expect(waitingFor(alarm("a", { at: "2026-10-20T07:00:00Z" }))).toBe("2026-10-20T07:00:00Z");
		expect(waitingFor(alarm("a", { status: "Snoozed", snoozed_until: "2026-10-21T07:00:00Z" }))).toBe("2026-10-21T07:00:00Z");
		expect(waitingFor(alarm("a", { status: "Snoozed", snoozed_until: null }))).toBe("2026-10-20T07:00:00Z");
	});
});

describe("time inputs", () => {
	it("round-trips the local time of the input through ISO", () => {
		expect(toInputValue(fromInputValue("2026-10-20T09:30")!)).toBe("2026-10-20T09:30");
		expect(fromInputValue("2026-10-20T09:30")).toBe(new Date("2026-10-20T09:30").toISOString());
	});

	it("has no value for an empty or invalid input", () => {
		expect(fromInputValue("")).toBeUndefined();
		expect(fromInputValue("morgen")).toBeUndefined();
	});
});

describe("notificationBody", () => {
	it("names the target of the alarm", () => {
		expect(notificationBody({ text: "Anrufen", target: null })).toBe("Anrufen");
		expect(notificationBody({ text: "Anrufen", target: { uid: "u", label: "STORY-001", title: "T", kind: "story", deleted: false } })).toBe("Anrufen (STORY-001)");
	});
});
