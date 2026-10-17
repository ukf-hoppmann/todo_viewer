import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

// The project root is two levels up; index.html and public/ live there.
const root = fileURLToPath(new URL("../..", import.meta.url));

// The backend of the rebuilt viewer listens on 5412 (the old viewer keeps 5411).
const backend = process.env.BACKEND_URL ?? "http://127.0.0.1:5412";

export default defineConfig({
	root,
	plugins: [react()],
	server: { proxy: { "/api": backend, "/mcp": backend } },
	build: { outDir: "dist", emptyOutDir: true },
});
