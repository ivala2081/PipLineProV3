/**
 * Transaction Type Definitions
 * Replaces 'any' types with proper interfaces
 */

export interface Transaction {
  id: number;
  client_name: string;
  company?: string;
  payment_method?: string;
  date: string; // ISO date string
  category: 'DEP' | 'WD';
  amount: number;
  commission?: number;
  net_amount: number;
  currency: string;
  psp?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: number;
  organization_id?: number;
  // Optional fields for foreign currency transactions
  amount_try?: number;
  commission_try?: number;
  net_amount_try?: number;
  exchange_rate?: number;
}

export interface TransactionCreateRequest {
  client_name: string;
  company?: string;
  payment_method?: string;
  date: string;
  category: 'DEP' | 'WD';
  amount: number | string;
  currency?: string;
  psp?: string;
  notes?: string;
  organization_id?: number;
}

export interface TransactionUpdateRequest {
  client_name?: string;
  company?: string;
  payment_method?: string;
  date?: string;
  category?: 'DEP' | 'WD';
  amount?: number | string;
  currency?: string;
  psp?: string;
  notes?: string;
}

export interface TransactionFilters {
  start_date?: string;
  end_date?: string;
  client_name?: string;
  category?: 'DEP' | 'WD';
  psp?: string;
  currency?: string;
  organization_id?: number;
  page?: number;
  per_page?: number;
}

export interface TransactionListResponse {
  transactions: Transaction[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
    has_prev: boolean;
    has_next: boolean;
  };
}

export interface TransactionStats {
  total_amount: number;
  deposit_amount: number;
  withdrawal_amount: number;
  transaction_count: number;
  period_days: number;
  start_date: string;
  end_date: string;
}

