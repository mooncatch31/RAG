/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./public/index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f1f5ff',
          100: '#e5edff',
          600: '#3b6cff',
          700: '#2b55d6',
          800: '#1f3ea8'
        }
      }
    },
  },
  plugins: [],
}

