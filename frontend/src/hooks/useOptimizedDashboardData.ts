import { useCallback, useMemo } from 'react';
import { usePerformanceOptimizedSWR } from './usePerformanceOptimizedSWR';
import { queryKeys } from '../config/swrConfig';

interface DashboardData {
  dashboardStats: any;
  systemPerformance: any;
  dataQuality: any;
  securityMetrics: any;
  commissionAnalytics: any;
  exchangeRates: any;
  clientAnalytics: any;
}

export const useOptimizedDashboardData = (timeRange: string = 'all') => {
  // Batch all dashboard-related API calls
  const dashboardKeys = useMemo(() => [
    queryKeys.dashboard.stats(timeRange),
    queryKeys.analytics.systemPerformance(),
    queryKeys.analytics.dataQuality(),
    queryKeys.analytics.securityMetrics(),
    queryKeys.analytics.commission(timeRange),
    queryKeys.exchangeRates.all(),
    queryKeys.analytics.clients(timeRange),
  ], [timeRange]);

  // Batch fetcher that makes multiple requests in parallel
  const batchFetcher = useCallback(async (urls: string[]) => {
    try {
      const requests = urls.map(url => 
        fetch(url, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'max-age=300', // 5 minutes cache
          },
        }).then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
      );

      const results = await Promise.allSettled(requests);
      
      // Return results in the same order as URLs
      return results.map((result, index) => ({
        url: urls[index],
        data: result.status === 'fulfilled' ? result.value : null,
        error: result.status === 'rejected' ? result.reason : null,
      }));
    } catch (error) {
      console.error('Batch fetch error:', error);
      throw error;
    }
  }, []);

  const { data: batchData, error, isLoading, mutate } = usePerformanceOptimizedSWR(
    `dashboard-batch-${timeRange}`,
    () => batchFetcher(dashboardKeys),
    {
      refreshInterval: 30 * 60 * 1000, // 30 minutes (increased from 15)
      cacheDuration: 60 * 60 * 1000, // 60 minutes (increased from 30)
      maxConcurrent: 1, // Only one batch at a time
    }
  );

  // Parse batch results into individual data objects
  const dashboardData = useMemo(() => {
    if (!batchData || !Array.isArray(batchData)) return null;

    const data: Partial<DashboardData> = {};
    
    batchData.forEach(({ url, data: resultData, error: resultError }) => {
      if (resultError) {
        console.warn(`Failed to fetch ${url}:`, resultError);
        return;
      }

      // Map URLs to data properties
      if (url.includes('dashboard/stats')) {
        data.dashboardStats = resultData;
      } else if (url.includes('system/performance')) {
        data.systemPerformance = resultData;
      } else if (url.includes('data/quality')) {
        data.dataQuality = resultData;
      } else if (url.includes('security/metrics')) {
        data.securityMetrics = resultData;
      } else if (url.includes('commission/analytics')) {
        data.commissionAnalytics = resultData;
      } else if (url.includes('exchange-rates')) {
        data.exchangeRates = resultData;
      } else if (url.includes('clients/analytics')) {
        data.clientAnalytics = resultData;
      }
    });

    return data as DashboardData;
  }, [batchData]);

  // Refresh function
  const refreshData = useCallback(() => {
    mutate();
  }, [mutate]);

  return {
    dashboardData,
    error,
    isLoading,
    refreshData,
    isRefreshing: isLoading && dashboardData !== null,
  };
};

// Hook for individual components that need specific data
export const useDashboardStats = (timeRange: string = 'all') => {
  return usePerformanceOptimizedSWR(
    queryKeys.dashboard.stats(timeRange),
    async (url) => {
      const response = await fetch(url, {
        credentials: 'include',
        headers: { 'Cache-Control': 'max-age=300' },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    },
    {
      refreshInterval: 45 * 60 * 1000, // 45 minutes (increased from 20)
      cacheDuration: 60 * 60 * 1000, // 60 minutes (increased from 30)
    }
  );
};

export const useSystemPerformance = () => {
  return usePerformanceOptimizedSWR(
    queryKeys.analytics.systemPerformance(),
    async (url) => {
      const response = await fetch(url, {
        credentials: 'include',
        headers: { 'Cache-Control': 'max-age=600' }, // 10 minutes cache
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    },
    {
      refreshInterval: 20 * 60 * 1000, // 20 minutes (increased from 10)
      cacheDuration: 40 * 60 * 1000, // 40 minutes (increased from 20)
    }
  );
};

export default useOptimizedDashboardData;
