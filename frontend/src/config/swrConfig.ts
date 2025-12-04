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
export const queryKeys = {
  // Dashboard queries
  dashboard: {
    stats: (range: string = 'all') => `/api/v1/analytics/dashboard/stats?range=${range}`,
    topPerformers: (range: string = 'all') => `/api/v1/analytics/top-performers?range=${range}`,
    revenueTrends: (range: string = 'all') => `/api/v1/analytics/revenue/trends?range=${range}`,
  },
  
  // Analytics queries
  analytics: {
    clients: (range: string) => `/api/v1/analytics/clients/analytics?range=${range}`,
    commission: (range: string) => `/api/v1/analytics/commission/analytics?range=${range}`,
    volumeAnalysis: (range: string) => `/api/v1/analytics/transactions/volume-analysis?range=${range}`,
    systemPerformance: () => '/api/v1/analytics/system/performance',
    dataQuality: () => '/api/v1/analytics/data/quality',
    integrationStatus: () => '/api/v1/analytics/integration/status',
    securityMetrics: () => '/api/v1/analytics/security/metrics',
    ledgerData: (days: number) => `/api/v1/analytics/ledger-data?days=${days}`,
  },
  
  // Transaction queries
  transactions: {
    all: (params?: any) => `/api/v1/transactions?${new URLSearchParams(params)}`,
    clients: () => '/api/v1/transactions/clients',
    dropdownOptions: () => '/api/v1/transactions/dropdown-options',
    pspSummaryStats: () => '/api/v1/transactions/psp_summary_stats',
  },
  
  // User queries
  users: {
    settings: () => '/api/v1/users/settings',
    profile: () => '/api/v1/users/profile',
  },
  
  // Auth queries
  auth: {
    check: () => '/api/v1/auth/check',
    csrfToken: () => '/api/v1/auth/csrf-token',
  },
  
  // Exchange rates queries
  exchangeRates: {
    all: () => '/api/exchange-rates',
    refresh: () => '/api/exchange-rates/refresh',
  },
} as const;

// Fetcher function for SWR
export const fetcher = async (url: string) => {
  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
};

export default swrConfig;
