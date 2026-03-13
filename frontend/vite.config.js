import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy Dash dashboard (and all its assets) to local Dash server
      '/analytics': { target: 'http://localhost:8050', changeOrigin: true },
      // Proxy API calls to local FastAPI server
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})



