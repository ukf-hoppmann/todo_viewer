import { describe, expect, it } from "vitest";
import { toLoggable } from "../../../../../../client/src/core/logging/toLoggable";

describe("toLoggable", () => {
	it("keeps JSON-compatible values unchanged", () => {
		const value = { a: 1, b: "text", c: [true, null, { d: 2 }] };

		expect(toLoggable(value)).toEqual(value);
	});

	it("returns a copy, not the reference", () => {
		const value = { a: { b: 1 } };

		const result = toLoggable(value) as typeof value;
		value.a.b = 2;

		expect(result.a.b).toBe(1);
	});

	it("replaces circular references", () => {
		const value: Record<string, unknown> = { name: "root" };
		value.self = value;
		value.list = [value];

		expect(toLoggable(value)).toEqual({
			name: "root",
			self: "[Circular]",
			list: ["[Circular]"],
		});
	});

	it("does not mark a repeated, non-circular reference", () => {
		const shared = { x: 1 };

		expect(toLoggable({ a: shared, b: shared })).toEqual({
			a: { x: 1 },
			b: { x: 1 },
		});
	});

	it("drops functions and symbols in objects and keeps array positions", () => {
		const value = { fn: () => 1, sym: Symbol("s"), kept: 1, list: [() => 1, 2] };

		expect(toLoggable(value)).toEqual({ kept: 1, list: [null, 2] });
	});

	it("converts dates, maps, sets and bigints", () => {
		const value = {
			date: new Date("2026-09-30T12:00:00.000Z"),
			map: new Map([["k", 1]]),
			set: new Set([1, 2]),
			big: 10n,
		};

		expect(toLoggable(value)).toEqual({
			date: "2026-09-30T12:00:00.000Z",
			map: { k: 1 },
			set: [1, 2],
			big: "10",
		});
	});

	it("handles an invalid date without throwing", () => {
		expect(toLoggable(new Date("nope"))).toBe("Invalid Date");
	});

	it("converts errors to name, message, stack and a recursive cause", () => {
		const error = new TypeError("outer", { cause: new Error("inner") });

		const result = toLoggable(error) as Record<string, unknown>;

		expect(result).toMatchObject({ name: "TypeError", message: "outer" });
		expect(result.stack).toEqual(expect.any(String));
		expect(result.cause).toMatchObject({ name: "Error", message: "inner" });
	});

	it("converts errors nested in objects", () => {
		const result = toLoggable({ error: new Error("x") }) as { error: { message: string } };

		expect(result.error.message).toBe("x");
	});

	it("keeps undefined at top level and drops it in objects", () => {
		expect(toLoggable(undefined)).toBeUndefined();
		expect(toLoggable({ a: undefined, b: 1 })).toEqual({ b: 1 });
	});

	describe("limits", () => {
		it("uses the defaults depth 10, 1000 entries and 10000 characters", () => {
			let deep: unknown = "leaf";
			for (let i = 0; i < 12; i++) deep = { next: deep };
			const flat = toLoggable(deep);
			let level = flat as Record<string, unknown>;
			let containers = 1;
			while (typeof level.next === "object") {
				level = level.next as Record<string, unknown>;
				containers++;
			}

			expect(containers).toBe(10);
			expect(level.next).toBe("[truncated]");

			const list = toLoggable(Array.from({ length: 1500 }, (_, i) => i)) as unknown[];
			expect(list).toHaveLength(1001);
			expect(list[1000]).toBe("[truncated]");

			const text = toLoggable("a".repeat(10_001)) as string;
			expect(text).toBe(`${"a".repeat(10_000)}[truncated]`);
		});

		it("keeps values exactly at the limits", () => {
			expect(toLoggable(Array.from({ length: 1000 }, () => 0))).toHaveLength(1000);
			expect(toLoggable("a".repeat(10_000))).toBe("a".repeat(10_000));
		});

		it("truncates containers below the configured depth", () => {
			expect(toLoggable({ a: { b: 1 }, c: 2 }, { depth: 1 })).toEqual({
				a: "[truncated]",
				c: 2,
			});
		});

		it("truncates objects above the configured number of entries", () => {
			expect(toLoggable({ a: 1, b: 2, c: 3 }, { entries: 2 })).toEqual({
				a: 1,
				b: 2,
				"[truncated]": 1,
			});
		});

		it("truncates arrays and sets above the configured number of entries", () => {
			expect(toLoggable([1, 2, 3], { entries: 2 })).toEqual([1, 2, "[truncated]"]);
			expect(toLoggable(new Set([1, 2, 3]), { entries: 2 })).toEqual([1, 2, "[truncated]"]);
		});

		it("truncates strings above the configured length, also inside objects", () => {
			expect(toLoggable({ s: "abcdef" }, { stringLength: 3 })).toEqual({
				s: "abc[truncated]",
			});
		});

		it("applies single options and keeps the defaults for the others", () => {
			expect(toLoggable("abcdef", { stringLength: 2 })).toBe("ab[truncated]");
			expect(toLoggable([1, 2, 3])).toEqual([1, 2, 3]);
		});
	});
});
