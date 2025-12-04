/**
 * Hook for batched dashboard data fetching
 * Reduces API calls by batching multiple analytics requests
 */

import { useState, useEffect, useCallback } from 'react';
import { api } from '../utils/apiClient';

interface DashboardData {
  stats: any;
  systemPerformance: any;
  dataQuality: any;
  securityMetrics: any;
  commissionAnalytics: any;
  exchangeRates: any;
  clientAnalytics: any;
  ledgerData: any;
  pspSummaryStats: any;
}

interface UseBatchedDashboardDataOptions {
  timeRange?: string;
  enabled?: boolean;
  batchDelay?: number;
}

export const useBatchedDashboardData = (
  options: UseBatchedDashboardDataOptions = {}
) => {
  const {
    timeRange = 'all',
    enabled = true,
    batchDelay = 100 // 100ms batch delay
  } = options;

  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchBatchedData = useCallback(async () => {
    if (!enabled) return;

    setLoading(true);
    setError(null);

    try {
      // Create batch key for analytics requests
      const batchKey = `analytics-${timeRange}-${Date.now()}`;
      
      // Batch all analytics requests
      const [
        stats,
        systemPerformance,
        dataQuality,
        securityMetrics,
        commissionAnalytics,
        exchangeRates,
        clientAnalytics,
        ledgerData,
        pspSummaryStats
      ] = await Promise.all([
        api.makeBatchedRequest(`/api/v1/analytics/dashboard/stats?range=${timeRange}`, {}, batchKey),
        api.makeBatchedRequest('/api/v1/analytics/system/performance', {}, batchKey),
        api.makeBatchedRequest('/api/v1/analytics/data/quality', {}, batchKey),
        api.makeBatchedRequest('/api/v1/analytics/security/metrics', {}, batchKey),
        api.makeBatchedRequest(`/api/v1/analytics/commission/analytics?range=${timeRange}`, {}, batchKey),
        api.makeBatchedRequest('/api/v1/exchange-rates/rates', {}, batchKey),
        api.makeBatchedRequest(`/api/v1/analytics/clients/analytics?range=${timeRange}`, {}, batchKey),
        api.makeBatchedRequest('/api/v1/analytics/ledger-data', {}, batchKey),
        api.makeBatchedRequest('/transactions/psp_summary_stats', {}, batchKey)
      ]);

      setData({
        stats,
        systemPerformance,
        dataQuality,
        securityMetrics,
        commissionAnalytics,
        exchangeRates,
        clientAnalytics,
        ledgerData,
        pspSummaryStats
      });

    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch dashboard data'));
    } finally {
      setLoading(false);
    }
  }, [enabled, timeRange, batchDelay]);

  // Fetch data on mount and when dependencies change
  useEffect(() => {
    fetchBatchedData();
  }, [fetchBatchedData]);

  // Refresh function
  const refresh = useCallback(() => {
    fetchBatchedData();
  }, [fetchBatchedData]);

  return {
    data,
    loading,
    error,
    refresh
  };
};

// Individual data hooks that use batching
export const useBatchedStats = (timeRange: string = 'all') => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const batchKey = `stats-${timeRange}-${Date.now()}`;
      const stats = await api.makeBatchedRequest(
        `/api/v1/analytics/dashboard/stats?range=${timeRange}`,
        {},
        batchKey
      );
      setData(stats);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch stats'));
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { data, loading, error, refresh: fetchStats };
};

export const useBatchedSystemPerformance = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchPerformance = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const batchKey = `performance-${Date.now()}`;
      const performance = await api.makeBatchedRequest(
        '/api/v1/analytics/system/performance',
        {},
        batchKey
      );
      setData(performance);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch system performance'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPerformance();
  }, [fetchPerformance]);

  return { data, loading, error, refresh: fetchPerformance };
};

export const useBatchedAnalytics = (timeRange: string = 'all') => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const batchKey = `analytics-${timeRange}-${Date.now()}`;
      const [dataQuality, securityMetrics, commissionAnalytics] = await Promise.all([
        api.makeBatchedRequest('/api/v1/analytics/data/quality', {}, batchKey),
        api.makeBatchedRequest('/api/v1/analytics/security/metrics', {}, batchKey),
        api.makeBatchedRequest(`/api/v1/analytics/commission/analytics?range=${timeRange}`, {}, batchKey)
      ]);

      setData({
        dataQuality,
        securityMetrics,
        commissionAnalytics
      });
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch analytics data'));
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return { data, loading, error, refresh: fetchAnalytics };
};

export default useBatchedDashboardData;
