import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: "#eef4fb",
          100: "#d8e5f5",
          200: "#b4ccea",
          300: "#84aad9",
          400: "#547fbe",
          500: "#3b639f",
          600: "#2f4f82",
          700: "#1f355f",
          800: "#152544",
          900: "#0f1d36"
        },
        gov: {
          success: "#1f8f4b",
          danger: "#c42f2f",
          warning: "#b7791f"
        }
      },
      boxShadow: {
        gov: "0 10px 30px rgba(15, 29, 54, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;
