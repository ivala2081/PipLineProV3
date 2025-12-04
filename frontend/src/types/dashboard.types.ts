/**
 * Dashboard Type Definitions
 * Tüm dashboard ile ilgili type'lar burada tanımlanır
 */

// Financial Performance Types
export interface FinancialPerformanceData {
  daily: FinancialPeriodData;
  monthly: FinancialPeriodData;
  annual: FinancialPeriodData;
  exchange_rate: number;
}

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

export interface FinancialPerformanceResponse {
  success: boolean;
  data: FinancialPerformanceData;
}

// Commission Analytics Types
export interface CommissionAnalytics {
  data: {
    total_commission: number;
    average_rate: number;
    top_psp: string | null;
  };
}

// Exchange Rates Types
export interface ExchangeRates {
  data: {
    USD_TRY?: number;
    [key: string]: number | undefined;
  };
}

// Dashboard State Types
export interface DashboardLoadingState {
  main: boolean;
  day: boolean;
  month: boolean;
  report: boolean;
  refreshing: boolean;
}

export interface DashboardState {
  data: DashboardData | null;
  financialPerformance: FinancialPerformanceResponse | null;
  commissionAnalytics: CommissionAnalytics | null;
  exchangeRates: ExchangeRates | null;
  selectedDay: Date;
  selectedMonth: Date;
  loading: DashboardLoadingState;
  error: string | null;
  lastUpdated: Date | null;
}

// Re-export from dashboardService
export type {
  DashboardData,
  DashboardStats,
  DashboardSummary,
  ChartData,
  RecentTransaction,
} from '../services/dashboardService';

// Financial Performance Breakdown Types
export interface FinancialBreakdownItem {
  timePeriod: 'Daily' | 'Monthly' | 'Total';
  metric: string;
  amount: number;
  usdAmount: number;
  tlAmount: number;
  count: number;
  trend: number;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  color: string;
  bgColor: string;
  iconColor: string;
  trendColor: string;
}

// Quick Stats Types
export interface QuickStat {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  change?: string;
  trend: 'up' | 'down';
}

// Chart Period Types
export type ChartPeriod = 'daily' | 'monthly' | 'annual';
export type ViewType = 'gross' | 'net';
export type TimeRange = 'all' | '7d' | '30d' | '90d' | '6m' | '1y';

