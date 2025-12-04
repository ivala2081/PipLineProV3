/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Professional Business Color System - Minimal & Corporate
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        
        // Primary - Professional Navy
        primary: {
          DEFAULT: "#1e293b", // Navy 800
          foreground: "#ffffff",
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
        
        // Secondary - Professional Gray
        secondary: {
          DEFAULT: "#f8fafc", // Gray 50
          foreground: "#334155",
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
        
        // Muted - Subtle Gray
        muted: {
          DEFAULT: "#f1f5f9", // Gray 100
          foreground: "#64748b",
        },
        
        // Accent - Subtle Blue
        accent: {
          DEFAULT: "#3b82f6", // Blue 500
          foreground: "#ffffff",
        },
        
        // Status Colors - Professional & Muted
        success: {
          DEFAULT: "#059669", // Green 600
          foreground: "#ffffff",
          50: "#ecfdf5",
          100: "#d1fae5",
          500: "#059669",
          600: "#047857",
        },
        
        warning: {
          DEFAULT: "#d97706", // Amber 600
          foreground: "#ffffff",
          50: "#fffbeb",
          100: "#fef3c7",
          500: "#d97706",
          600: "#b45309",
        },
        
        destructive: {
          DEFAULT: "#dc2626", // Red 600
          foreground: "#ffffff",
          50: "#fef2f2",
          100: "#fee2e2",
          500: "#dc2626",
          600: "#b91c1c",
        },
        
        // Card Colors
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        
        // Professional Gray Scale - Main Colors
        gray: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
        
        // Slate - Alternative Gray
        slate: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        business: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        heading: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      fontSize: {
        // Compact Professional Typography
        'xs': ['0.625rem', { lineHeight: '1.4' }],     // 10px - Small text
        'sm': ['0.75rem', { lineHeight: '1.4' }],      // 12px - Body text
        'base': ['0.875rem', { lineHeight: '1.5' }],   // 14px - Default text
        'lg': ['1rem', { lineHeight: '1.4' }],         // 16px - Large text
        'xl': ['1.125rem', { lineHeight: '1.3' }],     // 18px - Headings
        '2xl': ['1.25rem', { lineHeight: '1.2' }],     // 20px - Large headings
        '3xl': ['1.5rem', { lineHeight: '1.1' }],      // 24px - Page titles
      },
      fontWeight: {
        // Professional Font Weights - 4 Weights Only
        'normal': '400',    // Regular text
        'medium': '500',    // Emphasized text
        'semibold': '600',  // Headings
        'bold': '700',      // Important headings
      },
      lineHeight: {
        // Professional Line Heights - 3 Only
        'tight': '1.2',     // Headings
        'normal': '1.5',    // Body text
        'relaxed': '1.6',   // Large text
      },
      letterSpacing: {
        // Professional Letter Spacing - 2 Only
        'normal': '0em',    // Default
        'tight': '-0.025em', // Headings
      },
      animation: {
        // Professional Animations - Minimal Only
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.2s ease-out',
      },
      keyframes: {
        // Professional Keyframes - Minimal Only
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      boxShadow: {
        // Professional Shadows - Minimal & Clean
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        'xs': '0.25rem',    // 4px
        'xl': '1rem',       // 16px
        '2xl': '1.5rem',    // 24px
        '3xl': '2rem',      // 32px
      },
      spacing: {
        // Compact Professional Business Spacing System - 4px Grid
        '18': '4.5rem',     // 72px
        '88': '22rem',      // 352px
        '128': '32rem',     // 512px
        '144': '36rem',     // 576px
        // Compact business-specific spacing
        'business-xs': '0.25rem',   // 4px - reduced from 8px
        'business-sm': '0.375rem',  // 6px - reduced from 12px
        'business-md': '0.5rem',    // 8px - reduced from 16px
        'business-lg': '0.75rem',   // 12px - reduced from 24px
        'business-xl': '1rem',      // 16px - reduced from 32px
        'business-2xl': '1.5rem',   // 24px - reduced from 48px
        'business-3xl': '2rem',     // 32px - reduced from 64px
        'business-4xl': '3rem',     // 48px - reduced from 96px
        'business-5xl': '4rem',     // 64px - reduced from 128px
      },
      width: {
        '50': '12.5rem',    // 200px
        '18': '4.5rem',     // 72px
        // Business-specific widths
        'business-sm': '20rem',     // 320px
        'business-md': '28rem',     // 448px
        'business-lg': '36rem',     // 576px
        'business-xl': '48rem',     // 768px
        'business-2xl': '64rem',    // 1024px
        'business-3xl': '80rem',    // 1280px
      },
      height: {
        '18': '4.5rem',     // 72px
        // Business-specific heights
        'business-sm': '2rem',      // 32px
        'business-md': '2.5rem',    // 40px
        'business-lg': '3rem',      // 48px
        'business-xl': '4rem',      // 64px
        'business-2xl': '6rem',     // 96px
      },
      maxWidth: {
        '8xl': '88rem',     // 1408px
        '9xl': '96rem',     // 1536px
        // Business-specific max widths
        'business-sm': '20rem',     // 320px
        'business-md': '28rem',     // 448px
        'business-lg': '36rem',     // 576px
        'business-xl': '48rem',     // 768px
        'business-2xl': '64rem',    // 1024px
        'business-3xl': '80rem',    // 1280px
        'business-4xl': '96rem',    // 1536px
      },
      minHeight: {
        'screen-75': '75vh',
        'screen-85': '85vh',
        // Business-specific min heights
        'business-sm': '2rem',      // 32px
        'business-md': '2.5rem',    // 40px
        'business-lg': '3rem',      // 48px
        'business-xl': '4rem',      // 64px
        'business-2xl': '6rem',     // 96px
      },
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },
      backdropBlur: {
        'xs': '2px',
      },
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
      },
      transitionDuration: {
        '400': '400ms',
        '600': '600ms',
        '800': '800ms',
      },
      transitionTimingFunction: {
        'bounce-in': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [],
} 