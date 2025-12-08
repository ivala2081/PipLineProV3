import React, { useEffect, useRef, useState } from 'react';

interface CountUpProps {
  end: number;
  start?: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
  separator?: string;
  delay?: number;
}

/**
 * CountUp Component - Animates numbers from start to end value
 * 
 * Features:
 * - Smooth easing animation
 * - Customizable duration and delay
 * - Supports decimals, prefixes, suffixes
 * - Number formatting with separators
 * - Automatic visibility detection (animates when in view)
 * 
 * Usage:
 * <CountUp end={1234567.89} decimals={2} prefix="₺" separator="," duration={1500} />
 */
export const CountUp: React.FC<CountUpProps> = ({
  end,
  start = 0,
  duration = 2000,
  decimals = 0,
  prefix = '',
  suffix = '',
  className = '',
  separator = ',',
  delay = 0
}) => {
  const [count, setCount] = useState(start);
  const [hasAnimated, setHasAnimated] = useState(false);
  const elementRef = useRef<HTMLSpanElement>(null);
  const frameRef = useRef<number>();
  const startTimeRef = useRef<number>();

  // Easing function for smooth animation (easeOutCubic)
  const easeOutCubic = (t: number): number => {
    return 1 - Math.pow(1 - t, 3);
  };

  // Format number with separators
  const formatNumber = (num: number): string => {
    const fixedNum = num.toFixed(decimals);
    const [integer, decimal] = fixedNum.split('.');
    
    // Add thousand separators
    const formattedInteger = integer.replace(/\B(?=(\d{3})+(?!\d))/g, separator);
    
    return decimal ? `${formattedInteger}.${decimal}` : formattedInteger;
  };

  // Animation function
  const animate = (timestamp: number) => {
    if (!startTimeRef.current) {
      startTimeRef.current = timestamp;
    }

    const elapsed = timestamp - startTimeRef.current;
    const progress = Math.min(elapsed / duration, 1);
    
    // Apply easing
    const easedProgress = easeOutCubic(progress);
    
    // Calculate current value
    const currentValue = start + (end - start) * easedProgress;
    setCount(currentValue);

    if (progress < 1) {
      frameRef.current = requestAnimationFrame(animate);
    } else {
      setCount(end); // Ensure we end at exact value
    }
  };

  // Start animation when element is in viewport
  useEffect(() => {
    if (hasAnimated) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setHasAnimated(true);
          
          // Start animation after delay
          const timeoutId = setTimeout(() => {
            startTimeRef.current = undefined;
            frameRef.current = requestAnimationFrame(animate);
          }, delay);

          return () => clearTimeout(timeoutId);
        }
      },
      { threshold: 0.1 }
    );

    if (elementRef.current) {
      observer.observe(elementRef.current);
    }

    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
      observer.disconnect();
    };
  }, [hasAnimated, delay]);

  return (
    <span 
      ref={elementRef}
      className={`animate-count-up ${className}`}
    >
      {prefix}{formatNumber(count)}{suffix}
    </span>
  );
};

export default CountUp;

