import React from 'react';
import { LucideIcon } from 'lucide-react';
import { UnifiedCard } from '../design-system';
import { CardContent } from '../components/ui/card';
import { useAnimatedNumber } from '../hooks/useAnimatedNumber';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color: 'gray' | 'green' | 'purple' | 'orange' | 'red' | 'teal' | 'indigo' | 'pink';
  subtitle?: string;
  className?: string;
  animated?: boolean; // Enable number animation
  animationDuration?: number; // Animation duration in ms (default: 400)
  showGlass?: boolean; // Enable glassmorphism effect (Phase 2)
}

const colorMap = {
  gray: {
    text: 'text-gray-600',
    bg: 'bg-gray-50',
    iconBg: 'bg-gray-100'
  },
  green: {
    text: 'text-green-600',
    bg: 'bg-green-50',
    iconBg: 'bg-green-100'
  },
  purple: {
    text: 'text-purple-600',
    bg: 'bg-purple-50',
    iconBg: 'bg-purple-100'
  },
  orange: {
    text: 'text-orange-600',
    bg: 'bg-orange-50',
    iconBg: 'bg-orange-100'
  },
  red: {
    text: 'text-red-600',
    bg: 'bg-red-50',
    iconBg: 'bg-red-100'
  },
  teal: {
    text: 'text-teal-600',
    bg: 'bg-teal-50',
    iconBg: 'bg-teal-100'
  },
  indigo: {
    text: 'text-indigo-600',
    bg: 'bg-indigo-50',
    iconBg: 'bg-indigo-100'
  },
  pink: {
    text: 'text-pink-600',
    bg: 'bg-pink-50',
    iconBg: 'bg-pink-100'
  }
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon: Icon,
  color,
  subtitle,
  className = '',
  animated = false,
  animationDuration = 400,
  showGlass = false
}) => {
  const colors = colorMap[color];
  
  // Parse numeric value for animation
  const numericValue = typeof value === 'string' ? parseFloat(value.replace(/[^\d.-]/g, '')) || 0 : value;
  
  // Use animated number hook if animation is enabled and value is numeric
  const animatedNumber = useAnimatedNumber(numericValue, {
    duration: animationDuration,
    easing: 'easeOut',
    decimals: 0,
    prefix: typeof value === 'string' && value.includes('₺') ? '₺' : '',
    suffix: typeof value === 'string' && value.includes('%') ? '%' : ''
  });
  
  // Use animated value if animation is enabled, otherwise use original value
  const displayValue = animated && !isNaN(numericValue) ? animatedNumber.displayValue : value;
  
  // Glassmorphism class conditionally applied
  const glassClass = showGlass ? 'glass-card card-hover-subtle' : '';
  
  return (
    <UnifiedCard variant="elevated" className={`relative overflow-hidden shadow-premium ${glassClass} ${className}`}>
      {/* Background decorative element */}
      <div className={`absolute top-0 right-0 w-32 h-32 ${colors.bg} rounded-full -translate-y-16 translate-x-16`}></div>
      
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`w-12 h-12 ${colors.bg} rounded-xl flex items-center justify-center shadow-lg`}>
            <Icon className={`h-6 w-6 ${colors.text}`} />
          </div>
        </div>
        
        <div className="space-y-2">
          <p className="text-xs font-medium text-gray-600">{title}</p>
          <p 
            className="text-lg font-bold text-gray-900 transition-all duration-75 ease-out"
            style={{ 
              fontVariantNumeric: 'tabular-nums',
              willChange: animated ? 'contents' : 'auto'
            }}
          >
            {displayValue}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-500">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </UnifiedCard>
  );
};

export default MetricCard;
