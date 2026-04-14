/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 🎨 KKL Official Palette - Hilan Style
        // Primary Greens
        "fw-green": "#00994C",
        "fw-green-dark": "#007A3B",
        "fw-green-light": "#DFF7EC",
        "fw-green-hover": "#007A3B",
        
        // Neutrals
        "fw-bg": "#F5F7F8",
        "fw-text": "#4A4A4A",
        "fw-gray-light": "#EAEAEA",
        "fw-border": "#DDDDDD",
        "fw-white": "#FFFFFF",
        
        // Status Colors
        "fw-success": "#0FA958",
        "fw-warning": "#F2C94C",
        "fw-error": "#EB5757",
        "fw-info": "#56CCF2",
        
        // Legacy support
        "fw-blue": "#0072C6",
        "fw-brown": "#795548",
        
        // Brand Colors (legacy)
        "brand-bg": "#F5F7F8",
        "brand-primary": "#009557",
        "brand-primary-dark": "#007A48",
        "brand-secondary": "#56CCF2",
        "brand-secondary-dark": "#0072C6",
        "brand-accent": "#009557",
        "brand-accent-dark": "#007A48",
        
        // Background Colors
        "bg-page": "#F5F7F8",
        
        // Text Colors
        "text-primary": "#4A4A4A",
        "text-secondary": "#6B7280",
        
        // Status Colors (legacy)
        "success-green": "#0FA958",
        "error-red": "#EB5757",
        "info-purple": "#56CCF2",
        "neutral-gray": "#9CA3AF",
        
        // Material Design Colors
        primary: {
          DEFAULT: "#2e7d32",
          variant: "#1b5e20",
        },
        secondary: {
          DEFAULT: "#1976d2",
          variant: "#0d47a1",
        },
        surface: "#ffffff",
        background: "#f5f5f5",
        error: "#f44336",
        "on-primary": "#ffffff",
        "on-secondary": "#ffffff",
        "on-surface": "#212121",
        "on-background": "#212121",
        "on-error": "#ffffff",
        
        // shadcn colors
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      animation: {
        fadeIn: "fadeIn 0.5s ease-out",
        slideUp: "slideUp 0.5s ease-out",
        slideDown: "slideDown 0.5s ease-out",
        shake: "shake 0.5s ease-in-out",
        shimmerKKL: "shimmerKKL 2s linear infinite",
        pulseKKL: "pulseKKL 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        scaleIn: "scaleIn 0.3s ease-out",
        slideIn: "slideIn 0.5s ease-out",
        glowKKL: "glowKKL 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shake: {
          "0%, 100%": { transform: "translateX(0)" },
          "10%, 30%, 50%, 70%, 90%": { transform: "translateX(-5px)" },
          "20%, 40%, 60%, 80%": { transform: "translateX(5px)" },
        },
        shimmerKKL: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        pulseKKL: {
          "0%, 100%": {
            backgroundColor: "rgb(0, 114, 198)",
            boxShadow: "0 0 15px rgba(0, 114, 198, 0.5)",
          },
          "33%": {
            backgroundColor: "rgb(76, 175, 80)",
            boxShadow: "0 0 15px rgba(76, 175, 80, 0.5)",
          },
          "66%": {
            backgroundColor: "rgb(121, 85, 72)",
            boxShadow: "0 0 15px rgba(121, 85, 72, 0.5)",
          },
        },
        scaleIn: {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        slideIn: {
          "0%": {
            transform: "translateX(20px)",
            opacity: "0",
          },
          "100%": {
            transform: "translateX(0)",
            opacity: "1",
          },
        },
        glowKKL: {
          "0%, 100%": {
            boxShadow:
              "0 0 5px rgba(0, 114, 198, 0.5), 0 0 20px rgba(0, 114, 198, 0.2)",
          },
          "33%": {
            boxShadow:
              "0 0 5px rgba(76, 175, 80, 0.5), 0 0 20px rgba(76, 175, 80, 0.2)",
          },
          "66%": {
            boxShadow:
              "0 0 5px rgba(121, 85, 72, 0.5), 0 0 20px rgba(121, 85, 72, 0.2)",
          },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};
