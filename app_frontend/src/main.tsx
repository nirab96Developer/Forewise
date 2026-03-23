import React from "react" 
import ReactDOM from "react-dom/client" 
import { BrowserRouter } from "react-router-dom" 
import * as Sentry from "@sentry/react";
import App from "./App" 
import { AuthProvider } from "./contexts/AuthContext"
import "./index.css"  

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN as string | undefined,
  environment: import.meta.env.MODE,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration({
      maskAllText: false,
      blockAllMedia: false,
    }),
  ],
  tracesSampleRate: 1.0,
  replaysOnErrorSampleRate: 1.0,
  enabled: !!(import.meta.env.VITE_SENTRY_DSN) && import.meta.env.MODE === "production",
});

window.addEventListener('vite:preloadError', () => {
  const reloadKey = "forewise_chunk_reload";
  const lastReload = sessionStorage.getItem(reloadKey);
  const now = Date.now();
  if (!lastReload || now - parseInt(lastReload) > 10000) {
    sessionStorage.setItem(reloadKey, String(now));
    window.location.reload();
  }
});

window.addEventListener("error", (e) => {
  if (
    e.message?.includes("Failed to fetch dynamically imported module") ||
    e.message?.includes("Importing a module script failed") ||
    e.message?.includes("error loading dynamically imported module")
  ) {
    const reloadKey = "forewise_chunk_reload";
    const lastReload = sessionStorage.getItem(reloadKey);
    const now = Date.now();
    if (!lastReload || now - parseInt(lastReload) > 10000) {
      sessionStorage.setItem(reloadKey, String(now));
      window.location.reload();
    }
  }
});

window.addEventListener("unhandledrejection", (e) => {
  const msg = e.reason?.message || String(e.reason || "");
  if (
    msg.includes("Failed to fetch dynamically imported module") ||
    msg.includes("Importing a module script failed") ||
    msg.includes("error loading dynamically imported module")
  ) {
    const reloadKey = "forewise_chunk_reload";
    const lastReload = sessionStorage.getItem(reloadKey);
    const now = Date.now();
    if (!lastReload || now - parseInt(lastReload) > 10000) {
      sessionStorage.setItem(reloadKey, String(now));
      window.location.reload();
    }
  }
});

ReactDOM.createRoot(document.getElementById("root")!).render(   
  <React.StrictMode>     
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>   
  </React.StrictMode> 
)

if ("serviceWorker" in navigator) {
  const isProd = import.meta.env.PROD;
  const isLocalhost =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";

  // Never keep an active SW on Vite dev localhost.
  if (!isProd || isLocalhost) {
    navigator.serviceWorker.getRegistrations().then((regs) => {
      regs.forEach((reg) => reg.unregister());
    });
    caches.keys().then((keys) => {
      keys.forEach((key) => caches.delete(key));
    });
  } else {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").then((reg) => {
        // Check for updates every 5 minutes
        setInterval(() => reg.update(), 5 * 60 * 1000);

        reg.addEventListener("updatefound", () => {
          const newWorker = reg.installing;
          if (newWorker) {
            newWorker.addEventListener("statechange", () => {
              if (newWorker.state === "activated") {
                window.location.reload();
              }
            });
          }
        });
      }).catch((err) => {
        console.error("Service worker registration failed:", err);
      });
    });

    // SW update messages handled silently (no banner)
    navigator.serviceWorker.addEventListener("message", (event) => {
      if (event.data?.type === "APP_UPDATED") {
        // Auto-reload silently on update
        window.location.reload();
      }
    });
  }
}
