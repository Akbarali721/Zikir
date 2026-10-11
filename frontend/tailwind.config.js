/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js}"],
  theme: {
    extend: {
      colors: {
        cream: "#F6F0E5",
        ivory: "#FBF7EF",
        forest: "#123F35",
        emerald: {
          DEFAULT: "#0F5A4D",
          mid: "#246B5B",
        },
        gold: {
          DEFAULT: "#CFAE6A",
          soft: "#E7D4AA",
        },
        muted: "#66736E",
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', "Georgia", "serif"],
        sans: ['"Manrope"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
