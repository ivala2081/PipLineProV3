import React from 'react';
import { useAnimatedNumber } from '../hooks/useAnimatedNumber';

interface AnimatedValueProps {
  value: string | number;
  className?: string;
  duration?: number;
  animated?: boolean;
}

/**
 * AnimatedValue component for inline number animations
 * Can be used in any context where you want to animate a number display
 */
export const AnimatedValue: React.FC<AnimatedValueProps> = ({
  value,
  className = '',
  duration = 500,
  animated = true
}) => {
  // Parse numeric value for animation
  const numericValue = typeof value === 'string' ? parseFloat(value.replace(/[^\d.-]/g, '')) || 0 : value;
  
  // Detect currency symbol and other formatting
  const prefix = typeof value === 'string' && value.includes('$') ? '$' : 
                 typeof value === 'string' && value.includes('₺') ? '₺' : '';
  const suffix = typeof value === 'string' && value.includes('%') ? '%' : '';
  
  // Use animated number hook if animation is enabled and value is numeric
  const animatedNumber = useAnimatedNumber(numericValue, {
    duration,
    easing: 'easeOut',
    decimals: 0,
    prefix,
    suffix
  });
  
  // Use animated value if animation is enabled, otherwise use original value
  const displayValue = animated && !isNaN(numericValue) ? animatedNumber.displayValue : value;
  
  return (
    <span 
      className={className}
      style={{ 
        fontVariantNumeric: 'tabular-nums',
        willChange: animated ? 'contents' : 'auto'
      }}
    >
      {displayValue}
    </span>
  );
};

export default AnimatedValue;
