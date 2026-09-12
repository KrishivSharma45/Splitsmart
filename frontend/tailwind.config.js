/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        cream: {
          DEFAULT: "#F2EEE6",
          soft: "#F7F4ED",
          card: "#FBF9F4",
        },
        ink: {
          DEFAULT: "#17160F",
          soft: "#454234",
          faint: "#8A8672",
        },
        line: "#E3DDCC",
        accent: {
          green: "#3D6B4C",
          amber: "#B4762A",
          red: "#A5402F",
        },
      },
      fontFamily: {
        serif: ["Fraunces", "ui-serif", "Georgia", "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        xl: "0.85rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [],
};
