import useSWR, { useSWRConfig } from 'swr';
import { useCallback, useRef, useEffect } from 'react';

interface PerformanceOptions {
  // Reduce refresh frequency for heavy endpoints
  refreshInterval?: number;
  // Enable request deduplication
  dedupe?: boolean;
  // Cache duration in milliseconds
  cacheDuration?: number;
  // Maximum concurrent requests
  maxConcurrent?: number;
}

// Global request tracker to prevent excessive concurrent requests
const requestTracker = {
  activeRequests: new Set<string>(),
  maxConcurrent: 3, // Limit concurrent requests (reduced from 6)
};

export const usePerformanceOptimizedSWR = <T = any>(
  key: string | null,
  fetcher: (url: string) => Promise<T>,
  options: PerformanceOptions = {}
) => {
  const {
    refreshInterval = 30 * 60 * 1000, // 30 minutes default (increased from 15)
    dedupe = true,
    cacheDuration = 60 * 60 * 1000, // 60 minutes default (increased from 30)
    maxConcurrent = 2, // Reduced from 4
  } = options;

  const { mutate, cache } = useSWRConfig();
  const requestRef = useRef<string | null>(null);

  // Throttled fetcher to prevent excessive requests
  const throttledFetcher = useCallback(
    async (url: string): Promise<T> => {
      // Check if we've exceeded concurrent request limit
      if (requestTracker.activeRequests.size >= maxConcurrent) {
        console.warn(`Too many concurrent requests (${requestTracker.activeRequests.size}/${maxConcurrent}). Queuing request for ${url}`);
        // Wait a bit and retry
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // Add to active requests tracker
      requestTracker.activeRequests.add(url);
      requestRef.current = url;

      try {
        const result = await fetcher(url);
        return result;
      } finally {
        // Remove from active requests tracker
        requestTracker.activeRequests.delete(url);
        requestRef.current = null;
      }
    },
    [fetcher, maxConcurrent]
  );

  // Enhanced SWR configuration for performance
  const swrOptions = {
    refreshInterval,
    dedupingInterval: cacheDuration,
    revalidateOnFocus: false,
    revalidateOnMount: false,
    revalidateIfStale: false,
    errorRetryCount: 2,
    errorRetryInterval: 2000,
    loadingTimeout: 10000,
    compare: (a: T | undefined, b: T | undefined) => JSON.stringify(a) === JSON.stringify(b),
  };

  const { data, error, isLoading, mutate: swrMutate } = useSWR(
    key && dedupe ? key : null,
    key ? throttledFetcher : null,
    swrOptions
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (requestRef.current) {
        requestTracker.activeRequests.delete(requestRef.current);
      }
    };
  }, []);

  // Enhanced mutate function with cache management
  const optimizedMutate = useCallback(
    (data?: T | Promise<T>, shouldRevalidate = true) => {
      if (key) {
        return swrMutate(data, shouldRevalidate);
      }
      return Promise.resolve();
    },
    [key, swrMutate]
  );

  return {
    data,
    error,
    isLoading,
    mutate: optimizedMutate,
    isValidating: isLoading && !error,
  };
};

// Hook for batch operations to reduce API calls
export const useBatchSWR = <T = any>(
  keys: (string | null)[],
  fetcher: (urls: string[]) => Promise<T[]>,
  options: PerformanceOptions = {}
) => {
  const validKeys = keys.filter(Boolean) as string[];
  
  return usePerformanceOptimizedSWR(
    validKeys.length > 0 ? `batch:${validKeys.join(',')}` : null,
    async () => {
      if (validKeys.length === 0) return [];
      return await fetcher(validKeys);
    },
    {
      ...options,
      refreshInterval: 20 * 60 * 1000, // 20 minutes for batch requests
    }
  );
};

export default usePerformanceOptimizedSWR;
