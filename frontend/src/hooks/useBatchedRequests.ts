/**
 * Hook for batched API requests
 * Reduces network overhead by batching multiple requests
 */
import { useCallback, useEffect, useRef } from 'react';
import { ApiClient } from '../utils/apiClient';
import { getRequestBatcher } from '../utils/requestBatcher';

let apiClientInstance: ApiClient | null = null;

export function useBatchedRequests() {
  const batcherRef = useRef<ReturnType<typeof getRequestBatcher> | null>(null);

  useEffect(() => {
    // Initialize API client if needed
    if (!apiClientInstance) {
      apiClientInstance = new ApiClient('/api/v1');
    }

    // Initialize batcher
    batcherRef.current = getRequestBatcher(apiClientInstance);

    // Flush on unmount
    return () => {
      if (batcherRef.current) {
        batcherRef.current.flush();
      }
    };
  }, []);

  const batchedGet = useCallback(
    <T = any>(url: string, params?: Record<string, any>): Promise<T> => {
      if (!batcherRef.current) {
        throw new Error('RequestBatcher not initialized');
      }
      return batcherRef.current.add<T>(url, 'GET', params);
    },
    []
  );

  const batchedPost = useCallback(
    <T = any>(url: string, params?: Record<string, any>): Promise<T> => {
      if (!batcherRef.current) {
        throw new Error('RequestBatcher not initialized');
      }
      return batcherRef.current.add<T>(url, 'POST', params);
    },
    []
  );

  return {
    batchedGet,
    batchedPost,
    flush: () => batcherRef.current?.flush(),
  };
}

