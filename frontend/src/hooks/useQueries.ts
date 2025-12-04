import useSWR, { mutate } from 'swr';
import { queryKeys, fetcher } from '../config/swrConfig';

// Dashboard hooks
export const useDashboardStats = (range: string = '7d') => {
  return useSWR(queryKeys.dashboard.stats(range), fetcher, {
    refreshInterval: 2 * 60 * 1000, // 2 minutes for dashboard data
  });
};

export const useTopPerformers = (range: string = '7d') => {
  return useSWR(queryKeys.dashboard.topPerformers(range), fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 minutes for top performers
  });
};

export const useRevenueTrends = (range: string = '7d') => {
  return useSWR(queryKeys.dashboard.revenueTrends(range), fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 minutes for revenue trends
  });
};

// Analytics hooks
export const useClientsAnalytics = (range: string = 'all') => {
  return useSWR(queryKeys.analytics.clients(range), fetcher, {
    refreshInterval: 10 * 60 * 1000, // 10 minutes for client analytics
  });
};

export const useCommissionAnalytics = (range: string = 'all') => {
  return useSWR(queryKeys.analytics.commission(range), fetcher, {
    refreshInterval: 10 * 60 * 1000, // 10 minutes for commission analytics
  });
};

export const useVolumeAnalysis = (range: string = 'all') => {
  return useSWR(queryKeys.analytics.volumeAnalysis(range), fetcher, {
    refreshInterval: 10 * 60 * 1000, // 10 minutes for volume analysis
  });
};

export const useSystemPerformance = () => {
  return useSWR(queryKeys.analytics.systemPerformance(), fetcher, {
    refreshInterval: 30 * 1000, // 30 seconds for system performance
  });
};

export const useDataQuality = () => {
  return useSWR(queryKeys.analytics.dataQuality(), fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 minutes for data quality
  });
};

export const useIntegrationStatus = () => {
  return useSWR(queryKeys.analytics.integrationStatus(), fetcher, {
    refreshInterval: 2 * 60 * 1000, // 2 minutes for integration status
  });
};

export const useSecurityMetrics = () => {
  return useSWR(queryKeys.analytics.securityMetrics(), fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 minutes for security metrics
  });
};

export const useLedgerData = (days: number = 30) => {
  return useSWR(queryKeys.analytics.ledgerData(days), fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 minutes for ledger data
  });
};

// Transaction hooks
export const useTransactions = (params?: any) => {
  return useSWR(params ? queryKeys.transactions.all(params) : null, fetcher, {
    refreshInterval: 2 * 60 * 1000, // 2 minutes for transactions
  });
};

export const useTransactionClients = () => {
  return useSWR(queryKeys.transactions.clients(), fetcher, {
    refreshInterval: 10 * 60 * 1000, // 10 minutes for client list
  });
};

export const useTransactionDropdownOptions = () => {
  return useSWR(queryKeys.transactions.dropdownOptions(), fetcher, {
    refreshInterval: 30 * 60 * 1000, // 30 minutes for dropdown options
  });
};

export const usePSPSummaryStats = () => {
  return useSWR(queryKeys.transactions.pspSummaryStats(), fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 minutes for PSP stats
  });
};

// User hooks
export const useUserSettings = () => {
  return useSWR(queryKeys.users.settings(), fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 minutes for user settings
  });
};

// Auth hooks
export const useAuthCheck = () => {
  return useSWR(queryKeys.auth.check(), fetcher, {
    refreshInterval: 1 * 60 * 1000, // 1 minute for auth check
    errorRetryCount: 0, // Don't retry auth failures
  });
};

// Exchange rates hooks
export const useExchangeRates = () => {
  return useSWR(queryKeys.exchangeRates.all(), fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 minutes for exchange rates
  });
};

// Mutation functions
export const refreshExchangeRates = async () => {
  const response = await fetch(queryKeys.exchangeRates.refresh(), {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  // Invalidate and refetch exchange rates
  await mutate(queryKeys.exchangeRates.all());
  
  return response.json();
};

export const updateUserSettings = async (settings: any) => {
  const response = await fetch(queryKeys.users.settings(), {
    method: 'PUT',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(settings),
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  // Invalidate and refetch user settings
  await mutate(queryKeys.users.settings());
  
  return response.json();
};

// Utility function for optimistic updates
export const optimisticUpdate = <T>(
  key: string,
  updateFn: (oldData: T | undefined) => T
) => {
  return (newData: T) => {
    mutate(key, updateFn, false);
  };
};

export default {
  // Dashboard
  useDashboardStats,
  useTopPerformers,
  useRevenueTrends,
  
  // Analytics
  useClientsAnalytics,
  useCommissionAnalytics,
  useVolumeAnalysis,
  useSystemPerformance,
  useDataQuality,
  useIntegrationStatus,
  useSecurityMetrics,
  useLedgerData,
  
  // Transactions
  useTransactions,
  useTransactionClients,
  useTransactionDropdownOptions,
  usePSPSummaryStats,
  
  // Users
  useUserSettings,
  
  // Auth
  useAuthCheck,
  
  // Exchange Rates
  useExchangeRates,
  
  // Mutations
  refreshExchangeRates,
  updateUserSettings,
  optimisticUpdate,
};
