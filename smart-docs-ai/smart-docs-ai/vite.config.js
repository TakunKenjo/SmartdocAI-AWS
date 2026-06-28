import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from "@tailwindcss/vite";
import path from "path";
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    watch: {
      // Bỏ qua file db.json (tránh dẫn đến tình trạng web tự động reload khi file db.json thay đổi)
      // Ví dụ: nếu file nằm ở server/db.json
      ignored: ['**/db.json', '**/db/**']
    },
    proxy: {
      '/api': {
        target: 'https://d60866voq5.execute-api.us-east-1.amazonaws.com/prod',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path,
      }
    }
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    }
  }
})
