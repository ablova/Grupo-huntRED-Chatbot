/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/src/**/*.js"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Brand colors
      colors: {
        huntred: {
          DEFAULT: '#E63946',
          50: '#FEEBED',
          100: '#FDD8DC',
          200: '#FAB0B9',
          300: '#F88996',
          400: '#F56173',
          500: '#E63946',
          600: '#D11F2C',
          700: '#A01822',
          800: '#6F1018',
          900: '#3D090E',
          950: '#24060A'
        },
        // Business Units
        huntredExecutive: {
          DEFAULT: '#1D3557',
          light: '#A8DADC',
          dark: '#0A1A33'
        },
        huntred: {
          DEFAULT: '#E63946',
          light: '#F1FAEE',
          dark: '#A4161A'
        },
        huntu: {
          DEFAULT: '#457B9D',
          light: '#A8DADC',
          dark: '#1D3557'
        },
        amigro: {
          DEFAULT: '#F4A261',
          light: '#F8EDEB',
          dark: '#E76F51'
        },
        // Status colors
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        info: '#3B82F6',
        // Dark mode colors
        dark: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
          950: '#030712'
        }
      },
      // Custom fonts
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'sans-serif'],
        mono: ['Fira Code', 'monospace']
      },
      // Custom animations
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'fade-in-up': 'fadeInUp 0.6s ease-out',
        'fade-in-down': 'fadeInDown 0.6s ease-out',
        'fade-in-left': 'fadeInLeft 0.6s ease-out',
        'fade-in-right': 'fadeInRight 0.6s ease-out',
        'pulse-slow': 'pulse 6s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 3s infinite',
        'float': 'float 6s ease-in-out infinite',
        'gradient-x': 'gradientX 8s ease infinite',
        'gradient-y': 'gradientY 8s ease infinite',
        'gradient-xy': 'gradientXY 8s ease infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        fadeInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        gradientX: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          },
        },
        gradientY: {
          '0%, 100%': {
            'background-size': '400% 400%',
            'background-position': 'center top'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'center center'
          },
        },
        gradientXY: {
          '0%, 100%': {
            'background-position': '0% 50%',
            'background-size': '200% 200%',
          },
          '50%': {
            'background-position': '100% 50%',
            'background-size': '200% 200%',
          },
        },
      },
      // Custom shadows
      boxShadow: {
        'soft': '0 10px 25px -5px rgba(0, 0, 0, 0.03), 0 8px 10px -6px rgba(0, 0, 0, 0.01)',
        'soft-dark': '0 10px 25px -5px rgba(0, 0, 0, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
        'glow': '0 0 15px rgba(59, 130, 246, 0.3)',
        'glow-dark': '0 0 20px rgba(99, 102, 241, 0.4)',
        'inner-xl': 'inset 0 20px 25px -5px rgba(0, 0, 0, 0.1), inset 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      },
      // Custom transitions
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
        'width': 'width',
        'opacity': 'opacity',
        'transform': 'transform',
        'colors': 'background-color, border-color, color, fill, stroke',
      },
      // Custom z-index
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },
      // Custom container
      container: {
        center: true,
        padding: '1rem',
        screens: {
          sm: '640px',
          md: '768px',
          lg: '1024px',
          xl: '1280px',
          '2xl': '1440px',
        },
      },
    },
  },
  // Plugins
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),
    require('@tailwindcss/line-clamp'),
    // Custom components
    function({ addComponents, theme }) {
      addComponents({
        // Container with max-width and padding
        '.container': {
          width: '100%',
          marginLeft: 'auto',
          marginRight: 'auto',
          paddingLeft: theme('spacing.4'),
          paddingRight: theme('spacing.4'),
          '@screen sm': { maxWidth: theme('screens.sm') },
          '@screen md': { maxWidth: theme('screens.md') },
          '@screen lg': { maxWidth: theme('screens.lg') },
          '@screen xl': { maxWidth: theme('screens.xl') },
          '@screen 2xl': { maxWidth: theme('screens.2xl') },
        },
        // Buttons
        '.btn': {
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: '600',
          borderRadius: '9999px',
          transition: 'all 0.2s ease-in-out',
          '&:focus': {
            outline: 'none',
            ring: '2px',
            ringColor: 'currentColor',
            ringOffset: '2px',
          },
        },
        // Card
        '.card': {
          backgroundColor: theme('colors.white'),
          borderRadius: theme('borderRadius.lg'),
          boxShadow: theme('boxShadow.sm'),
          overflow: 'hidden',
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: theme('boxShadow.lg'),
            transform: 'translateY(-2px)',
          },
          '@media (prefers-color-scheme: dark)': {
            backgroundColor: theme('colors.dark.800'),
          },
        },
        // Form inputs
        '.form-input': {
          borderWidth: '1px',
          borderColor: theme('colors.gray.300'),
          borderRadius: theme('borderRadius.md'),
          padding: `${theme('spacing.2')} ${theme('spacing.3')}`,
          fontSize: theme('fontSize.base'),
          lineHeight: theme('lineHeight.normal'),
          transition: 'border-color 0.2s, box-shadow 0.2s',
          '&:focus': {
            borderColor: theme('colors.blue.500'),
            boxShadow: `0 0 0 3px ${theme('colors.blue.100')}`,
            outline: 'none',
          },
          '@media (prefers-color-scheme: dark)': {
            borderColor: theme('colors.gray.700'),
            backgroundColor: theme('colors.dark.700'),
            color: theme('colors.white'),
            '&:focus': {
              borderColor: theme('colors.blue.600'),
              boxShadow: `0 0 0 3px ${theme('colors.blue.900')}`,
            },
          },
        },
      });
    },
  ],
  // Variants
  variants: {
    extend: {
      backgroundColor: ['active', 'disabled'],
      borderColor: ['active', 'disabled'],
      textColor: ['active', 'disabled'],
      opacity: ['disabled'],
      cursor: ['disabled'],
    },
  },
  // Core plugins
  corePlugins: {
    // Disable default container to use our custom one
    container: false,
  },
  // Important for overriding other styles
  important: true,
};
