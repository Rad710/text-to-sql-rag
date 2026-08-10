import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vitest/config";

// Vitest runs the component tests in jsdom so <App /> actually mounts — the assistant-ui
// runtime initialises exactly as it does in the browser. A mount-time crash (e.g. the
// 0.11.58 `_getInitializePromise` throw under React 19) fails the test, which `tsc`/`vite
// build` never caught. See docs/tasks/0010-react-frontend/.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
  },
});
