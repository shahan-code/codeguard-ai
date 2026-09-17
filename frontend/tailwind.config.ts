import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0c11",
          900: "#0f121a",
          800: "#151923",
          700: "#1c212e",
          600: "#262c3b",
          500: "#3a4256",
        },
        mist: {
          400: "#5b6478",
          300: "#7d879c",
          200: "#a8b0c0",
          100: "#dde1e9",
          50: "#eef0f4",
        },
        signal: {
          600: "#4a5fd6",
          500: "#6c7ef0",
          400: "#8d9bf5",
        },
        risk: {
          low: "#4f8ff7",
          medium: "#e0a530",
          high: "#e2694b",
          critical: "#c23f52",
        },
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        sm: "4px",
        md: "6px",
        lg: "10px",
      },
    },
  },
  plugins: [],
};
export default config;
