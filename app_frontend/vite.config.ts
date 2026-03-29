import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { sentryVitePlugin } from "@sentry/vite-plugin";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: false,
      includeAssets: ["favicon.svg", "icons/forewise-tree.svg"],
      manifest: {
        name: "Forewise — מערכת לניהול פרויקטים ויערות",
        short_name: "Forewise",
        description: "מערכת לניהול פרויקטים, הזמנות עבודה, דיווחים, ספקים וציוד",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#00994C",
        orientation: "portrait-primary",
        lang: "he",
        dir: "rtl",
        icons: [
          {
            src: "/icons/forewise-tree.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any",
          },
          {
            src: "/favicon.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any",
          },
        ],
        categories: ["productivity", "utilities"],
        shortcuts: [
          {
            name: "פרויקטים",
            short_name: "פרויקטים",
            url: "/projects",
            description: "פתח את רשימת הפרויקטים",
          },
          {
            name: "ממתינים לסנכרון",
            short_name: "סנכרון",
            url: "/pending-sync",
            description: "צפה בפריטים שנשמרו אופליין וממתינים לסנכרון",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,ico,webp,json}"],
        navigateFallback: "/index.html",
        cleanupOutdatedCaches: true,
        runtimeCaching: [
          {
            urlPattern: ({ request }) => request.destination === "document",
            handler: "NetworkFirst",
            options: {
              cacheName: "pages-cache",
              networkTimeoutSeconds: 3,
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 7 * 24 * 60 * 60,
              },
            },
          },
          {
            urlPattern: ({ request }) =>
              request.destination === "script" ||
              request.destination === "style" ||
              request.destination === "worker",
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "assets-cache",
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 30 * 24 * 60 * 60,
              },
            },
          },
          {
            urlPattern: ({ request }) => request.destination === "image",
            handler: "CacheFirst",
            options: {
              cacheName: "images-cache",
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 30 * 24 * 60 * 60,
              },
            },
          },
        ],
      },
      devOptions: {
        enabled: false,
      },
    }),
    sentryVitePlugin({
      org: "forewise",
      project: "forewise-backend",
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
  base: "/",
  server: {
    port: 5173,
    strictPort: true,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html')
      }
    }
  },
  define: {
    'process.env.VITE_GOOGLE_MAPS_API_KEY': JSON.stringify(process.env.VITE_GOOGLE_MAPS_API_KEY),
    'process.env': {},
    global: {}
  },
  optimizeDeps: {
    exclude: ['electron']
  }
});