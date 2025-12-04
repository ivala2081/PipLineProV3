import { useState, useEffect } from 'react';
import { designTokens, componentTokens, themeVariants } from './design-tokens';

// Hook for managing design system state (light theme only)
export const useDesignSystem = () => {
  // Force light theme
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('dark');
  }, []);

  return {
    theme: 'light' as const,
    setTheme: () => {}, // No-op since we only support light theme
    isDark: false,
    tokens: designTokens,
    componentTokens,
    themeVariants: themeVariants.light,
  };
};

// Hook for consistent spacing
export const useSpacing = () => {
  return {
    space: (size: keyof typeof designTokens.spacing) => designTokens.spacing[size],
    padding: (size: keyof typeof designTokens.spacing) => `p-${size}`,
    margin: (size: keyof typeof designTokens.spacing) => `m-${size}`,
    gap: (size: keyof typeof designTokens.spacing) => `gap-${size}`,
  };
};

// Hook for consistent colors
export const useColors = () => {
  return {
    primary: (shade: keyof typeof designTokens.colors.primary) => designTokens.colors.primary[shade],
    secondary: (shade: keyof typeof designTokens.colors.secondary) => designTokens.colors.secondary[shade],
    success: (shade: keyof typeof designTokens.colors.success) => designTokens.colors.success[shade],
    warning: (shade: keyof typeof designTokens.colors.warning) => designTokens.colors.warning[shade],
    error: (shade: keyof typeof designTokens.colors.error) => designTokens.colors.error[shade],
    neutral: (shade: keyof typeof designTokens.colors.neutral) => designTokens.colors.neutral[shade],
  };
};

// Hook for consistent typography
export const useTypography = () => {
  return {
    fontFamily: designTokens.typography.fontFamily,
    fontSize: (size: keyof typeof designTokens.typography.fontSize) => designTokens.typography.fontSize[size],
    fontWeight: (weight: keyof typeof designTokens.typography.fontWeight) => designTokens.typography.fontWeight[weight],
    lineHeight: (height: keyof typeof designTokens.typography.lineHeight) => designTokens.typography.lineHeight[height],
  };
};

// Hook for responsive design
export const useResponsive = () => {
  const [breakpoint, setBreakpoint] = useState<'sm' | 'md' | 'lg' | 'xl' | '2xl'>('lg');

  useEffect(() => {
    const updateBreakpoint = () => {
      const width = window.innerWidth;
      if (width < 640) setBreakpoint('sm');
      else if (width < 768) setBreakpoint('md');
      else if (width < 1024) setBreakpoint('lg');
      else if (width < 1280) setBreakpoint('xl');
      else setBreakpoint('2xl');
    };

    updateBreakpoint();
    window.addEventListener('resize', updateBreakpoint);
    return () => window.removeEventListener('resize', updateBreakpoint);
  }, []);

  return {
    breakpoint,
    isMobile: breakpoint === 'sm',
    isTablet: breakpoint === 'md',
    isDesktop: breakpoint === 'lg' || breakpoint === 'xl' || breakpoint === '2xl',
  };
};

// Hook for component variants
export const useComponentVariants = () => {
  return {
    button: {
      variants: ['primary', 'secondary', 'outline', 'ghost', 'destructive', 'success', 'warning'],
      sizes: ['sm', 'md', 'lg'],
    },
    badge: {
      variants: ['default', 'secondary', 'destructive', 'outline', 'success', 'warning', 'info'],
      sizes: ['sm', 'md', 'lg'],
    },
    card: {
      variants: ['default', 'outlined', 'elevated', 'flat'],
      sizes: ['sm', 'md', 'lg'],
    },
    input: {
      sizes: ['sm', 'md', 'lg'],
      types: ['text', 'email', 'password', 'number', 'tel', 'url'],
    },
  };
};
