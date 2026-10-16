import { fileURLToPath } from "node:url";
import { defineConfig, mergeConfig } from "vitest/config";
import baseConfig from "./vite.config";

const clientRoot = fileURLToPath(new URL("../..", import.meta.url));
const testsRoot = fileURLToPath(new URL("../../../tests/", import.meta.url));

// Implementation tests only; their folder mirrors `client/src/` (scope client 7). The tests live outside of
// `client/`; `npm install` links `tests/node_modules` to `client/node_modules` so that their imports resolve.
export default mergeConfig(
	baseConfig,
	defineConfig({
		server: { fs: { allow: [clientRoot, testsRoot] } },
		test: {
			include: ["../tests/implementation/unit/client/**/*.test.{ts,tsx}"],
			environment: "jsdom",
		},
	}),
);
