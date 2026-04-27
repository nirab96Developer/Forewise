// src/components/common/VersionFooter.tsx
//
// Phase 3 Wave 2.6 — small, unobtrusive version stamp at the bottom
// of the screen. Reads VITE_APP_VERSION from .env at build time.
// Frontend doesn't fetch /version at runtime to keep the bundle
// size + initial paint tight; the env-var approach matches the
// build artifact 1:1.

import React from "react";

const APP_VERSION =
  (import.meta.env.VITE_APP_VERSION as string | undefined) || "dev";

const VersionFooter: React.FC = () => {
  return (
    <div
      dir="rtl"
      className="fixed bottom-1 left-2 z-10 text-[10px] text-gray-400 select-none pointer-events-none"
      aria-label={`גרסת המערכת: ${APP_VERSION}`}
      title={`גרסת המערכת: ${APP_VERSION}`}
    >
      v{APP_VERSION}
    </div>
  );
};

export default VersionFooter;
