import { describe, expect, it } from "vitest";
import { validatePluginManifest } from "../../../../../../client/src/core/plugins/validatePluginManifest";

describe("validatePluginManifest: valid manifests", () => {
	it("accepts an empty list requires", () => {
		expect(validatePluginManifest({ requires: [] })).toEqual({ ok: true, manifest: { requires: [] } });
	});

	it("accepts kebab-case plugin ids under requires", () => {
		const manifest = { requires: ["patient-table", "variant-filter2"] };

		expect(validatePluginManifest(manifest)).toEqual({ ok: true, manifest });
	});
});

describe("validatePluginManifest: invalid manifests", () => {
	it.each([
		["no object", "requires", "must be object"],
		["missing requires", {}, "must have required property 'requires'"],
		["requires is no list", { requires: "a" }, "/requires: must be array"],
		["duplicate entries", { requires: ["a", "a"] }, "/requires: must NOT have duplicate items"],
		["id not kebab-case", { requires: ["Patient_Table"] }, "/requires/0: must match pattern"],
		["entry is no string", { requires: [1] }, "/requires/0: must be string"],
		["additional field", { requires: [], id: "x" }, "must NOT have additional properties: id"],
		["undefined (file missing)", undefined, "must be object"],
	])("rejects %s", (_name, raw, expected) => {
		const result = validatePluginManifest(raw);

		expect(result.ok).toBe(false);
		if (!result.ok) expect(result.message).toContain(expected);
	});

	it("names every violation, not only the first", () => {
		const result = validatePluginManifest({ requires: ["A", "B"], id: "x" });

		expect(result.ok).toBe(false);
		if (!result.ok) {
			expect(result.message).toContain("/requires/0");
			expect(result.message).toContain("/requires/1");
			expect(result.message).toContain("additional properties: id");
		}
	});
});
