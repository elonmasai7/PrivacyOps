import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        baobab: {
          50: "#eef9f1",
          100: "#d5f2dc",
          200: "#b0e6be",
          300: "#84d69c",
          400: "#57bc78",
          500: "#349a5b",
          600: "#247f49",
          700: "#1e653d",
          800: "#1a5133",
          900: "#16432d"
        },
        savanna: {
          50: "#fffaf0",
          100: "#fff1d6",
          200: "#ffe1ad",
          300: "#ffcb7b",
          400: "#f5b04e",
          500: "#df8e22",
          600: "#b76f15",
          700: "#8f540f",
          800: "#713f10",
          900: "#5f3412"
        },
        slatecoast: {
          900: "#0f1a26",
          800: "#15273a",
          700: "#1f3348"
        }
      }
    },
  },
  plugins: [],
};

export default config;
