import { describe, expect, it } from "vitest";
import { attentionOf, fromInputValue, groupAlarms, heading, notificationBody, toInputValue, waitingFor } from "../../../../../../client/src/plugins/alarms/model";
import { alarm, target } from "../../../../../helpers/client/alarmsFixtures";

/** 18 October 2026, 12:00 local time. */
const NOW = new Date(2026, 9, 18, 12, 0);
const local = (day: number, hour: number) => new Date(2026, 9, day, hour, 0).toISOString();

describe("groupAlarms", () => {
	it("groups by time: due, today, later, and finished last", () => {
		const list = [
			alarm("done", { status: "Done", done_at: local(18, 9) }),
			alarm("later", { at: local(20, 7) }),
			alarm("snoozed", { status: "Snoozed", at: local(1, 7), snoozed_until: local(25, 7) }),
			alarm("tonight", { at: local(18, 20) }),
			alarm("fired", { status: "Due", at: local(17, 7) }),
			alarm("missed", { at: local(18, 11) }),
			alarm("expired", { status: "Expired", done_at: local(18, 10), targets: [target("s", { open: false })] }),
		];

		expect(groupAlarms(list, NOW).map((group) => [group.key, group.alarms.map((entry) => entry.uid)])).toEqual([
			["due", ["fired", "missed"]],
			["today", ["tonight"]],
			["later", ["later", "snoozed"]],
			["done", ["expired", "done"]],
		]);
	});

	it("leaves out empty groups and does not change the list it is given", () => {
		const list = [alarm("b", { at: local(21, 7) }), alarm("a", { at: local(21, 7) })];

		expect(groupAlarms(list, NOW)).toEqual([{ key: "later", alarms: [list[1], list[0]] }]);
		expect(list.map((entry) => entry.uid)).toEqual(["b", "a"]);
	});
});

describe("heading", () => {
	it("is the text, or the title of the first element of a reminder without text", () => {
		expect(heading(alarm("a", { text: "Telefonieren" }))).toBe("Telefonieren");
		expect(heading(alarm("a", { text: "", targets: [target("n10", { title: "Note zehn" }), target("s")] }))).toBe("Note zehn");
		expect(heading(alarm("a", { text: "", target_text: "Misc:MEMO-003" }))).toBe("Misc:MEMO-003");
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
	it("is the heading with the labels of the elements", () => {
		expect(notificationBody(alarm("a", { text: "Anrufen" }))).toBe("Anrufen");
		expect(notificationBody(alarm("a", { text: "Nachfragen", targets: [target("story-001"), target("memo-002")] }))).toBe("Nachfragen (STORY-001, MEMO-002)");
		expect(notificationBody(alarm("a", { text: "", targets: [target("memo-010", { title: "Memo zehn" })] }))).toBe("Memo zehn (MEMO-010)");
	});
});

describe("attentionOf", () => {
	it("is due since it spoke (the snoozed time if snoozed), headed like the list, with its elements", () => {
		const story = target("s1", { label: "STORY-001", title: "Eine Story" });
		const snoozed = alarm("a", { text: "", status: "Snoozed", at: "2026-10-18T07:00:00Z", snoozed_until: "2026-10-18T09:00:00Z", targets: [story] });

		expect(attentionOf(snoozed)).toEqual({ key: "alarms:a", projectUid: "p1", dueSince: "2026-10-18T09:00:00Z", title: "Eine Story", caption: "STORY-001" });
		expect(attentionOf(alarm("b", { text: "Frei" })).caption).toBeUndefined();
	});
});
