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
        theme_color: '#0F1A17',
        background_color: '#0F1A17',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
        navigateFallbackDenylist: [/^\/api\//, /^\/healthz/, /^\/tiles\//],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/api/') && !url.pathname.startsWith('/api/admin/'),
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'api-reads' }
          }
        ]
      }
    })
  ],
  server: {
    proxy: { '/api': 'http://localhost:8000', '/healthz': 'http://localhost:8000', '/tiles': 'http://localhost:8000' }
  }
});
