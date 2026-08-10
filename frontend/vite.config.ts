import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, proxy the API to the FastAPI backend so the SPA and API share an origin.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/chat": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
