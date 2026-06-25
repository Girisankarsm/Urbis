/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        civic: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
      animation: {
        'welcome-fade-up': 'welcome-fade-up 0.7s ease-out both',
        'welcome-fade-in': 'welcome-fade-in 0.5s ease-out both',
        'welcome-pulse-ring': 'welcome-pulse-ring 2s ease-out infinite',
        'welcome-spin-slow': 'welcome-spin 3s linear infinite',
        'welcome-shimmer': 'welcome-shimmer 1.8s ease-in-out infinite',
        'welcome-dot-bounce': 'welcome-dot-bounce 1.4s ease-in-out infinite',
      },
      keyframes: {
        'welcome-fade-up': {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'welcome-fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'welcome-pulse-ring': {
          '0%': { transform: 'scale(0.85)', opacity: '0.6' },
          '70%': { transform: 'scale(1.35)', opacity: '0' },
          '100%': { transform: 'scale(1.35)', opacity: '0' },
        },
        'welcome-spin': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        'welcome-shimmer': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'welcome-dot-bounce': {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.4' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
