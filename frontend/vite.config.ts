import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { tanstackRouter } from "@tanstack/router-plugin/vite";

export default defineConfig({
  plugins: [
    // Must come before the React plugin. Every route becomes its own chunk.
    tanstackRouter({ target: "react", autoCodeSplitting: true }),
    react(),
  ],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8091" },
  },
  build: {
    target: "es2022",
    cssCodeSplit: false,
    sourcemap: false,
    chunkSizeWarningLimit: 300,
  },
});
