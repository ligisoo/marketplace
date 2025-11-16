/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html", 
    "./static/js/*.js",
    "./apps/**/static/**/*.js"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Ligisooke color system
        background: 'hsl(227, 27%, 14%)', // Dark Blue/Indigo
        foreground: 'hsl(0, 0%, 98%)',
        card: 'hsl(227, 27%, 18%)',
        'card-foreground': 'hsl(0, 0%, 98%)',
        border: 'hsl(227, 27%, 22%)',
        primary: 'hsl(120, 50%, 60%)', // Bright Green
        'primary-foreground': 'hsl(227, 27%, 14%)',
        secondary: 'hsl(227, 27%, 20%)',
        'secondary-foreground': 'hsl(0, 0%, 98%)',
        accent: 'hsl(39, 86%, 62%)', // Gold/Yellow
        'accent-foreground': 'hsl(227, 27%, 14%)',
        muted: 'hsl(227, 27%, 25%)',
        'muted-foreground': 'hsl(0, 0%, 65%)'
      },
      fontFamily: {
        body: ['"PT Sans"', 'sans-serif'],
        headline: ['"PT Sans"', 'serif'],
        sans: ['"PT Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography')
  ]
}