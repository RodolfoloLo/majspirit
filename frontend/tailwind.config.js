/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#102624",
          800: "#1a3735",
          700: "#214341",
        },
        rice: {
          50: "#f7f1e6",
          100: "#f2e9d8",
          200: "#e8dac1",
        },
        cinnabar: {
          500: "#8e2f2a",
          600: "#7b2824",
        },
        jade: {
          500: "#3f6a63",
          600: "#32564f",
        },
        brass: {
          400: "#b8975f",
          500: "#a9854c",
        },
      },
      fontFamily: {
        serifcn: ["Noto Serif SC", "serif"],
        brush: ["Ma Shan Zheng", "cursive"],
      },
      boxShadow: {
        paper: "0 16px 45px rgba(8, 27, 24, 0.18)",
        tile: "0 5px 0 #d5ccb8, 0 14px 20px rgba(21, 30, 28, 0.24)",
        tileStrong: "0 7px 0 #d5ccb8, 0 20px 24px rgba(14, 22, 21, 0.3)",
      },
    },
  },
  plugins: [],
}

