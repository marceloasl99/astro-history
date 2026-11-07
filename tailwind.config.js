/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./src/web/templates/**/*.html",
    "./src/web/static/js/**/*.js",
    "./src/**/*.py"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"Cinzel"', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace']
      },
      colors: {
        astro: {
          950: '#03050a',
          900: '#060913',
          850: '#0b1120',
          800: '#0f172a',
          700: '#1e293b',
          600: '#334155',
          gold: '#fbbf24',
          amber: '#f59e0b',
          cyan: '#38bdf8',
          sky: '#0284c7',
          purple: '#a855f7',
          indigo: '#818cf8',
          rose: '#f43f5e',
          emerald: '#10b981'
        }
      }
    }
  },
  plugins: []
}
