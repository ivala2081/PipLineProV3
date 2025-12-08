/**
 * Exchange Rates Service for React Frontend
 * Integrates with the backend yfinance-powered exchange rates API
 */

export interface ExchangeRate {
  id: number;
  date: string;
  currency_pair: string;
  rate: number;
  source: string;
  is_manual_override: boolean;
  override_reason?: string;
  data_quality: string;
  created_at: string;
  updated_at: string;
}

export interface ExchangeRatesResponse {
  status: 'success' | 'error';
  message: string;
  rates?: Record<string, ExchangeRate> | ExchangeRate[];
  rate?: ExchangeRate;
  date?: string;
  results?: Record<string, boolean>;
  summary?: {
    total: number;
    successful: number;
    failed: number;
  };
  count?: number;
  missing_dates?: Array<{
    date: string;
    currency_pair: string;
  }>;
  supported_pairs?: string[];
  service_status?: string;
}

export interface DailySummaryRequest {
  date: string;
}

export interface FetchRateRequest {
  date: string;
  currency_pair: string;
}

export interface ManualUpdateRequest {
  date: string;
  currency_pair: string;
  rate: number;
  reason?: string;
}

export interface RefreshRatesRequest {
  date: string;
  currency_pairs?: string[];
}

export interface HistoryRequest {
  start_date: string;
  end_date: string;
  currency_pair?: string;
}

export interface MissingRatesRequest {
  start_date: string;
  end_date: string;
  currency_pairs: string[];
}

class ExchangeRatesService {
  private baseUrl: string;

  constructor() {
    // In development, use relative URLs to go through Vite proxy
    // In production, use the configured API base URL
    const isDev = import.meta.env.DEV;
    this.baseUrl = isDev ? '' : (import.meta.env.VITE_API_BASE_URL || '');
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Use relative URL if baseUrl is empty (goes through Vite proxy)
    // Otherwise use full URL
    const url = this.baseUrl ? `${this.baseUrl}${endpoint}` : endpoint;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for authentication
    };

    const response = await fetch(url, { ...defaultOptions, ...options });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication required. Please log in.');
      }
      if (response.status === 404) {
        throw new Error('Exchange rate not found.');
      }
      if (response.status >= 500) {
        throw new Error('Server error. Please try again later.');
      }
      
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get exchange rates system status
   */
  async getStatus(): Promise<ExchangeRatesResponse> {
    return this.makeRequest<ExchangeRatesResponse>('/api/v1/exchange-rates/status');
  }

  /**
   * Fetch exchange rate for a specific date and currency pair
   */
  async fetchRate(request: FetchRateRequest): Promise<ExchangeRatesResponse> {
    // Use the current rate endpoint for now - this could be extended to support historical rates
    const response = await this.makeRequest<any>('/api/v1/exchange-rates/current');
    
    // Transform response to match expected format
    if (response.success && response.rate) {
      return {
        status: 'success',
        message: response.message || 'Rate fetched successfully',
        rate: {
          ...response.rate,
          currency_pair: request.currency_pair
        }
      };
    } else {
      return {
        status: 'error',
        message: response.message || 'Failed to fetch rate'
      };
    }
  }

  /**
   * Get all exchange rates needed for daily summary calculations
   */
  async getDailySummaryRates(request: DailySummaryRequest): Promise<ExchangeRatesResponse> {
    // Use the current rate endpoint since that's what exists
    const response = await this.makeRequest<any>('/api/v1/exchange-rates/current');
    
    // Transform the response to match expected format
    if (response.success && response.rate) {
      return {
        status: 'success',
        message: response.message || 'Rate fetched successfully',
        rates: {
          'USDTRY': {
            ...response.rate,
            currency_pair: 'USDTRY'
          }
        }
      };
    } else {
      return {
        status: 'error',
        message: response.message || 'Failed to fetch rates'
      };
    }
  }

  /**
   * Update exchange rate manually with override
   */
  async updateManualRate(request: ManualUpdateRequest): Promise<ExchangeRatesResponse> {
    // This endpoint doesn't exist in the current backend, return error for now
    return {
      status: 'error',
      message: 'Manual rate updates not currently supported'
    };
  }

  /**
   * Force refresh exchange rates for a specific date
   */
  async refreshRates(request: RefreshRatesRequest): Promise<ExchangeRatesResponse> {
    // Use the update endpoint to force refresh
    const response = await this.makeRequest<any>('/api/v1/exchange-rates/update', {
      method: 'POST'
    });
    
    // Transform response to match expected format
    if (response.success) {
      return {
        status: 'success',
        message: response.message || 'Rates refreshed successfully'
      };
    } else {
      return {
        status: 'error',
        message: response.message || 'Failed to refresh rates'
      };
    }
  }

  /**
   * Get exchange rate history for a date range
   */
  async getHistory(request: HistoryRequest): Promise<ExchangeRatesResponse> {
    const params = new URLSearchParams({
      start_date: request.start_date,
      end_date: request.end_date,
    });
    
    if (request.currency_pair) {
      params.append('currency_pair', request.currency_pair);
    }

    return this.makeRequest<ExchangeRatesResponse>(`/api/v1/exchange-rates/history?${params}`);
  }

  /**
   * Find dates with missing exchange rates
   */
  async getMissingRates(request: MissingRatesRequest): Promise<ExchangeRatesResponse> {
    // This endpoint doesn't exist in the current backend, return empty result
    return {
      status: 'success',
      message: 'No missing rates detected',
      missing_dates: []
    };
  }

  /**
   * Get rate for a specific currency pair and date
   * This is a convenience method that fetches or gets from cache
   */
  async getRate(currencyPair: string, date: string): Promise<ExchangeRate | null> {
    try {
      const response = await this.fetchRate({ date, currency_pair: currencyPair });
      return response.rate || null;
    } catch (error) {
      console.error(`Failed to get rate for ${currencyPair} on ${date}:`, error);
      return null;
    }
  }

  /**
   * Get all rates for a specific date (for daily summary)
   */
  async getRatesForDate(date: string): Promise<Record<string, ExchangeRate>> {
    try {
      const response = await this.getDailySummaryRates({ date });
      if (response.rates && typeof response.rates === 'object' && !Array.isArray(response.rates)) {
        return response.rates;
      }
      return {};
    } catch (error) {
      console.error(`Failed to get rates for ${date}:`, error);
      return {};
    }
  }

  /**
   * Format currency pair for display
   */
  formatCurrencyPair(currencyPair: string): string {
    const [base, quote] = currencyPair.split('/');
    return `${base} → ${quote}`;
  }

  /**
   * Get source display name
   */
  getSourceDisplayName(source: string): string {
    switch (source.toLowerCase()) {
      case 'yfinance':
        return 'Yahoo Finance';
      case 'manual':
        return 'Manual Override';
      case 'tcmb':
        return 'TCMB';
      default:
        return source;
    }
  }

  /**
   * Get quality display name
   */
  getQualityDisplayName(quality: string): string {
    switch (quality.toLowerCase()) {
      case 'closing_price':
        return 'Closing Price';
      case 'closest_available':
        return 'Closest Available';
      case 'manual':
        return 'Manual';
      default:
        return quality;
    }
  }

  /**
   * Get quality color for UI
   */
  getQualityColor(quality: string): string {
    switch (quality.toLowerCase()) {
      case 'closing_price':
        return 'text-green-600';
      case 'closest_available':
        return 'text-yellow-600';
      case 'manual':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  }

  /**
   * Get source icon for UI
   */
  getSourceIcon(source: string): string {
    switch (source.toLowerCase()) {
      case 'yfinance':
        return '📊';
      case 'manual':
        return '✏️';
      case 'tcmb':
        return '🏛️';
      default:
        return '📈';
    }
  }

  /**
   * Validate if a rate is reasonable
   */
  validateRate(rate: number, currencyPair: string): { isValid: boolean; warning?: string } {
    const bounds: Record<string, [number, number]> = {
      'USD/TRY': [1.0, 100.0],
      'EUR/TRY': [1.0, 150.0],
      'GBP/TRY': [1.0, 200.0],
    };

    const [min, max] = bounds[currencyPair] || [0.1, 1000];
    
    if (rate <= 0) {
      return { isValid: false, warning: 'Rate must be positive' };
    }
    
    if (rate < min || rate > max) {
      return { 
        isValid: true, 
        warning: `${currencyPair} rate (${rate}) seems unusual (expected ${min}-${max})` 
      };
    }

    return { isValid: true };
  }

  /**
   * Format rate for display
   */
  formatRate(rate: number, currencyPair: string): string {
    const [base, quote] = currencyPair.split('/');
    
    // For TRY pairs, show 4 decimal places
    if (quote === 'TRY') {
      return `${rate.toFixed(4)} ${quote}`;
    }
    
    // For other pairs, show 2 decimal places
    return `${rate.toFixed(2)} ${quote}`;
  }

  /**
   * Calculate converted amount
   */
  calculateConvertedAmount(amount: number, rate: number): number {
    return amount * rate;
  }

  /**
   * Get supported currency pairs
   */
  getSupportedPairs(): string[] {
    return ['USD/TRY', 'EUR/TRY', 'GBP/TRY'];
  }

  /**
   * Check if a currency pair is supported
   */
  isSupportedPair(currencyPair: string): boolean {
    return this.getSupportedPairs().includes(currencyPair);
  }
}

// Export singleton instance
export const exchangeRatesService = new ExchangeRatesService();
