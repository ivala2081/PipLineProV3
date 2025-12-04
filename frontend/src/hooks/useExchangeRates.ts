/**
 * React Hook for Exchange Rates Management
 * Provides state management and operations for exchange rates
 */

import { useState, useCallback, useEffect } from 'react';
import { 
  exchangeRatesService, 
  ExchangeRate, 
  ExchangeRatesResponse,
  DailySummaryRequest,
  FetchRateRequest,
  ManualUpdateRequest,
  RefreshRatesRequest
} from '../services/exchangeRatesService';

interface UseExchangeRatesState {
  rates: Record<string, ExchangeRate>;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

interface UseExchangeRatesReturn extends UseExchangeRatesState {
  // Actions
  fetchRatesForDate: (date: string) => Promise<void>;
  fetchRate: (currencyPair: string, date: string) => Promise<ExchangeRate | null>;
  updateManualRate: (request: ManualUpdateRequest) => Promise<boolean>;
  refreshRates: (request: RefreshRatesRequest) => Promise<boolean>;
  
  // Utilities
  getRate: (currencyPair: string) => ExchangeRate | null;
  hasRate: (currencyPair: string) => boolean;
  getRateValue: (currencyPair: string) => number | null;
  calculateAmount: (amount: number, currencyPair: string) => number | null;
  
  // State management
  clearError: () => void;
  clearRates: () => void;
}

export const useExchangeRates = (initialDate?: string): UseExchangeRatesReturn => {
  const [state, setState] = useState<UseExchangeRatesState>({
    rates: {},
    loading: false,
    error: null,
    lastUpdated: null,
  });

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Clear rates
  const clearRates = useCallback(() => {
    setState(prev => ({ 
      ...prev, 
      rates: {}, 
      lastUpdated: null 
    }));
  }, []);

  // Fetch rates for a specific date
  const fetchRatesForDate = useCallback(async (date: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await exchangeRatesService.getDailySummaryRates({ date });
      
      if (response.status === 'success' && response.rates) {
        // Convert rates to Record format if it's an array
        const ratesRecord = Array.isArray(response.rates) 
          ? response.rates.reduce((acc, rate) => {
              acc[rate.currency_pair] = rate;
              return acc;
            }, {} as Record<string, ExchangeRate>)
          : response.rates;
        
        setState(prev => ({
          ...prev,
          rates: ratesRecord,
          loading: false,
          lastUpdated: new Date(),
        }));
      } else {
        throw new Error(response.message || 'Failed to fetch rates');
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }));
    }
  }, []);

  // Fetch a specific rate
  const fetchRate = useCallback(async (currencyPair: string, date: string): Promise<ExchangeRate | null> => {
    try {
      const response = await exchangeRatesService.fetchRate({ 
        currency_pair: currencyPair, 
        date 
      });
      
      if (response.status === 'success' && response.rate) {
        // Update the rates state with the new rate
        setState(prev => ({
          ...prev,
          rates: {
            ...prev.rates,
            [currencyPair]: response.rate!,
          },
          lastUpdated: new Date(),
        }));
        
        return response.rate;
      } else {
        throw new Error(response.message || 'Failed to fetch rate');
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }));
      return null;
    }
  }, []);

  // Update rate manually
  const updateManualRate = useCallback(async (request: ManualUpdateRequest): Promise<boolean> => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await exchangeRatesService.updateManualRate(request);
      
      if (response.status === 'success' && response.rate) {
        setState(prev => ({
          ...prev,
          rates: {
            ...prev.rates,
            [request.currency_pair]: response.rate!,
          },
          loading: false,
          lastUpdated: new Date(),
        }));
        return true;
      } else {
        throw new Error(response.message || 'Failed to update rate');
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }));
      return false;
    }
  }, []);

  // Refresh rates
  const refreshRates = useCallback(async (request: RefreshRatesRequest): Promise<boolean> => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await exchangeRatesService.refreshRates(request);
      
      if (response.status === 'success') {
        // Re-fetch rates for the date to get updated data
        await fetchRatesForDate(request.date);
        return true;
      } else {
        throw new Error(response.message || 'Failed to refresh rates');
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }));
      return false;
    }
  }, [fetchRatesForDate]);

  // Get rate for a currency pair
  const getRate = useCallback((currencyPair: string): ExchangeRate | null => {
    return state.rates[currencyPair] || null;
  }, [state.rates]);

  // Check if rate exists for a currency pair
  const hasRate = useCallback((currencyPair: string): boolean => {
    return currencyPair in state.rates;
  }, [state.rates]);

  // Get rate value for a currency pair
  const getRateValue = useCallback((currencyPair: string): number | null => {
    const rate = state.rates[currencyPair];
    return rate ? rate.rate : null;
  }, [state.rates]);

  // Calculate converted amount
  const calculateAmount = useCallback((amount: number, currencyPair: string): number | null => {
    const rate = getRateValue(currencyPair);
    return rate ? amount * rate : null;
  }, [getRateValue]);

  // Auto-fetch rates if initial date is provided
  useEffect(() => {
    if (initialDate) {
      fetchRatesForDate(initialDate);
    }
  }, [initialDate, fetchRatesForDate]);

  return {
    // State
    rates: state.rates,
    loading: state.loading,
    error: state.error,
    lastUpdated: state.lastUpdated,
    
    // Actions
    fetchRatesForDate,
    fetchRate,
    updateManualRate,
    refreshRates,
    
    // Utilities
    getRate,
    hasRate,
    getRateValue,
    calculateAmount,
    
    // State management
    clearError,
    clearRates,
  };
};

// Hook for managing a single exchange rate
export const useExchangeRate = (currencyPair: string, date: string) => {
  const [rate, setRate] = useState<ExchangeRate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRate = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await exchangeRatesService.fetchRate({ 
        currency_pair: currencyPair, 
        date 
      });
      
      if (response.status === 'success' && response.rate) {
        setRate(response.rate);
      } else {
        throw new Error(response.message || 'Failed to fetch rate');
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, [currencyPair, date]);

  const updateRate = useCallback(async (newRate: number, reason?: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await exchangeRatesService.updateManualRate({
        date,
        currency_pair: currencyPair,
        rate: newRate,
        reason,
      });
      
      if (response.status === 'success' && response.rate) {
        setRate(response.rate);
        return true;
      } else {
        throw new Error(response.message || 'Failed to update rate');
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
      return false;
    } finally {
      setLoading(false);
    }
  }, [currencyPair, date]);

  // Auto-fetch rate when currency pair or date changes
  useEffect(() => {
    if (currencyPair && date) {
      fetchRate();
    }
  }, [currencyPair, date, fetchRate]);

  return {
    rate,
    loading,
    error,
    fetchRate,
    updateRate,
    clearError: () => setError(null),
  };
};

// Hook for exchange rates status
export const useExchangeRatesStatus = () => {
  const [status, setStatus] = useState<{
    operational: boolean;
    supportedPairs: string[];
    loading: boolean;
    error: string | null;
  }>({
    operational: false,
    supportedPairs: [],
    loading: true,
    error: null,
  });

  const checkStatus = useCallback(async () => {
    setStatus(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await exchangeRatesService.getStatus();
      
      if (response.status === 'success') {
        setStatus({
          operational: response.service_status === 'active',
          supportedPairs: response.supported_pairs || [],
          loading: false,
          error: null,
        });
      } else {
        throw new Error(response.message || 'Failed to check status');
      }
    } catch (error) {
      setStatus(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }));
    }
  }, []);

  // Check status on mount
  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  return {
    ...status,
    checkStatus,
  };
};
