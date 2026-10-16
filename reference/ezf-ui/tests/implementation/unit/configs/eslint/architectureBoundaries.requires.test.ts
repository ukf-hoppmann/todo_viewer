// @vitest-environment node
import { RuleTester } from "eslint";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterAll, describe, it } from "vitest";
import { boundaries } from "../../../../../configs/eslint/architectureBoundaries.ts";

RuleTester.describe = describe;
RuleTester.it = it;
RuleTester.itOnly = it.only;

// A real project folder: the rule reads the manifest `plugin.json` of the importing plugin from disk.
const root = mkdtempSync(path.join(os.tmpdir(), "boundaries-requires-"));
afterAll(() => rmSync(root, { recursive: true, force: true }));

function plugin(id: string, manifest?: string) {
	const folder = path.join(root, "src", "plugins", id);
	mkdirSync(folder, { recursive: true });
	if (manifest !== undefined) writeFileSync(path.join(folder, "plugin.json"), manifest);
}

plugin("a", JSON.stringify({ requires: ["b"] }));
plugin("b", JSON.stringify({ requires: [] }));
plugin("c", JSON.stringify({ requires: [] }));
plugin("no-manifest");
plugin("broken-json", "{ not json");
plugin("requires-text", JSON.stringify({ requires: "b" }));
plugin("requires-numbers", JSON.stringify({ requires: [1] }));
plugin("requires-missing", JSON.stringify({}));
plugin("manifest-null", "null");

const file = (relative: string) => path.join(root, relative);
const options = [{ root }];

const ruleTester = new RuleTester({
	languageOptions: { ecmaVersion: 2022, sourceType: "module" },
});

describe("architecture/boundaries: plugin imports through requires", () => {
	ruleTester.run("boundaries", boundaries, {
		valid: [
			// plugin a requires b: its public API may be imported, however it is written
			{ code: `import { x } from "../b";`, filename: file("src/plugins/a/x.ts"), options },
			{ code: `import { x } from "../b/index";`, filename: file("src/plugins/a/x.ts"), options },
			{ code: `import { x } from "../b/index.ts";`, filename: file("src/plugins/a/x.ts"), options },
			{ code: `export { x } from "../b";`, filename: file("src/plugins/a/x.ts"), options },
			{ code: `export * from "../b";`, filename: file("src/plugins/a/x.ts"), options },
			{ code: `const m = import("../b");`, filename: file("src/plugins/a/x.ts"), options },
			{ code: `import { x } from "../../b";`, filename: file("src/plugins/a/deep/x.ts"), options },
			// a plugin may always use its own files, core, and shared
			{ code: `import { x } from "./internal/y";`, filename: file("src/plugins/a/x.ts"), options },
			{ code: `import { x } from "../../core";`, filename: file("src/plugins/a/x.ts"), options },
			{ code: `import { x } from "../../shared";`, filename: file("src/plugins/a/x.ts"), options },
			// the manifest is read only for imports into other plugins
			{ code: `import { x } from "../../core";`, filename: file("src/plugins/no-manifest/x.ts"), options },
			{ code: `import { x } from "./y";`, filename: file("src/plugins/broken-json/x.ts"), options },
			// the app may import any plugin entry point
			{ code: `import { x } from "../plugins/c";`, filename: file("src/app/main.tsx"), options },
		],
		invalid: [
			// c is not in `requires` of a
			{
				code: `import { x } from "../c";`,
				filename: file("src/plugins/a/x.ts"),
				options,
				errors: [{ messageId: "pluginToPlugin", data: { from: "a", to: "c" } }],
			},
			{
				code: `export { x } from "../c";`,
				filename: file("src/plugins/a/x.ts"),
				options,
				errors: [{ messageId: "pluginToPlugin", data: { from: "a", to: "c" } }],
			},
			{
				code: `const m = import("../c");`,
				filename: file("src/plugins/a/x.ts"),
				options,
				errors: [{ messageId: "pluginToPlugin", data: { from: "a", to: "c" } }],
			},
			// b requires nothing, so it must not import a, although a requires b
			{
				code: `import { x } from "../a";`,
				filename: file("src/plugins/b/x.ts"),
				options,
				errors: [{ messageId: "pluginToPlugin", data: { from: "b", to: "a" } }],
			},
			// deep imports stay forbidden, also into a required plugin
			{
				code: `import { x } from "../b/internal/y";`,
				filename: file("src/plugins/a/x.ts"),
				options,
				errors: [{ messageId: "deepImport" }],
			},
			{
				code: `const m = import("../b/Page");`,
				filename: file("src/plugins/a/x.ts"),
				options,
				errors: [{ messageId: "deepImport" }],
			},
			// a manifest that cannot be used: every import into another plugin is reported, the rule does not crash
			{
				code: `import { x } from "../b";`,
				filename: file("src/plugins/no-manifest/x.ts"),
				options,
				errors: [{ messageId: "manifestUnreadable", data: { manifest: "src/plugins/no-manifest/plugin.json" } }],
			},
			{
				code: `import { x } from "../b";`,
				filename: file("src/plugins/broken-json/x.ts"),
				options,
				errors: [{ messageId: "manifestUnreadable", data: { manifest: "src/plugins/broken-json/plugin.json" } }],
			},
			{
				code: `import { x } from "../b";`,
				filename: file("src/plugins/requires-text/x.ts"),
				options,
				errors: [{ messageId: "manifestUnreadable", data: { manifest: "src/plugins/requires-text/plugin.json" } }],
			},
			{
				code: `import { x } from "../b";`,
				filename: file("src/plugins/requires-numbers/x.ts"),
				options,
				errors: [{ messageId: "manifestUnreadable", data: { manifest: "src/plugins/requires-numbers/plugin.json" } }],
			},
			{
				code: `import { x } from "../b";`,
				filename: file("src/plugins/requires-missing/x.ts"),
				options,
				errors: [{ messageId: "manifestUnreadable", data: { manifest: "src/plugins/requires-missing/plugin.json" } }],
			},
			{
				code: `import { x } from "../b";`,
				filename: file("src/plugins/manifest-null/x.ts"),
				options,
				errors: [{ messageId: "manifestUnreadable", data: { manifest: "src/plugins/manifest-null/plugin.json" } }],
			},
			// each import is reported on its own
			{
				code: `import { x } from "../b"; import { y } from "../c"; const m = import("../c");`,
				filename: file("src/plugins/a/x.ts"),
				options,
				errors: [{ messageId: "pluginToPlugin" }, { messageId: "pluginToPlugin" }],
			},
			// the other layers are unchanged
			{
				code: `import { x } from "../plugins/a";`,
				filename: file("src/core/x.ts"),
				options,
				errors: [{ messageId: "coreToPlugin" }],
			},
		],
	});
});
