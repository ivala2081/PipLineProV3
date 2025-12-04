/**
 * Component Optimization Hooks
 * Advanced component loading and interaction optimizations
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';

// === INTERSECTION OBSERVER HOOK ===
export const useIntersectionObserver = (
  options: IntersectionObserverInit = {}
) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
        if (entry.isIntersecting && !hasIntersected) {
          setHasIntersected(true);
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
        ...options,
      }
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [options, hasIntersected]);

  return { elementRef, isIntersecting, hasIntersected };
};

// === LAZY LOADING HOOK ===
export const useLazyLoading = <T>(
  loader: () => Promise<T>,
  dependencies: React.DependencyList = []
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);

  const load = useCallback(async () => {
    if (hasLoaded) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await loader();
      setData(result);
      setHasLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load'));
    } finally {
      setLoading(false);
    }
  }, [loader, hasLoaded]);

  const reload = useCallback(() => {
    setHasLoaded(false);
    setData(null);
    load();
  }, [load]);

  return {
    data,
    loading,
    error,
    load,
    reload,
    hasLoaded,
  };
};

// === VIRTUAL SCROLLING HOOK ===
export const useVirtualScrolling = <T>(
  items: T[],
  itemHeight: number,
  containerHeight: number,
  overscan: number = 5
) => {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    
    return { startIndex, endIndex };
  }, [scrollTop, itemHeight, containerHeight, items.length, overscan]);

  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.startIndex, visibleRange.endIndex + 1);
  }, [items, visibleRange]);

  const totalHeight = items.length * itemHeight;
  const offsetY = visibleRange.startIndex * itemHeight;

  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop);
  }, []);

  return {
    containerRef,
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    visibleRange,
  };
};

// === DEBOUNCED SEARCH HOOK ===
export const useDebouncedSearch = (
  searchTerm: string,
  delay: number = 300
) => {
  const [debouncedTerm, setDebouncedTerm] = useState(searchTerm);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedTerm(searchTerm);
    }, delay);

    return () => clearTimeout(timer);
  }, [searchTerm, delay]);

  return debouncedTerm;
};

// === INFINITE SCROLLING HOOK ===
export const useInfiniteScroll = <T>(
  loadMore: () => Promise<T[]>,
  initialData: T[] = [],
  hasMore: boolean = true
) => {
  const [data, setData] = useState<T[]>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [page, setPage] = useState(1);
  const [hasMoreData, setHasMoreData] = useState(hasMore);

  const loadMoreData = useCallback(async () => {
    if (loading || !hasMoreData) return;

    setLoading(true);
    setError(null);

    try {
      const newData = await loadMore();
      setData(prev => [...prev, ...newData]);
      setPage(prev => prev + 1);
      setHasMoreData(newData.length > 0);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load more data'));
    } finally {
      setLoading(false);
    }
  }, [loadMore, loading, hasMoreData]);

  const reset = useCallback(() => {
    setData(initialData);
    setPage(1);
    setHasMoreData(hasMore);
    setError(null);
  }, [initialData, hasMore]);

  return {
    data,
    loading,
    error,
    loadMore: loadMoreData,
    reset,
    hasMore: hasMoreData,
    page,
  };
};

// === PERFORMANCE MONITORING HOOK ===
export const usePerformanceMonitoring = (componentName: string) => {
  const renderCount = useRef(0);
  const mountTime = useRef(Date.now());
  const lastRenderTime = useRef(Date.now());

  useEffect(() => {
    renderCount.current += 1;
    const now = Date.now();
    const renderTime = now - lastRenderTime.current;
    lastRenderTime.current = now;

    // Log performance metrics in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`${componentName} render #${renderCount.current}`, {
        renderTime: `${renderTime}ms`,
        totalTime: `${now - mountTime.current}ms`,
      });
    }
  });

  const getMetrics = useCallback(() => {
    return {
      renderCount: renderCount.current,
      totalTime: Date.now() - mountTime.current,
      avgRenderTime: (Date.now() - mountTime.current) / renderCount.current,
    };
  }, []);

  return { getMetrics };
};

// === MEMOIZATION HOOK ===
export const useMemoizedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  dependencies: React.DependencyList
): T => {
  return useCallback(callback, dependencies);
};

// === CONDITIONAL RENDERING HOOK ===
export const useConditionalRender = (
  condition: boolean,
  fallback?: React.ReactNode
) => {
  const [shouldRender, setShouldRender] = useState(condition);

  useEffect(() => {
    if (condition) {
      setShouldRender(true);
      return;
    } else {
      const timer = setTimeout(() => setShouldRender(false), 300);
      return () => clearTimeout(timer);
    }
  }, [condition]);

  return shouldRender ? null : fallback;
};

// === ELEMENT SIZE HOOK ===
export const useElementSize = () => {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });

    resizeObserver.observe(element);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  return { elementRef, size };
};

// === CLICK OUTSIDE HOOK ===
export const useClickOutside = (
  callback: () => void,
  enabled: boolean = true
) => {
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!enabled) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (elementRef.current && !elementRef.current.contains(event.target as Node)) {
        callback();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [callback, enabled]);

  return elementRef;
};

// === KEYBOARD SHORTCUTS HOOK ===
export const useKeyboardShortcuts = (
  shortcuts: Record<string, () => void>,
  enabled: boolean = true
) => {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      const modifier = event.ctrlKey || event.metaKey;
      const shortcutKey = modifier ? `ctrl+${key}` : key;
      
      if (shortcuts[shortcutKey]) {
        event.preventDefault();
        shortcuts[shortcutKey]();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts, enabled]);
};

// === COMPONENT OPTIMIZATION UTILITIES ===
export const optimizeComponent = <P extends object>(
  Component: React.ComponentType<P>,
  options: {
    memo?: boolean;
    lazy?: boolean;
    suspense?: boolean;
    errorBoundary?: boolean;
  } = {}
) => {
  let OptimizedComponent = Component;

  // Memoization
  if (options.memo) {
    OptimizedComponent = React.memo(OptimizedComponent) as unknown as React.ComponentType<P>;
  }

  // Lazy loading
  if (options.lazy) {
    const LazyComponent = React.lazy(() => Promise.resolve({ default: Component }));
    OptimizedComponent = LazyComponent as unknown as React.ComponentType<P>;
  }

  // Suspense wrapper
  if (options.suspense && options.lazy) {
    const SuspenseWrapper = (props: P) => {
      return React.createElement(
        React.Suspense,
        { fallback: React.createElement('div', null, 'Loading...') },
        React.createElement(OptimizedComponent, props)
      );
    };
    OptimizedComponent = SuspenseWrapper as React.ComponentType<P>;
  }

  return OptimizedComponent;
};

export default {
  useIntersectionObserver,
  useLazyLoading,
  useVirtualScrolling,
  useDebouncedSearch,
  useInfiniteScroll,
  usePerformanceMonitoring,
  useMemoizedCallback,
  useConditionalRender,
  useElementSize,
  useClickOutside,
  useKeyboardShortcuts,
  optimizeComponent,
};
