import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#070708",
        panel: "#101012",
        acid: "#c7ff4a",
      },
      boxShadow: {
        glow: "0 0 36px rgba(199, 255, 74, 0.18)",
      },
    },
  },
  plugins: [],
} satisfies Config;
