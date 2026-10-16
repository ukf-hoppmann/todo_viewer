import { describe, expect, it } from "vitest";
import { initI18n } from "../../../../../src/core";
import de from "../../../../../src/core/i18n/locales/de.json";
import en from "../../../../../src/core/i18n/locales/en.json";
import fr from "../../../../../src/core/i18n/locales/fr.json";
import { buildDetails } from "../../../../../src/core/errors/buildDetails";
import { translateText } from "../../../../../src/core/modals/text";
import type { LogEntry } from "../../../../../src/core/logging/types";

const localTime = new Date(2026, 8, 30, 15, 1, 23, 456);

function entry(overrides: Partial<LogEntry> = {}): LogEntry {
	return {
		id: "a1b2c3d4",
		time: localTime.toISOString(),
		level: "error",
		origin: "core",
		sessionId: "0123456789abcdef0123456789abcdef",
		route: "/",
		...overrides,
	};
}

function byKey(rows: ReturnType<typeof buildDetails>) {
	return Object.fromEntries(
		rows.map((row) => [typeof row.label === "string" ? row.label : row.label.key, row.value]),
	);
}

describe("buildDetails", () => {
	it("lists time, error id and session id of the entry", () => {
		const rows = buildDetails(entry(), { showStack: false });

		expect(rows).toEqual([
			{ label: { key: "reportError.details.time" }, value: "2026-09-30 15:01:23" },
			{ label: { key: "reportError.details.errorId" }, value: "a1b2c3d4" },
			{ label: { key: "reportError.details.sessionId" }, value: "0123456789abcdef0123456789abcdef" },
		]);
	});

	it("formats the time in local time to the second, independent of the language", () => {
		const late = new Date(2026, 0, 5, 3, 4, 5).toISOString();

		expect(byKey(buildDetails(entry({ time: late }), { showStack: false }))["reportError.details.time"]).toBe(
			"2026-01-05 03:04:05",
		);
	});

	it("shows an Error as name and message", () => {
		const rows = byKey(buildDetails(entry({ error: new TypeError("bad input") }), { showStack: false }));

		expect(rows["reportError.details.error"]).toBe("TypeError: bad input");
	});

	it("shows other thrown values as text", () => {
		const text = (error: unknown) =>
			byKey(buildDetails(entry({ error }), { showStack: false }))["reportError.details.error"];

		expect(text("plain failure")).toBe("plain failure");
		expect(text(404)).toBe("404");
		expect(text({ status: 500 })).toBe('{"status":500}');
	});

	it("shows a thrown object with a cycle without failing", () => {
		const cyclic: Record<string, unknown> = { a: 1 };
		cyclic.self = cyclic;

		const rows = byKey(buildDetails(entry({ error: cyclic }), { showStack: false }));

		expect(rows["reportError.details.error"]).toBe('{"a":1,"self":"[Circular]"}');
	});

	it.each([undefined, null, ""])("leaves out the error line for %j", (error) => {
		const rows = byKey(buildDetails(entry({ error }), { showStack: true }));

		expect(rows).not.toHaveProperty("reportError.details.error");
		expect(rows).not.toHaveProperty("reportError.details.stack");
	});

	it("adds the stack trace only when it is to be shown", () => {
		const error = new Error("x");

		const hidden = byKey(buildDetails(entry({ error }), { showStack: false }));
		const shown = byKey(buildDetails(entry({ error }), { showStack: true }));

		expect(hidden).not.toHaveProperty("reportError.details.stack");
		expect(shown["reportError.details.stack"]).toBe(error.stack);
	});

	it("has no stack line for a value without a stack", () => {
		const rows = byKey(buildDetails(entry({ error: "text" }), { showStack: true }));

		expect(rows).not.toHaveProperty("reportError.details.stack");
	});

	it("puts the error and the stack after the ids", () => {
		const rows = buildDetails(entry({ error: new Error("x") }), { showStack: true });

		expect(rows.map((row) => (row.label as { key: string }).key)).toEqual([
			"reportError.details.time",
			"reportError.details.errorId",
			"reportError.details.sessionId",
			"reportError.details.error",
			"reportError.details.stack",
		]);
	});

	it("leaves out a line with an empty value", () => {
		const rows = byKey(buildDetails(entry({ sessionId: "" }), { showStack: false }));

		expect(rows).not.toHaveProperty("reportError.details.sessionId");
	});
});

describe("texts of reportError", () => {
	it.each(["time", "errorId", "sessionId", "error", "stack"])("has a translation of %s in all languages", async (name) => {
		const key = `reportError.details.${name}`;
		for (const lng of ["de", "en", "fr"]) {
			const i18n = await initI18n({ lng });
			expect(translateText(i18n.t, { key })).not.toBe(key);
		}
	});

	it("exist with the same keys in German, English and French", () => {
		const keys = (value: object) => Object.keys((value as { reportError: { details: object } }).reportError.details).sort();

		expect(keys(en)).toEqual(keys(de));
		expect(keys(fr)).toEqual(keys(de));
	});
});
