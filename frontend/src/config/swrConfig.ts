import { SWRConfiguration } from 'swr';
import { isDevelopment } from './environment';

// SWR configuration for data fetching and caching - PERFORMANCE OPTIMIZED
export const swrConfig: SWRConfiguration = {
  // Revalidate data every 30 minutes (increased from 15 minutes)
  refreshInterval: 30 * 60 * 1000,
  // Keep data in cache for 60 minutes (increased from 30 minutes)
  dedupingInterval: 60 * 60 * 1000,
  // Retry failed requests only once (reduced from 2)
  errorRetryCount: 1,
  // Retry delay with exponential backoff
  errorRetryInterval: 5000,
  // Disable focus revalidation to reduce unnecessary requests
  revalidateOnFocus: false,
  // Disable reconnect revalidation to reduce requests
  revalidateOnReconnect: false,
  // Only revalidate on mount if data is very stale
  revalidateOnMount: false,
  // Optimized compare function
  compare: (a, b) => JSON.stringify(a) === JSON.stringify(b),
  // Add stale-while-revalidate behavior
  revalidateIfStale: false,
  // Increase loading timeout
  loadingTimeout: 15000,
};

// Query keys factory for consistent key management
// Use relative paths (without /api/v1 prefix) since api client already has baseUrl
export const queryKeys = {
  // Dashboard queries
  dashboard: {
    stats: (range: string = 'all') => `/analytics/dashboard/stats?range=${range}`,
    topPerformers: (range: string = 'all') => `/analytics/top-performers?range=${range}`,
    revenueTrends: (range: string = 'all') => `/analytics/revenue/trends?range=${range}`,
  },
  
  // Analytics queries
  analytics: {
    clients: (range: string) => `/analytics/clients/analytics?range=${range}`,
    commission: (range: string) => `/analytics/commission/analytics?range=${range}`,
    volumeAnalysis: (range: string) => `/analytics/transactions/volume-analysis?range=${range}`,
    systemPerformance: () => '/analytics/system/performance',
    dataQuality: () => '/analytics/data/quality',
    integrationStatus: () => '/analytics/integration/status',
    securityMetrics: () => '/analytics/security/metrics',
    ledgerData: (days: number) => `/analytics/ledger-data?days=${days}`,
  },
  
  // Transaction queries
  transactions: {
    all: (params?: any) => `/transactions?${new URLSearchParams(params)}`,
    clients: () => '/transactions/clients',
    dropdownOptions: () => '/transactions/dropdown-options',
    pspSummaryStats: () => '/transactions/psp_summary_stats',
  },
  
  // User queries
  users: {
    settings: () => '/users/settings',
    profile: () => '/users/profile',
  },
  
  // Auth queries
  auth: {
    check: () => '/auth/check',
    csrfToken: () => '/auth/csrf-token',
  },
  
  // Exchange rates queries
  exchangeRates: {
    all: () => '/exchange-rates/rates',
    refresh: () => '/exchange-rates/refresh',
  },
} as const;

// Fetcher function for SWR - uses api client to avoid double /api/v1
export const fetcher = async (url: string) => {
  // Import api client dynamically to avoid circular dependencies
  const { api } = await import('../utils/apiClient');
  const response = await api.get(url);
  return response.data;
};

export default swrConfig;
