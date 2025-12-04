import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { cn } from '../lib/utils';

// Re-export unified components
export { UnifiedWrapper, UnifiedSection, UnifiedGrid } from './UnifiedWrapper';

// Unified Card component that extends the base Card with consistent styling
interface UnifiedCardProps {
  children: React.ReactNode;
  className?: string;
  header?: {
    title?: React.ReactNode;
    description?: React.ReactNode;
    actions?: React.ReactNode;
  };
  footer?: React.ReactNode;
  variant?: 'default' | 'outlined' | 'elevated' | 'flat';
  size?: 'sm' | 'md' | 'lg';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  showGlass?: boolean; // Enable glassmorphism effect (Phase 2)
}

export const UnifiedCard: React.FC<UnifiedCardProps> = ({
  children,
  className,
  header,
  footer,
  variant = 'default',
  size = 'md',
  padding = 'md',
  showGlass = false
}) => {
  const variantStyles = {
    default: 'bg-card border border-border shadow-sm',
    outlined: 'bg-transparent border-2 border-border',
    elevated: 'bg-card shadow-lg border-0',
    flat: 'bg-card border-0 shadow-none',
  };

  const sizeStyles = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  };

  const paddingStyles = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  // Glassmorphism class conditionally applied
  const glassClass = showGlass ? 'glass-card card-hover-subtle' : '';

  return (
    <Card className={cn(variantStyles[variant], sizeStyles[size], glassClass, className)}>
      {header && (
        <CardHeader className={cn('border-b border-border', paddingStyles[padding])}>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              {header.title && (
                <CardTitle className="text-lg font-semibold text-foreground">
                  {header.title}
                </CardTitle>
              )}
              {header.description && (
                <CardDescription className="text-muted-foreground">
                  {header.description}
                </CardDescription>
              )}
            </div>
            {header.actions && (
              <div className="flex items-center gap-2">
                {header.actions}
              </div>
            )}
          </div>
        </CardHeader>
      )}
      
      <CardContent className={cn(paddingStyles[padding])}>
        {children}
      </CardContent>
      
      {footer && (
        <div className={cn('border-t border-border', paddingStyles[padding])}>
          {footer}
        </div>
      )}
    </Card>
  );
};

// Unified Button component with consistent variants
interface UnifiedButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'success' | 'warning';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export const UnifiedButton: React.FC<UnifiedButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className,
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  onClick,
  type = 'button',
}) => {
  const variantStyles = {
    primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
    secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
    outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
    ghost: 'hover:bg-accent hover:text-accent-foreground',
    destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
    success: 'bg-green-600 text-white hover:bg-green-700',
    warning: 'bg-yellow-600 text-white hover:bg-yellow-700',
  };

  const sizeStyles = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-10 px-4 py-2',
    lg: 'h-12 px-6 text-lg',
  };

  return (
    <Button
      type={type}
      variant="ghost"
      disabled={disabled || loading}
      onClick={onClick}
      className={cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {loading && (
        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
      )}
      {icon && iconPosition === 'left' && (
        <span className="mr-2">{icon}</span>
      )}
      {children}
      {icon && iconPosition === 'right' && (
        <span className="ml-2">{icon}</span>
      )}
    </Button>
  );
};

// Unified Badge component with consistent styling
interface UnifiedBadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const UnifiedBadge: React.FC<UnifiedBadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className,
}) => {
  const variantStyles = {
    default: 'bg-primary text-primary-foreground hover:bg-primary/80',
    secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
    destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/80',
    outline: 'text-foreground border border-border',
    success: 'bg-green-100 text-green-800 hover:bg-green-200',
    warning: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200',
    info: 'bg-blue-100 text-blue-800 hover:bg-blue-200',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };

  return (
    <Badge
      variant="outline"
      className={cn(
        'inline-flex items-center rounded-full font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {children}
    </Badge>
  );
};

// Unified Input component with consistent styling
interface UnifiedInputProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
  disabled?: boolean;
  error?: string;
  label?: string;
  helperText?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export const UnifiedInput: React.FC<UnifiedInputProps> = ({
  placeholder,
  value,
  onChange,
  type = 'text',
  disabled = false,
  error,
  label,
  helperText,
  size = 'md',
  className,
  icon,
  iconPosition = 'left',
}) => {
  const sizeStyles = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-10 px-3',
    lg: 'h-12 px-4 text-lg',
  };

  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm font-medium text-foreground">
          {label}
        </label>
      )}
      
      <div className="relative">
        {icon && iconPosition === 'left' && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground">
            {icon}
          </div>
        )}
        
        <Input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          disabled={disabled}
          className={cn(
            'w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            sizeStyles[size],
            icon && iconPosition === 'left' && 'pl-10',
            icon && iconPosition === 'right' && 'pr-10',
            error && 'border-destructive focus-visible:ring-destructive',
            className
          )}
        />
        
        {icon && iconPosition === 'right' && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground">
            {icon}
          </div>
        )}
      </div>
      
      {(error || helperText) && (
        <p className={cn(
          'text-sm',
          error ? 'text-destructive' : 'text-muted-foreground'
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  );
};

// Unified Table component for consistent data display
interface UnifiedTableProps {
  data: any[];
  columns: Array<{
    key: string;
    label: string;
    render?: (value: any, row: any) => React.ReactNode;
    sortable?: boolean;
  }>;
  className?: string;
  striped?: boolean;
  hover?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const UnifiedTable: React.FC<UnifiedTableProps> = ({
  data,
  columns,
  className,
  striped = true,
  hover = true,
  size = 'md',
}) => {
  const sizeStyles = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className="overflow-x-auto">
      <table className={cn('w-full border-collapse', className)}>
        <thead>
          <tr className="border-b border-border">
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  'text-left font-medium text-muted-foreground',
                  sizeStyles[size],
                  'px-4 py-3'
                )}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr
              key={index}
              className={cn(
                'border-b border-border transition-colors',
                striped && index % 2 === 0 && 'bg-muted/50',
                hover && 'hover:bg-muted/50'
              )}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn(
                    'px-4 py-3',
                    sizeStyles[size]
                  )}
                >
                  {column.render ? column.render(row[column.key], row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
