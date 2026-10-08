import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The phone only talks to Vite; Vite forwards /api to Flask on this laptop.
// Flask runs on 5001 because macOS uses 5000 for AirPlay.
export default defineConfig({
  plugins: [react()],
  // Vega is ~850 kB minified. It's lazy-loaded (Charts.jsx), so the first screen doesn't wait for it.
  build: { chunkSizeWarningLimit: 900 },
  server: {
    proxy: { "/api": "http://127.0.0.1:5001" },
  },
});
