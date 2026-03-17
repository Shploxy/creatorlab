import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        panel: "var(--panel)",
        line: "var(--line)",
        foreground: "var(--foreground)",
        muted: "var(--muted)",
        brand: {
          DEFAULT: "var(--brand)",
          soft: "var(--brand-soft)"
        },
        accent: "var(--accent)"
      },
      borderRadius: {
        xl2: "1.5rem"
      },
      boxShadow: {
        soft: "0 20px 60px rgba(15, 23, 42, 0.12)"
      },
      backgroundImage: {
        grid: "radial-gradient(circle at center, rgba(148, 163, 184, 0.18) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};

export default config;
