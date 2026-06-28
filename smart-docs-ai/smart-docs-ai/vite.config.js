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
        // Timeout đủ dài để Lambda cold start nạp mô hình (tối đa ~60 giây)
        proxyTimeout: 180000,
        timeout: 180000,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.log('[Vite Proxy Error]', err.message);
          });
          proxy.on('proxyReq', (proxyReq, req) => {
            console.log('[Vite Proxy]', req.method, req.url, '→ AWS Lambda');
          });
        },
      }
    }
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    }
  }
})
