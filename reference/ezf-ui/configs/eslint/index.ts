import type { ESLint } from "eslint";
import { boundaries } from "./architectureBoundaries.ts";

/** Project ESLint plugin; registered as `architecture` in eslint.config.js. */
export const architecturePlugin: ESLint.Plugin = {
	rules: { boundaries },
};
