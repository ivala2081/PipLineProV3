/**
 * Custom Hook: useDashboardData
 * Dashboard verilerini yönetir ve API çağrılarını handle eder
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardService } from '../services/dashboardService';
import { logger } from '../utils/logger';
import type { DashboardData, TimeRange, ViewType } from '../types/dashboard.types';

interface UseDashboardDataOptions {
  timeRange: TimeRange;
  viewType: ViewType;
  enabled?: boolean;
}

interface UseDashboardDataReturn {
  data: DashboardData | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  lastUpdated: Date | null;
}

export const useDashboardData = ({
  timeRange,
  viewType,
  enabled = true,
}: UseDashboardDataOptions): UseDashboardDataReturn => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  const loadData = useCallback(async () => {
    if (!enabled) return;

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setLoading(true);
    setError(null);

    try {
      logger.dashboard('Loading dashboard data', { timeRange, viewType });

      const result = await dashboardService.getConsolidatedDashboard(timeRange, true);

      if (!isMountedRef.current || abortControllerRef.current.signal.aborted) {
        return;
      }

      // Parse and set data
      const safeParseFloat = (value: any, defaultValue: number = 0): number => {
        if (!value) return defaultValue;
        const str = String(value).replace(/[₺,%,]/g, '');
        const parsed = parseFloat(str);
        return isNaN(parsed) ? defaultValue : parsed;
      };

      const safeParseInt = (value: any, defaultValue: number = 0): number => {
        if (!value) return defaultValue;
        const str = String(value).replace(/[,]/g, '');
        const parsed = parseInt(str);
        return isNaN(parsed) ? defaultValue : parsed;
      };

      // Chart data kontrolü ve düzeltmesi
      let chartData = result?.chart_data || { daily_revenue: [], client_distribution: [] };
      if (!chartData.daily_revenue || !Array.isArray(chartData.daily_revenue)) {
        chartData = { ...chartData, daily_revenue: [] };
      }

      const dashboardStats: DashboardData = {
        stats: result?.stats || {
          total_revenue: { value: '0', change: '0%', changeType: 'positive' },
          total_transactions: { value: '0', change: '0%', changeType: 'positive' },
          active_clients: { value: '0', change: '0%', changeType: 'positive' },
          growth_rate: { value: '0%', change: '0%', changeType: 'positive' },
        },
        chart_data: chartData,
        recent_transactions: result?.recent_transactions || [],
        summary: {
          total_revenue: safeParseFloat(result?.stats?.total_revenue?.value),
          total_commission: result?.commission_analytics?.total_commission || 0,
          total_net:
            safeParseFloat(result?.stats?.total_revenue?.value) -
            (result?.commission_analytics?.total_commission || 0),
          transaction_count: safeParseInt(result?.stats?.total_transactions?.value),
          active_clients: safeParseInt(result?.stats?.active_clients?.value),
          growth_rate: safeParseFloat(result?.stats?.growth_rate?.value),
          // CRITICAL FIX: Net cash verisini summary'den al (en guvenilir kaynak)
          // summary.net_cash backend'de deposits - withdrawals olarak hesaplanir
          net_cash: (() => {
            const summaryNetCash = result?.summary?.net_cash;
            if (summaryNetCash !== undefined && summaryNetCash !== null) {
              const parsed = typeof summaryNetCash === 'number' ? summaryNetCash : parseFloat(String(summaryNetCash));
              return !isNaN(parsed) ? parsed : 0;
            }
            const financialPerfNetCash = result?.financial_performance?.annual?.net_cash_tl;
            if (financialPerfNetCash !== undefined && financialPerfNetCash !== null) {
              const parsed = typeof financialPerfNetCash === 'number' ? financialPerfNetCash : parseFloat(String(financialPerfNetCash));
              return !isNaN(parsed) ? parsed : 0;
            }
            return 0;
          })(),
        },
        // CRITICAL FIX: exchange_rates ve financial_performance verilerini ekle
        exchange_rates: result?.exchange_rates || { USD_TRY: 48.0 },
        financial_performance: result?.financial_performance || null,
      };

      // Debug: Log financial performance data in DETAILED format

      setData(dashboardStats);
      setLastUpdated(new Date());
      logger.dashboard('Dashboard data loaded successfully');
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
              : 'Dashboard verisi yüklenemedi. Lütfen tekrar deneyin.';

      logger.error('Error loading dashboard data:', err);
      setError(errorMessage);

      // Set fallback data
      setData({
        stats: {
          total_revenue: { value: '0', change: '0%', changeType: 'positive' },
          total_transactions: { value: '0', change: '0%', changeType: 'positive' },
          active_clients: { value: '0', change: '0%', changeType: 'positive' },
          growth_rate: { value: '0%', change: '0%', changeType: 'positive' },
        },
        chart_data: { daily_revenue: [], client_distribution: [] },
        recent_transactions: [],
        summary: {
          total_revenue: 0,
          total_commission: 0,
          total_net: 0,
          transaction_count: 0,
          active_clients: 0,
          growth_rate: 0,
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

  return { data, loading, error, refresh, lastUpdated };
};

