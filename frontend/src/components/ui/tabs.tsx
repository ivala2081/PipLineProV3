import * as React from "react"
import * as TabsPrimitive from "@radix-ui/react-tabs"
import { cn } from "../../lib/utils"

// Enhanced Radix UI Tabs with professional styling
const Tabs = TabsPrimitive.Root

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-lg bg-gray-100/50 p-1 text-muted-foreground border border-gray-200/50 shadow-sm",
      className
    )}
    {...props}
  />
))
TabsList.displayName = TabsPrimitive.List.displayName

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "group relative inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all duration-300 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-md data-[state=active]:border data-[state=active]:border-gray-200 hover:bg-white/80 hover:text-gray-800 hover:scale-[1.02] hover:shadow-sm hover:border hover:border-gray-200/50",
      className
    )}
    {...props}
  />
))
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      "mt-4 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 animate-in fade-in-0 slide-in-from-top-2 duration-300",
      className
    )}
    {...props}
  />
))
TabsContent.displayName = TabsPrimitive.Content.displayName

// Professional Tab Variants
interface ProfessionalTabsProps {
  variant?: 'card' | 'underline' | 'segmented' | 'pill' | 'minimal';
  size?: 'sm' | 'md' | 'lg';
  orientation?: 'horizontal' | 'vertical';
  className?: string;
  children: React.ReactNode;
}

const ProfessionalTabs = React.forwardRef<HTMLDivElement, ProfessionalTabsProps>(
  ({ variant = 'card', size = 'md', orientation = 'horizontal', className, children }, ref) => {
    const baseClasses = 'flex gap-1';
    const orientationClasses = orientation === 'vertical' ? 'flex-col' : 'flex-row';
    const sizeClasses = {
      sm: 'text-xs',
      md: 'text-sm',
      lg: 'text-base'
    };

    const variantClasses = {
      card: 'bg-white rounded-xl shadow-sm border border-gray-200 p-1',
      underline: 'border-b border-gray-200',
      segmented: 'bg-gray-100 rounded-lg p-1',
      pill: 'bg-gray-100 rounded-full p-1',
      minimal: 'space-x-6'
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseClasses,
          orientationClasses,
          sizeClasses[size],
          variantClasses[variant],
          className
        )}
      >
        {children}
      </div>
    );
  }
);

ProfessionalTabs.displayName = 'ProfessionalTabs';

// Enhanced TabsList with professional variants
const ProfessionalTabsList = React.forwardRef<
  HTMLDivElement,
  ProfessionalTabsProps
>(({ variant = 'card', size = 'md', orientation = 'horizontal', className, children }, ref) => {
  return (
    <ProfessionalTabs
      ref={ref}
      variant={variant}
      size={size}
      orientation={orientation}
      className={className}
    >
      {children}
    </ProfessionalTabs>
  );
});

ProfessionalTabsList.displayName = 'ProfessionalTabsList';

// Enhanced TabsTrigger with professional styling
interface ProfessionalTabsTriggerProps {
  id: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  disabled?: boolean;
  active?: boolean;
  onClick?: () => void;
  className?: string;
  variant?: 'card' | 'underline' | 'segmented' | 'pill' | 'minimal';
}

const ProfessionalTabsTrigger = React.forwardRef<HTMLButtonElement, ProfessionalTabsTriggerProps>(
  ({ 
    id, 
    label, 
    icon: Icon, 
    badge, 
    disabled = false, 
    active = false, 
    onClick, 
    className,
    variant = 'card'
  }, ref) => {
    const baseClasses = 'relative inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';
    
    const stateClasses = active
      ? 'text-blue-600 bg-white shadow-sm'
      : 'text-gray-600 hover:text-gray-800 hover:bg-white/50';

    const sizeClasses = {
      sm: 'px-3 py-1.5 text-xs',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base'
    };

    const variantClasses = {
      card: 'rounded-lg border border-gray-200',
      underline: 'border-b-2 border-transparent hover:border-gray-300 rounded-none',
      segmented: 'rounded-md',
      pill: 'rounded-full',
      minimal: 'border-b-2 border-transparent hover:border-gray-300 rounded-none'
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
          className
        )}
      >
        {Icon && <Icon className="w-4 h-4 mr-2" />}
        <span>{label}</span>
        {badge && (
          <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">
            {badge}
          </span>
        )}
      </button>
    );
  }
);

ProfessionalTabsTrigger.displayName = 'ProfessionalTabsTrigger';

export { 
  Tabs, 
  TabsList, 
  TabsTrigger, 
  TabsContent,
  ProfessionalTabs,
  ProfessionalTabsList,
  ProfessionalTabsTrigger
}
