import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, proxy the API to the FastAPI backend so the SPA and API share an origin.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/chat": "http://localhost:8000",
      "/auth": "http://localhost:8000",
      "/conversations": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
