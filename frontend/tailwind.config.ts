import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Design system color tokens mapped to CSS variables
        ink: {
          DEFAULT: "var(--color-ink)",
          muted: "var(--color-ink-muted)",
        },
        paper: {
          DEFAULT: "var(--color-paper)",
          raised: "var(--color-paper-raised)",
        },
        forest: {
          DEFAULT: "var(--color-forest)",
          hover: "var(--color-forest-hover)",
        },
        brass: {
          DEFAULT: "var(--color-brass)",
          soft: "var(--color-brass-soft)",
        },
        teal: {
          DEFAULT: "var(--color-teal)",
        },
        clay: {
          alert: "var(--color-clay-alert)",
        },
        line: "var(--color-line)",

        // shadcn/ui palette mapping
        primary: {
          DEFAULT: "var(--color-forest)",
          foreground: "#FFFFFF",
        },
        background: "var(--color-paper)",
        foreground: "var(--color-ink)",
        card: {
          DEFAULT: "var(--color-paper-raised)",
          foreground: "var(--color-ink)",
        },
        muted: {
          DEFAULT: "var(--color-paper)",
          foreground: "var(--color-ink-muted)",
        },
        border: "var(--color-line)",
      },
      fontFamily: {
        display: ["var(--font-display)", "Fraunces", "serif"],
        body: ["var(--font-body)", "IBM Plex Sans", "sans-serif"],
        mono: ["var(--font-mono)", "IBM Plex Mono", "monospace"],
        sans: ["var(--font-body)", "IBM Plex Sans", "sans-serif"],
      },
      fontSize: {
        "display-xl": ["3.5rem", { lineHeight: "1.05" }],
        "display-lg": ["2.5rem", { lineHeight: "1.1" }],
        "display-md": ["1.75rem", { lineHeight: "1.2" }],
        "body-lg": ["1.125rem", { lineHeight: "1.6" }],
        body: ["1rem", { lineHeight: "1.6" }],
        "body-sm": ["0.875rem", { lineHeight: "1.5" }],
        "data-lg": ["2rem", { lineHeight: "1" }],
        data: ["0.875rem", { lineHeight: "1.4" }],
      },
      borderRadius: {
        md: "0.375rem", // 6px for buttons/inputs
        xl: "0.75rem", // 12px for cards
      },
    },
  },
  plugins: [],
};

export default config;
