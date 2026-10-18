import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    svelte(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg'],
      manifest: {
        name: 'Holdover',
        short_name: 'Holdover',
        description: 'Oregon fishing planner and journal',
        theme_color: '#0b1613',
        background_color: '#0b1613',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,woff2,pbf}'],
        navigateFallbackDenylist: [/^\/api\//, /^\/healthz/, /^\/tiles\//, /^\/fonts\//],
        runtimeCaching: [
          {
            // /api/auth and /api/me are never cached: they say who is signed in. /api/day is excluded on purpose: the app keeps its own IndexedDB copy with an explicit as-of time,
            // so an offline fetch must fail rather than silently return old data labelled live.
            urlPattern: ({ url }) => url.pathname.startsWith('/api/') && !/^\/api\/(admin|day|journal|sync|auth|me)\//.test(url.pathname),
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'api-reads' }
          }
        ]
      }
    })
  ],
  server: {
    proxy: Object.fromEntries(['/api', '/healthz', '/tiles'].map((p) => [p, process.env.API_URL || 'http://localhost:8000']))
  }
});
