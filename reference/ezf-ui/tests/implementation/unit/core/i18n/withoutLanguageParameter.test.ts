import { describe, expect, it } from "vitest";
import { withoutLanguageParameter } from "../../../../../src/core/i18n/withoutLanguageParameter";

describe("withoutLanguageParameter", () => {
	it("removes the language parameter and keeps the path", () => {
		expect(withoutLanguageParameter("/core/home?lng=en")).toBe("/core/home");
	});

	it("keeps other parameters and their order", () => {
		expect(withoutLanguageParameter("/overview?a=1&lng=en&b=2")).toBe("/overview?a=1&b=2");
	});

	it("keeps the fragment", () => {
		expect(withoutLanguageParameter("/overview?lng=fr#prefill")).toBe("/overview#prefill");
	});

	it("removes the parameter also without a value", () => {
		expect(withoutLanguageParameter("/overview?lng=")).toBe("/overview");
	});

	it.each(["/overview", "/overview?a=1", "/overview#lng=en", "/"])("returns %s unchanged without the parameter", (url) => {
		expect(withoutLanguageParameter(url)).toBe(url);
	});
});
