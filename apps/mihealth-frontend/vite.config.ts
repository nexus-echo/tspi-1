import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server on 5173. Proxy /api -> MiHealth backend so the SPA uses same-origin calls.
export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,

    allowedHosts: [
      "nexusneural.pro",
      "www.nexusneural.pro",
    ],

    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://localhost:8001",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
