import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { LucideIcon } from 'lucide-react';

// Professional Tab Types
export type ProfessionalTabVariant = 'card' | 'underline' | 'segmented' | 'pill' | 'minimal';
export type ProfessionalTabSize = 'sm' | 'md' | 'lg';

interface ProfessionalTabProps {
  variant?: ProfessionalTabVariant;
  size?: ProfessionalTabSize;
  className?: string;
  children: React.ReactNode;
}

interface ProfessionalTabItemProps {
  id: string;
  label: string;
  icon?: LucideIcon;
  badge?: string | number;
  disabled?: boolean;
  active?: boolean;
  onClick?: () => void;
  className?: string;
}

// Generic Professional Tabs Container
export const ProfessionalTabs = forwardRef<HTMLDivElement, ProfessionalTabProps>(
  ({ variant = 'card', size = 'md', className, children }, ref) => {
    const baseClasses = 'flex items-center gap-2';
    
    return (
      <div ref={ref} className={cn(baseClasses, className)}>
        {children}
      </div>
    );
  }
);

ProfessionalTabs.displayName = 'ProfessionalTabs';

export const ProfessionalTabItem = forwardRef<HTMLButtonElement, ProfessionalTabItemProps>(
  ({ id, label, icon: Icon, badge, disabled = false, active = false, onClick, className }, ref) => {
    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          'px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200',
          active
            ? 'bg-blue-500 text-white shadow-md'
            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200',
          disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
      >
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4" />}
          <span>{label}</span>
          {badge && (
            <span className={cn(
              'px-2 py-0.5 text-xs rounded-full',
              active ? 'bg-white/20 text-white' : 'bg-blue-100 text-blue-600'
            )}>
              {badge}
            </span>
          )}
        </div>
      </button>
    );
  }
);

ProfessionalTabItem.displayName = 'ProfessionalTabItem';

// Card Tabs - Elevated cards with shadows
export const CardTabs = forwardRef<HTMLDivElement, ProfessionalTabProps>(
  ({ size = 'md', className, children }, ref) => {
    const sizeClasses = {
      sm: 'gap-2',
      md: 'gap-3',
      lg: 'gap-4'
    };

    return (
      <div
        ref={ref}
        className={cn(
          'flex items-center flex-wrap',
          sizeClasses[size],
          className
        )}
      >
        {children}
      </div>
    );
  }
);

CardTabs.displayName = 'CardTabs';

export const CardTabItem = forwardRef<HTMLButtonElement, ProfessionalTabItemProps>(
  ({ id, label, icon: Icon, badge, disabled = false, active = false, onClick, className }, ref) => {
    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          'group relative px-6 py-3 rounded-xl font-medium transition-all duration-300',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          active
            ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30 scale-105'
            : 'bg-white text-gray-700 hover:bg-gray-50 hover:shadow-md border border-gray-200 hover:border-blue-200',
          disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
          className
        )}
      >
        <div className="flex items-center gap-3">
          {Icon && (
            <Icon className={cn(
              'h-5 w-5 transition-transform duration-300',
              active ? 'scale-110' : 'group-hover:scale-110'
            )} />
          )}
          <span className="text-sm">{label}</span>
          {badge && (
            <span className={cn(
              'px-2.5 py-0.5 text-xs font-semibold rounded-full transition-colors',
              active 
                ? 'bg-white/20 text-white backdrop-blur-sm' 
                : badge === '!' 
                  ? 'bg-red-100 text-red-600' 
                  : 'bg-blue-50 text-blue-600'
            )}>
              {badge}
            </span>
          )}
        </div>
        {active && (
          <div className="absolute inset-0 rounded-xl bg-white/10 pointer-events-none" />
        )}
      </button>
    );
  }
);

CardTabItem.displayName = 'CardTabItem';

// Underline Tabs - Clean underline style
export const UnderlineTabs = forwardRef<HTMLDivElement, ProfessionalTabProps>(
  ({ size = 'md', className, children }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex items-center gap-8 border-b border-gray-200',
          className
        )}
      >
        {children}
      </div>
    );
  }
);

UnderlineTabs.displayName = 'UnderlineTabs';

export const UnderlineTabItem = forwardRef<HTMLButtonElement, ProfessionalTabItemProps>(
  ({ id, label, icon: Icon, badge, disabled = false, active = false, onClick, className }, ref) => {
    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          'relative px-1 py-4 text-sm font-medium transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          active
            ? 'text-blue-600'
            : 'text-gray-600 hover:text-gray-900',
          disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
      >
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4" />}
          <span>{label}</span>
          {badge && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-600">
              {badge}
            </span>
          )}
        </div>
        {active && (
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-t-full" />
        )}
      </button>
    );
  }
);

UnderlineTabItem.displayName = 'UnderlineTabItem';

// Segmented Tabs - iOS style segmented control
export const SegmentedTabs = forwardRef<HTMLDivElement, ProfessionalTabProps>(
  ({ size = 'md', className, children }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center p-1 bg-gray-100 rounded-lg',
          className
        )}
      >
        {children}
      </div>
    );
  }
);

SegmentedTabs.displayName = 'SegmentedTabs';

export const SegmentedTabItem = forwardRef<HTMLButtonElement, ProfessionalTabItemProps>(
  ({ id, label, icon: Icon, disabled = false, active = false, onClick, className }, ref) => {
    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          'px-4 py-2 text-sm font-medium rounded-md transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-blue-500',
          active
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-600 hover:text-gray-900',
          disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
      >
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4" />}
          <span>{label}</span>
        </div>
      </button>
    );
  }
);

SegmentedTabItem.displayName = 'SegmentedTabItem';

// Pill Tabs - Rounded pill style
export const PillTabs = forwardRef<HTMLDivElement, ProfessionalTabProps>(
  ({ size = 'md', className, children }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex items-center gap-2 flex-wrap',
          className
        )}
      >
        {children}
      </div>
    );
  }
);

PillTabs.displayName = 'PillTabs';

export const PillTabItem = forwardRef<HTMLButtonElement, ProfessionalTabItemProps>(
  ({ id, label, icon: Icon, badge, disabled = false, active = false, onClick, className }, ref) => {
    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          'px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          active
            ? 'bg-blue-500 text-white shadow-md'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
          disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
      >
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4" />}
          <span>{label}</span>
          {badge && (
            <span className={cn(
              'px-2 py-0.5 text-xs rounded-full',
              active ? 'bg-white/20 text-white' : 'bg-white text-gray-700'
            )}>
              {badge}
            </span>
          )}
        </div>
      </button>
    );
  }
);

PillTabItem.displayName = 'PillTabItem';

// Minimal Tabs - Very minimal, just text
export const MinimalTabs = forwardRef<HTMLDivElement, ProfessionalTabProps>(
  ({ size = 'md', className, children }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex items-center gap-6',
          className
        )}
      >
        {children}
      </div>
    );
  }
);

MinimalTabs.displayName = 'MinimalTabs';

export const MinimalTabItem = forwardRef<HTMLButtonElement, ProfessionalTabItemProps>(
  ({ id, label, icon: Icon, disabled = false, active = false, onClick, className }, ref) => {
    return (
      <button
        ref={ref}
        id={id}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          'py-2 text-sm font-medium transition-colors duration-200',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          active
            ? 'text-blue-600 font-semibold'
            : 'text-gray-600 hover:text-gray-900',
          disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
      >
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4" />}
          <span>{label}</span>
        </div>
      </button>
    );
  }
);

MinimalTabItem.displayName = 'MinimalTabItem';

// Tab Content Container
export const TabContent = forwardRef<HTMLDivElement, { children: React.ReactNode; className?: string }>(
  ({ children, className }, ref) => {
    return (
      <div ref={ref} className={cn('mt-6', className)}>
        {children}
      </div>
    );
  }
);

TabContent.displayName = 'TabContent';

