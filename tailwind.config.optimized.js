/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class", "[data-theme=\"dark\"]"],
  content: [
    "./app/templates/**/*.{html,js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}",
    "./index.html",
    "./app/templates/**/*.html",
    "./app/templates/front/src/**/*.{js,ts,jsx,tsx}",
    "./static/src/**/*.js",
    "./app/templates/front/src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/templates/front/src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/templates/front/src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/templates/front/src/lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1400px'
      }
    },
    extend: {
      colors: {
        // Paleta principal moderna
        'huntred': {
          primary: '#2563EB',      // Azul más intenso
          secondary: '#1D4ED8',    // Azul oscuro
          tertiary: '#3B82F6',     // Azul claro
          light: '#60A5FA',        // Azul muy claro
          dark: '#1E40AF',         // Azul marino
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
          950: '#172554',
        },
        // Colores de interfaz
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))'
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))'
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))'
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))'
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))'
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))'
        },
        // Colores técnicos
        tech: {
          blue: '#2563EB',     // Azul más intenso
          blueLight: '#3B82F6',
          blueDark: '#1D4ED8',
          red: '#EF4444',
          green: '#10B981',    // Verde más intenso
          greenLight: '#34D399',
          greenDark: '#059669',
          cyan: '#06B6D4',     // Cian más intenso
          purple: '#8B5CF6',   // Mantenido para compatibilidad
        },
        // Colores de estado
        success: {
          DEFAULT: '#10B981',  // Verde más intenso
          light: '#34D399',
          dark: '#059669',
        },
        warning: {
          DEFAULT: '#F59E0B',
          light: '#FBBF24',    // Amarillo más claro
          dark: '#D97706',     // Naranja oscuro
        },
        error: {
          DEFAULT: '#EF4444',
          light: '#F87171',    // Rojo más claro
          dark: '#DC2626',     // Rojo más oscuro
        },
        info: {
          DEFAULT: '#3B82F6',  // Azul
          light: '#60A5FA',    // Azul claro
          dark: '#2563EB',     // Azul oscuro
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'accordion-down': {
          from: { height: 0 },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: 0 },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
      // Utilidades adicionales
      boxShadow: {
        'soft': '0 4px 14px 0 rgba(0, 0, 0, 0.05)',
        'soft-lg': '0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.025)',
        'glow': '0 0 15px rgba(79, 70, 229, 0.5)',
      },
      // Gradientes personalizados
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        // Degradados personalizados
        'gradient-blue-dark-light': 'linear-gradient(90deg, #1E40AF 0%, #3B82F6 100%)',
        'gradient-blue-red': 'linear-gradient(90deg, #1f3544 0%, #ff0000 100%)',  // Nuevo degradado azul oscuro a rojo
        'gradient-blue-green': 'linear-gradient(90deg, #1f3544 0%, #10B981 100%)',  // Azul oscuro a verde
        'gradient-red-green': 'linear-gradient(90deg, #ff0000 0%, #10B981 100%)',
        'gradient-cyan-blue': 'linear-gradient(90deg, #06B6D4 0%, #1f3544 100%)',  // Cian a azul oscuro
        'gradient-darkblue-red': 'linear-gradient(90deg, #1f3544 0%, #ff0000 100%)',  // Alias para el nuevo degradado
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/line-clamp'),
    require('@tailwindcss/aspect-ratio'),
    require('tailwindcss-animate'),
  ],
}
