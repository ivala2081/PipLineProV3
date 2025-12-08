import { useEffect, useRef, useCallback } from 'react';

interface TouchGestureOptions {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number;
  minSwipeDistance?: number;
}

interface TouchPoint {
  x: number;
  y: number;
  timestamp: number;
}

export const useTouchGestures = (
  elementRef: React.RefObject<HTMLElement>,
  options: TouchGestureOptions = {}
) => {
  const {
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    threshold = 50,
    minSwipeDistance = 50
  } = options;

  const touchStartRef = useRef<TouchPoint | null>(null);
  const touchEndRef = useRef<TouchPoint | null>(null);
  const isSwipingRef = useRef(false);

  const getTouchPoint = (touch: Touch): TouchPoint => ({
    x: touch.clientX,
    y: touch.clientY,
    timestamp: Date.now()
  });

  const handleTouchStart = useCallback((event: TouchEvent) => {
    if (event.touches.length === 1) {
      const touch = event.touches[0];
      touchStartRef.current = getTouchPoint(touch);
      isSwipingRef.current = false;
    }
  }, []);

  const handleTouchMove = useCallback((event: TouchEvent) => {
    if (event.touches.length === 1 && touchStartRef.current) {
      const touch = event.touches[0];
      const currentPoint = getTouchPoint(touch);
      
      const deltaX = Math.abs(currentPoint.x - touchStartRef.current.x);
      const deltaY = Math.abs(currentPoint.y - touchStartRef.current.y);
      
      if (deltaX > threshold || deltaY > threshold) {
        isSwipingRef.current = true;
      }
    }
  }, [threshold]);

  const handleTouchEnd = useCallback((event: TouchEvent) => {
    if (event.changedTouches.length === 1 && touchStartRef.current) {
      const touch = event.changedTouches[0];
      touchEndRef.current = getTouchPoint(touch);
      
      if (isSwipingRef.current && touchStartRef.current && touchEndRef.current) {
        const deltaX = touchEndRef.current.x - touchStartRef.current.x;
        const deltaY = touchEndRef.current.y - touchStartRef.current.y;
        const deltaTime = touchEndRef.current.timestamp - touchStartRef.current.timestamp;
        
        // Only trigger if swipe is fast enough and long enough
        if (deltaTime < 300 && Math.abs(deltaX) > minSwipeDistance || Math.abs(deltaY) > minSwipeDistance) {
          if (Math.abs(deltaX) > Math.abs(deltaY)) {
            // Horizontal swipe
            if (deltaX > 0 && onSwipeRight) {
              onSwipeRight();
            } else if (deltaX < 0 && onSwipeLeft) {
              onSwipeLeft();
            }
          } else {
            // Vertical swipe
            if (deltaY > 0 && onSwipeDown) {
              onSwipeDown();
            } else if (deltaY < 0 && onSwipeUp) {
              onSwipeUp();
            }
          }
        }
      }
      
      // Reset
      touchStartRef.current = null;
      touchEndRef.current = null;
      isSwipingRef.current = false;
    }
  }, [onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, minSwipeDistance]);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchmove', handleTouchMove, { passive: true });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [elementRef, handleTouchStart, handleTouchMove, handleTouchEnd]);

  return {
    isSwiping: isSwipingRef.current
  };
};
