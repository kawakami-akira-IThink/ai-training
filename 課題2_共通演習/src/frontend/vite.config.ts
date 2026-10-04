import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 開発サーバのポートは 5173 固定（バックエンドの CORS 許可オリジンと一致させる）
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
