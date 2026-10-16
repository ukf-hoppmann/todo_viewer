import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

// The project root is two levels up; index.html and public/ live there.
const root = fileURLToPath(new URL("../..", import.meta.url));

export default defineConfig({
	root,
	plugins: [react()],
});
