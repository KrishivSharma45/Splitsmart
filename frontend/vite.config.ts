import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Same-origin proxy so the backend's httpOnly refresh-token cookie
      // (SameSite=Lax) is sent on requests -- it would be silently dropped
      // as cross-site if the frontend called http://localhost:8000 directly.
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
