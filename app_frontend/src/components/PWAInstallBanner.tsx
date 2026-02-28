// PWAInstallBanner.tsx
// iOS Safari install prompt — shown once per session when user hasn't installed the app

import React, { useState, useEffect } from "react";
import { X, Share, PlusSquare } from "lucide-react";

const DISMISSED_KEY = "pwa-install-dismissed";

const PWAInstallBanner: React.FC = () => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Only show on iOS Safari when running in browser (not standalone)
    const isIOS =
      /iphone|ipad|ipod/i.test(navigator.userAgent) ||
      // iPad on iOS 13+ reports as "MacIntel" with touch
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

    const isSafari =
      /safari/i.test(navigator.userAgent) &&
      !/chrome|crios|fxios|android/i.test(navigator.userAgent);

    const isStandalone =
      ("standalone" in navigator && (navigator as any).standalone === true) ||
      window.matchMedia("(display-mode: standalone)").matches;

    const dismissed = sessionStorage.getItem(DISMISSED_KEY);

    if (isIOS && isSafari && !isStandalone && !dismissed) {
      // Small delay so it doesn't pop immediately
      const t = setTimeout(() => setVisible(true), 2500);
      return () => clearTimeout(t);
    }
  }, []);

  const dismiss = () => {
    setVisible(false);
    sessionStorage.setItem(DISMISSED_KEY, "1");
  };

  if (!visible) return null;

  return (
    <div
      dir="rtl"
      className="fixed bottom-0 inset-x-0 z-50 px-4 pb-safe-area-inset-bottom"
      style={{ paddingBottom: "env(safe-area-inset-bottom, 16px)" }}
    >
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-4 mb-4 flex items-start gap-3 animate-slide-up">
        {/* KKL green accent bar */}
        <div className="flex-shrink-0 w-1 self-stretch bg-[#00994C] rounded-full" />

        <div className="flex-1 min-w-0">
          <p className="font-bold text-slate-800 text-sm mb-1">
            הוסף לשולחן הבית לחוויה מלאה
          </p>
          <p className="text-slate-500 text-xs leading-relaxed">
            לחץ על{" "}
            <Share
              className="inline w-4 h-4 text-blue-500 mx-0.5"
              aria-label="שתף"
            />
            ואז בחר{" "}
            <span className="font-medium text-slate-700">
              &quot;הוסף למסך הבית&quot;
            </span>{" "}
            <PlusSquare className="inline w-4 h-4 text-slate-600 mx-0.5" />
          </p>
        </div>

        <button
          onClick={dismiss}
          aria-label="סגור"
          className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 hover:bg-slate-200 active:bg-slate-300 transition-colors"
        >
          <X className="w-4 h-4 text-slate-500" />
        </button>
      </div>
    </div>
  );
};

export default PWAInstallBanner;
