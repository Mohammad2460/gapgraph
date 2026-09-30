import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // Shared demo data lives at repo root so backend + frontend use the SAME fixtures.
    alias: { '@fixtures': path.resolve(import.meta.dirname, '../fixtures') },
  },
  server: {
    fs: { allow: ['..'] },
    proxy: { '/api': 'http://localhost:8000' },
  },
})
