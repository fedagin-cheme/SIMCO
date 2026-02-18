export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: { 400: '#2dd4bf', 500: '#14b8a6', 600: '#0d9488' },
        surface: {
          400: '#484f58',
          500: '#30363d',
          600: '#21262d',
          700: '#1c2128',
          800: '#161b22',
          900: '#0f1117',
        },
      },
    },
  },
  plugins: [],
}
