import React from 'react';
import { LucideIcon } from 'lucide-react';

interface ModernCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    label: string;
    isPositive?: boolean;
  };
  variant?: 'default' | 'gradient' | 'glass' | 'elevated';
  color?: 'gray' | 'green' | 'red' | 'purple' | 'amber' | 'gray';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  children?: React.ReactNode;
}

export const ModernCard: React.FC<ModernCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = 'default',
  color = 'gray',
  size = 'md',
  className = '',
  children
}) => {
  const colorClasses = {
    gray: {
      gradient: 'from-gray-500/10 to-gray-600/5',
      border: 'border-gray-200/60',
      icon: 'text-gray-600 bg-gray-100',
      trend: 'text-gray-600'
    },
    green: {
      gradient: 'from-emerald-500/10 to-emerald-600/5',
      border: 'border-emerald-200/60',
      icon: 'text-emerald-600 bg-emerald-100',
      trend: 'text-emerald-600'
    },
    red: {
      gradient: 'from-red-500/10 to-red-600/5',
      border: 'border-red-200/60',
      icon: 'text-red-600 bg-red-100',
      trend: 'text-red-600'
    },
    purple: {
      gradient: 'from-purple-500/10 to-purple-600/5',
      border: 'border-purple-200/60',
      icon: 'text-purple-600 bg-purple-100',
      trend: 'text-purple-600'
    },
    amber: {
      gradient: 'from-amber-500/10 to-amber-600/5',
      border: 'border-amber-200/60',
      icon: 'text-amber-600 bg-amber-100',
      trend: 'text-amber-600'
    }
  };

  const sizeClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  const variantClasses = {
    default: `bg-white border ${colorClasses[color].border} shadow-sm hover:shadow-md`,
    gradient: `bg-gradient-to-br ${colorClasses[color].gradient} border ${colorClasses[color].border} shadow-sm hover:shadow-md backdrop-blur-sm`,
    glass: 'bg-white/80 backdrop-blur-md border border-white/20 shadow-lg hover:shadow-xl',
    elevated: 'bg-white border border-gray-200/60 shadow-lg hover:shadow-xl'
  };

  return (
    <div className={`
      ${variantClasses[variant]}
      ${sizeClasses[size]}
      rounded-2xl 
      transition-all 
      duration-300 
      group 
      hover:scale-[1.02] 
      hover:-translate-y-1
      ${className}
    `}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-600 mb-1 tracking-wide">
            {title}
          </h3>
          <div className="text-lg font-bold text-gray-900 mb-1">
            {value}
          </div>
          {subtitle && (
            <p className="text-xs text-gray-500">
              {subtitle}
            </p>
          )}
        </div>
        
        {Icon && (
          <div className={`
            ${colorClasses[color].icon}
            p-3 
            rounded-xl 
            transition-transform 
            duration-300 
            group-hover:scale-110
          `}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>

      {/* Trend Indicator */}
      {trend && (
        <div className="flex items-center gap-2 mb-4">
          <div className={`
            flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium
            ${trend.isPositive !== false 
              ? 'bg-emerald-100 text-emerald-700' 
              : 'bg-red-100 text-red-700'
            }
          `}>
            <span className={trend.isPositive !== false ? '↗' : '↘'}>
              {trend.isPositive !== false ? '↗' : '↘'}
            </span>
            {Math.abs(trend.value)}%
          </div>
          <span className="text-xs text-gray-500">
            {trend.label}
          </span>
        </div>
      )}

      {/* Custom Content */}
      {children && (
        <div className="mt-4">
          {children}
        </div>
      )}

      {/* Subtle Animation Bar */}
      <div className={`
        h-1 
        bg-gradient-to-r 
        ${colorClasses[color].gradient}
        rounded-full 
        mt-4 
        transform 
        scale-x-0 
        group-hover:scale-x-100 
        transition-transform 
        duration-500 
        origin-left
      `} />
    </div>
  );
};

export default ModernCard;
