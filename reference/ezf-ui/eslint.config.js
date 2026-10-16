import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import { defineConfig, globalIgnores } from "eslint/config";
import globals from "globals";
import tseslint from "typescript-eslint";
import { architecturePlugin } from "./configs/eslint/index.ts";

export default defineConfig([
	// src_old is a read-only reference (architecture rule 0).
	globalIgnores(["dist", "src_old"]),
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
	// Import boundaries of docs/development/architecture.md (rules 0.1, 1, 2.1).
	{
		files: ["src/**/*.{ts,tsx}", "tests/**/*.{ts,tsx}", "configs/**/*.ts"],
		plugins: { architecture: architecturePlugin },
		rules: { "architecture/boundaries": "error" },
	},
]);
