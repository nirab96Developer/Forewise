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
                showUpdateBanner();
              }
            });
          }
        });
      }).catch((err) => {
        console.error("Service worker registration failed:", err);
      });
    });

    // Listen for update messages from SW
    navigator.serviceWorker.addEventListener("message", (event) => {
      if (event.data?.type === "APP_UPDATED") {
        showUpdateBanner(event.data.version);
      }
    });
  }
}

function showUpdateBanner(_version?: string) {
  if (document.getElementById("forewise-update-banner")) return;
  const banner = document.createElement("div");
  banner.id = "forewise-update-banner";
  banner.dir = "rtl";
  banner.style.cssText =
    "position:fixed;bottom:16px;right:16px;z-index:9999;" +
    "background:#fff;color:#333;padding:10px 14px;border-radius:12px;" +
    "box-shadow:0 4px 20px rgba(0,0,0,0.12);border:1px solid #e0e0e0;" +
    "display:flex;align-items:center;gap:10px;" +
    "font-family:Heebo,sans-serif;font-size:13px;" +
    "animation:slideUp .3s ease;max-width:280px";
  banner.innerHTML =
    `<div style="width:8px;height:8px;background:#2e7d32;border-radius:50%;flex-shrink:0;animation:pulse 2s infinite"></div>` +
    `<span style="flex:1;color:#555">עדכון זמין</span>` +
    `<button onclick="window.location.reload()" style="background:#2e7d32;color:#fff;border:none;` +
    `padding:5px 12px;border-radius:8px;font-weight:600;cursor:pointer;font-family:inherit;font-size:12px">` +
    `רענן</button>` +
    `<button onclick="this.parentElement.remove()" style="background:none;border:none;color:#bbb;` +
    `cursor:pointer;font-size:16px;padding:0 2px;line-height:1">✕</button>`;
  document.body.appendChild(banner);
}
