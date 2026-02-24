import React from "react" 
import ReactDOM from "react-dom/client" 
import { BrowserRouter } from "react-router-dom" 
import App from "./App" 
import { AuthProvider } from "./contexts/AuthContext"
import "./index.css"  

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
      navigator.serviceWorker.register("/sw.js").catch((err) => {
        console.error("Service worker registration failed:", err);
      });
    });
  }
}
