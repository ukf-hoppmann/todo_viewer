import { defineConfig, mergeConfig } from "vitest/config";
import baseConfig from "./vite.config";

// Functional tests of the project owner; not part of `npm test`
// (see tests/README.md).
export default mergeConfig(
	baseConfig,
	defineConfig({
		test: {
			include: ["tests/functional/**/*.test.{ts,tsx}"],
			environment: "jsdom",
		},
	}),
);
