/**
 * Shared types for Clients page components
 */

export interface Client {
  client_name: string;
  company_name?: string;
  payment_method?: string;
  category?: string;
  total_amount: number;
  total_commission: number;
  total_net: number;
  transaction_count: number;
  first_transaction: string;
  last_transaction: string;
  currencies: string[];
  psps: string[];
  avg_transaction: number;
}

export interface Transaction {
  id: number;
  client_name: string;
  company?: string;
  iban?: string;
  payment_method?: string;
  category: string;
  amount: number;
  commission: number;
  net_amount: number;
  currency?: string;
  psp?: string;
  notes?: string;
  date?: string;
  created_at?: string;
  updated_at?: string;
  amount_tl?: number;
  commission_tl?: number;
  net_amount_tl?: number;
  exchange_rate?: number;
}

export interface ClientsResponse {
  clients: Client[];
  total_clients: number;
}

export interface DailySummary {
  date: string;
  date_str: string;
  usd_rate: number | null;
  total_amount_tl: number;
  total_amount_usd: number;
  total_commission_tl: number;
  total_commission_usd: number;
  total_net_tl: number;
  total_net_usd: number;
  gross_balance_tl?: number;
  gross_balance_usd?: number;
  total_deposits_tl?: number;
  total_deposits_usd?: number;
  total_withdrawals_tl?: number;
  total_withdrawals_usd?: number;
  transaction_count: number;
  unique_clients: number;
  payment_method_totals?: {
    BANK?: {
      amount_tl: number;
      amount_usd: number;
      count: number;
    };
    CC?: {
      amount_tl: number;
      amount_usd: number;
      count: number;
    };
    TETHER?: {
      amount_tl: number;
      amount_usd: number;
      count: number;
    };
  };
  psp_summary: Array<{
    name: string;
    gross_tl?: number;
    gross_usd?: number;
    amount_tl: number;
    amount_usd: number;
    commission_tl: number;
    commission_usd: number;
    net_tl: number;
    net_usd: number;
    count: number;
    is_tether: boolean;
    primary_currency: 'USD' | 'TRY';
  }>;
  category_summary: Array<{
    name: string;
    amount_tl: number;
    amount_usd: number;
    commission_tl: number;
    commission_usd: number;
    net_tl: number;
    net_usd: number;
    count: number;
  }>;
  payment_method_summary: Array<{
    name: string;
    gross_tl?: number;
    gross_usd?: number;
    amount_tl?: number;
    amount_usd?: number;
    net_amount_tl?: number;
    net_amount_usd?: number;
    commission_tl: number;
    commission_usd: number;
    net_tl: number;
    net_usd: number;
    count: number;
  }>;
  transactions: Array<{
    id: number;
    client_name: string;
    company?: string;
    payment_method?: string;
    category: string;
    amount: number;
    commission: number;
    net_amount: number;
    currency: string;
    psp?: string;
    notes?: string;
    date: string;
    created_at?: string;
    updated_at?: string;
    amount_tl?: number;
    commission_tl?: number;
    net_amount_tl?: number;
    exchange_rate?: number;
  }>;
}

export interface FilterState {
  search: string;
  category: string;
  paymentMethod: string;
  psp: string;
  company: string;
  dateFrom: string;
  dateTo: string;
  minAmount: string;
  maxAmount: string;
  currency: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

export interface DropdownOptions {
  categories: string[];
  payment_methods: string[];
  psps: string[];
  companies: string[];
  currencies: string[];
}

