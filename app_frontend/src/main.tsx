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

function showUpdateBanner(version?: string) {
  if (document.getElementById("forewise-update-banner")) return;
  const banner = document.createElement("div");
  banner.id = "forewise-update-banner";
  banner.dir = "rtl";
  banner.style.cssText =
    "position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:9999;" +
    "background:#1a6b3a;color:#fff;padding:12px 20px;border-radius:14px;" +
    "box-shadow:0 8px 32px rgba(0,0,0,0.25);display:flex;align-items:center;gap:12px;" +
    "font-family:Heebo,sans-serif;font-size:14px;max-width:90vw;animation:slideUp .4s ease";
  banner.innerHTML =
    `<span>🌲 גרסה חדשה${version ? " " + version : ""} זמינה</span>` +
    `<button onclick="window.location.reload()" style="background:#fff;color:#1a6b3a;border:none;` +
    `padding:6px 16px;border-radius:8px;font-weight:700;cursor:pointer;font-family:inherit;font-size:13px">` +
    `עדכן עכשיו</button>` +
    `<button onclick="this.parentElement.remove()" style="background:none;border:none;color:#fff;` +
    `cursor:pointer;font-size:18px;padding:0 4px">✕</button>`;
  document.body.appendChild(banner);
}
