/**
 * Custom hook for managing lazy loading with preloading and caching
 */

import { useCallback, useEffect, useRef, useState } from 'react';

interface LazyLoadingOptions {
  preload?: boolean;
  preloadDelay?: number;
  cache?: boolean;
  retryCount?: number;
  retryDelay?: number;
}

interface LazyLoadingState {
  isLoading: boolean;
  isLoaded: boolean;
  error: Error | null;
  retryCount: number;
}

interface LazyLoadingReturn {
  state: LazyLoadingState;
  preload: () => Promise<void>;
  retry: () => Promise<void>;
  clearCache: () => void;
}

// Cache for loaded components
const componentCache = new Map<string, any>();

// Preload queue for components
const preloadQueue = new Set<string>();

export const useLazyLoading = (
  importFn: () => Promise<any>,
  options: LazyLoadingOptions = {}
): LazyLoadingReturn => {
  const {
    preload = false,
    preloadDelay = 0,
    cache = true,
    retryCount: maxRetryCount = 3,
    retryDelay = 1000,
  } = options;

  const [state, setState] = useState<LazyLoadingState>({
    isLoading: false,
    isLoaded: false,
    error: null,
    retryCount: 0,
  });

  const importFnRef = useRef(importFn);
  const cacheKey = useRef(importFn.toString());

  // Update import function reference
  useEffect(() => {
    importFnRef.current = importFn;
    cacheKey.current = importFn.toString();
  }, [importFn]);

  const loadComponent = useCallback(async (): Promise<void> => {
    const key = cacheKey.current;

    // Check cache first
    if (cache && componentCache.has(key)) {
      setState(prev => ({
        ...prev,
        isLoaded: true,
        isLoading: false,
        error: null,
      }));
      return;
    }

    setState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const component = await importFnRef.current();
      
      // Cache the component
      if (cache) {
        componentCache.set(key, component);
      }

      setState(prev => ({
        ...prev,
        isLoaded: true,
        isLoading: false,
        error: null,
        retryCount: 0,
      }));
    } catch (error) {
      const currentRetryCount = state.retryCount;
      
      if (currentRetryCount < maxRetryCount) {
        // Retry after delay
        setTimeout(() => {
          setState(prev => ({
            ...prev,
            retryCount: prev.retryCount + 1,
          }));
          loadComponent();
        }, retryDelay);
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error as Error,
        }));
      }
    }
  }, [cache, maxRetryCount, retryDelay, state.retryCount]);

  const preloadComponent = useCallback(async (): Promise<void> => {
    const key = cacheKey.current;
    
    if (preloadQueue.has(key)) {
      return; // Already in preload queue
    }

    preloadQueue.add(key);

    if (preloadDelay > 0) {
      await new Promise(resolve => setTimeout(resolve, preloadDelay));
    }

    try {
      const component = await importFnRef.current();
      
      if (cache) {
        componentCache.set(key, component);
      }

      preloadQueue.delete(key);
    } catch (error) {
      preloadQueue.delete(key);
      console.warn('Failed to preload component:', error);
    }
  }, [preloadDelay, cache]);

  const retry = useCallback(async (): Promise<void> => {
    setState(prev => ({
      ...prev,
      retryCount: 0,
      error: null,
    }));
    await loadComponent();
  }, [loadComponent]);

  const clearCache = useCallback((): void => {
    const key = cacheKey.current;
    componentCache.delete(key);
    setState(prev => ({
      ...prev,
      isLoaded: false,
    }));
  }, []);

  // Auto-preload if enabled
  useEffect(() => {
    if (preload) {
      preloadComponent();
    }
  }, [preload, preloadComponent]);

  return {
    state,
    preload: preloadComponent,
    retry,
    clearCache,
  };
};

// Hook for preloading multiple components
export const usePreloadComponents = (
  importFns: (() => Promise<any>)[],
  options: LazyLoadingOptions = {}
) => {
  const [preloadedCount, setPreloadedCount] = useState(0);
  const [isPreloading, setIsPreloading] = useState(false);

  const preloadAll = useCallback(async (): Promise<void> => {
    setIsPreloading(true);
    setPreloadedCount(0);

    const promises = importFns.map(async (importFn, index) => {
      try {
        await importFn();
        setPreloadedCount(prev => prev + 1);
      } catch (error) {
        console.warn(`Failed to preload component ${index}:`, error);
      }
    });

    await Promise.allSettled(promises);
    setIsPreloading(false);
  }, [importFns]);

  return {
    preloadAll,
    preloadedCount,
    isPreloading,
    totalComponents: importFns.length,
  };
};

// Utility function to clear all cached components
export const clearAllComponentCache = (): void => {
  componentCache.clear();
  preloadQueue.clear();
};

// Utility function to get cache statistics
export const getCacheStats = () => ({
  cachedComponents: componentCache.size,
  preloadQueueSize: preloadQueue.size,
  cacheKeys: Array.from(componentCache.keys()),
});
