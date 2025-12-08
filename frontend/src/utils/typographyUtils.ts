// Typography Utility System
// Centralized typography management for consistent UI/UX

export const typographyTokens = {
  // Font sizes - consistent across all components
  fontSize: {
    xs: 'text-xs',      // 12px
    sm: 'text-sm',      // 14px
    base: 'text-base',  // 16px
    lg: 'text-lg',      // 18px
    xl: 'text-xl',      // 20px
    '2xl': 'text-2xl',  // 24px
    '3xl': 'text-3xl',  // 30px
    '4xl': 'text-4xl',  // 36px
  },

  // Font weights - consistent hierarchy
  fontWeight: {
    light: 'font-light',     // 300
    normal: 'font-normal',   // 400
    medium: 'font-medium',   // 500
    semibold: 'font-semibold', // 600
    bold: 'font-bold',       // 700
  },

  // Line heights - consistent spacing
  lineHeight: {
    tight: 'leading-tight',    // 1.25
    normal: 'leading-normal',  // 1.5
    relaxed: 'leading-relaxed', // 1.75
  },

  // Text colors - consistent with design system
  textColor: {
    primary: 'text-foreground',
    secondary: 'text-muted-foreground',
    accent: 'text-primary',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
    info: 'text-blue-600',
  },

  // Text alignment
  textAlign: {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
    justify: 'text-justify',
  },

  // Text decoration
  decoration: {
    none: 'no-underline',
    underline: 'underline',
    lineThrough: 'line-through',
  },

  // Text transform
  transform: {
    none: 'normal-case',
    uppercase: 'uppercase',
    lowercase: 'lowercase',
    capitalize: 'capitalize',
  }
};

// Typography hierarchy components
export const typographyHierarchy = {
  // Headings - consistent hierarchy
  heading: {
    h1: {
      size: typographyTokens.fontSize['4xl'],
      weight: typographyTokens.fontWeight.bold,
      lineHeight: typographyTokens.lineHeight.tight,
      color: typographyTokens.textColor.primary,
    },
    h2: {
      size: typographyTokens.fontSize['3xl'],
      weight: typographyTokens.fontWeight.bold,
      lineHeight: typographyTokens.lineHeight.tight,
      color: typographyTokens.textColor.primary,
    },
    h3: {
      size: typographyTokens.fontSize['2xl'],
      weight: typographyTokens.fontWeight.semibold,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    },
    h4: {
      size: typographyTokens.fontSize.xl,
      weight: typographyTokens.fontWeight.semibold,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    },
    h5: {
      size: typographyTokens.fontSize.lg,
      weight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    },
    h6: {
      size: typographyTokens.fontSize.base,
      weight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    }
  },

  // Body text - consistent sizing
  body: {
    large: {
      size: typographyTokens.fontSize.lg,
      weight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.relaxed,
      color: typographyTokens.textColor.primary,
    },
    default: {
      size: typographyTokens.fontSize.base,
      weight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    },
    small: {
      size: typographyTokens.fontSize.sm,
      weight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    },
    xs: {
      size: typographyTokens.fontSize.xs,
      weight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    }
  },

  // UI text - consistent for interface elements
  ui: {
    label: {
      size: typographyTokens.fontSize.sm,
      weight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.secondary,
    },
    caption: {
      size: typographyTokens.fontSize.xs,
      weight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.secondary,
    },
    button: {
      size: typographyTokens.fontSize.sm,
      weight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    },
    badge: {
      size: typographyTokens.fontSize.xs,
      weight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    }
  },

  // Data display - consistent for metrics and numbers
  data: {
    metric: {
      size: typographyTokens.fontSize['2xl'],
      weight: typographyTokens.fontWeight.semibold,
      lineHeight: typographyTokens.lineHeight.tight,
      color: typographyTokens.textColor.primary,
    },
    value: {
      size: typographyTokens.fontSize.lg,
      weight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.primary,
    },
    secondary: {
      size: typographyTokens.fontSize.sm,
      weight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
      color: typographyTokens.textColor.secondary,
    }
  }
};

// Utility functions for consistent typography
export const getHeadingStyles = (level: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6') => {
  const styles = typographyHierarchy.heading[level];
  return `${styles.size} ${styles.weight} ${styles.lineHeight} ${styles.color}`;
};

export const getBodyStyles = (size: 'large' | 'default' | 'small' | 'xs' = 'default') => {
  const styles = typographyHierarchy.body[size];
  return `${styles.size} ${styles.weight} ${styles.lineHeight} ${styles.color}`;
};

export const getUIStyles = (type: 'label' | 'caption' | 'button' | 'badge') => {
  const styles = typographyHierarchy.ui[type];
  return `${styles.size} ${styles.weight} ${styles.lineHeight} ${styles.color}`;
};

export const getDataStyles = (type: 'metric' | 'value' | 'secondary') => {
  const styles = typographyHierarchy.data[type];
  return `${styles.size} ${styles.weight} ${styles.lineHeight} ${styles.color}`;
};

// Combined utility for common patterns
export const getTypographyStyles = (
  variant: 'heading' | 'body' | 'ui' | 'data',
  type: string,
  options?: {
    color?: keyof typeof typographyTokens.textColor;
    weight?: keyof typeof typographyTokens.fontWeight;
    align?: keyof typeof typographyTokens.textAlign;
    transform?: keyof typeof typographyTokens.transform;
  }
) => {
  let baseStyles = '';
  
  switch (variant) {
    case 'heading':
      baseStyles = getHeadingStyles(type as any);
      break;
    case 'body':
      baseStyles = getBodyStyles(type as any);
      break;
    case 'ui':
      baseStyles = getUIStyles(type as any);
      break;
    case 'data':
      baseStyles = getDataStyles(type as any);
      break;
  }

  if (options?.color) {
    baseStyles += ` ${typographyTokens.textColor[options.color]}`;
  }
  if (options?.weight) {
    baseStyles += ` ${typographyTokens.fontWeight[options.weight]}`;
  }
  if (options?.align) {
    baseStyles += ` ${typographyTokens.textAlign[options.align]}`;
  }
  if (options?.transform) {
    baseStyles += ` ${typographyTokens.transform[options.transform]}`;
  }

  return baseStyles.trim();
};
