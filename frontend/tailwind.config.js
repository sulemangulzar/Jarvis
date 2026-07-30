/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        mist: "#f5f7fb",
        electric: "#2563eb",
      },
      boxShadow: {
        card: "0 24px 70px rgba(15, 23, 42, 0.10)",
      },
    },
  },
  plugins: [],
};
