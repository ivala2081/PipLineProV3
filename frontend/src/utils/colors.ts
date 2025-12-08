/**
 * Color utility functions
 * Consistent color usage across the application
 */

import { colors, semanticColors } from '../lib/design-system';

// Color utility function
export const getColor = (colorPath: string) => {
  const keys = colorPath.split('.');
  let value: any = colors;
  for (const key of keys) {
    value = value?.[key];
  }
  return value;
};

// Semantic color mapping
export const getSemanticColor = (semanticPath: string) => {
  const keys = semanticPath.split('.');
  let value: any = semanticColors;
  for (const key of keys) {
    value = value?.[key];
  }
  return value;
};

// Color variants for components
export const colorVariants = {
  primary: {
    bg: colors.primary[500],
    bgHover: colors.primary[600],
    bgActive: colors.primary[700],
    text: colors.primary[50],
    border: colors.primary[500],
    ring: colors.primary[200],
  },
  secondary: {
    bg: colors.secondary[500],
    bgHover: colors.secondary[600],
    bgActive: colors.secondary[700],
    text: colors.secondary[50],
    border: colors.secondary[500],
    ring: colors.secondary[200],
  },
  success: {
    bg: colors.success[500],
    bgHover: colors.success[600],
    bgActive: colors.success[700],
    text: colors.success[50],
    border: colors.success[500],
    ring: colors.success[200],
  },
  warning: {
    bg: colors.warning[500],
    bgHover: colors.warning[600],
    bgActive: colors.warning[700],
    text: colors.warning[50],
    border: colors.warning[500],
    ring: colors.warning[200],
  },
  error: {
    bg: colors.error[500],
    bgHover: colors.error[600],
    bgActive: colors.error[700],
    text: colors.error[50],
    border: colors.error[500],
    ring: colors.error[200],
  },
  info: {
    bg: colors.info[500],
    bgHover: colors.info[600],
    bgActive: colors.info[700],
    text: colors.info[50],
    border: colors.info[500],
    ring: colors.info[200],
  },
  neutral: {
    bg: colors.neutral[500],
    bgHover: colors.neutral[600],
    bgActive: colors.neutral[700],
    text: colors.neutral[50],
    border: colors.neutral[500],
    ring: colors.neutral[200],
  },
} as const;

// Background color variants
export const backgroundVariants = {
  primary: {
    light: colors.primary[50],
    medium: colors.primary[100],
    dark: colors.primary[200],
  },
  secondary: {
    light: colors.secondary[50],
    medium: colors.secondary[100],
    dark: colors.secondary[200],
  },
  success: {
    light: colors.success[50],
    medium: colors.success[100],
    dark: colors.success[200],
  },
  warning: {
    light: colors.warning[50],
    medium: colors.warning[100],
    dark: colors.warning[200],
  },
  error: {
    light: colors.error[50],
    medium: colors.error[100],
    dark: colors.error[200],
  },
  info: {
    light: colors.info[50],
    medium: colors.info[100],
    dark: colors.info[200],
  },
  neutral: {
    light: colors.neutral[50],
    medium: colors.neutral[100],
    dark: colors.neutral[200],
  },
} as const;

// Text color variants
export const textVariants = {
  primary: {
    light: colors.primary[600],
    medium: colors.primary[700],
    dark: colors.primary[800],
  },
  secondary: {
    light: colors.secondary[600],
    medium: colors.secondary[700],
    dark: colors.secondary[800],
  },
  success: {
    light: colors.success[600],
    medium: colors.success[700],
    dark: colors.success[800],
  },
  warning: {
    light: colors.warning[600],
    medium: colors.warning[700],
    dark: colors.warning[800],
  },
  error: {
    light: colors.error[600],
    medium: colors.error[700],
    dark: colors.error[800],
  },
  info: {
    light: colors.info[600],
    medium: colors.info[700],
    dark: colors.info[800],
  },
  neutral: {
    light: colors.neutral[600],
    medium: colors.neutral[700],
    dark: colors.neutral[800],
  },
} as const;

// Border color variants
export const borderVariants = {
  primary: {
    light: colors.primary[200],
    medium: colors.primary[300],
    dark: colors.primary[400],
  },
  secondary: {
    light: colors.secondary[200],
    medium: colors.secondary[300],
    dark: colors.secondary[400],
  },
  success: {
    light: colors.success[200],
    medium: colors.success[300],
    dark: colors.success[400],
  },
  warning: {
    light: colors.warning[200],
    medium: colors.warning[300],
    dark: colors.warning[400],
  },
  error: {
    light: colors.error[200],
    medium: colors.error[300],
    dark: colors.error[400],
  },
  info: {
    light: colors.info[200],
    medium: colors.info[300],
    dark: colors.info[400],
  },
  neutral: {
    light: colors.neutral[200],
    medium: colors.neutral[300],
    dark: colors.neutral[400],
  },
} as const;

// Gradient combinations
export const gradientCombinations = {
  primary: `linear-gradient(135deg, ${colors.primary[500]}, ${colors.primary[700]})`,
  secondary: `linear-gradient(135deg, ${colors.secondary[500]}, ${colors.secondary[700]})`,
  success: `linear-gradient(135deg, ${colors.success[500]}, ${colors.success[700]})`,
  warning: `linear-gradient(135deg, ${colors.warning[500]}, ${colors.warning[700]})`,
  error: `linear-gradient(135deg, ${colors.error[500]}, ${colors.error[700]})`,
  info: `linear-gradient(135deg, ${colors.info[500]}, ${colors.info[700]})`,
  sunset: `linear-gradient(135deg, ${colors.warning[500]}, ${colors.error[500]})`,
  ocean: `linear-gradient(135deg, ${colors.info[500]}, ${colors.success[500]})`,
  forest: `linear-gradient(135deg, ${colors.success[500]}, ${colors.info[500]})`,
  purple: `linear-gradient(135deg, ${colors.primary[500]}, ${colors.info[500]})`,
} as const;

// Color validation
export const validateColor = (colorPath: string): boolean => {
  const keys = colorPath.split('.');
  let value: any = colors;
  for (const key of keys) {
    if (value && typeof value === 'object' && key in value) {
      value = value[key];
    } else {
      return false;
    }
  }
  return typeof value === 'string';
};

// Get color with fallback
export const getColorWithFallback = (colorPath: string, fallback: string = colors.neutral[500]) => {
  return validateColor(colorPath) ? getColor(colorPath) : fallback;
};

// Generate color classes
export const generateColorClasses = () => {
  const classes: Record<string, string> = {};
  
  // Background color classes
  Object.entries(colors).forEach(([colorName, colorScale]) => {
    Object.entries(colorScale).forEach(([shade, value]) => {
      classes[`bg-${colorName}-${shade}`] = `background-color: ${value}`;
      classes[`text-${colorName}-${shade}`] = `color: ${value}`;
      classes[`border-${colorName}-${shade}`] = `border-color: ${value}`;
    });
  });
  
  return classes;
};

// Accessibility helpers
export const getContrastColor = (backgroundColor: string): string => {
  // Simple contrast calculation - in a real app, you'd use a proper contrast library
  const hex = backgroundColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;
  return brightness > 128 ? colors.neutral[900] : colors.neutral[50];
};

// Color theme helpers
export const getThemeColors = (theme: 'light' | 'dark' = 'light') => {
  if (theme === 'dark') {
    return {
      background: colors.neutral[900],
      surface: colors.neutral[800],
      text: colors.neutral[50],
      textSecondary: colors.neutral[300],
      border: colors.neutral[700],
    };
  }
  
  return {
    background: colors.neutral[50],
    surface: '#ffffff',
    text: colors.neutral[900],
    textSecondary: colors.neutral[600],
    border: colors.neutral[200],
  };
};

export default {
  getColor,
  getSemanticColor,
  colorVariants,
  backgroundVariants,
  textVariants,
  borderVariants,
  gradientCombinations,
  validateColor,
  getColorWithFallback,
  generateColorClasses,
  getContrastColor,
  getThemeColors,
};
