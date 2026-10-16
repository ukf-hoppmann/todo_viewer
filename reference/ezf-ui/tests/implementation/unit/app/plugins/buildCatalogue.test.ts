import { describe, expect, it } from "vitest";
import { buildCatalogue } from "../../../../../src/app/plugins/buildCatalogue";

const loadA = async () => ({});
const loadB = async () => ({});

describe("buildCatalogue", () => {
	it("joins manifest and loader of each plugin folder under the folder name", () => {
		const catalogue = buildCatalogue(
			{ "../plugins/a/plugin.json": { requires: [] }, "../plugins/b-c/plugin.json": { requires: ["a"] } },
			{ "../plugins/a/index.ts": loadA, "../plugins/b-c/index.ts": loadB },
		);

		expect(catalogue).toEqual({
			a: { manifest: { requires: [] }, load: loadA },
			"b-c": { manifest: { requires: ["a"] }, load: loadB },
		});
	});

	it("keeps a folder with only one of the two files, so that it is reported as broken", () => {
		const catalogue = buildCatalogue({ "../plugins/a/plugin.json": { requires: [] } }, { "../plugins/b/index.ts": loadB });

		expect(catalogue).toEqual({
			a: { manifest: { requires: [] } },
			b: { manifest: undefined, load: loadB },
		});
	});

	it("takes the folder name as it is, also when it is no valid id", () => {
		expect(Object.keys(buildCatalogue({ "../plugins/Bad_Name/plugin.json": {} }, {}))).toEqual(["Bad_Name"]);
	});

	it("works with any path prefix before the plugin folder", () => {
		expect(Object.keys(buildCatalogue({ "/tests/fixtures/plugins/x/plugin.json": {} }, {}))).toEqual(["x"]);
	});
});
