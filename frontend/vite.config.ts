/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: process.env.BACKEND_URL ?? 'http://localhost:8000', changeOrigin: true },
    },
  },
  // Unit tests only: e2e/ holds Playwright specs, which blow up when Vitest
  // collects them.
  test: { include: ['src/**/*.test.ts'] },
})
