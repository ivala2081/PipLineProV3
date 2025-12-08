/**
 * Spacing utility functions
 * Consistent spacing patterns across the application
 */

import { spacing } from '../lib/design-system';

// Spacing utility function
export const getSpacing = (size: keyof typeof spacing) => spacing[size];

// Common spacing patterns
export const spacingPatterns = {
  // Container spacing
  container: {
    padding: spacing.lg,
    margin: spacing.lg,
    gap: spacing.md,
  },
  
  // Card spacing
  card: {
    padding: spacing['2xl'],
    gap: spacing.lg,
    margin: spacing.md,
  },
  
  // Form spacing
  form: {
    fieldGap: spacing.lg,
    labelGap: spacing.sm,
    inputPadding: spacing.md,
    buttonGap: spacing.md,
  },
  
  // Grid spacing
  grid: {
    gap: spacing.lg,
    itemGap: spacing.md,
  },
  
  // Section spacing
  section: {
    padding: spacing['4xl'],
    margin: spacing['2xl'],
    gap: spacing['2xl'],
  },
  
  // Navigation spacing
  nav: {
    itemGap: spacing.md,
    padding: spacing.lg,
    margin: spacing.sm,
  },
  
  // Button spacing
  button: {
    padding: spacing.md,
    gap: spacing.sm,
    margin: spacing.xs,
  },
  
  // Modal spacing
  modal: {
    padding: spacing['2xl'],
    gap: spacing.lg,
    margin: spacing.lg,
  },
  
  // Table spacing
  table: {
    cellPadding: spacing.md,
    rowGap: spacing.sm,
    headerPadding: spacing.lg,
  },
  
  // List spacing
  list: {
    itemGap: spacing.sm,
    padding: spacing.md,
    margin: spacing.sm,
  },
} as const;

// Responsive spacing patterns
export const responsiveSpacing = {
  // Mobile first approach
  mobile: {
    container: spacing.md,
    section: spacing.lg,
    card: spacing.lg,
    form: spacing.md,
  },
  
  // Tablet spacing
  tablet: {
    container: spacing.lg,
    section: spacing['2xl'],
    card: spacing['2xl'],
    form: spacing.lg,
  },
  
  // Desktop spacing
  desktop: {
    container: spacing['2xl'],
    section: spacing['4xl'],
    card: spacing['2xl'],
    form: spacing.lg,
  },
  
  // Large desktop spacing
  large: {
    container: spacing['3xl'],
    section: spacing['5xl'],
    card: spacing['3xl'],
    form: spacing['2xl'],
  },
} as const;

// Spacing classes generator
export const generateSpacingClasses = () => {
  const classes: Record<string, string> = {};
  
  // Generate padding classes
  Object.entries(spacing).forEach(([size, value]) => {
    classes[`p-${size}`] = `padding: ${value}`;
    classes[`pt-${size}`] = `padding-top: ${value}`;
    classes[`pr-${size}`] = `padding-right: ${value}`;
    classes[`pb-${size}`] = `padding-bottom: ${value}`;
    classes[`pl-${size}`] = `padding-left: ${value}`;
    classes[`px-${size}`] = `padding-left: ${value}; padding-right: ${value}`;
    classes[`py-${size}`] = `padding-top: ${value}; padding-bottom: ${value}`;
  });
  
  // Generate margin classes
  Object.entries(spacing).forEach(([size, value]) => {
    classes[`m-${size}`] = `margin: ${value}`;
    classes[`mt-${size}`] = `margin-top: ${value}`;
    classes[`mr-${size}`] = `margin-right: ${value}`;
    classes[`mb-${size}`] = `margin-bottom: ${value}`;
    classes[`ml-${size}`] = `margin-left: ${value}`;
    classes[`mx-${size}`] = `margin-left: ${value}; margin-right: ${value}`;
    classes[`my-${size}`] = `margin-top: ${value}; margin-bottom: ${value}`;
  });
  
  // Generate gap classes
  Object.entries(spacing).forEach(([size, value]) => {
    classes[`gap-${size}`] = `gap: ${value}`;
    classes[`gap-x-${size}`] = `column-gap: ${value}`;
    classes[`gap-y-${size}`] = `row-gap: ${value}`;
  });
  
  return classes;
};

// Common spacing combinations
export const commonSpacing = {
  // Tight spacing for compact layouts
  tight: {
    padding: spacing.sm,
    margin: spacing.xs,
    gap: spacing.xs,
  },
  
  // Normal spacing for standard layouts
  normal: {
    padding: spacing.lg,
    margin: spacing.md,
    gap: spacing.md,
  },
  
  // Loose spacing for spacious layouts
  loose: {
    padding: spacing['2xl'],
    margin: spacing.lg,
    gap: spacing.lg,
  },
  
  // Extra loose spacing for hero sections
  extraLoose: {
    padding: spacing['4xl'],
    margin: spacing['2xl'],
    gap: spacing['2xl'],
  },
} as const;

// Spacing validation
export const validateSpacing = (size: string): size is keyof typeof spacing => {
  return size in spacing;
};

// Get spacing with fallback
export const getSpacingWithFallback = (size: string, fallback: keyof typeof spacing = 'md') => {
  return validateSpacing(size) ? spacing[size] : spacing[fallback];
};

export default {
  getSpacing,
  spacingPatterns,
  responsiveSpacing,
  generateSpacingClasses,
  commonSpacing,
  validateSpacing,
  getSpacingWithFallback,
};
