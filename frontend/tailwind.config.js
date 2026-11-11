/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          700: '#1b365d',
          800: '#102a43',
          900: '#0b1d3a',
          950: '#061024',
        },
        biomedical: {
          teal: '#0d9488',
          tealLight: '#14b8a6',
          blue: '#2563eb',
          cyan: '#06b6d4',
          surface: '#0f172a',
          surfaceCard: '#1e293b',
          surfaceBorder: '#334155',
        }
      }
    },
  },
  plugins: [],
}

