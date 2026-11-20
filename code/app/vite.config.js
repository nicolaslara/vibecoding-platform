import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Behind a Modal connect token the page is served from a modal.host name over HTTPS,
// so the dev server must accept that host and the HMR client must dial port 443.
// Vite swaps its dependency cache by renaming the directory, so the cache lives in memory:
// made by this Sandbox, never part of a snapshot it wakes from.
export default defineConfig({
  plugins: [react()],
  cacheDir: '/dev/shm/vite',
  server: { host: true, port: 8080, allowedHosts: true, hmr: { clientPort: 443 } },
})
