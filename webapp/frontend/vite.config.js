import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build to ./dist; FastAPI serves it at "/".
// Dev server proxies /api to the FastAPI backend on :8000.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { outDir: "dist", emptyOutDir: true },
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
});
