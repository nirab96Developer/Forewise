/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_BASE_URL: string
  readonly VITE_GOOGLE_MAPS_API_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface Window {
  googleMapsLoaded?: boolean
  showToast?: (message: string, type?: 'success' | 'error' | 'warning' | 'info', duration?: number) => void
}

// הרחבה ל-Notification API
interface Notification {
  description?: string
  time?: Date | string
}





















