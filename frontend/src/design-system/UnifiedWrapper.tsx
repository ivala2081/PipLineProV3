import React from 'react';
import { cn } from '../lib/utils';

// Unified wrapper component that applies consistent styling
interface UnifiedWrapperProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'card' | 'section' | 'container';
  spacing?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  margin?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  background?: 'default' | 'muted' | 'card' | 'transparent';
  border?: boolean;
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}

const variantStyles = {
  default: '',
  card: 'bg-card border border-border rounded-lg shadow-sm',
  section: 'bg-background',
  container: 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
};

const spacingStyles = {
  none: '',
  sm: 'space-y-2',
  md: 'space-y-4',
  lg: 'space-y-6',
  xl: 'space-y-8',
};

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
};

const marginStyles = {
  none: '',
  sm: 'm-2',
  md: 'm-4',
  lg: 'm-6',
  xl: 'm-8',
};

const backgroundStyles = {
  default: 'bg-background',
  muted: 'bg-muted',
  card: 'bg-card',
  transparent: 'bg-transparent',
};

const shadowStyles = {
  none: '',
  sm: 'shadow-sm',
  md: 'shadow-md',
  lg: 'shadow-lg',
};

const roundedStyles = {
  none: '',
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
};

export const UnifiedWrapper: React.FC<UnifiedWrapperProps> = ({
  children,
  className,
  variant = 'default',
  spacing = 'md',
  padding = 'md',
  margin = 'none',
  background = 'default',
  border = false,
  shadow = 'none',
  rounded = 'md',
}) => {
  return (
    <div
      className={cn(
        // Base styles
        'transition-colors duration-200',
        
        // Variant styles
        variantStyles[variant],
        
        // Spacing
        spacingStyles[spacing],
        
        // Padding
        paddingStyles[padding],
        
        // Margin
        marginStyles[margin],
        
        // Background
        backgroundStyles[background],
        
        // Border
        border && 'border border-border',
        
        // Shadow
        shadowStyles[shadow],
        
        // Rounded
        roundedStyles[rounded],
        
        // Custom className
        className
      )}
    >
      {children}
    </div>
  );
};

// Unified section component for consistent page sections
interface UnifiedSectionProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
  headerClassName?: string;
  contentClassName?: string;
  actions?: React.ReactNode;
}

export const UnifiedSection: React.FC<UnifiedSectionProps> = ({
  children,
  title,
  description,
  className,
  headerClassName,
  contentClassName,
  actions,
}) => {
  return (
    <UnifiedWrapper
      variant="section"
      spacing="lg"
      className={className}
    >
      {(title || description || actions) && (
        <div className={cn('flex items-center justify-between', headerClassName)}>
          <div className="space-y-1">
            {title && (
              <h2 className="text-2xl font-semibold text-foreground">
                {title}
              </h2>
            )}
            {description && (
              <p className="text-muted-foreground">
                {description}
              </p>
            )}
          </div>
          {actions && (
            <div className="flex items-center gap-2">
              {actions}
            </div>
          )}
        </div>
      )}
      
      <div className={cn('space-y-4', contentClassName)}>
        {children}
      </div>
    </UnifiedWrapper>
  );
};

// Unified grid component for consistent layouts
interface UnifiedGridProps {
  children: React.ReactNode;
  cols?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
  gap?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  responsive?: boolean;
}

export const UnifiedGrid: React.FC<UnifiedGridProps> = ({
  children,
  cols = 1,
  gap = 'md',
  className,
  responsive = true,
}) => {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    5: 'grid-cols-5',
    6: 'grid-cols-6',
    12: 'grid-cols-12',
  };

  const gapStyles = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
    xl: 'gap-8',
  };

  const responsiveGrid = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
    5: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5',
    6: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6',
    12: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 2xl:grid-cols-12',
  };

  return (
    <div
      className={cn(
        'grid',
        responsive ? responsiveGrid[cols] : gridCols[cols],
        gapStyles[gap],
        className
      )}
    >
      {children}
    </div>
  );
};

// Unified card component for consistent card styling
interface UnifiedCardProps {
  children: React.ReactNode;
  className?: string;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  variant?: 'default' | 'outlined' | 'elevated' | 'flat';
  size?: 'sm' | 'md' | 'lg';
}

export const UnifiedCard: React.FC<UnifiedCardProps> = ({
  children,
  className,
  header,
  footer,
  variant = 'default',
  size = 'md',
}) => {
  const variantStyles = {
    default: 'bg-card border border-border',
    outlined: 'bg-transparent border-2 border-border',
    elevated: 'bg-card shadow-lg border-0',
    flat: 'bg-card border-0',
  };

  const sizeStyles = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  return (
    <div
      className={cn(
        'rounded-lg transition-all duration-200',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {header && (
        <div className="border-b border-border pb-3 mb-4">
          {header}
        </div>
      )}
      
      <div className="space-y-4">
        {children}
      </div>
      
      {footer && (
        <div className="border-t border-border pt-3 mt-4">
          {footer}
        </div>
      )}
    </div>
  );
};
