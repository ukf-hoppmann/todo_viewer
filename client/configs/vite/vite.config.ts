import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

// The project root is two levels up; index.html and public/ live there.
const root = fileURLToPath(new URL("../..", import.meta.url));

// The backend of the rebuilt viewer listens on 5411 (the old viewer moved to 5412).
const backend = process.env.BACKEND_URL ?? "http://127.0.0.1:5411";

export default defineConfig({
	root,
	plugins: [react()],
	server: { proxy: { "/api": backend, "/mcp": backend } },
	build: { outDir: "dist", emptyOutDir: true },
});
