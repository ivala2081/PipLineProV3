/**
 * TypeScript type definitions for API responses
 * Standardized API response format: { data, error, meta }
 */

// Standard API response envelope
export interface ApiResponse<T = any> {
  data?: T;
  error?: ApiError;
  meta?: ApiMeta;
}

// Error response structure
export interface ApiError {
  code: string;
  message: string;
  status_code?: number;
  timestamp?: string;
  request_id?: string;
  details?: Record<string, any>;
  context?: Record<string, any>;
  technical_message?: string;
  retryable?: boolean;
}

// Metadata structure
export interface ApiMeta {
  message?: string;
  timestamp?: string;
  pagination?: PaginationMeta;
  [key: string]: any;
}

// Pagination metadata
export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_prev: boolean;
  has_next: boolean;
  prev_page?: number | null;
  next_page?: number | null;
}

// Transaction types
export interface Transaction {
  id: number;
  client_name: string;
  amount: number;
  amount_tl?: number;
  currency: 'TL' | 'USD' | 'EUR';
  category: 'WD' | 'DEP';
  date: string;
  payment_method?: string;
  psp?: string;
  company?: string;
  description?: string;
  notes?: string;
  commission?: number;
  commission_rate?: number;
  net_amount?: number;
  net_amount_try?: number;
  eur_rate?: number;
  usd_rate?: number;
  created_at: string;
  updated_at?: string;
  status?: string;
}

// Dashboard stats
export interface DashboardStats {
  total_revenue: StatValue;
  total_transactions: StatValue;
  active_clients: StatValue;
  growth_rate: StatValue;
  net_cash: StatValue;
}

export interface StatValue {
  value: string;
  change: string;
  changeType: 'positive' | 'negative';
}

// Revenue trend
export interface RevenueTrend {
  date: string;
  amount: number;
}

// Dashboard response
export interface DashboardResponse {
  stats: DashboardStats;
  summary: {
    total_revenue: number;
    total_commission: number;
    total_net: number;
    total_net_amount: number;
    net_cash: number;
    total_deposits: number;
    total_withdrawals: number;
    transaction_count: number;
    active_clients: number;
    daily_revenue: number;
    weekly_revenue: number;
    monthly_revenue: number;
    annual_revenue: number;
    daily_revenue_trend: number;
    weekly_revenue_trend: number;
    monthly_revenue_trend: number;
    annual_revenue_trend: number;
  };
  recent_transactions: Transaction[];
  chart_data: {
    daily_revenue: RevenueTrend[];
  };
  revenue_trends: RevenueTrend[];
}

// User types
export interface User {
  id: number;
  username: string;
  email?: string;
  role: 'admin' | 'user' | 'viewer';
  admin_level?: number;
  is_active: boolean;
  created_at: string;
}

// Exchange rate types
export interface ExchangeRate {
  id: number;
  currency: string;
  rate: number;
  date: string;
  source?: string;
  is_manual?: boolean;
  created_at: string;
  updated_at: string;
}

// Dropdown option types
export interface DropdownOption {
  id: number;
  field_name: string;
  value: string;
  commission_rate?: number;
  is_active: boolean;
  created_at?: string;
}

// Paginated response
export interface PaginatedResponse<T> {
  data: T[];
  error: null;
  meta: {
    pagination: PaginationMeta;
    [key: string]: any;
  };
}

