import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
    "./context/**/*.{js,jsx,ts,tsx}",
    "./lib/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background) / <alpha-value>)",
        foreground: "hsl(var(--foreground) / <alpha-value>)",
        card: "hsl(var(--card) / <alpha-value>)",
        "card-foreground": "hsl(var(--card-foreground) / <alpha-value>)",
        popover: "hsl(var(--popover) / <alpha-value>)",
        "popover-foreground": "hsl(var(--popover-foreground) / <alpha-value>)",
        primary: "hsl(var(--primary) / <alpha-value>)",
        "primary-foreground": "hsl(var(--primary-foreground) / <alpha-value>)",
        secondary: "hsl(var(--secondary) / <alpha-value>)",
        "secondary-foreground": "hsl(var(--secondary-foreground) / <alpha-value>)",
        muted: "hsl(var(--muted) / <alpha-value>)",
        "muted-foreground": "hsl(var(--muted-foreground) / <alpha-value>)",
        accent: "hsl(var(--accent) / <alpha-value>)",
        "accent-foreground": "hsl(var(--accent-foreground) / <alpha-value>)",
        border: "hsl(var(--border) / <alpha-value>)",
        input: "hsl(var(--input) / <alpha-value>)",
        ring: "hsl(var(--ring) / <alpha-value>)",
        success: "hsl(var(--success) / <alpha-value>)",
        "success-surface": "hsl(var(--success-surface) / <alpha-value>)",
        warning: "hsl(var(--warning) / <alpha-value>)",
        "warning-surface": "hsl(var(--warning-surface) / <alpha-value>)",
        danger: "hsl(var(--danger) / <alpha-value>)",
        "danger-surface": "hsl(var(--danger-surface) / <alpha-value>)",
        "neutral-surface": "hsl(var(--neutral-surface) / <alpha-value>)",
        canvas: "#F7F5F0",
        surface: "#FFFDF9",
        panel: "#F2F1EC",
        night: "#111B1A",
        "night-surface": "#17211F",
        emerald: {
          50: "#E7F1EC",
          100: "#DCEEE7",
          500: "#1F6B58",
          600: "#1B584A",
          700: "#184B40",
        },
        sage: {
          50: "#EDF2EE",
          100: "#DCE1DB",
          500: "#6D7773",
          600: "#4E5C59",
        },
        ink: {
          950: "#17211F",
          900: "#1A2523",
          800: "#2C3734",
          700: "#465754",
          600: "#60706B",
          500: "#73817D",
        },
        paper: {
          50: "#F9F7F3",
          100: "#F3F1EC",
          200: "#EAE4DF",
        },
        saffron: {
          50: "#FBF6E9",
          100: "#F3E7C7",
          500: "#C7913A",
          600: "#A9702A",
        },
        clay: {
          50: "#F9EEE9",
          100: "#F1DCD6",
          500: "#B55B50",
          600: "#944B43",
        },
        pass: {
          DEFAULT: "#1F6B58",
          bg: "#E7F1EC",
          fg: "#1A5346",
        },
        fail: {
          DEFAULT: "#B55B50",
          bg: "#F8EEEC",
          fg: "#8A403C",
        },
        review: {
          DEFAULT: "#C7913A",
          bg: "#FBF6E9",
          fg: "#8B5D21",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      backgroundImage: {
        "hero-wash": "linear-gradient(135deg, #F7F5F0 0%, #EEF4F0 45%, #F9F4EA 100%)",
        "inspection-grid":
          "linear-gradient(rgba(31,107,88,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(31,107,88,0.06) 1px, transparent 1px)",
        "brass-grid":
          "linear-gradient(rgba(199,145,58,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(199,145,58,0.08) 1px, transparent 1px)",
        "ink-radial":
          "radial-gradient(circle at 20% 20%, rgba(199,145,58,0.12), transparent 40%), radial-gradient(circle at 80% 70%, rgba(31,107,88,0.15), transparent 48%)",
      },
      keyframes: {
        scanline: {
          "0%": { top: "0%" },
          "100%": { top: "100%" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(0.9)", opacity: "0.6" },
          "100%": { transform: "scale(1.35)", opacity: "0" },
        },
        drift: {
          "0%": { transform: "translate3d(0,0,0)" },
          "50%": { transform: "translate3d(0,-6px,0)" },
          "100%": { transform: "translate3d(0,0,0)" },
        },
      },
      animation: {
        scanline: "scanline 2.2s ease-in-out infinite alternate",
        "fade-up": "fade-up 0.5s ease-out both",
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.4,0,0.6,1) infinite",
        drift: "drift 10s ease-in-out infinite",
      },
      boxShadow: {
        glass: "0 8px 32px rgba(23,33,31,0.08)",
        card: "0 18px 38px rgba(23,33,31,0.06), 0 2px 8px rgba(23,33,31,0.04)",
        "card-hover": "0 22px 48px rgba(23,33,31,0.10), 0 4px 10px rgba(23,33,31,0.05)",
        hero: "0 24px 60px rgba(23,33,31,0.14)",
        seal: "inset 0 0 0 1px rgba(31,107,88,0.18)",
      },
    },
  },
  plugins: [],
};

export default config;
