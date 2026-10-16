import { defineConfig, mergeConfig } from "vitest/config";
import baseConfig from "./vite.config";

// Implementation tests only; functional and system tests have their own
// commands (see tests/README.md).
export default mergeConfig(
	baseConfig,
	defineConfig({
		test: {
			include: ["tests/implementation/{unit,integration}/**/*.test.{ts,tsx}"],
			environment: "jsdom",
		},
	}),
);
