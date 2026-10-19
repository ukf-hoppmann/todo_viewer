import { describe, expect, it } from "vitest";
import { attentionFor, sortAttention, type AttentionEntry } from "../../../../../../client/src/plugins/workspace/attention";

const entry = (key: string, projectUid: string, dueSince: string): AttentionEntry => ({
	key,
	projectUid,
	dueSince,
	icon: () => null,
	title: key,
	actions: [],
	open: () => {},
});

describe("attention", () => {
	it("puts the newest first and keeps the order stable for the same time", () => {
		const sorted = sortAttention([
			entry("alarms:a", "p1", "2026-10-19T08:00:00Z"),
			entry("notes:b", "p2", "2026-10-19T09:00:00Z"),
			entry("notes:a", "p1", "2026-10-19T08:00:00Z"),
		]);

		expect(sorted.map((e) => e.key)).toEqual(["notes:b", "alarms:a", "notes:a"]);
	});

	it("keeps the entries of one project, or all without a project", () => {
		const entries = [entry("a", "p1", "2026-10-19T08:00:00Z"), entry("b", "p2", "2026-10-19T08:00:00Z")];

		expect(attentionFor(entries, "p2").map((e) => e.key)).toEqual(["b"]);
		expect(attentionFor(entries).map((e) => e.key)).toEqual(["a", "b"]);
	});
});
