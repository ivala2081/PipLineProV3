import { useState, useEffect, useRef } from 'react';

interface UseAnimatedNumberOptions {
  duration?: number; // Animation duration in milliseconds
  easing?: 'easeOut' | 'easeIn' | 'linear' | 'easeInOut';
  decimals?: number; // Number of decimal places to show
  prefix?: string; // Currency prefix like '₺' or '$'
  suffix?: string; // Currency suffix
  separator?: string; // Thousand separator (default: ',')
}

/**
 * Custom hook for animating numbers from 0 to target value
 * Fast animation (300-500ms) for professional financial dashboards
 */
export const useAnimatedNumber = (
  targetValue: number,
  options: UseAnimatedNumberOptions = {}
) => {
  const {
    duration = 400, // Fast animation - 400ms
    easing = 'easeOut',
    decimals = 0,
    prefix = '',
    suffix = '',
    separator = ','
  } = options;

  const [displayValue, setDisplayValue] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const animationRef = useRef<number>();
  const startTimeRef = useRef<number>();
  const startValueRef = useRef<number>(0);

  // Easing functions for smooth animation
  const easingFunctions = {
    linear: (t: number) => t,
    easeOut: (t: number) => {
      // Quintic ease-out for ultra-smooth deceleration
      return 1 - Math.pow(1 - t, 5);
    },
    easeIn: (t: number) => Math.pow(t, 3), // Cubic ease-in
    easeInOut: (t: number) => {
      // Smooth ease-in-out with better acceleration/deceleration
      return t < 0.5 
        ? 4 * Math.pow(t, 3) 
        : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }
  };

  // Format number with separators and decimal places
  const formatNumber = (value: number): string => {
    const fixedValue = value.toFixed(decimals);
    const parts = fixedValue.split('.');
    
    // Add thousand separators to integer part
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, separator);
    
    const formattedNumber = parts.join('.');
    return `${prefix}${formattedNumber}${suffix}`;
  };

  // Animation frame function with smooth interpolation
  const animate = (currentTime: number) => {
    if (!startTimeRef.current) {
      startTimeRef.current = currentTime;
    }

    const elapsed = currentTime - startTimeRef.current;
    const progress = Math.min(elapsed / duration, 1);
    
    // Apply easing for smooth motion
    const easedProgress = easingFunctions[easing](progress);
    
    // Calculate current value with smooth interpolation
    const currentValue = startValueRef.current + (targetValue - startValueRef.current) * easedProgress;
    
    // Use smoother rounding for large numbers
    const smoothValue = Math.abs(currentValue) > 1000 
      ? Math.round(currentValue) 
      : currentValue;
    
    setDisplayValue(smoothValue);

    if (progress < 1) {
      // Continue animation
      animationRef.current = requestAnimationFrame(animate);
    } else {
      // Animation complete - ensure exact final value
      setDisplayValue(targetValue);
      setIsAnimating(false);
      animationRef.current = undefined;
      startTimeRef.current = undefined;
    }
  };

  // Start animation when target value changes
  useEffect(() => {
    // Cancel any existing animation
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    // Don't animate if values are the same or target is 0
    if (targetValue === displayValue || targetValue === 0) {
      setDisplayValue(targetValue);
      return;
    }

    // Start new animation
    setIsAnimating(true);
    startValueRef.current = displayValue;
    startTimeRef.current = undefined;
    
    animationRef.current = requestAnimationFrame(animate);

    // Cleanup function
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [targetValue]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  return {
    displayValue: formatNumber(displayValue),
    rawValue: displayValue,
    isAnimating,
    targetValue
  };
};

export default useAnimatedNumber;
