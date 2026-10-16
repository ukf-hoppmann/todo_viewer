import { describe, expect, it } from "vitest";
import { toBackendPayload } from "../../../../../src/core/logging/backendPayload";
import { toLoggable } from "../../../../../src/core/logging/toLoggable";
import type { LogEntry } from "../../../../../src/core/logging/types";

const base: LogEntry = {
	id: "a3f9c2d1",
	time: "2026-09-30T14:32:05.123Z",
	level: "error",
	origin: "process-manager",
	sessionId: "5c1e0b7f9a2d4e6b8c0a1f3e5d7b9c2a",
	route: "/patients/123/process",
};

const convert = (value: unknown) => toLoggable(value);

describe("toBackendPayload: fields", () => {
	it("takes over the fields of the entry", () => {
		const entry: LogEntry = {
			...base,
			element: "process-manager.save-button",
			action: "click",
			message: "POST childForm failed",
			userMessage: "process-manager:errors.save-unreachable",
		};

		expect(toBackendPayload(entry, convert)).toEqual(entry);
	});

	it("leaves out empty fields", () => {
		const payload = toBackendPayload({ ...base, element: undefined, message: "", data: undefined }, convert);

		expect(Object.keys(payload).sort()).toEqual(["id", "level", "origin", "route", "sessionId", "time"]);
	});

	it("does not send fields the format does not know", () => {
		const entry = { ...base, extra: "x" } as LogEntry;

		expect(toBackendPayload(entry, convert)).not.toHaveProperty("extra");
	});
});

describe("toBackendPayload: data", () => {
	it("converts data with the given function, so that the configured limits apply", () => {
		const data = { text: "abcdef", list: [1, 2, 3] };
		const payload = toBackendPayload({ ...base, data }, (value) => toLoggable(value, { stringLength: 3, entries: 2 }));

		expect(payload.data).toEqual({ text: "abc[truncated]", list: [1, 2, "[truncated]"] });
	});

	it("survives cycles", () => {
		const data: Record<string, unknown> = { name: "loop" };
		data.self = data;

		expect(JSON.stringify(toBackendPayload({ ...base, data }, convert))).toContain("[Circular]");
	});
});

describe("toBackendPayload: error", () => {
	it("sends an Error as name, message and stack", () => {
		const error = new TypeError("Failed to fetch");
		const payload = toBackendPayload({ ...base, error }, convert);

		expect(payload.error).toEqual({ name: "TypeError", message: "Failed to fetch", stack: error.stack });
	});

	it("nests the cause in the same form", () => {
		const error = new Error("outer", { cause: new RangeError("inner") });
		const payload = toBackendPayload({ ...base, error }, convert);

		expect(payload.error).toMatchObject({ name: "Error", cause: { name: "RangeError", message: "inner" } });
	});

	it("leaves out a missing stack instead of sending null", () => {
		const error = new Error("no stack");
		error.stack = undefined;

		expect(toBackendPayload({ ...base, error }, convert).error).toEqual({ name: "Error", message: "no stack" });
	});

	it.each([
		["a thrown text", "boom", "boom"],
		["a number", 42, "42"],
		["a plain object", { code: 7 }, '{"code":7}'],
	])("sends %s as NonError", (_name, error, message) => {
		expect(toBackendPayload({ ...base, error }, convert).error).toEqual({ name: "NonError", message });
	});

	it("sends a cause that is no error as NonError", () => {
		const error = new Error("outer", { cause: "the reason" });

		expect(toBackendPayload({ ...base, error }, convert).error).toMatchObject({
			cause: { name: "NonError", message: "the reason" },
		});
	});

	it("sends null as error like any other value that is no error", () => {
		expect(toBackendPayload({ ...base, error: null }, convert).error).toEqual({ name: "NonError", message: "null" });
	});
});
