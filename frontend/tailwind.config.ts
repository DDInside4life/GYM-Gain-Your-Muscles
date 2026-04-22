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
          400: "#9f7aea",
          500: "#8b5cf6",
          600: "#7c3aed",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["'Plus Jakarta Sans'", "Inter", "sans-serif"],
      },
      boxShadow: {
        glass: "0 8px 32px rgba(0,0,0,0.08)",
        "glass-dark": "0 8px 32px rgba(0,0,0,0.45)",
        glow: "0 0 0 1px rgba(255,255,255,0.06), 0 10px 40px -10px rgba(139,92,246,0.45)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg,#ff5f4c 0%,#ff4533 45%,#8b5cf6 100%)",
        "dark-hero": "radial-gradient(1200px 600px at 70% -10%, rgba(139,92,246,0.35), transparent 60%), radial-gradient(800px 400px at 10% 10%, rgba(255,95,76,0.18), transparent 60%)",
      },
      animation: {
        "fade-up": "fadeUp .5s ease-out both",
        "pulse-soft": "pulseSoft 2.4s ease-in-out infinite",
      },
      keyframes: {
        fadeUp: { "0%": { opacity: "0", transform: "translateY(12px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        pulseSoft: { "0%,100%": { opacity: "0.6" }, "50%": { opacity: "1" } },
      },
    },
  },
  plugins: [],
} satisfies Config;
