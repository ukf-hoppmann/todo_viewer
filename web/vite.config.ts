/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev the API runs separately (python backend/main.py); Vite proxies /api to it.
const backend = process.env.BACKEND_URL ?? "http://127.0.0.1:5411";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": backend } },
  build: { outDir: "dist", emptyOutDir: true },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["src/test/setup.ts"],
  },
});
