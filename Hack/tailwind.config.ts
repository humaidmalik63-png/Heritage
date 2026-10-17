import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        heritage: {
          deep: "#05070C",
          surface: "#11131A",
          elevated: "#1A1D27",
          line: "rgba(232, 209, 203, 0.15)",
        },
        ink: {
          primary: "#F2F4F7",
          secondary: "#A5ABB6",
          muted: "#6B7280",
        },
        accent: {
          gold: "#D4B483",
          metallic: "#C4C7CE",
          warm: "#E8D1CB",
        },
      },
      fontFamily: {
        editorial: ["Playfair Display", "Georgia", "serif"],
        garamond: ["Cormorant Garamond", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Manrope", "Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        "display-xl": ["clamp(2.5rem, 8vw, 6rem)", { lineHeight: "1.05", fontWeight: "600" }],
        "display-lg": ["clamp(2rem, 5vw, 3.5rem)", { lineHeight: "1.1", fontWeight: "600" }],
        "display-md": ["clamp(1.5rem, 4vw, 2.5rem)", { lineHeight: "1.15", fontWeight: "600" }],
      },
      spacing: {
        "section": "clamp(4rem, 12vh, 8rem)",
      },
      maxWidth: {
        content: "1400px",
      },
      animation: {
        "fade-up": "fadeUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) both",
        "fade-in": "fadeIn 0.6s ease both",
        "float": "float 6s ease-in-out infinite",
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "shimmer": "shimmer 2s linear infinite",
        "slide-up": "slideUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(40px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
      backgroundImage: {
        "gradient-gold": "linear-gradient(135deg, #D4B483 0%, #C4C7CE 50%, #E8D1CB 100%)",
        "gradient-heritage": "linear-gradient(180deg, #05070C 0%, #11131A 100%)",
      },
      boxShadow: {
        "gold-glow": "0 0 60px -12px rgba(212, 180, 131, 0.45)",
        "gold-soft": "0 8px 32px -8px rgba(212, 180, 131, 0.25)",
        "glass": "0 8px 32px -8px rgba(0, 0, 0, 0.6)",
      },
    },
  },
  plugins: [],
} satisfies Config;