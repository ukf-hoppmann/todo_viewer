import { describe, expect, it, vi } from "vitest";
import { consumeReturnTo, returnToKey } from "../../../../../src/core/auth/returnTo";
import type { Logger } from "../../../../../src/core/logging/types";
import { fakeStorage } from "../../../../helpers/fakeBrowser";

const savedAt = 1_700_000_000_000;
const minute = 60_000;

function entry(path: string, at = savedAt) {
	return JSON.stringify({ path, savedAt: at });
}

function setup(stored: string | undefined, { minutesLater = 1, maxAgeMinutes, available = true }: { minutesLater?: number; maxAgeMinutes?: number; available?: boolean | ((path: string) => boolean) } = {}) {
	const storage = fakeStorage(stored === undefined ? {} : { [returnToKey]: stored });
	const info = vi.fn();
	const logger = { debug: vi.fn(), info, warn: vi.fn(), error: vi.fn() } as unknown as Logger;
	const isAvailable = vi.fn(typeof available === "function" ? available : () => available);
	const run = () => consumeReturnTo({ storage, now: () => savedAt + minutesLater * minute, maxAgeMinutes, isAvailable, logger });
	return { storage, info, isAvailable, run };
}

describe("consumeReturnTo: address that is used", () => {
	it("returns path, query and fragment of a young entry for an available view", () => {
		const { run } = setup(entry("/patients/7?tab=lab#top"));

		expect(run()).toBe("/patients/7?tab=lab#top");
	});

	it("checks the view with the path alone, without query and fragment", () => {
		const { run, isAvailable } = setup(entry("/patients/7?tab=lab#top"));

		run();

		expect(isAvailable).toHaveBeenCalledExactlyOnceWith("/patients/7");
	});

	it("deletes the entry as soon as it is read", () => {
		const { run, storage } = setup(entry("/patients/7"));

		run();

		expect(storage.getItem(returnToKey)).toBeNull();
	});

	it("writes nothing to the log", () => {
		const { run, info } = setup(entry("/patients/7"));

		run();

		expect(info).not.toHaveBeenCalled();
	});
});

describe("consumeReturnTo: age", () => {
	it("is valid for 10 minutes by default", () => {
		expect(setup(entry("/a/b"), { minutesLater: 10 }).run()).toBe("/a/b");
	});

	it("is too old after 10 minutes by default", () => {
		expect(setup(entry("/a/b"), { minutesLater: 11 }).run()).toBeUndefined();
	});

	it("follows the configured value: valid within it", () => {
		expect(setup(entry("/a/b"), { minutesLater: 25, maxAgeMinutes: 30 }).run()).toBe("/a/b");
	});

	it("follows the configured value: too old beyond it", () => {
		expect(setup(entry("/a/b"), { minutesLater: 3, maxAgeMinutes: 2 }).run()).toBeUndefined();
	});

	it("logs an old entry at info level with the reason expired, and still deletes it", () => {
		const { run, info, storage } = setup(entry("/a/b"), { minutesLater: 60 });

		run();

		expect(info).toHaveBeenCalledExactlyOnceWith(expect.objectContaining({ action: "return-to", data: expect.objectContaining({ reason: "expired" }) }));
		expect(storage.getItem(returnToKey)).toBeNull();
	});
});

describe("consumeReturnTo: address that is dropped", () => {
	it.each([
		["a second slash at the start", "//evil.example/path"],
		["a scheme", "https://evil.example/path"],
		["a scheme without slashes", "javascript:alert(1)"],
		["no slash at the start", "patients/7"],
		["a backslash after the slash", "/\\evil.example"],
		["an empty text", ""],
	])("drops an address with %s, without asking for the view", (_name, path) => {
		const { run, isAvailable, info } = setup(entry(path));

		expect(run()).toBeUndefined();

		expect(isAvailable).not.toHaveBeenCalled();
		expect(info).toHaveBeenCalledExactlyOnceWith(expect.objectContaining({ action: "return-to", data: expect.objectContaining({ reason: "invalid-path" }) }));
	});

	it("drops a view that is not available and logs the reason", () => {
		const { run, info } = setup(entry("/gone/view"), { available: false });

		expect(run()).toBeUndefined();

		expect(info).toHaveBeenCalledExactlyOnceWith(
			expect.objectContaining({ action: "return-to", data: expect.objectContaining({ reason: "not-available", path: "/gone/view" }) }),
		);
	});

	it.each([
		["not JSON", "{ nope"],
		["no object", "42"],
		["without path", JSON.stringify({ savedAt })],
		["without time", JSON.stringify({ path: "/a/b" })],
		["with a path that is no text", JSON.stringify({ path: 5, savedAt })],
		["with a time that is no number", JSON.stringify({ path: "/a/b", savedAt: "now" })],
	])("drops an entry that is %s, deletes it, and logs the reason", (_name, stored) => {
		const { run, info, storage } = setup(stored);

		expect(run()).toBeUndefined();

		expect(info).toHaveBeenCalledExactlyOnceWith(expect.objectContaining({ action: "return-to", data: expect.objectContaining({ reason: "unreadable" }) }));
		expect(storage.getItem(returnToKey)).toBeNull();
	});

	it("returns nothing and logs nothing without an entry", () => {
		const { run, info, isAvailable } = setup(undefined);

		expect(run()).toBeUndefined();

		expect(info).not.toHaveBeenCalled();
		expect(isAvailable).not.toHaveBeenCalled();
	});
});
