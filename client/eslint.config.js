import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import { defineConfig, globalIgnores } from "eslint/config";
import globals from "globals";
import tseslint from "typescript-eslint";
import { architecturePlugin } from "./configs/eslint/index.ts";

// Run from the repository root so that the tests under `tests/` are covered too:
//   client/node_modules/.bin/eslint -c client/eslint.config.js client tests/implementation/unit/client tests/helpers/client
// (`npm run lint` does this). Paths below are relative to the repository root.
export default defineConfig([
	globalIgnores(["client/dist", "client/node_modules", "client/src/shared/api/schema.d.ts"]),
	{
		files: ["**/*.{ts,tsx}"],
		extends: [
			js.configs.recommended,
			tseslint.configs.recommended,
			reactHooks.configs.flat.recommended,
			reactRefresh.configs.vite,
		],
		languageOptions: {
			ecmaVersion: 2022,
			globals: globals.browser,
		},
	},
	// Import boundaries of docs/development/architecture.md and the scope client.
	{
		files: ["client/src/**/*.{ts,tsx}", "tests/**/*.{ts,tsx}", "client/configs/**/*.ts"],
		plugins: { architecture: architecturePlugin },
		rules: { "architecture/boundaries": "error" },
	},
]);
