/**
 * Dashboard API Service
 * Handles all dashboard-related API calls to the backend
 */

import { logger } from '../utils/logger';
import { apiClient } from '../utils/apiClient';

export interface DashboardStats {
  total_revenue: {
    value: string;
    change: string;
    changeType: 'positive' | 'negative';
  };
  total_transactions: {
    value: string;
    change: string;
    changeType: 'positive' | 'negative';
  };
  active_clients: {
    value: string;
    change: string;
    changeType: 'positive' | 'negative';
  };
  growth_rate: {
    value: string;
    change: string;
    changeType: 'positive' | 'negative';
  };
}

export interface RecentTransaction {
  id: number;
  client_name: string;
  amount: number;
  currency: string;
  date: string;
  status: string;
  created_at: string;
}

export interface DashboardSummary {
  total_revenue: number;
  total_commission: number;
  total_net: number;
  transaction_count: number;
  active_clients: number;
  growth_rate: number;
  net_cash?: number; // Net cash = Deposits - Withdrawals (TL)
}

export interface ChartData {
  daily_revenue: Array<{
    date: string;
    amount: number;
  }>;
  client_distribution: Array<{
    name: string;
    value: number;
  }>;
}

export interface ClientSegment {
  client_name: string;
  transaction_count: number;
  total_volume: number;
  avg_transaction: number;
  last_transaction: string;
  volume_percentage: number;
  segment: 'VIP' | 'Premium' | 'Regular' | 'Standard';
}

export interface ClientAnalytics {
  client_analytics: ClientSegment[];
  segment_distribution: {
    [key: string]: {
      count: number;
      volume: number;
      percentage: number;
    };
  };
  metrics: {
    total_clients: number;
    total_volume: number;
    avg_volume_per_client: number;
    top_client_volume: number;
  };
}

// Financial Performance Period Data (imported from types)
export interface FinancialPeriodData {
  total_bank_usd: number;
  total_bank_tl: number;
  total_cc_usd: number;
  total_cc_tl: number;
  total_tether_usd: number;
  total_tether_tl: number;
  conv_usd: number;
  conv_tl: number;
  total_transactions: number;
  bank_count: number;
  cc_count: number;
  tether_count: number;
  total_deposits_usd?: number;
  total_deposits_tl?: number;
  total_withdrawals_usd?: number;
  total_withdrawals_tl?: number;
  net_cash_usd?: number;
  net_cash_tl?: number;
}

export interface DashboardData {
  stats: DashboardStats;
  recent_transactions: RecentTransaction[];
  summary: DashboardSummary;
  chart_data: ChartData;
  exchange_rates?: {
    USD_TRY?: number;
    [key: string]: number | undefined;
  };
  financial_performance?: {
    annual?: FinancialPeriodData;
    monthly?: FinancialPeriodData;
    daily?: FinancialPeriodData;
  } | null;
}

export interface SystemPerformance {
  api_response_time: number;
  database_response_time: number;
  uptime_percentage: number;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  system_health: string;
}

export interface DataQuality {
  overall_quality_score: number;
  client_completeness: number;
  amount_completeness: number;
  date_completeness: number;
  potential_duplicates: number;
  total_records: number;
  data_freshness: string;
  validation_status: string;
}

export interface SecurityMetrics {
  failed_logins: {
    today: number;
    this_week: number;
    this_month: number;
    trend: string;
  };
  suspicious_activities: {
    total_alerts: number;
    high_priority: number;
    medium_priority: number;
    low_priority: number;
    last_alert: string;
  };
  session_management: {
    active_sessions: number;
    expired_sessions: number;
    average_session_duration: string;
  };
  access_patterns: {
    normal_access: number;
    unusual_access: number;
    last_analysis: string;
  };
  security_incidents: {
    total_incidents: number;
    resolved_incidents: number;
    open_incidents: number;
  };
}

class DashboardService {
  private baseUrl = '/api/v1';
  private cache = new Map<string, { data: any; timestamp: number }>();
  private readonly CACHE_DURATION = 30000; // 30 seconds cache
  private pendingRequests = new Map<string, Promise<any>>(); // Request deduplication

  /**
   * Check if cached data is still valid
   */
  private isCacheValid(key: string): boolean {
    const cached = this.cache.get(key);
    if (!cached) return false;
    return Date.now() - cached.timestamp < this.CACHE_DURATION;
  }

  /**
   * Get cached data or fetch new data with request deduplication
   * CRITICAL FIX: Added bypassCache parameter for initial load
   */
  private async getCachedOrFetch<T>(key: string, fetchFn: () => Promise<T>, bypassCache: boolean = false): Promise<T> {
    // CRITICAL FIX: İlk yüklemede cache bypass et
    if (!bypassCache && this.isCacheValid(key)) {
      logger.debug(`Using cached data for ${key}`);
      return this.cache.get(key)!.data;
    }

    // Check if there's already a pending request for this key
    if (this.pendingRequests.has(key)) {
      logger.debug(`Waiting for pending request for ${key}`);
      return this.pendingRequests.get(key)!;
    }

    logger.debug(`Fetching fresh data for ${key} ${bypassCache ? '(cache bypassed)' : ''}`);
    const requestPromise = fetchFn().then(data => {
      this.cache.set(key, { data, timestamp: Date.now() });
      this.pendingRequests.delete(key);
      return data;
    }).catch(error => {
      this.pendingRequests.delete(key);
      throw error;
    });

    this.pendingRequests.set(key, requestPromise);
    return requestPromise;
  }

  /**
   * Clear cache for specific key or all cache
   */
  clearCache(key?: string): void {
    if (key) {
      this.cache.delete(key);
      this.pendingRequests.delete(key);
      logger.debug(`Cleared cache for ${key}`);
    } else {
      this.cache.clear();
      this.pendingRequests.clear();
      logger.debug(`Cleared all cache and pending requests`);
    }
  }

  /**
   * Get dashboard statistics
   */
  async getDashboardStats(timeRange: string = 'all'): Promise<DashboardData> {
    const cacheKey = `dashboard-stats-${timeRange}`;
    return this.getCachedOrFetch(cacheKey, async () => {
      const response = await apiClient.get<DashboardData>(`/dashboard/consolidated?range=${timeRange}`, {
        timeout: 10000,
        retries: 2,
      });
      return response.data;
    });
  }

  /**
   * Get system performance metrics
   */
  async getSystemPerformance(): Promise<SystemPerformance> {
    const response = await apiClient.get<SystemPerformance>('/analytics/system/performance', {
      timeout: 10000,
      retries: 2,
    });
    return response.data;
  }

  /**
   * Get data quality metrics
   */
  async getDataQuality(): Promise<DataQuality> {
    const response = await apiClient.get<DataQuality>('/analytics/data/quality', {
      timeout: 10000,
      retries: 2,
    });
    return response.data;
  }

  /**
   * Get security metrics
   */
  async getSecurityMetrics(): Promise<SecurityMetrics> {
    const response = await apiClient.get<SecurityMetrics>('/analytics/security/metrics', {
      timeout: 10000,
      retries: 2,
    });
    return response.data;
  }

  /**
   * Get consolidated dashboard data (all metrics in one call) - OPTIMIZED
   */
  /**
   * Get consolidated dashboard data
   * CRITICAL FIX: Added bypassCache parameter to force fresh data on initial load
   */
  async getConsolidatedDashboard(timeRange: string = 'all', bypassCache: boolean = false): Promise<any> {
    const cacheKey = `consolidated-dashboard-${timeRange}`;
    return this.getCachedOrFetch(
      cacheKey,
      async () => {
        const cacheBuster = bypassCache ? `&_t=${Date.now()}` : '';
        const response = await apiClient.get<any>(`/dashboard/consolidated?range=${timeRange}${cacheBuster}`, {
          timeout: 15000,
          retries: 3,
        });
        
        const data = response.data;
        
        // Debug: Log response structure
        if (import.meta.env.DEV) {
          logger.debug('Consolidated dashboard response', {
            hasStats: !!data?.stats,
            hasChartData: !!data?.chart_data,
            hasFinancialPerformance: !!data?.financial_performance,
            chartDataLength: data?.chart_data?.daily_revenue?.length || 0,
          });
        }
        
        // Validate response structure
        if (!data) {
          throw new Error('Empty response from consolidated dashboard endpoint');
        }
        
        return data;
      },
      bypassCache,
    );
  }

  /**
   * Get revenue trends
   */
  async getRevenueTrends(timeRange: string = 'all'): Promise<any> {
    const response = await apiClient.get<any>(`/analytics/revenue/trends?range=${timeRange}`, {
      timeout: 10000,
      retries: 2,
    });
    return response.data;
  }

  /**
   * Get top performers
   */
  async getTopPerformers(timeRange: string = 'all'): Promise<any> {
    const response = await apiClient.get<any>(`/analytics/top-performers?range=${timeRange}`, {
      timeout: 10000,
      retries: 2,
    });
    return response.data;
  }

/**
   * Get commission analytics
   */
  async getCommissionAnalytics(timeRange: string = 'all'): Promise<any> {
    const cacheKey = `commission-analytics-${timeRange}`;
    return this.getCachedOrFetch(cacheKey, async () => {
      const response = await apiClient.get<any>(`/analytics/commission/analytics?range=${timeRange}`, {
        timeout: 10000,
        retries: 2,
      });
      return response.data;
    });
  }

  /**
   * Get current exchange rates
   */
  async getExchangeRates(): Promise<any> {
    const cacheKey = 'exchange-rates';
    return this.getCachedOrFetch(cacheKey, async () => {
      const response = await apiClient.get<any>('/exchange-rates/rates', {
        timeout: 10000,
        retries: 2,
      });
      return response.data;
    });
  }

  /**
   * Get transaction volume analysis
   */
  async getTransactionVolumeAnalysis(timeRange: string = 'all'): Promise<any> {
    const response = await apiClient.get<any>(`/analytics/transactions/volume-analysis?range=${timeRange}`, {
      timeout: 10000,
      retries: 2,
    });
    return response.data;
  }

  /**
   * Get client analytics and segmentation
   */
  async getClientAnalytics(timeRange: string = 'all'): Promise<ClientAnalytics> {
    const response = await apiClient.get<{ data: ClientAnalytics }>(`/analytics/clients/analytics?range=${timeRange}`, {
      timeout: 10000,
      retries: 2,
    });
    return response.data.data;
  }

  /**
   * Get PSP rollover summary
   */
  async getPspRolloverSummary(): Promise<any> {
    const response = await apiClient.get<any>('/analytics/psp-rollover-summary', {
      timeout: 10000,
      retries: 2,
    });
    return response.data;
  }

  /**
   * Get financial performance data with retry mechanism
   * CRITICAL FIX: Increased timeout and improved retry logic for initial load
   */
  async getFinancialPerformance(timeRange: string = 'all', view: 'gross' | 'net' = 'net'): Promise<any> {
    const cacheKey = `financial-performance-${timeRange}-${view}`;
    return this.getCachedOrFetch(cacheKey, async () => {
      try {
        const response = await apiClient.get<any>(`/financial-performance?range=${timeRange}&view=${view}`, {
          timeout: 60000, // 60 seconds - backend might be slow with large datasets
          retries: 2, // Reduce retries
        });

        const data = response.data;

        // Response alındı - production'da log yok

        // Check if response is empty or invalid
        if (!data) {
          throw new Error('Empty response from backend');
        }

        // Validate that we got actual data structure (even if values are 0)
        if (data && data.data && (data.data.daily || data.data.monthly || data.data.annual)) {
          return data;
        } else {
          throw new Error('Invalid data structure in response');
        }
      } catch (error: any) {
        // Sadece ciddi hatalari log et
        if (!error.message?.includes('timeout') && !error.message?.includes('Timeout')) {
          logger.error('Error loading financial performance:', error);
        }
        throw error;
      }
    });
  }

  /**
   * Refresh dashboard data
   */
  async refreshDashboard(timeRange: string = 'all'): Promise<DashboardData> {
    // Clear cached data and fetch fresh
    this.clearCache();
    return this.getDashboardStats(timeRange);
  }
}

// Export singleton instance
export const dashboardService = new DashboardService();
export default dashboardService;
