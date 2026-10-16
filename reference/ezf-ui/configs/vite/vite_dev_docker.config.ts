import { defineConfig, mergeConfig } from "vite";
import baseConfig from "./vite.config";

// Dev server inside Docker: reachable from outside the container, polling
// because file events do not cross the volume mount.
export default mergeConfig(
	baseConfig,
	defineConfig({
		server: {
			host: "0.0.0.0",
			watch: {
				usePolling: true,
			},
		},
	}),
);
