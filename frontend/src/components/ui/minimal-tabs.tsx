import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { LucideIcon } from 'lucide-react';

// Minimal Tab Types
export type MinimalTabVariant = 'clean' | 'subtle' | 'elegant' | 'modern';
export type MinimalTabSize = 'sm' | 'md' | 'lg';

interface MinimalTabProps {
  variant?: MinimalTabVariant;
  size?: MinimalTabSize;
  className?: string;
  children: React.ReactNode;
}

interface MinimalTabItemProps {
  id: string;
  label: string;
  icon?: LucideIcon;
  badge?: string | number;
  disabled?: boolean;
  active?: boolean;
  onClick?: () => void;
  className?: string;
  variant?: MinimalTabVariant;
}

// Clean Minimal Tabs - No borders, just text with hover effects
export const CleanTabs = forwardRef<HTMLDivElement, MinimalTabProps>(
  ({ variant = 'clean', size = 'md', className, children }, ref) => {
    const baseClasses = 'flex items-center space-x-8';
    const sizeClasses = {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg'
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseClasses,
          sizeClasses[size],
          className
        )}
      >
        {children}
      </div>
    );
  }
);

CleanTabs.displayName = 'CleanTabs';

export const CleanTabItem = forwardRef<HTMLButtonElement, MinimalTabItemProps>(
  ({ 
    id, 
    label, 
    icon: Icon, 
    badge, 
    disabled = false, 
    active = false, 
    onClick, 
    className,
    variant = 'clean'
  }, ref) => {
    const baseClasses = 'relative py-2 px-1 text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 flex items-center gap-2';
    
    const stateClasses = active
      ? 'text-gray-900 font-semibold'
      : 'text-gray-600 hover:text-gray-900 hover:font-medium';

    const sizeClasses = {
      sm: 'text-sm py-1',
      md: 'text-base py-2',
      lg: 'text-lg py-3'
    };

    const variantClasses = {
      clean: 'border-b-2 border-transparent hover:border-gray-300',
      subtle: 'rounded-md hover:bg-gray-50 px-3',
      elegant: 'relative after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-blue-500 after:scale-x-0 after:transition-transform hover:after:scale-x-100',
      modern: 'relative before:absolute before:bottom-0 before:left-0 before:right-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-gray-300 before:to-transparent before:scale-x-0 before:transition-transform hover:before:scale-x-100'
    };

    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          baseClasses,
          stateClasses,
          sizeClasses.md,
          variantClasses[variant],
          active && variant === 'elegant' && 'after:scale-x-100',
          active && variant === 'modern' && 'before:scale-x-100',
          className
        )}
      >
        {Icon && <Icon className="w-4 h-4" />}
        <span>{label}</span>
        {badge && (
          <span className="ml-1 px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full transition-colors duration-200 group-hover:bg-gray-200">
            {badge}
          </span>
        )}
      </button>
    );
  }
);

CleanTabItem.displayName = 'CleanTabItem';

// Subtle Minimal Tabs - Very light background on hover
export const SubtleTabs = forwardRef<HTMLDivElement, MinimalTabProps>(
  ({ variant = 'subtle', size = 'md', className, children }, ref) => {
    const baseClasses = 'flex items-center space-x-2';
    const sizeClasses = {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg'
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseClasses,
          sizeClasses[size],
          className
        )}
      >
        {children}
      </div>
    );
  }
);

SubtleTabs.displayName = 'SubtleTabs';

export const SubtleTabItem = forwardRef<HTMLButtonElement, MinimalTabItemProps>(
  ({ 
    id, 
    label, 
    icon: Icon, 
    badge, 
    disabled = false, 
    active = false, 
    onClick, 
    className,
    variant = 'subtle'
  }, ref) => {
    const baseClasses = 'relative py-2 px-4 text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 flex items-center gap-2 rounded-md';
    
    const stateClasses = active
      ? 'text-gray-900 bg-gray-100 font-semibold'
      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50';

    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          baseClasses,
          stateClasses,
          className
        )}
      >
        {Icon && <Icon className="w-4 h-4" />}
        <span>{label}</span>
        {badge && (
          <span className="ml-1 px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded-full">
            {badge}
          </span>
        )}
      </button>
    );
  }
);

SubtleTabItem.displayName = 'SubtleTabItem';

// Elegant Minimal Tabs - Animated underline effect
export const ElegantTabs = forwardRef<HTMLDivElement, MinimalTabProps>(
  ({ variant = 'elegant', size = 'md', className, children }, ref) => {
    const baseClasses = 'flex items-center space-x-8';
    const sizeClasses = {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg'
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseClasses,
          sizeClasses[size],
          className
        )}
      >
        {children}
      </div>
    );
  }
);

ElegantTabs.displayName = 'ElegantTabs';

export const ElegantTabItem = forwardRef<HTMLButtonElement, MinimalTabItemProps>(
  ({ 
    id, 
    label, 
    icon: Icon, 
    badge, 
    disabled = false, 
    active = false, 
    onClick, 
    className,
    variant = 'elegant'
  }, ref) => {
    const baseClasses = 'relative py-2 px-1 text-sm font-medium transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 flex items-center gap-2 group';
    
    const stateClasses = active
      ? 'text-gray-900 font-semibold'
      : 'text-gray-600 hover:text-gray-900';

    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          baseClasses,
          stateClasses,
          'after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-blue-500 after:scale-x-0 after:transition-transform after:duration-300 hover:after:scale-x-100',
          active && 'after:scale-x-100',
          className
        )}
      >
        {Icon && <Icon className="w-4 h-4" />}
        <span>{label}</span>
        {badge && (
          <span className="ml-1 px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded-full transition-colors duration-200 group-hover:bg-blue-100">
            {badge}
          </span>
        )}
      </button>
    );
  }
);

ElegantTabItem.displayName = 'ElegantTabItem';

// Modern Minimal Tabs - Gradient line effect
export const ModernTabs = forwardRef<HTMLDivElement, MinimalTabProps>(
  ({ variant = 'modern', size = 'md', className, children }, ref) => {
    const baseClasses = 'flex items-center space-x-8';
    const sizeClasses = {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg'
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseClasses,
          sizeClasses[size],
          className
        )}
      >
        {children}
      </div>
    );
  }
);

ModernTabs.displayName = 'ModernTabs';

export const ModernTabItem = forwardRef<HTMLButtonElement, MinimalTabItemProps>(
  ({ 
    id, 
    label, 
    icon: Icon, 
    badge, 
    disabled = false, 
    active = false, 
    onClick, 
    className,
    variant = 'modern'
  }, ref) => {
    const baseClasses = 'relative py-2 px-1 text-sm font-medium transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 flex items-center gap-2 group';
    
    const stateClasses = active
      ? 'text-gray-900 font-semibold'
      : 'text-gray-600 hover:text-gray-900';

    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          baseClasses,
          stateClasses,
          'before:absolute before:bottom-0 before:left-0 before:right-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-gray-300 before:to-transparent before:scale-x-0 before:transition-transform before:duration-300 hover:before:scale-x-100',
          active && 'before:scale-x-100 before:via-blue-500',
          className
        )}
      >
        {Icon && <Icon className="w-4 h-4" />}
        <span>{label}</span>
        {badge && (
          <span className="ml-1 px-2 py-0.5 text-xs bg-gradient-to-r from-gray-100 to-gray-200 text-gray-600 rounded-full transition-all duration-200 group-hover:from-blue-50 group-hover:to-blue-100 group-hover:text-blue-600">
            {badge}
          </span>
        )}
      </button>
    );
  }
);

ModernTabItem.displayName = 'ModernTabItem';

// Tab Content Container
export const MinimalTabContent = forwardRef<HTMLDivElement, { 
  children: React.ReactNode; 
  className?: string;
  active?: boolean;
}>(
  ({ children, className, active = true }, ref) => {
    if (!active) return null;
    
    return (
      <div
        ref={ref}
        className={cn(
          'mt-6 animate-in fade-in-0 slide-in-from-top-2 duration-300',
          className
        )}
      >
        {children}
      </div>
    );
  }
);

MinimalTabContent.displayName = 'MinimalTabContent';
