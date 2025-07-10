import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "0.0.0.0", // Cambiado de "::" a "0.0.0.0" para mejor compatibilidad
    port: 3000,
    allowedHosts: ["ai.huntred.com"], // Permitir acceso desde el dominio
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  plugins: [
    react(),
    // Removido lovable-tagger que causa error ESM
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-checkbox', '@radix-ui/react-slider', '@radix-ui/react-tooltip'],
        },
      },
    },
  },
  preview: {
    host: "0.0.0.0",
    allowedHosts: ["ai.huntred.com"], // <-- Agrega esto
    port: 3000,
  },
}));
