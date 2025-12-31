/**
 * Custom hook for managing clients data fetching and state
 */
import { useState, useCallback, useRef } from 'react';
import { api } from '../utils/apiClient';
import { handleApiError } from '../utils/errorHandler';
import { Client, ClientsResponse, Transaction, DropdownOptions } from '../components/clients/types';

interface UseClientsDataReturn {
  clients: Client[];
  transactions: Transaction[];
  clientsSummary: any;
  dropdownOptions: DropdownOptions;
  loading: boolean;
  error: string | null;
  clientsError: string | null;
  dataLoadingState: {
    clients: boolean;
    transactions: boolean;
    analytics: boolean;
    dropdowns: boolean;
    allLoaded: boolean;
  };
  fetchClientsData: () => Promise<void>;
  fetchTransactionsData: (skipLoadingState?: boolean, isLoadMore?: boolean) => Promise<void>;
  fetchDropdownOptions: () => Promise<void>;
  retryClientsData: () => void;
}

const FETCH_THROTTLE_MS = 5000;

export const useClientsData = (): UseClientsDataReturn => {
  const [clients, setClients] = useState<Client[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [clientsSummary, setClientsSummary] = useState<any>(null);
  const [dropdownOptions, setDropdownOptions] = useState<DropdownOptions>({
    categories: [],
    payment_methods: [],
    psps: [],
    companies: [],
    currencies: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clientsError, setClientsError] = useState<string | null>(null);
  const [dataLoadingState, setDataLoadingState] = useState({
    clients: false,
    transactions: false,
    analytics: false,
    dropdowns: false,
    allLoaded: false,
  });

  // Throttling refs
  const lastFetchTimeRef = useRef<number>(0);
  const loadingInProgressRef = useRef(false);

  const fetchClientsData = useCallback(async () => {
    const now = Date.now();
    
    // Throttle requests
    if (now - lastFetchTimeRef.current < FETCH_THROTTLE_MS) {
      console.log('Fetch throttled - too soon since last fetch');
      return;
    }

    if (loadingInProgressRef.current) {
      console.log('Fetch already in progress');
      return;
    }

    try {
      loadingInProgressRef.current = true;
      lastFetchTimeRef.current = now;
      
      setDataLoadingState(prev => ({ ...prev, clients: true }));
      setClientsError(null);

      const endpoint = `/transactions/clients?_t=${Date.now()}&_refresh=${Math.random()}`;
      const response = await api.get(endpoint);

      if (response.ok) {
        const data = await api.parseResponse(response);
        
        if (data && data.clients) {
          const clientsArray = Array.isArray(data.clients) ? data.clients : [];
          
          const transformedData: Client[] = clientsArray.map((item: any) => ({
            client_name: item.client_name || '',
            company_name: item.company_name,
            payment_method: item.payment_method,
            category: item.category,
            total_amount: item.total_amount || 0,
            total_commission: item.total_commission || 0,
            total_net: item.total_net || 0,
            transaction_count: item.transaction_count || 0,
            first_transaction: item.first_transaction || '',
            last_transaction: item.last_transaction || '',
            currencies: item.currencies || [],
            psps: item.psps || [],
            avg_transaction: item.avg_transaction || 0,
          }));

          setClients(transformedData);
          setClientsSummary(data.summary || null);
          console.log('Clients data loaded successfully:', transformedData.length);
        } else {
          console.warn('No clients data in response');
          setClients([]);
          setClientsSummary(null);
        }
      } else {
        throw new Error('Failed to fetch clients data');
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
      const errorMessage = handleApiError(error, 'fetchClientsData');
      setClientsError(errorMessage.message);
      setClients([]);
    } finally {
      setDataLoadingState(prev => ({ ...prev, clients: false }));
      loadingInProgressRef.current = false;
    }
  }, []);

  const fetchTransactionsData = useCallback(async (skipLoadingState = false, isLoadMore = false) => {
    try {
      if (!skipLoadingState) {
        setDataLoadingState(prev => ({ ...prev, transactions: true }));
      }

      const params = new URLSearchParams();
      params.append('page', '1');
      params.append('per_page', '100');

      const response = await api.get(`/transactions/?${params.toString()}`);

      if (response.ok) {
        const data = await api.parseResponse(response);
        const transactionsData = Array.isArray(data.transactions) ? data.transactions : [];
        
        if (isLoadMore) {
          setTransactions(prev => [...prev, ...transactionsData]);
        } else {
          setTransactions(transactionsData);
        }
      }
    } catch (error) {
      console.error('Error fetching transactions:', error);
      const errorMessage = handleApiError(error, 'fetchTransactionsData');
      setError(errorMessage.message);
    } finally {
      if (!skipLoadingState) {
        setDataLoadingState(prev => ({ ...prev, transactions: false }));
      }
    }
  }, []);

  const fetchDropdownOptions = useCallback(async () => {
    try {
      setDataLoadingState(prev => ({ ...prev, dropdowns: true }));
      
      const response = await api.get('/transactions/dropdown-options');
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        setDropdownOptions({
          categories: data.categories || [],
          payment_methods: data.payment_methods || [],
          psps: data.psps || [],
          companies: data.companies || [],
          currencies: data.currencies || [],
        });
      }
    } catch (error) {
      console.error('Error fetching dropdown options:', error);
    } finally {
      setDataLoadingState(prev => ({ ...prev, dropdowns: false }));
    }
  }, []);

  const retryClientsData = useCallback(() => {
    setClientsError(null);
    fetchClientsData();
  }, [fetchClientsData]);

  return {
    clients,
    transactions,
    clientsSummary,
    dropdownOptions,
    loading,
    error,
    clientsError,
    dataLoadingState,
    fetchClientsData,
    fetchTransactionsData,
    fetchDropdownOptions,
    retryClientsData,
  };
};

