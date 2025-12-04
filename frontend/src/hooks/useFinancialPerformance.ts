/**
 * Custom Hook: useFinancialPerformance
 * Financial performance verilerini yönetir
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardService } from '../services/dashboardService';
import { logger } from '../utils/logger';
import { apiClient } from '../utils/apiClient';
import type {
  FinancialPerformanceResponse,
  FinancialPeriodData,
  TimeRange,
  ViewType,
} from '../types/dashboard.types';

interface UseFinancialPerformanceOptions {
  timeRange: TimeRange;
  viewType: ViewType;
  enabled?: boolean;
}

interface UseFinancialPerformanceReturn {
  data: FinancialPerformanceResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  getDayData: (date: Date) => Promise<FinancialPeriodData | null>;
  getMonthData: (date: Date) => Promise<FinancialPeriodData | null>;
}

export const useFinancialPerformance = ({
  timeRange,
  viewType,
  enabled = true,
}: UseFinancialPerformanceOptions): UseFinancialPerformanceReturn => {
  const [data, setData] = useState<FinancialPerformanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  const loadData = useCallback(async () => {
    if (!enabled) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setLoading(true);
    setError(null);

    try {
      logger.dashboard('Loading financial performance data', { timeRange, viewType });

      const result = await dashboardService.getFinancialPerformance(timeRange, viewType);

      if (!isMountedRef.current || abortControllerRef.current.signal.aborted) {
        return;
      }

      // Debug: Log result structure
      if (import.meta.env.DEV) {
        logger.dashboard('Financial performance result received', {
          hasResult: !!result,
          hasData: !!result?.data,
          hasDaily: !!result?.data?.daily,
          hasMonthly: !!result?.data?.monthly,
          hasAnnual: !!result?.data?.annual,
          dailySample: result?.data?.daily ? {
            total_bank_tl: result.data.daily.total_bank_tl,
            total_cc_tl: result.data.daily.total_cc_tl,
            net_cash_tl: result.data.daily.net_cash_tl,
          } : null,
          monthlySample: result?.data?.monthly ? {
            total_bank_tl: result.data.monthly.total_bank_tl,
            total_cc_tl: result.data.monthly.total_cc_tl,
            net_cash_tl: result.data.monthly.net_cash_tl,
          } : null,
          annualSample: result?.data?.annual ? {
            total_bank_tl: result.data.annual.total_bank_tl,
            total_cc_tl: result.data.annual.total_cc_tl,
            net_cash_tl: result.data.annual.net_cash_tl,
          } : null,
        });
      }

      setData(result);
      logger.dashboard('Financial performance data loaded successfully');
    } catch (err: any) {
      if (!isMountedRef.current || abortControllerRef.current.signal.aborted) {
        return;
      }

      const errorMessage =
        err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError')
          ? 'Bağlantı hatası. Lütfen internet bağlantınızı kontrol edin.'
          : err.message?.includes('401') || err.message?.includes('403')
            ? 'Yetki hatası. Lütfen tekrar giriş yapın.'
            : err.message?.includes('500')
              ? 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.'
              : 'Finansal performans verisi yüklenemedi. Lütfen tekrar deneyin.';

      logger.error('Error loading financial performance:', err);
      setError(errorMessage);

      // Set fallback data
      const emptyData: FinancialPeriodData = {
        total_bank_usd: 0,
        total_bank_tl: 0,
        total_cc_usd: 0,
        total_cc_tl: 0,
        total_tether_usd: 0,
        total_tether_tl: 0,
        conv_usd: 0,
        conv_tl: 0,
        total_transactions: 0,
        bank_count: 0,
        cc_count: 0,
        tether_count: 0,
      };

      setData({
        success: true,
        data: {
          daily: emptyData,
          monthly: emptyData,
          annual: emptyData,
          exchange_rate: 48.0,
        },
      });
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [timeRange, viewType, enabled]);

  const refresh = useCallback(async () => {
    dashboardService.clearCache();
    await loadData();
  }, [loadData]);

  const getDayData = useCallback(async (date: Date): Promise<FinancialPeriodData | null> => {
    try {
      const dateStr = date.toISOString().split('T')[0];
      const response = await apiClient.get<{ success: boolean; data: FinancialPeriodData }>(
        `/financial-performance/daily?date=${dateStr}`,
        {
          timeout: 30000, // 30 seconds - backend might be slow
          retries: 1, // Reduce retries to fail faster
        },
      );
      // apiClient.get already returns { data: T, status, headers }
      // So response.data is the backend response: { success: boolean, data: FinancialPeriodData }
      const backendResponse = response.data;
      if (backendResponse && backendResponse.success && backendResponse.data) {
        return backendResponse.data;
      }
      logger.warn('Day data response missing data:', backendResponse);
      return null;
    } catch (err: any) {
      // Don't log timeout errors as errors - backend might be slow
      if (err.message?.includes('timeout') || err.message?.includes('Timeout')) {
        logger.warn('Day data request timeout - backend may be slow');
      } else if (err.message?.includes('ERR_EMPTY_RESPONSE') || err.message?.includes('Failed to fetch')) {
        logger.warn('Backend not responding for day data (non-critical)');
      } else {
        logger.error('Error fetching day data:', err);
      }
      return null;
    }
  }, []);

  const getMonthData = useCallback(async (date: Date): Promise<FinancialPeriodData | null> => {
    try {
      const year = date.getFullYear();
      const monthNum = date.getMonth() + 1;
      const response = await apiClient.get<{ success: boolean; data: FinancialPeriodData }>(
        `/financial-performance/monthly?year=${year}&month=${monthNum}&view=${viewType}`,
        {
          timeout: 30000, // 30 seconds - backend might be slow
          retries: 1, // Reduce retries to fail faster
        },
      );
      // apiClient.get already returns { data: T, status, headers }
      // So response.data is the backend response: { success: boolean, data: FinancialPeriodData }
      const backendResponse = response.data;
      if (backendResponse && backendResponse.success && backendResponse.data) {
        return backendResponse.data;
      }
      logger.warn('Month data response missing data:', backendResponse);
      return null;
    } catch (err: any) {
      // Don't log timeout errors as errors - backend might be slow
      if (err.message?.includes('timeout') || err.message?.includes('Timeout')) {
        logger.warn('Month data request timeout - backend may be slow');
      } else {
        logger.error('Error fetching month data:', err);
      }
      return null;
    }
  }, [viewType]);

  useEffect(() => {
    isMountedRef.current = true;
    loadData();

    return () => {
      isMountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [loadData]);

  return { data, loading, error, refresh, getDayData, getMonthData };
};

