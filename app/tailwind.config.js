/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/src/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#E63946',
          light: '#F8D7DA',
          dark: '#721C24'
        },
        secondary: {
          DEFAULT: '#1D3557',
          light: '#D1E7FF',
          dark: '#0A1A33'
        },
        accent: {
          DEFAULT: '#457B9D',
          light: '#E3F2FD',
          dark: '#1A365D'
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
