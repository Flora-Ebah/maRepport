import type { Config } from "tailwindcss";

/**
 * MA2E Trésorerie — Design System
 *
 * Inspiration : banques européennes (Société Générale, BNP Paribas, ING).
 * Règles imposées :
 *   - TOUT CARRÉ : borderRadius = 0 partout (aucun arrondi, même avatars).
 *   - AUCUNE BORDURE : la séparation se fait par aplats de fond / contraste.
 *   - Palette bleu marine + neutres zinc, densité d'information élevée.
 *   - Typographie Sen, échelle compacte.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    container: { center: true, padding: "1.5rem", screens: { "2xl": "1400px" } },
    extend: {
      colors: {
        primary: {
          50: "#F0F5FA", 100: "#DEEBF7", 200: "#B6D2EA", 300: "#8AB6DC",
          400: "#5B97CC", 500: "#2E75B6", 600: "#1F4E79", 700: "#173D60",
          800: "#102C47", 900: "#0A1D30", 950: "#050F1A",
        },
        neutral: {
          50: "#FAFAFA", 100: "#F4F4F5", 200: "#E4E4E7", 300: "#D4D4D8",
          400: "#A1A1AA", 500: "#71717A", 600: "#52525B", 700: "#3F3F46",
          800: "#27272A", 900: "#18181B", 950: "#0A0A0B",
        },
        success: { DEFAULT: "#548235", light: "#E8F0DE", dark: "#3E6126" },
        warning: { DEFAULT: "#ED7D31", light: "#FCE8D9", dark: "#B85E25" },
        danger: { DEFAULT: "#C9302C", light: "#F9DEDD", dark: "#962420" },
        info: { DEFAULT: "#7030A0", light: "#EFE3F4", dark: "#542477" },
        background: "#F4F4F5",
        foreground: "#18181B",
        muted: "#F4F4F5",
        "muted-foreground": "#71717A",
      },
      fontFamily: {
        sans: ['"Sen"', "system-ui", "Segoe UI", "Roboto", "Arial", "sans-serif"],
        display: ['"Sen"', "system-ui", "Segoe UI", "Roboto", "Arial", "sans-serif"],
        mono: ['"JetBrains Mono"', "Menlo", "Consolas", "monospace"],
      },
      fontSize: {
        xs: ["11px", { lineHeight: "16px", letterSpacing: "0.01em" }],
        sm: ["13px", { lineHeight: "20px" }],
        base: ["14px", { lineHeight: "22px" }],
        lg: ["16px", { lineHeight: "24px" }],
        xl: ["18px", { lineHeight: "26px" }],
        "2xl": ["22px", { lineHeight: "30px", letterSpacing: "-0.01em" }],
        "3xl": ["28px", { lineHeight: "36px", letterSpacing: "-0.02em" }],
        "4xl": ["36px", { lineHeight: "44px", letterSpacing: "-0.02em" }],
      },
      borderRadius: {
        // TOUT CARRÉ — aucun arrondi nulle part.
        none: "0", DEFAULT: "0", sm: "0", md: "0", lg: "0", xl: "0", "2xl": "0", "3xl": "0", full: "0",
      },
      boxShadow: {
        none: "none",
        sm: "0 1px 0 rgba(0,0,0,0.04)",
        DEFAULT: "0 1px 2px rgba(0,0,0,0.05)",
      },
      spacing: { "4.5": "18px", "5.5": "22px", "7.5": "30px", "13": "52px", "15": "60px" },
      animation: { "fade-in": "fadeIn .15s ease-in-out" },
      keyframes: { fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } } },
    },
  },
  plugins: [],
};

export default config;
