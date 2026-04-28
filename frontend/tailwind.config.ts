import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fff1f0",
          100: "#ffdedb",
          200: "#ffb8b0",
          300: "#ff8a7c",
          400: "#ff5f4c",
          500: "#ff4533",
          600: "#e22d1b",
          700: "#b82315",
          800: "#891810",
          900: "#5d100a",
        },
        violet: {
          300: "#c4b5fd",
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
        },
        accent: {
          400: "#c084fc",
          500: "#a855f7",
          600: "#9333ea",
        },
        pink: {
          400: "#f472b6",
          500: "#ec4899",
          600: "#db2777",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["'Plus Jakarta Sans'", "Inter", "sans-serif"],
      },
      boxShadow: {
        glass: "0 8px 32px rgba(15,23,42,0.06)",
        "glass-dark": "0 12px 38px rgba(0,0,0,0.55)",
        glow: "0 0 0 1px rgba(255,255,255,0.06), 0 14px 50px -16px rgba(168,85,247,0.55)",
        "glow-brand": "0 0 0 1px rgba(255,255,255,0.06), 0 14px 50px -16px rgba(255,69,51,0.55)",
        soft: "0 6px 20px rgba(15,23,42,0.06)",
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg,#ff5f4c 0%,#ff4533 45%,#ec4899 100%)",
        "neon-gradient":
          "linear-gradient(135deg,#a855f7 0%,#8b5cf6 45%,#ec4899 100%)",
        "dark-hero":
          "radial-gradient(1200px 600px at 70% -10%, rgba(168,85,247,0.32), transparent 60%), radial-gradient(800px 400px at 10% 10%, rgba(236,72,153,0.18), transparent 60%)",
      },
      animation: {
        "fade-up": "fadeUp .5s ease-out both",
        "pulse-soft": "pulseSoft 2.4s ease-in-out infinite",
        "spin-slow": "spin 14s linear infinite",
      },
      keyframes: {
        fadeUp: { "0%": { opacity: "0", transform: "translateY(12px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        pulseSoft: { "0%,100%": { opacity: "0.6" }, "50%": { opacity: "1" } },
      },
    },
  },
  plugins: [],
} satisfies Config;
