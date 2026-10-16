// @vitest-environment node
import { RuleTester } from "eslint";
import path from "node:path";
import { describe, it } from "vitest";
import { boundaries } from "../../../../../../client/configs/eslint/architectureBoundaries.ts";

RuleTester.describe = describe;
RuleTester.it = it;
RuleTester.itOnly = it.only;

const root = "/project";
const file = (relative: string) => path.join(root, relative);
const options = [{ root }];

const ruleTester = new RuleTester({
	languageOptions: { ecmaVersion: 2022, sourceType: "module" },
});

describe("architecture/boundaries: layers, src_old and test code", () => {
	ruleTester.run("boundaries", boundaries, {
		valid: [
			// inside the own unit
			{ code: `import { x } from "./i18n/initI18n";`, filename: file("client/src/core/index.ts"), options },
			{ code: `import { x } from "../testIds";`, filename: file("client/src/core/navigation/AppFrame.tsx"), options },
			// packages are not checked
			{ code: `import React from "react";`, filename: file("client/src/shared/index.ts"), options },
			// allowed directions through the public API
			{ code: `import { x } from "../shared";`, filename: file("client/src/core/a.ts"), options },
			{ code: `import { x } from "../core";`, filename: file("client/src/app/main.tsx"), options },
			{ code: `import { x } from "../plugins/demo";`, filename: file("client/src/app/main.tsx"), options },
			{ code: `import { x } from "../../core";`, filename: file("client/src/plugins/demo/a.ts"), options },
			{ code: `import { x } from "../../shared";`, filename: file("client/src/plugins/demo/a.ts"), options },
			{ code: `const m = import("../plugins/demo");`, filename: file("client/src/app/main.tsx"), options },
			// tests may import anything from src, including internals
			{ code: `import { x } from "../../../../client/src/core/i18n/initI18n";`, filename: file("tests/implementation/unit/client/a.test.ts"), options },
		],
		invalid: [
			{
				code: `import { x } from "../../../src_old/main";`,
				filename: file("client/src/core/a.ts"),
				options,
				errors: [{ messageId: "legacy" }],
			},
			{
				code: `import { x } from "../../../reference/ezf-ui/src/core";`,
				filename: file("client/src/app/a.ts"),
				options,
				errors: [{ messageId: "legacy" }],
			},
			{
				code: `import { x } from "../src_old/Views/x";`,
				filename: file("tests/a.test.ts"),
				options,
				errors: [{ messageId: "legacy" }],
			},
			{
				code: `import { x } from "../../../tests/helpers/x";`,
				filename: file("client/src/core/a.ts"),
				options,
				errors: [{ messageId: "testCode" }],
			},
			{
				code: `import { x } from "../core";`,
				filename: file("client/src/shared/a.ts"),
				options,
				errors: [{ messageId: "direction" }],
			},
			{
				code: `import { x } from "../plugins/demo";`,
				filename: file("client/src/core/a.ts"),
				options,
				errors: [{ messageId: "coreToPlugin" }],
			},
			{
				code: `export { x } from "../app/main";`,
				filename: file("client/src/core/a.ts"),
				options,
				errors: [{ messageId: "direction" }],
			},
			{
				code: `import { x } from "../../app/main";`,
				filename: file("client/src/plugins/demo/a.ts"),
				options,
				errors: [{ messageId: "direction" }],
			},
			{
				code: `import { x } from "../shared";`,
				filename: file("client/src/app/main.tsx"),
				options,
				errors: [{ messageId: "direction" }],
			},
		],
	});
});

describe("architecture/boundaries: public API only", () => {
	ruleTester.run("boundaries", boundaries, {
		valid: [
			{ code: `import { x } from "../core/index";`, filename: file("client/src/app/main.tsx"), options },
			{ code: `import { x } from "../core/index.ts";`, filename: file("client/src/app/main.tsx"), options },
			{ code: `import { x } from "../../shared/index.ts";`, filename: file("client/src/plugins/demo/a.ts"), options },
		],
		invalid: [
			{
				code: `import { x } from "../core/i18n/initI18n";`,
				filename: file("client/src/app/main.tsx"),
				options,
				errors: [{ messageId: "deepImport" }],
			},
			{
				code: `import { x } from "../../core/testIds";`,
				filename: file("client/src/plugins/demo/a.ts"),
				options,
				errors: [{ messageId: "deepImport" }],
			},
			{
				code: `import { x } from "../shared/ui/ErrorBox";`,
				filename: file("client/src/core/a.ts"),
				options,
				errors: [{ messageId: "deepImport" }],
			},
			{
				code: `import { x } from "../plugins/demo/internal";`,
				filename: file("client/src/app/main.tsx"),
				options,
				errors: [{ messageId: "deepImport" }],
			},
		],
	});
});
