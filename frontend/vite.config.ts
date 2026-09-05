import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      // Service workers are disabled by default under `vite dev` (only
      // active after a production build) — enabled here too since demos
      // and manual offline-testing typically run against the dev server.
      devOptions: { enabled: true, type: 'module' },
      manifest: {
        name: 'AgriNova',
        short_name: 'AgriNova',
        description: 'AI-powered smart agriculture command center',
        theme_color: '#08110D',
        background_color: '#08110D',
        display: 'standalone',
        icons: [{ src: '/favicon.svg', sizes: 'any', type: 'image/svg+xml' }],
      },
      workbox: {
        // App shell + static assets: served from cache first (they don't
        // change between deploys of the same build), falling back to the
        // network only on a cache miss.
        globPatterns: ['**/*.{js,css,html,svg,woff2}'],
        // Live data (sensor readings, AI predictions, alerts, market/scheme
        // data) always tries the network first so it's never stale when
        // online — but falls back to the last successful response when
        // offline, so the dashboard shows "last known" data instead of a
        // blank/broken screen with no connectivity.
        runtimeCaching: [
          {
            urlPattern: ({ url, sameOrigin }) => sameOrigin && url.pathname.startsWith('/api/') && url.pathname !== '/api/auth/me',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'agrinova-api-cache',
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 }, // 1 day
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    host: true, // listen on 0.0.0.0 so phones on the same LAN can reach it
    port: 5173,
    strictPort: true,
  },
})
