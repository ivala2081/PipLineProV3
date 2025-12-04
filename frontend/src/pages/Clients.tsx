import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTabPersistence } from '../hooks/useTabPersistence';
import * as XLSX from 'xlsx';
import { handleApiError, getUserFriendlyMessage } from '../utils/errorHandler';
import {
  BarChart3,
  Users,
  TrendingUp,
  TrendingDown,
  DollarSign,
  CreditCard,
  Building2,
  FileText,
  Calendar,
  Eye,
  Edit,
  Trash2,
  Filter,
  Search,
  Download,
  AlertCircle,
  Award,
  Star,
  BarChart,
  User,
  Building,
  Plus,
  LineChart,
  Activity,
  X,
  PieChart as PieChartIcon,
  Globe,
  ArrowUpRight,
  RefreshCw,
  CheckCircle,
  Clock,
  MoreHorizontal,
  Upload,
  Info,
  Settings,
  CalendarDays,
  ChevronDown
} from 'lucide-react';
import {
  BarChart as RechartsBarChart,
  Bar,
  LineChart as RechartsLineChart,
  Line,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ComposedChart,
} from 'recharts';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../utils/apiClient';
import { formatCurrency as formatCurrencyUtil, formatCurrencyPositive } from '../utils/currencyUtils';
import { usePSPRefresh } from '../hooks/usePSPRefresh';
import Modal from '../components/Modal';
import TransactionDetailView from '../components/TransactionDetailView';
import TransactionEditForm from '../components/TransactionEditForm';
import BulkUSDRates from '../components/BulkUSDRates';
import TransactionFilterPanel from '../components/TransactionFilterPanel';
import TransactionRow from '../components/TransactionRow';
import { 
  UnifiedCard, 
  UnifiedButton, 
  UnifiedBadge, 
  UnifiedSection, 
  UnifiedGrid
} from '../design-system';
import { Breadcrumb } from '../components/ui';
// Using Unified components for consistency
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { FormField } from '../components/ui/form-field';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import StandardMetricsCard from '../components/StandardMetricsCard';
import MetricCard from '../components/MetricCard';
import { ClientsPageSkeleton } from '../components/EnhancedSkeletonLoaders';

interface Client {
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

interface Transaction {
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


interface ClientsResponse {
  clients: Client[];
  total_clients: number;
}

interface DailySummary {
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
  psp_summary: Array<{
    name: string;
    gross_tl?: number;  // Gross amount (before commission)
    gross_usd?: number;  // Gross amount (before commission)
    amount_tl: number;  // For backward compatibility
    amount_usd: number;  // For backward compatibility
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
    gross_tl?: number;  // Gross amount (before commission)
    gross_usd?: number;  // Gross amount (before commission)
    amount_tl?: number;  // For backward compatibility
    amount_usd?: number;  // For backward compatibility
    net_amount_tl?: number;  // For backward compatibility
    net_amount_usd?: number;  // For backward compatibility
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

export default function Clients() {
  const { t } = useLanguage();
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const navigate = useNavigate();
  const { refreshPSPDataSilent } = usePSPRefresh();
  
  // KRITIK: Infinite loop guard - prevent multiple simultaneous data loads
  const dataLoadedRef = useRef(false);
  const loadingInProgressRef = useRef(false);
  const lastFetchTimeRef = useRef<number>(0);
  const FETCH_THROTTLE_MS = 5000;  // 5 saniye minimum aralık

  // Clear stale localStorage on component mount (one-time cleanup)
  useEffect(() => {
    console.log('🧹 Clearing stale localStorage cache...');
    try {
      localStorage.removeItem('pipeline_clients_data');
      localStorage.removeItem('pipeline_transactions_data');
      localStorage.removeItem('pipeline_dashboard_cache');
      console.log('✅ Stale cache cleared');
    } catch (e) {
      console.warn('Failed to clear stale cache:', e);
    }
  }, []); // Only run once on mount
  
  // Initialize state - ALWAYS start fresh (don't use old localStorage)
  // Old cache causes incorrect values after bulk delete/import
  const [clients, setClients] = useState<Client[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [clientsSummary, setClientsSummary] = useState<any>(null); // Summary metrics from API
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clientsError, setClientsError] = useState<string | null>(null);
  const [dataLoadingState, setDataLoadingState] = useState({
    clients: false,
    transactions: false,
    analytics: false,
    dropdowns: false,
    allLoaded: false
  });
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [selectedTransactions, setSelectedTransactions] = useState<number[]>(
    []
  );
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false);
  const [bulkDeleteLoading, setBulkDeleteLoading] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [expandedClients, setExpandedClients] = useState<Set<string>>(new Set());
  const [clientTransactions, setClientTransactions] = useState<Record<string, Transaction[]>>({});
  const [loadingClientTransactions, setLoadingClientTransactions] = useState<Record<string, boolean>>({});
  
  // State for daily summary modal
  const [showDailySummaryModal, setShowDailySummaryModal] = useState(false);
  const [dailySummaryData, setDailySummaryData] = useState<DailySummary | null>(null);
  const [dailySummaryLoading, setDailySummaryLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState('');
  
  // State for daily gross balances (deposits - withdrawals, before commission)
  const [dailyGrossBalances, setDailyGrossBalances] = useState<Record<string, { tl: number; usd: number; rate: number }>>({});
  
  // State for exchange rate edit modal
  const [showRateEditModal, setShowRateEditModal] = useState(false);
  const [editingDate, setEditingDate] = useState('');
  const [editingRate, setEditingRate] = useState('');
  const [rateEditLoading, setRateEditLoading] = useState(false);
  
  // State for calendar date picker
  const [showCalendar, setShowCalendar] = useState(false);
  const [selectedCalendarDate, setSelectedCalendarDate] = useState('');
  
  // State for current exchange rate (for fallback calculations)
  const [currentUsdRate, setCurrentUsdRate] = useState<number>(48.9); // Default fallback rate

  // Fetch current exchange rate for fallback calculations
  const fetchCurrentExchangeRate = async () => {
    try {
      const response = await api.get('/exchange-rates/current');
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data && data.rates && data.rates.USD_TRY) {
          setCurrentUsdRate(data.rates.USD_TRY.rate);
        }
      }
    } catch (error) {
      console.warn('Failed to fetch current exchange rate, using fallback:', error);
    }
  };

  // Fetch current exchange rate on component mount
  useEffect(() => {
    fetchCurrentExchangeRate();
  }, []);



  const [dropdownOptions, setDropdownOptions] = useState({
    psps: [] as string[],
    categories: [] as string[],
    payment_methods: [] as string[],
    currencies: [] as string[],
    companies: [] as string[],
  });
  const [filters, setFilters] = useState({
    search: '',
    category: 'all',
    psp: 'all',
    company: 'all',
    payment_method: 'all',
    currency: 'all',
    status: 'all',
    date_from: '',
    date_to: '',
    amount_min: '',
    amount_max: '',
    commission_min: '',
    commission_max: '',
    client_name: '',
    sort_by: 'date',
    sort_order: 'desc',
  });
  const [showFilters, setShowFilters] = useState(false);
  
  const [expandedFilterSections, setExpandedFilterSections] = useState({
    basic: true,
    advanced: false,
    amounts: false,
    dates: false,
  });
  // Load More functionality state
  const [loadMoreState, setLoadMoreState] = useState({
    currentOffset: 0,
    itemsPerLoad: 100, // Changed from 500 to 100 for better UX
    total: 0,
    hasMore: true,
    loading: false,
    oldestDate: null as string | null, // Track the oldest transaction date to load older transactions
  });
  // Track how many transactions to display (pagination for UI display)
  const [displayLimit, setDisplayLimit] = useState(100);
  const [exporting, setExporting] = useState(false);
  const location = useLocation();
  const [activeTab, handleTabChangeBase] = useTabPersistence<'overview' | 'transactions' | 'analytics' | 'clients'>('overview');
  const [isChangingPagination, setIsChangingPagination] = useState(false);
  const [paginationLoading, setPaginationLoading] = useState(false);
  const [loadingTimeout, setLoadingTimeout] = useState<NodeJS.Timeout | null>(null);
  const [showViewModal, setShowViewModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showViewTransactionModal, setShowViewTransactionModal] = useState(false);
  const [showEditTransactionModal, setShowEditTransactionModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);

  
  // Debug initial state
  console.log('🔍 Component state:', {
    isAuthenticated,
    authLoading,
    activeTab,
    transactionsLength: transactions.length,
    loading
  });
  
  // Import functionality state
  const [importing, setImporting] = useState(false);
  const [showImportGuide, setShowImportGuide] = useState(false);
  const [showImportPreview, setShowImportPreview] = useState(false);
  const [importData, setImportData] = useState<Transaction[]>([]);
  const [importPreview, setImportPreview] = useState<Transaction[]>([]);
  const [showPasteImport, setShowPasteImport] = useState(false);
  const [pasteData, setPasteData] = useState('');

  // Unified data loading function
  const loadAllData = useCallback(async () => {
    // KRITIK: Infinite loop prevention
    if (loadingInProgressRef.current) {
      console.log('⏸️ Clients: loadAllData already in progress, skipping...');
      return;
    }
    
    if (dataLoadedRef.current) {
      console.log('⏸️ Clients: Data already loaded, skipping...');
      return;
    }
    
    if (!isAuthenticated || authLoading) {
      console.log('🔄 Clients: Skipping loadAllData - not authenticated or loading');
      return;
    }
    
    console.log('🔄 Clients: Starting loadAllData...', new Date().toISOString());
    loadingInProgressRef.current = true;
    setLoading(true);
    setError(null);

    try {
      // Load all data simultaneously using Promise.all
      const [clientsResult, dropdownsResult, transactionsResult] = await Promise.allSettled([
        fetchClientsData(),
        fetchDropdownOptionsData(),
        fetchTransactionsData()
      ]);

      // Debug: Log the results
      console.log('🔄 Clients: loadAllData results:', {
        clients: clientsResult.status,
        dropdowns: dropdownsResult.status,
        transactions: transactionsResult.status,
        transactionsData: transactionsResult.status === 'fulfilled' ? transactionsResult.value?.length : 'failed'
      });

      // Update loading states
      setDataLoadingState(prev => ({
        ...prev,
        clients: clientsResult.status === 'fulfilled',
        dropdowns: dropdownsResult.status === 'fulfilled',
        transactions: transactionsResult.status === 'fulfilled',
        allLoaded: true
      }));

      // Clear any previous errors if data loaded successfully
      if (clientsResult.status === 'fulfilled') {
        setClientsError(null);
      }
      if (transactionsResult.status === 'fulfilled') {
        setError(null);
      }
      
      // Mark data as loaded
      dataLoadedRef.current = true;
      console.log('✅ Clients: Data loading completed, guard set');
    } catch (error) {
      console.error('❌ Error loading data:', error);
      setError('Failed to load data. Please try again.');
    } finally {
      loadingInProgressRef.current = false;
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, authLoading]);  // SADECE auth - function references cause re-renders!


  // Fallback: Ensure clients data loads on page load (DISABLED - causes infinite loop)
  // useEffect(() => {
  //   if (isAuthenticated && !authLoading && clients.length === 0 && !clientsError) {
  //     // Add a small delay to ensure authentication is fully established
  //     setTimeout(() => {
  //       console.log('🔄 Clients: Fallback loading clients data...');
  //       fetchClientsData();
  //     }, 100);
  //   }
  // }, [isAuthenticated, authLoading]);  // REMOVED clients.length - causes infinite loop!

  // Force load clients data when component mounts and we're on overview tab (DISABLED - causes infinite loop)
  // useEffect(() => {
  //   if (isAuthenticated && !authLoading && activeTab === 'overview' && clients.length === 0) {
  //     console.log('🔄 Clients: Force loading clients data for overview tab...');
  //     fetchClientsData();
  //   }
  // }, [isAuthenticated, authLoading, activeTab]);  // DISABLED - loadAllData handles this

  // Add a refresh mechanism that can be called externally
  useEffect(() => {
    const handleRefresh = (event: Event) => {
      const customEvent = event as CustomEvent;
      console.log('🔄 Clients page: Received transactionsUpdated event', customEvent?.detail);
      
      // Skip refresh if this page triggered the update
      if (customEvent?.detail?.skipCurrentPage) {
        console.log('🔄 Clients page: Skipping refresh - update originated from this page');
        return;
      }
      
      if (isAuthenticated && !authLoading) {
        console.log('🔄 Clients page: Refreshing data...');
        // Reset load more state for new transactions
        if (customEvent?.detail?.action === 'create') {
          setLoadMoreState(prev => ({ ...prev, currentOffset: 0, hasMore: true, oldestDate: null }));
        }
        // Use skipLoadingState to prevent loading conflicts
        fetchTransactionsData(true);
        fetchClientsData();
      } else {
        console.log('🔄 Clients page: Not authenticated or still loading, skipping refresh');
      }
    };

    // Listen for transaction updates from other components
    window.addEventListener('transactionsUpdated', handleRefresh);
    
    return () => {
      window.removeEventListener('transactionsUpdated', handleRefresh);
    };
  }, [isAuthenticated, authLoading]);

  // Cleanup timeouts on component unmount
  useEffect(() => {
    return () => {
      if (loadingTimeout) {
        clearTimeout(loadingTimeout);
      }
    };
  }, [loadingTimeout]);

  // Retry mechanism for failed clients data
  const retryClientsData = () => {
    setClientsError(null);
    fetchClientsData();
  };

  // fetchTransactions - fetchTransactionsData() kullanarak tutarli bir wrapper
  // Bu fonksiyon loading state yonetir ve filter uygulama gibi durumlarda kullanilir
  const fetchTransactions = useCallback(async () => {
    console.log('🎯 fetchTransactions called!');
    
    // Prevent multiple simultaneous calls
    if (loading) {
      console.log('🔄 fetchTransactions: Already loading, skipping...');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // Reset load more state when applying filters
      setLoadMoreState(prev => ({ ...prev, currentOffset: 0, hasMore: true, oldestDate: null }));
      
      // fetchTransactionsData() kullan - skipLoadingState=true cunku loading state'i burada yonetiyoruz
      await fetchTransactionsData(true, false);
      
    } catch (error: any) {
      console.error('❌ Fetch Transactions Error:', error);
      const pipLineError = handleApiError(error, 'fetchTransactions');
      setError(getUserFriendlyMessage(pipLineError));
    } finally {
      setLoading(false);
      setPaginationLoading(false);
      // Clear any pending timeouts
      if (loadingTimeout) {
        clearTimeout(loadingTimeout);
        setLoadingTimeout(null);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, loadMoreState.itemsPerLoad, loading]);

  // Update active tab based on route - only on initial load or route change
  useEffect(() => {
    // Don't change tabs if we're in the middle of changing pagination
    if (isChangingPagination) return;
    
    // Only change tabs on actual route changes, not on data updates
    if (location.pathname === '/transactions') {
      handleTabChangeBase('transactions');
      // Refresh data when navigating to transactions if we don't have recent data
      if (isAuthenticated && !authLoading && transactions.length === 0) {
        console.log('🔄 Clients: Navigating to transactions, refreshing data...');
        loadAllData();
      }
    }
    // Note: /clients route doesn't force a tab change - uses default 'overview' from initialization
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname, isAuthenticated, authLoading, isChangingPagination, loadAllData]); // loadAllData eklendi

  // Main data loading effect - simplified and reliable
  useEffect(() => {
    // KRITIK: Bu effect sadece auth durumu değiştiğinde çalışmalı
    // clients/transactions length'i dependency'ye EKLEMEYİN - infinite loop'a neden olur!
    console.log('🔄 Clients: Main data loading effect triggered', {
      isAuthenticated,
      authLoading,
      activeTab,
      transactionsLength: transactions.length,
      clientsLength: clients.length
    });

    if (isAuthenticated && !authLoading) {
      // Only load data if we have NO data at all (both arrays empty)
      if (clients.length === 0 && transactions.length === 0) {
        console.log('🔄 Clients: No data found, loading all data...', {
          clientsLength: clients.length,
          transactionsLength: transactions.length
        });
        loadAllData();
      } else {
        console.log('✅ Clients: Data exists, skipping load', {
          clientsLength: clients.length,
          transactionsLength: transactions.length
        });
      }
    } else if (!isAuthenticated && !authLoading) {
      // Only clear data if we actually have data to clear
      if (clients.length > 0 || transactions.length > 0) {
        console.log('🧹 Clients: Clearing data - not authenticated', {
          clientsLength: clients.length,
          transactionsLength: transactions.length
        });
        setClients([]);
        setTransactions([]);
        setError(null);
        // Also clear localStorage when not authenticated
        try {
          localStorage.removeItem('pipeline_clients_data');
          localStorage.removeItem('pipeline_transactions_data');
        } catch (error) {
          console.error('Failed to clear localStorage:', error);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, authLoading, loadAllData]); // SADECE auth - clients/transactions EKLEMEYİN!

  // Handle tab changes without clearing data
  useEffect(() => {
    console.log('🔄 Clients: Tab changed to:', activeTab);
    // Don't reload data on tab change, just log it
    // Data should persist across tab changes
  }, [activeTab]);

  // Transactions sekmesi acildiginda veri yukle
  useEffect(() => {
    if (activeTab === 'transactions' && isAuthenticated && !authLoading && transactions.length === 0 && !loading) {
      console.log('🔄 Clients: Transactions tab opened with no data, loading transactions...');
      fetchTransactionsData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, isAuthenticated, authLoading]);

  // Debug: Log transactions state changes (DISABLED - causes excessive logging)
  // useEffect(() => {
  //   console.log('🔄 Clients: Transactions state changed:', {
  //     transactionsLength: transactions.length,
  //     activeTab,
  //     isAuthenticated,
  //     authLoading
  //   });
  // }, [transactions, activeTab, isAuthenticated, authLoading]);

  // Persist and restore display limit
  useEffect(() => {
    // When component mounts, try to restore display limit from localStorage
    try {
      const savedDisplayLimit = localStorage.getItem('clients_transactions_display_limit');
      if (savedDisplayLimit && activeTab === 'transactions') {
        const limit = parseInt(savedDisplayLimit, 10);
        if (!isNaN(limit) && limit >= 100) {
          console.log('🔄 Restoring display limit from localStorage:', limit);
          setDisplayLimit(limit);
        } else {
          console.log('🔄 Invalid saved display limit, using default: 100');
          setDisplayLimit(100);
        }
      } else {
        console.log('🔄 No saved display limit, using default: 100');
        setDisplayLimit(100);
      }
    } catch (error) {
      console.error('Failed to restore display limit from localStorage:', error);
      setDisplayLimit(100);
    }
  }, [location.pathname, activeTab]);

  // Save display limit to localStorage whenever it changes
  useEffect(() => {
    if (activeTab === 'transactions' && displayLimit > 0) {
      try {
        localStorage.setItem('clients_transactions_display_limit', displayLimit.toString());
        console.log('💾 Saved display limit to localStorage:', displayLimit);
      } catch (error) {
        console.error('Failed to save display limit to localStorage:', error);
      }
    }
  }, [displayLimit, activeTab]);

  // DISABLED: LocalStorage persistence causes stale data issues
  // After bulk delete/import, old cached values were showing
  // Now always fetch fresh data from API instead of using localStorage cache
  
  // useEffect(() => {
  //   if (clients.length > 0) {
  //     localStorage.setItem('pipeline_clients_data', JSON.stringify(clients));
  //   }
  // }, [clients]);
  
  // useEffect(() => {
  //   if (transactions.length > 0) {
  //     localStorage.setItem('pipeline_transactions_data', JSON.stringify(transactions));
  //   }
  // }, [transactions]);
  
  // DISABLED: Restore from localStorage (causes stale data)
  // useEffect(() => {
  //   if (isAuthenticated && !authLoading && transactions.length === 0) {
  //     const saved = localStorage.getItem('pipeline_transactions_data');
  //     if (saved) setTransactions(JSON.parse(saved));
  //   }
  // }, [isAuthenticated, authLoading]);

  // DISABLED: Cleanup on unmount (no longer needed since we don't use localStorage cache)
  // useEffect(() => {
  //   return () => {
  //     if (!isAuthenticated) {
  //       localStorage.removeItem('pipeline_clients_data');
  //       localStorage.removeItem('pipeline_transactions_data');
  //     }
  //   };
  // }, [isAuthenticated]);

  // Removed force data loading on component mount to prevent conflicts

  // Removed conflicting data loading effects to prevent data clearing

  // Debug: Log transactions state changes (DISABLED - causes excessive renders)
  // useEffect(() => {
  //   console.log('🔄 Clients: Transactions state changed:', transactions.length, 'transactions');
  // }, [transactions]);

  // Debug: Log clients state changes (DISABLED - causes excessive renders)
  // useEffect(() => {
  //   console.log('🔄 Clients: Clients state changed:', {
  //     clientsLength: clients.length,
  //     clientsError,
  //     isAuthenticated,
  //     authLoading,
  //     activeTab
  //   });
  // }, [clients, clientsError, isAuthenticated, authLoading, activeTab]);

  // Handle filter changes for transactions tab (DISABLED - causes infinite API loop)
  // useEffect(() => {
  //   if (isAuthenticated && !authLoading && activeTab === 'transactions') {
  //     // Reset load more state when filters change
  //     setLoadMoreState(prev => ({
  //       ...prev,
  //       currentOffset: 0,
  //       hasMore: true,
  //       oldestDate: null,
  //     }));
  //     
  //     // Debounce filter changes to avoid too many API calls
  //     const timeoutId = setTimeout(() => {
  //       console.log('🔄 Clients: Filter changed, refreshing transactions...');
  //       // Only fetch if we don't already have data or if filters actually changed
  //       if (transactions.length === 0 || Object.values(filters).some(filter => filter && filter.trim() !== '')) {
  //         fetchTransactionsData();
  //       }
  //     }, 1000); // Increased to 1000ms debounce to prevent flickering
  //     
  //     return () => clearTimeout(timeoutId);
  //   }
  //   return undefined;
  // }, [filters, isAuthenticated, authLoading, activeTab]);  // DISABLED - manual filter button instead

  // Individual data fetching functions (without loading states)
  const fetchClientsData = async () => {
    try {
      // KRITIK: Throttle protection
      const now = Date.now();
      if ((now - lastFetchTimeRef.current) < FETCH_THROTTLE_MS) {
        console.log(`⏸️ fetchClientsData throttled: ${((FETCH_THROTTLE_MS - (now - lastFetchTimeRef.current)) / 1000).toFixed(1)}s remaining`);
        return [];
      }
      
      console.log('🔄 Clients: Fetching clients data...', {
        isAuthenticated,
        authLoading,
        currentClientsLength: clients.length
      });
      setClientsError(null);
      // Check authentication first
      if (!isAuthenticated) {
        console.log('🔄 Clients: Not authenticated, skipping clients fetch');
        setClientsError('Authentication required');
        return [];
      }

      const response = await api.get(`/transactions/clients?_t=${Date.now()}&_refresh=${Math.random()}`);

      console.log('🔄 Clients: Clients API response:', {
        status: response.status,
        ok: response.ok,
        statusText: response.statusText
      });

      if (response.status === 401) {
        console.log('❌ Unauthorized access');
        return [];
      }

      if (response.ok) {
        const data = await api.parseResponse(response);
        console.log('🔄 Clients: Clients data received:', data);
        
        // New API format: { clients: [], summary: {} } OR old format: []
        // Backward compatible with both formats
        let clientsArray: any[];
        let summary: any = null;
        
        if (data && typeof data === 'object' && 'clients' in data) {
          // New format with summary
          clientsArray = data.clients || [];
          summary = data.summary || null;
        } else if (Array.isArray(data)) {
          // Old format - just array
          clientsArray = data;
        } else {
          clientsArray = [];
        }
        
        const transformedData: Client[] = clientsArray.map((item: any) => ({
          client_name: item.client_name || 'Unknown',
          company_name: item.company_name || null,
          payment_method: item.payment_method || null,
          category: item.category || null,
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

        console.log('🔄 Clients: Transformed clients data:', transformedData.length, 'clients');
        console.log('🔄 Clients: Summary metrics:', summary);
        
        setClients(transformedData);
        setClientsSummary(summary); // Store summary metrics
        setClientsError(null); // Clear any previous errors
        return transformedData;
      } else {
        console.error('🔄 Clients: Clients API failed:', response.status, response.statusText);
        setClientsError('Failed to load clients data');
        setClients([]);
        return [];
      }
    } catch (error) {
      console.error('❌ Clients fetch error:', error);
      setClientsError('Failed to load clients data. Please try again.');
      setClients([]);
      return [];
    }
  };

  const fetchDropdownOptionsData = async () => {
    try {
      const response = await api.get('/transactions/dropdown-options');
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data) {
          // Extract just the 'value' property from each option object
          setDropdownOptions({
            currencies: (data.currencies || data.currency || []).map((option: any) => option.value),
            payment_methods: (data.payment_method || []).map((option: any) => option.value),
            categories: (data.category || []).map((option: any) => option.value),
            psps: (data.psp || []).map((option: any) => option.value),
            companies: (data.company || []).map((option: any) => option.value),
          });
        }
        return data;
      }
      return {};
    } catch (error) {
      console.error('Error fetching dropdown options:', error);
      return {};
    }
  };

  const fetchTransactionsData = async (skipLoadingState = false, isLoadMore = false) => {
    try {
      // KRITIK: Throttle protection - prevent excessive API calls
      const now = Date.now();
      if (!skipLoadingState && !isLoadMore && (now - lastFetchTimeRef.current) < FETCH_THROTTLE_MS) {
        console.log(`⏸️ fetchTransactionsData throttled: ${((FETCH_THROTTLE_MS - (now - lastFetchTimeRef.current)) / 1000).toFixed(1)}s remaining`);
        return [];
      }
      lastFetchTimeRef.current = now;
      
      // Check authentication first
      if (!isAuthenticated) {
        console.log('🔄 Clients: Not authenticated, skipping transactions fetch');
        return [];
      }
      
      // Prevent multiple simultaneous calls unless explicitly allowed
      if (loading && !skipLoadingState) {
        console.log('🔄 fetchTransactionsData: Already loading, skipping...');
        return [];
      }

      console.log('🔄 Clients: Fetching transactions data...', { skipLoadingState, isLoadMore, loadMoreState });

      const params = new URLSearchParams();
      
      // Add pagination parameters - always page 1 since we're filtering by date
      params.append('page', '1');
      params.append('per_page', loadMoreState.itemsPerLoad.toString());
      
      // Add all filter parameters
      if (filters.search && filters.search.trim() !== '') params.append('search', filters.search);
      if (filters.category && filters.category.trim() !== '' && filters.category !== 'all') params.append('category', filters.category);
      if (filters.psp && filters.psp.trim() !== '' && filters.psp !== 'all') params.append('psp', filters.psp);
      if (filters.company && filters.company.trim() !== '' && filters.company !== 'all') params.append('company', filters.company);
      if (filters.payment_method && filters.payment_method.trim() !== '' && filters.payment_method !== 'all') params.append('payment_method', filters.payment_method);
      if (filters.currency && filters.currency.trim() !== '' && filters.currency !== 'all') params.append('currency', filters.currency);
      if (filters.status && filters.status.trim() !== '' && filters.status !== 'all') params.append('status', filters.status);
      if (filters.date_from && filters.date_from.trim() !== '') params.append('date_from', filters.date_from);
      
      // For Load More, use the oldest date as the upper bound to get older transactions
      // Note: We sort by 'date' field, so this pagination works correctly
      if (isLoadMore && loadMoreState.oldestDate) {
        // Get transactions BEFORE the oldest date we have
        const oldestDate = new Date(loadMoreState.oldestDate);
        oldestDate.setDate(oldestDate.getDate() - 1); // Go to the day before the oldest
        params.append('date_to', oldestDate.toISOString().split('T')[0]);
        console.log('🔄 Load More: Loading transactions with date older than', loadMoreState.oldestDate, 'using date_to =', oldestDate.toISOString().split('T')[0]);
      } else if (filters.date_to && filters.date_to.trim() !== '') {
        params.append('date_to', filters.date_to);
      }
      
      if (filters.amount_min && filters.amount_min.trim() !== '') params.append('amount_min', filters.amount_min);
      if (filters.amount_max && filters.amount_max.trim() !== '') params.append('amount_max', filters.amount_max);
      if (filters.commission_min && filters.commission_min.trim() !== '') params.append('commission_min', filters.commission_min);
      if (filters.commission_max && filters.commission_max.trim() !== '') params.append('commission_max', filters.commission_max);
      if (filters.client_name && filters.client_name.trim() !== '') params.append('client', filters.client_name);
      if (filters.sort_by && filters.sort_by.trim() !== '') params.append('sort_by', filters.sort_by);
      if (filters.sort_order && filters.sort_order.trim() !== '') params.append('sort_order', filters.sort_order);

      console.log('🔄 Clients: Fetching transactions...');
      console.log('🔄 API URL:', `/api/v1/transactions/?${params.toString()}`);
      
      const response = await api.get(`/transactions/?${params.toString()}`);

      console.log('🔍 fetchTransactionsData API Response:', response);
      console.log('🔍 Response Type:', typeof response);
      console.log('🔍 Is Response Object:', response instanceof Response);
      console.log('🔍 Response OK:', response.ok);
      console.log('🔍 Response Status:', response.status);
      console.log('🔍 Response StatusText:', response.statusText);

      if (response.status === 401) {
        console.log('🔄 Clients: Authentication failed, clearing transactions data');
        setTransactions([]);
        setError('Authentication required. Please log in again.');
        return [];
      }

      if (!response.ok) {
        // Handle non-401 errors
        console.error('❌ fetchTransactionsData: API response not OK:', response.status, response.statusText);
        try {
          const errorData = await api.parseResponse(response);
          const errorMessage = errorData?.message || errorData?.error || `Failed to fetch transactions: ${response.status} ${response.statusText}`;
          setError(errorMessage);
          console.error('❌ Error data from API:', errorData);
        } catch (parseError) {
          console.error('❌ Failed to parse error response:', parseError);
          setError(`Failed to fetch transactions: ${response.status} ${response.statusText}`);
        }
        return [];
      }

      // Get raw response BEFORE parsing to access meta.pagination
      const rawResponseData = (response as any).data;
      
      console.log('🔍 Raw API Response (before parseResponse):', {
        status: response.status,
        ok: response.ok,
        hasRawData: !!rawResponseData,
        rawDataKeys: rawResponseData ? Object.keys(rawResponseData) : [],
        rawDataHasData: !!rawResponseData?.data,
        rawDataIsArray: Array.isArray(rawResponseData?.data),
        rawDataLength: Array.isArray(rawResponseData?.data) ? rawResponseData.data.length : 'not array',
        rawDataFirstItem: Array.isArray(rawResponseData?.data) && rawResponseData.data.length > 0 ? rawResponseData.data[0] : 'empty array',
        rawMetaKeys: rawResponseData?.meta ? Object.keys(rawResponseData.meta) : [],
        rawPaginationTotal: rawResponseData?.meta?.pagination?.total,
        fullRawResponse: JSON.stringify(rawResponseData).substring(0, 1000)
      });
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        console.log('✅ fetchTransactionsData API Response parsed successfully:', {
          hasTransactions: !!data?.transactions,
          transactionCount: data?.transactions?.length || 0,
          hasPagination: !!data?.pagination,
          paginationData: data?.pagination,
          responseKeys: data && typeof data === 'object' && !Array.isArray(data) ? Object.keys(data) : [],
          dataTotal: (data as any)?.total,
          paginationTotal: (data as any)?.pagination?.total,
          fullPaginationObject: (data as any)?.pagination,
          isDataArray: Array.isArray(data),
          dataLength: Array.isArray(data) ? data.length : 'not array',
          firstItem: Array.isArray(data) && data.length > 0 ? data[0] : 'N/A'
        });
        
        // Backend API response format: {data: [...transactions...], meta: {pagination: {...}}}
        // parseResponse extracts data.data, so data should be the array directly
        // But also check raw response in case parseResponse doesn't extract it
        let transactionsData: any[] = [];
        
        if (Array.isArray(data)) {
          // parseResponse extracted the array correctly
          transactionsData = data;
        } else if (rawResponseData?.data && Array.isArray(rawResponseData.data)) {
          // parseResponse didn't extract it, get from raw response
          transactionsData = rawResponseData.data;
        } else if (Array.isArray(data?.transactions)) {
          // Legacy format: data.transactions
          transactionsData = data.transactions;
        } else if (Array.isArray(data?.meta?.transactions)) {
          // Another legacy format: data.meta.transactions
          transactionsData = data.meta.transactions;
        }
        
        console.log('🔄 Clients: Setting transactions data:', transactionsData.length, 'transactions', {
          isDataArray: Array.isArray(data),
          dataArrayLength: Array.isArray(data) ? data.length : 'not array',
          dataType: typeof data,
          rawResponseHasData: !!rawResponseData?.data,
          rawResponseDataIsArray: Array.isArray(rawResponseData?.data),
          rawResponseDataLength: Array.isArray(rawResponseData?.data) ? rawResponseData.data.length : 'not array',
          rawResponseMeta: rawResponseData?.meta,
          rawResponsePaginationTotal: rawResponseData?.meta?.pagination?.total,
          whichSource: Array.isArray(data) ? 'parsed data array' : 
                      (rawResponseData?.data && Array.isArray(rawResponseData.data)) ? 'raw response data' :
                      'other/empty'
        });
        
        // Get pagination from raw response or parsed data
        const paginationTotal = rawResponseData?.meta?.pagination?.total || 
                              rawResponseData?.meta?.total ||
                              data?.pagination?.total || 
                              data?.meta?.pagination?.total ||
                              0;
        
        // Eger transactions bos ama pagination.total > 0 ise uyari ver
        if (transactionsData.length === 0 && paginationTotal > 0) {
          console.warn('⚠️ WARNING: API returned 0 transactions but pagination.total > 0!', {
            paginationTotal: paginationTotal,
            fullData: data,
            rawResponseData: rawResponseData
          });
        }
        
        // Log the date range of loaded transactions for debugging
        if (transactionsData.length > 0) {
          const dates: string[] = transactionsData.map((t: any) => t.date).filter(Boolean);
          const minDate = dates.length > 0 ? Math.min(...dates.map((d) => new Date(d).getTime())) : null;
          const maxDate = dates.length > 0 ? Math.max(...dates.map((d) => new Date(d).getTime())) : null;
          console.log('📅 Loaded transactions date range:', {
            min: minDate ? new Date(minDate).toISOString().split('T')[0] : 'N/A',
            max: maxDate ? new Date(maxDate).toISOString().split('T')[0] : 'N/A',
            count: transactionsData.length,
            isLoadMore: isLoadMore,
            requestedDateTo: isLoadMore && loadMoreState.oldestDate ? new Date(new Date(loadMoreState.oldestDate).getTime() - 86400000).toISOString().split('T')[0] : 'N/A'
          });
        }
        
        // Process transaction data
        if (isLoadMore) {
          // Deduplicate and filter transactions
          setTransactions(prev => {
            const existingIds = new Set(prev.map(t => t.id));
            
            console.log('🔍 Load More - Before filtering:', {
              incomingTransactions: transactionsData.length,
              existingTransactions: prev.length,
              oldestDateThreshold: loadMoreState.oldestDate,
              incomingDateRange: transactionsData.length > 0 ? {
                min: Math.min(...transactionsData.map((t: any) => t.date).filter(Boolean)),
                max: Math.max(...transactionsData.map((t: any) => t.date).filter(Boolean))
              } : 'N/A'
            });
            
            // Filter out duplicates AND transactions that aren't actually older
            const newTransactions = transactionsData.filter((t: any) => {
              // Must not already exist
              if (existingIds.has(t.id)) {
                console.log('⚠️ Filtering out duplicate transaction ID:', t.id);
                return false;
              }
              
              // If we have an oldestDate, ensure this transaction is actually older
              if (loadMoreState.oldestDate && t.date) {
                const transactionDate = new Date(t.date).toISOString().split('T')[0];
                const oldestDateStr = new Date(loadMoreState.oldestDate).toISOString().split('T')[0];
                // Only include if transaction date is strictly less than oldestDate
                if (transactionDate >= oldestDateStr) {
                  console.log('⚠️ Filtering out transaction ID:', t.id, 'with date', transactionDate, 'because it is not older than', oldestDateStr);
                  return false;
                }
              }
              
              return true;
            });
            
            console.log('🔍 Deduplication & Filtering Result:', {
              previousCount: prev.length,
              newDataCount: transactionsData.length,
              duplicatesAndNewerFiltered: transactionsData.length - newTransactions.length,
              acceptedTransactions: newTransactions.length,
              finalCount: prev.length + newTransactions.length,
              oldestDateThreshold: loadMoreState.oldestDate,
              newTransactionIds: newTransactions.map((t: any) => t.id),
              newTransactionDates: newTransactions.map((t: any) => t.date)
            });
            return [...prev, ...newTransactions];
          });
        } else {
        setTransactions(transactionsData);
        }
        
        // Find the oldest transaction date from the newly loaded data
        let oldestDate = loadMoreState.oldestDate;
        if (transactionsData.length > 0) {
          const dates = transactionsData
            .map((t: any) => t.date || t.created_at)
            .filter((d: any) => d !== null && d !== undefined)
            .sort();
          
          if (dates.length > 0) {
            const newOldestDate = dates[0]; // First date after sorting (oldest)
            if (!oldestDate || newOldestDate < oldestDate) {
              oldestDate = newOldestDate;
            }
          }
        }
        
        // Update load more state
        // Get total from raw response meta.pagination or parsed data
        const total = paginationTotal || 0;
        const newOffset = isLoadMore ? loadMoreState.currentOffset + transactionsData.length : transactionsData.length;
        // Better hasMore logic: 
        // 1. If we got a full page, there might be more
        // 2. If we got less than a full page, check if we've reached the total
        // 3. If total is available, check if we've loaded all available transactions
        const gotFullPage = transactionsData.length === loadMoreState.itemsPerLoad;
        const currentLoaded = isLoadMore ? loadMoreState.currentOffset + transactionsData.length : transactionsData.length;
        const hasReachedTotal = total > 0 && currentLoaded >= total;
        
        // Has more if:
        // - We got a full page (500 transactions), OR
        // - We haven't reached the total count yet (even if we got less than 500)
        const hasMore = gotFullPage || (total > 0 && !hasReachedTotal);
        
        console.log('🔍 Load More State Update:', {
          total: total,
          currentOffset: loadMoreState.currentOffset,
          newOffset: newOffset,
          validTransactionsLength: transactionsData.length,
          gotFullPage: gotFullPage,
          currentLoaded: currentLoaded,
          hasReachedTotal: hasReachedTotal,
          hasMore: hasMore,
          isLoadMore: isLoadMore,
          oldestDate: oldestDate,
          paginationData: data.pagination,
          itemsPerLoad: loadMoreState.itemsPerLoad,
          logic: `gotFullPage(${gotFullPage}) || (total(${total}) > 0 && !hasReachedTotal(${hasReachedTotal}))`
        });
        
        setLoadMoreState(prev => ({
          ...prev,
          currentOffset: newOffset,
          total: total,
          hasMore: hasMore,
          oldestDate: oldestDate,
        }));
        
        // Fetch daily gross balances for all dates
        fetchDailyGrossBalances(transactionsData);
        
        return transactionsData;
      }
      return [];
    } catch (error) {
      console.error('❌ Error fetching transactions:', error);
      console.error('❌ Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
        error: error
      });
      setError(`Failed to load transactions: ${error instanceof Error ? error.message : 'Unknown error'}`);
      return [];
    }
  };

  // Legacy function for backward compatibility
  const fetchClients = async () => {
    setLoading(true);
    await fetchClientsData();
    setLoading(false);
  };



  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      category: '',
      psp: '',
      company: '',
      payment_method: '',
      currency: '',
      status: '',
      date_from: '',
      date_to: '',
      amount_min: '',
      amount_max: '',
      commission_min: '',
      commission_max: '',
      client_name: '',
      sort_by: 'date',
      sort_order: 'desc',
    });
    // Reset load more state when filters are reset
    setLoadMoreState(prev => ({ ...prev, currentOffset: 0, hasMore: true, oldestDate: null }));
  };

  const toggleFilterSection = (section: keyof typeof expandedFilterSections) => {
    setExpandedFilterSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const clearAllFilters = () => {
    resetFilters();
  };

  const getActiveFilterCount = () => {
    return Object.values(filters).filter(value => 
      value && value !== 'created_at' && value !== 'desc'
    ).length;
  };

  const applyQuickFilter = (filterType: string) => {
    switch (filterType) {
      case 'today':
        const today = new Date().toISOString().split('T')[0];
        setFilters(prev => ({
          ...prev,
          date_from: today,
          date_to: today,
        }));
        break;
      case 'thisWeek':
        const startOfWeek = new Date();
        startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay());
        const endOfWeek = new Date();
        endOfWeek.setDate(endOfWeek.getDate() + (6 - endOfWeek.getDay()));
        setFilters(prev => ({
          ...prev,
          date_from: startOfWeek.toISOString().split('T')[0],
          date_to: endOfWeek.toISOString().split('T')[0],
        }));
        break;
      case 'deposits':
        setFilters(prev => ({
          ...prev,
          category: 'DEP',
        }));
        break;
      case 'withdrawals':
        setFilters(prev => ({
          ...prev,
          category: 'WD',
        }));
        break;
      case 'highValue':
        setFilters(prev => ({
          ...prev,
          amount_min: '10000',
        }));
        break;
    }
    // Reset load more state ve otomatik fetch
    setLoadMoreState(prev => ({ ...prev, currentOffset: 0, hasMore: true, oldestDate: null }));
    // Quick filter uygulandiktan sonra otomatik fetch yap
    setTimeout(() => {
      fetchTransactions();
    }, 100);
  };

  const formatCurrency = (amount: number, currency?: string) => {
    // Use the shared utility for proper currency formatting
    return formatCurrencyUtil(amount, currency || 'USD');
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const formatDateHeader = (dateString: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // Check if it's today
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    
    // Check if it's yesterday
    if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    
    // For other dates, show formatted date
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  // Group transactions by date
  const groupTransactionsByDate = (transactions: Transaction[]) => {
    const grouped = transactions.reduce((acc, transaction) => {
      const dateKey = transaction.date || 'Unknown';
      if (!acc[dateKey]) {
        acc[dateKey] = [];
      }
      acc[dateKey].push(transaction);
      return acc;
    }, {} as Record<string, Transaction[]>);

    const result = Object.entries(grouped)
      .sort(([a], [b]) => b.localeCompare(a))
      .map(([dateKey, transactions]) => ({
        dateKey,
        date: dateKey,
        transactions: transactions.sort(
          (a, b) => {
            const dateA = a.date ? new Date(a.date).getTime() : 0;
            const dateB = b.date ? new Date(b.date).getTime() : 0;
            return dateB - dateA;
          }
        ),
        grossBalance: dailyGrossBalances[dateKey] || null, // Add gross balance (TL and USD) from state
      }));
      
      console.log('🗓️ Grouped transactions with gross balances:', result.map((g: any) => ({
        date: g.date,
        hasGrossBalance: !!g.grossBalance,
        rate: g.grossBalance?.rate,
        tl: g.grossBalance?.tl,
        usd: g.grossBalance?.usd
      })));
      
      // Also log the first few items in detail
      result.slice(0, 3).forEach((g: any, index: number) => {
        console.log(`📊 Date ${index + 1}: ${g.date}`, {
          grossBalance: g.grossBalance,
          hasGrossBalance: !!g.grossBalance,
          rate: g.grossBalance?.rate
        });
      });
      
      return result;
  };

  // Fetch daily summary data for all dates (gross balance = deposits - withdrawals before commission)
  const fetchDailyGrossBalances = async (transactions: Transaction[]) => {
    console.log('🔍 fetchDailyGrossBalances called with', transactions.length, 'transactions');
    const dates = [...new Set(transactions.map(t => t.date).filter(Boolean))] as string[];
    console.log('📅 Unique dates found:', dates);
    const grossBalances: Record<string, { tl: number; usd: number; rate: number }> = {};
    
    if (dates.length === 0) {
      console.log('⚠️ No dates found, skipping gross balance fetch');
      setDailyGrossBalances(grossBalances);
      return;
    }
    
    // Use batch endpoint for efficiency
    // Note: This endpoint is on transactions_bp which has no prefix, so it's at /api/summary/batch
    // We need to use the full path from root, not relative to /api/v1
    try {
      const datesParam = dates.join(',');
      // Use fetch directly to avoid api client's /api/v1 prefix
      const response = await fetch(`/api/summary/batch?dates=${encodeURIComponent(datesParam)}`, {
        credentials: 'include',
        headers: {
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        const batchData = await response.json();
        if (batchData && batchData.success && batchData.summaries) {
          // Extract gross_balance_tl, gross_balance_usd, and exchange_rate from each date summary
          Object.entries(batchData.summaries).forEach(([date, summary]: [string, any]) => {
            if (summary && summary.gross_balance_tl !== undefined) {
              // Get exchange rate - use from summary if available, otherwise try to get from current rate
              let exchangeRate = Number(summary.exchange_rate) || 0;
              
              // If rate is 0 or missing, try to use current exchange rate as fallback
              if (exchangeRate === 0 || !summary.exchange_rate) {
                // Try to get current rate from state or use a default
                const currentRate = currentUsdRate || 48.0;
                exchangeRate = currentRate;
                console.log(`⚠️ No exchange rate for ${date}, using fallback rate: ${exchangeRate}`);
              }
              
              // Normalize numeric values - ensure they are numbers
              grossBalances[date] = {
                tl: Number(summary.gross_balance_tl) || 0,
                usd: Number(summary.gross_balance_usd) || 0,
                rate: exchangeRate
              };
            }
          });
          console.log(`✅ Clients: Batch loaded ${Object.keys(batchData.summaries).length} gross balances (TL, USD, Rate) in 1 request`);
        } else {
          console.warn('⚠️ Batch summary response missing expected data structure:', batchData);
        }
      } else {
        console.warn('⚠️ Batch summary API returned non-OK status:', response.status, response.statusText);
        try {
          const errorData = await response.json();
          console.error('❌ Error data:', errorData);
        } catch (parseError) {
          console.error('❌ Failed to parse error response:', parseError);
        }
      }
    } catch (error) {
      console.error('❌ Failed to fetch batch daily summaries in Clients:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('❌ Error details:', errorMessage);
    }
    
    setDailyGrossBalances(grossBalances);
  };

  const handleExport = () => {
    const headers = [
      'Client Name',
      'Payment',
      'Total Amount',
      'Commissions',
      'Net Amount',
      'Transactions',
      'Currency',
      'PSP',
    ];
    const rows = sortedClients.map(client => {
      // Determine primary currency for this client
      const primaryCurrency =
        Array.isArray(client.currencies) && client.currencies.length > 0
          ? client.currencies[0]
          : 'USD';

      return [
        client.client_name || 'Unknown',
        client.payment_method || 'N/A',
        formatCurrency(client.total_amount || 0, primaryCurrency),
        formatCurrency(client.total_commission || 0, primaryCurrency),
        formatCurrency(client.total_net || 0, primaryCurrency),
        client.transaction_count || 0,
        Array.isArray(client.currencies) && client.currencies.length > 0
          ? client.currencies.join(', ')
          : 'N/A',
        Array.isArray(client.psps) ? client.psps.join(', ') : 'N/A',
      ];
    });

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'clients_export.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Helper function for exporting transactions to CSV
  const exportTransactionsToCSV = (transactionsToExport: Transaction[], filename: string) => {
    const headers = [
      'ID',
      'Date',
      'Client Name',
      'Payment Method',
      'PSP',
      'Amount (TRY)',
      'Amount (USD)',
      'Currency',
      'Transaction Type',
      'Commission Rate',
      'Commission Amount',
      'Net Amount',
      'Description',
      'Created At'
    ];

    const rows = transactionsToExport.map(transaction => {
      // Escape CSV special characters
      const escape = (str: any) => {
        if (str === null || str === undefined) return '';
        const s = String(str);
        if (s.includes(',') || s.includes('"') || s.includes('\n')) {
          return `"${s.replace(/"/g, '""')}"`;
        }
        return s;
      };

      // Calculate commission rate if amount exists
      const commissionRate = transaction.amount && transaction.amount > 0 
        ? ((transaction.commission || 0) / transaction.amount * 100).toFixed(2)
        : 0;

      return [
        escape(transaction.id),
        escape(transaction.date),
        escape(transaction.client_name || 'Unknown'),
        escape(transaction.payment_method || '-'),
        escape(transaction.psp || '-'),
        escape(transaction.amount_tl || transaction.amount || 0),
        escape((transaction as any).amount_usd || 0),
        escape(transaction.currency || 'TRY'),
        escape((transaction as any).transaction_type || transaction.category || 'deposit'),
        escape(commissionRate + '%'),
        escape(transaction.commission_tl || transaction.commission || 0),
        escape(transaction.net_amount_tl || transaction.net_amount || 0),
        escape(transaction.notes || ''),
        escape(transaction.created_at)
      ];
    });

    const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    
    // Add UTF-8 BOM (Byte Order Mark) for proper Turkish character support in Excel
    const BOM = '\uFEFF';
    const csvWithBOM = BOM + csvContent;
    
    const blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Export displayed transactions only
  const handleExportDisplayedTransactions = () => {
    console.log('📤 Exporting displayed transactions...', {
      displayLimit,
      totalTransactions: transactions.length,
      transactionsToExport: Math.min(displayLimit, transactions.length)
    });

    // Get only the displayed transactions
    const displayedTransactions = transactions.slice(0, displayLimit);
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `transactions_displayed_${displayedTransactions.length}_${timestamp}.csv`;
    
    exportTransactionsToCSV(displayedTransactions, filename);
    console.log('✅ Export completed:', displayedTransactions.length, 'transactions');
  };

  // Export all transactions from database (fetch everything with pagination)
  const handleExportAllTransactions = async () => {
    console.log('📤 Fetching and exporting ALL transactions from database...');
    
    setExporting(true);
    
    try {
      const allTransactions: any[] = [];
      const PER_PAGE = 500; // Fetch in chunks of 500 (matches backend max)
      let currentPage = 1;
      let hasMore = true;
      let totalPages = 1;
      
      // Build base params with filters (skip "all" or empty values)
      const baseParams = new URLSearchParams();
      if (filters.search && filters.search.trim() !== '') baseParams.append('search', filters.search);
      if (filters.client_name && filters.client_name.trim() !== '' && filters.client_name !== 'all') baseParams.append('client_name', filters.client_name);
      if (filters.payment_method && filters.payment_method.trim() !== '' && filters.payment_method !== 'all') baseParams.append('payment_method', filters.payment_method);
      if (filters.psp && filters.psp.trim() !== '' && filters.psp !== 'all') baseParams.append('psp', filters.psp);
      if (filters.date_from && filters.date_from.trim() !== '') baseParams.append('date_from', filters.date_from);
      if (filters.date_to && filters.date_to.trim() !== '') baseParams.append('date_to', filters.date_to);
      if (filters.amount_min && filters.amount_min.trim() !== '') baseParams.append('amount_min', filters.amount_min);
      if (filters.amount_max && filters.amount_max.trim() !== '') baseParams.append('amount_max', filters.amount_max);
      
      // Fetch all pages
      while (hasMore && currentPage <= totalPages) {
        const params = new URLSearchParams(baseParams);
        params.append('per_page', PER_PAGE.toString());
        params.append('page', currentPage.toString());
        
        console.log(`📥 Fetching page ${currentPage} of transactions...`);
        const response = await api.get(`/transactions/?${params.toString()}`);
        const data = await api.parseResponse(response);
        
        const transactions = data.transactions || [];
        allTransactions.push(...transactions);
        
        // Get pagination info
        if (data.pagination) {
          totalPages = data.pagination.pages || 1;
          hasMore = currentPage < totalPages && transactions.length === PER_PAGE;
        } else {
          // If no pagination info, stop if we got less than a full page
          hasMore = transactions.length === PER_PAGE;
        }
        
        currentPage++;
        
        // Safety limit: don't fetch more than 100 pages (50,000 transactions max)
        if (currentPage > 100) {
          console.warn('⚠️ Export limited to 50,000 transactions. Consider using filtered exports for larger datasets.');
          break;
        }
      }
      
      console.log('✅ Fetched all transactions from database:', allTransactions.length);
      
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `transactions_all_${allTransactions.length}_${timestamp}.csv`;
      
      exportTransactionsToCSV(allTransactions, filename);
      console.log('✅ Export completed:', allTransactions.length, 'transactions');
      
    } catch (error) {
      console.error('❌ Error fetching all transactions:', error);
      alert(t('transactions.export_failed'));
    } finally {
      setExporting(false);
    }
  };

  // Import functionality - Excel files only (backend processing)
  const triggerFileInput = () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.xlsx,.xls';  // Only Excel files supported
    fileInput.onchange = handleImport;
    fileInput.click();
  };

    const handleImport = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) {
      return;
    }
    
    console.log('📁 File details:', {
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: new Date(file.lastModified).toISOString()
    });
    
    // Check file extension - only Excel files supported
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    if (fileExt !== 'xlsx' && fileExt !== 'xls') {
      alert('Please upload an Excel file (.xlsx or .xls)');
      return;
    }
    
    setImporting(true);
    console.log('✅ Importing state set to true');
    
    try {
      console.log('📤 Uploading file to backend for processing...');
      
      // Create FormData to send file to backend
      const formData = new FormData();
      formData.append('file', file);
      
      // Optional: specify which sheets to import
      const sheetsToImport = ['HAZIRAN', 'TEMMUZ', 'AĞUSTOS', 'EKİM', 'KASIM'];
      formData.append('sheets', JSON.stringify(sheetsToImport));
      
      // Send file to new import-excel endpoint
      const response = await fetch('/api/v1/transactions/import-excel', { // Note: Using fetch directly with full path
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Import failed');
      }
      
      const result = await response.json();
      console.log('✅ Import successful:', result);
      
      // Show detailed success message
      let message = `Excel Import Completed!\n\n`;
      message += `✅ Imported: ${result.data.imported_count} transactions\n`;
      message += `⚠️ Skipped: ${result.data.skipped_count} rows\n`;
      message += `📄 Sheets processed: ${result.data.sheets_processed}\n`;
      
      if (result.data.warnings && result.data.warnings.length > 0) {
        message += `\n⚠️ Warnings (${result.data.warnings.length}):\n`;
        result.data.warnings.slice(0, 5).forEach((w: string) => message += `• ${w}\n`);
        if (result.data.warnings.length > 5) {
          message += `• ... and ${result.data.warnings.length - 5} more\n`;
        }
      }
      
      if (result.data.errors && result.data.errors.length > 0) {
        message += `\n❌ Errors (${result.data.errors.length}):\n`;
        result.data.errors.slice(0, 5).forEach((e: string) => message += `• ${e}\n`);
      }
      
      alert(message);
      
      // Refresh data
      console.log('🔄 Refreshing data...');
      if (activeTab === 'transactions') {
        await fetchTransactions();
      }
      await fetchClients();
      await fetchPaymentMethodData();
      
      console.log('✅ Import completed successfully');
      
    } catch (error: any) {
      console.error('❌ Import error:', error);
      alert(`Import Error: ${error.message}\n\nPlease check the file format and try again.`);
    } finally {
      setImporting(false);
    }
  };

  // Parse pasted transaction data (tab-separated format)
  const parsePastedData = (data: string): Transaction[] => {
    const transactions: Transaction[] = [];
    const lines = data.trim().split('\n');
    const USD_RATE = 42.6;

    const parseAmount = (amountStr: string): number => {
      // Binlik ayırıcıları kaldır (nokta), virgülü noktaya çevir
      const cleaned = amountStr.replace(/\./g, '').replace(',', '.');
      return parseFloat(cleaned) || 0;
    };

    const parseDate = (dateStr: string): string | null => {
      try {
        // DD.MM.YYYY formatını YYYY-MM-DD'ye çevir
        const parts = dateStr.split('.');
        if (parts.length === 3) {
          const day = parts[0].padStart(2, '0');
          const month = parts[1].padStart(2, '0');
          const year = parts[2];
          return `${year}-${month}-${day}`;
        }
        return null;
      } catch {
        return null;
      }
    };

    const mapCategory = (category: string): string => {
      const cat = category.trim().toUpperCase();
      if (cat === 'YATIRIM') return 'DEP';
      if (cat === 'ÇEKME') return 'WD';
      return 'DEP';
    };

    for (const line of lines) {
      if (!line.trim()) continue;

      const parts = line.split('\t');
      if (parts.length < 12) {
        console.warn('Eksik veri satırı:', line);
        continue;
      }

      const clientName = parts[0].trim();
      const paymentMethod = parts[1].trim();
      const company = parts[2].trim();
      const dateStr = parts[4].trim();
      const categoryStr = parts[5].trim();
      const amountStr = parts[6].trim();
      const commissionStr = parts[7].trim();
      const netAmountStr = parts[8].trim();
      const currency = parts[9].trim();
      const psp = parts[10].trim();

      const date = parseDate(dateStr);
      if (!date) {
        console.warn('Geçersiz tarih:', dateStr);
        continue;
      }

      const category = mapCategory(categoryStr);
      let amount = parseAmount(amountStr);
      const commission = parseAmount(commissionStr);
      let netAmount = parseAmount(netAmountStr);

      // ÇEKME işlemleri için amount negatif olmalı
      if (category === 'WD' && amount > 0) {
        amount = -amount;
        netAmount = -netAmount;
      }

      const transaction: Transaction = {
        id: 0, // Yeni transaction için 0
        client_name: clientName,
        company: company || 'Unknown',
        payment_method: paymentMethod,
        category: category,
        date: date,
        amount: amount,
        commission: commission,
        net_amount: netAmount,
        currency: currency,
        psp: psp,
        notes: ''
      };

      // USD işlemleri için exchange_rate ekle
      if (currency === 'USD') {
        transaction.exchange_rate = USD_RATE;
      }

      transactions.push(transaction);
    }

    return transactions;
  };

  // Handle paste and import
  const handlePasteImport = async () => {
    if (!pasteData.trim()) {
      alert('Lütfen veri yapıştırın');
      return;
    }

    try {
      const parsedTransactions = parsePastedData(pasteData);
      
      if (parsedTransactions.length === 0) {
        alert('Parse edilen transaction bulunamadı. Lütfen veri formatını kontrol edin.');
        return;
      }

      setImporting(true);

      // Prepare transactions for import
      const transactionsToImport = parsedTransactions.map(transaction => ({
        client_name: transaction.client_name,
        company: transaction.company || '',
        payment_method: transaction.payment_method || '',
        category: transaction.category,
        amount: transaction.amount,
        commission: transaction.commission || 0,
        net_amount: transaction.net_amount || transaction.amount,
        currency: transaction.currency || 'TL',
        psp: transaction.psp || '',
        notes: transaction.notes || '',
        date: transaction.date || new Date().toISOString().split('T')[0],
        exchange_rate: transaction.exchange_rate
      }));

      console.log('🚀 Importing transactions:', transactionsToImport);

      // Send transactions to backend API
      const response = await api.post('/transactions/bulk-import', {
        transactions: transactionsToImport
      });

      if (response.ok) {
        const result = await api.parseResponse(response);
        console.log('✅ Import successful:', result);
        
        let message = `Import tamamlandı!\n\n`;
        message += `✅ Başarılı: ${result.data.successful_imports} transaction\n`;
        message += `❌ Başarısız: ${result.data.failed_imports} transaction\n`;
        message += `⚠️ Atlandı: ${result.data.skipped_duplicates} transaction\n`;
        message += `📝 Toplam işlenen: ${result.data.total_rows} satır\n`;
        
        if (result.data.warnings && result.data.warnings.length > 0) {
          message += `\n⚠️ Uyarılar:\n`;
          result.data.warnings.slice(0, 5).forEach((w: string) => {
            message += `• ${w}\n`;
          });
        }
        
        if (result.data.errors && result.data.errors.length > 0) {
          message += `\n❌ Hatalar:\n`;
          result.data.errors.slice(0, 5).forEach((e: string) => {
            message += `• ${e}\n`;
          });
        }
        
        alert(message);
        
        // Close modal and clear data
        setShowPasteImport(false);
        setPasteData('');
        
        // Refresh data
        if (activeTab === 'transactions') {
          await fetchTransactions();
        }
        await fetchClients();
        await fetchPaymentMethodData();
        
      } else {
        const errorData = await api.parseResponse(response);
        alert(`Import başarısız: ${errorData.error || 'Bilinmeyen hata'}`);
      }
      
    } catch (error: any) {
      console.error('❌ Import error:', error);
      alert(`Import hatası: ${error.message || 'Bilinmeyen hata oluştu'}`);
    } finally {
      setImporting(false);
    }
  };

  // Handle final import of transactions to the system
  const handleFinalImport = async () => {
    if (!importData || importData.length === 0) {
      alert(t('transactions.no_data_import'));
      return;
    }

    setImporting(true);
    
    try {
      // Prepare transactions for import
      const transactionsToImport = importData.map(transaction => ({
        client_name: transaction.client_name,
        company: transaction.company || '',
        payment_method: transaction.payment_method || '',
        category: transaction.category,
        amount: transaction.amount,
        commission: transaction.commission || 0,
        net_amount: transaction.net_amount || transaction.amount,
        currency: transaction.currency || 'TL',
        psp: transaction.psp || '',
        notes: transaction.notes || '',
        date: transaction.date || new Date().toISOString().split('T')[0]
      }));

      console.log('🚀 Importing transactions:', transactionsToImport);

      // Send transactions to backend API
      const response = await api.post('/transactions/bulk-import', {
        transactions: transactionsToImport
      });

      if (response.ok) {
        const result = await api.parseResponse(response);
        console.log('✅ Import successful:', result);
        
        // Show detailed success message with import statistics
        let message = `Import completed successfully!\n\n`;
        message += `📊 Import Summary:\n`;
        message += `✅ Successfully imported: ${result.data.successful_imports} transactions\n`;
        message += `❌ Failed imports: ${result.data.failed_imports} transactions\n`;
        message += `⚠️ Duplicates skipped: ${result.data.skipped_duplicates} transactions\n`;
        message += `📝 Total rows processed: ${result.data.total_rows}\n`;
        
        // Add warnings if any
        if (result.data.warnings && result.data.warnings.length > 0) {
          message += `\n⚠️ Warnings:\n`;
          result.data.warnings.slice(0, 5).forEach((warning: string) => {
            message += `• ${warning}\n`;
          });
          if (result.data.warnings.length > 5) {
            message += `• ... and ${result.data.warnings.length - 5} more warnings\n`;
          }
        }
        
        // Add errors if any
        if (result.data.errors && result.data.errors.length > 0) {
          message += `\n❌ Errors:\n`;
          result.data.errors.slice(0, 5).forEach((error: string) => {
            message += `• ${error}\n`;
          });
          if (result.data.errors.length > 5) {
            message += `• ... and ${result.data.errors.length - 5} more errors\n`;
          }
        }
        
        // Add summary statistics if available
        if (result.data.summary) {
          message += `\n💰 Summary:\n`;
          message += `• Total amount imported: ${result.data.summary.total_amount?.toLocaleString() || 'N/A'} ₺\n`;
          message += `• Categories imported: ${result.data.summary.categories_imported?.join(', ') || 'N/A'}\n`;
        }
        
        // Show the detailed message
        alert(message);
        
        // Close modal
        setShowImportPreview(false);
        
        // Clear import data
        setImportData([]);
        setImportPreview([]);
        
        // Refresh the page data
        if (activeTab === 'transactions') {
          fetchTransactions();
        }
        fetchClients();
        
      } else {
        console.error('❌ Import failed:', response);
        alert(`${t('transactions.import_failed')}: ${response.statusText || 'Unknown error'}`);
      }
      
    } catch (error: any) {
      console.error('❌ Import error:', error);
      alert(`${t('transactions.import_error')}: ${error.message || 'Unknown error occurred'}`);
    } finally {
      setImporting(false);
    }
  };

  // Handle bulk delete of all transactions
  const handleBulkDeleteAll = async () => {
    if (confirmationCode !== '4561') {
      alert(t('transactions.invalid_confirmation_code'));
      return;
    }
    
    if (!confirm(t('transactions.confirm_delete_all'))) {
      return;
    }
    
    setDeleting(true);
    try {
      const response = await api.post('/transactions/bulk-delete', {
        confirmation_code: confirmationCode
      });
      
      if (response.ok) {
        const result = await api.parseResponse(response);
        alert(t('transactions.deleted_success').replace('{count}', result.data.deleted_count));
        setShowBulkDeleteModal(false);
        setConfirmationCode('');
        
        // Clear all local state and caches
        console.log('🧹 Clearing all local state and caches after bulk delete');
        
        // Clear payment method data
        setPaymentMethodData(null);
        setPaymentMethodTransactionCount(0);
        
        // Clear localStorage caches
        try {
          localStorage.removeItem('pipeline_transactions_data');
          localStorage.removeItem('pipeline_clients_data');
          localStorage.removeItem('pipeline_dashboard_cache');
          console.log('✅ LocalStorage cleared');
        } catch (e) {
          console.warn('Failed to clear localStorage:', e);
        }
        
        // Reset all state
        setTransactions([]);
        setClients([]);
        // setTotalTransactions(0);  // REMOVED - state doesn't exist
        // setCurrentPage(1);  // REMOVED - state doesn't exist
        dataLoadedRef.current = false;  // Reset data loaded flag
        
        // Refresh all data
        await loadAllData();
        await fetchPaymentMethodData();
        // await Promise.all([
        //   fetchClients(),
        //   fetchTransactions(),
        //   fetchPaymentMethodData()
        // ]);
        
        console.log('✅ All data refreshed after bulk delete');
      } else {
        const errorData = await api.parseResponse(response);
        alert(`${t('transactions.bulk_delete_failed')}: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error: any) {
      console.error('❌ Bulk delete error:', error);
      alert(`${t('transactions.bulk_delete_failed')}: ${error.message || 'Unknown error'}`);
    } finally {
      setDeleting(false);
    }
  };

  // Action handlers
  const handleViewClient = (client: Client) => {
    setSelectedClient(client);
    setShowViewModal(true);
  };

  const handleEditClient = (client: Client) => {
    setSelectedClient(client);
    setShowEditModal(true);
  };

  const handleDeleteClient = (client: Client) => {
    setSelectedClient(client);
    setShowDeleteModal(true);
  };

  // Transaction action handlers
  const handleViewTransaction = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setShowViewTransactionModal(true);
  };

  const handleEditTransaction = async (transaction: Transaction) => {
    try {
      // Ensure dropdown options are loaded before opening edit modal
      await fetchDropdownOptionsData();
      
      // Fetch full transaction details before editing
      const response = await api.get(`/transactions/${transaction.id}`);
      if (response.ok) {
        const result = await api.parseResponse(response);
        setSelectedTransaction(result.transaction || result);
        setShowEditTransactionModal(true);
      } else {
        console.error('Failed to fetch transaction details for editing');
        // Fallback to using the transaction data we have
        setSelectedTransaction(transaction);
        setShowEditTransactionModal(true);
      }
    } catch (error) {
      console.error('Error fetching transaction details for editing:', error);
      // Fallback to using the transaction data we have
      setSelectedTransaction(transaction);
      setShowEditTransactionModal(true);
    }
  };

  const handleDeleteTransaction = async (transaction: Transaction) => {
    if (
      confirm(
        `${t('transactions.confirm_delete_transaction')}\n\n${t('transactions.client_name')}: ${transaction.client_name}\n${t('common.amount')}: ${formatCurrency(transaction.amount, transaction.currency)}`
      )
    ) {
      try {
        const response = await api.delete(
          `/transactions/${transaction.id}`
        );

        if (response.ok) {
          const data = await api.parseResponse(response);
          if (data?.success) {
            // Remove transaction from local state
            setTransactions(prev => prev.filter(t => t.id !== transaction.id));
            
            // Update load more state - total count decreased
            setLoadMoreState(prev => ({
              ...prev,
              total: prev.total > 0 ? prev.total - 1 : 0
            }));

            // Refresh PSP data automatically after successful deletion
            try {
              await refreshPSPDataSilent();
              console.log('PSP data refreshed after transaction deletion');
            } catch (pspError) {
              console.warn(
                'Failed to refresh PSP data after transaction deletion:',
                pspError
              );
              // Don't fail the deletion if PSP refresh fails
            }

            // Broadcast event to notify other components
            window.dispatchEvent(new CustomEvent('transactionsUpdated', {
              detail: { 
                action: 'delete',
                transactionId: transaction.id
              }
            }));

            alert(t('transactions.transaction_deleted_success'));
          } else {
            alert(data?.message || t('transactions.failed_delete_transaction'));
          }
        } else {
          const data = await api.parseResponse(response);
          alert(data?.message || t('transactions.failed_delete_transaction'));
        }
      } catch (error) {
        console.error('Error deleting transaction:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        alert(`${t('transactions.delete_transaction_error')}: ${errorMessage}`);
      }
    }
  };

  // Function to refresh PSP data
  const refreshPSPData = async () => {
    try {
      console.log('🔄 Starting PSP data refresh from Clients page...');
      
      // Clear cache first
      api.clearCacheForUrl('psp_summary_stats');
      
      // Force refresh by disabling cache
      const response = await api.get('/transactions/psp_summary_stats');
      console.log('📡 PSP API response from Clients:', response);
      
      if (response.status === 200) {
        const pspData = api.parseResponse(response);
        // Update any PSP-related state if needed
        console.log('✅ PSP data refreshed from Clients:', pspData);
        return pspData;
      } else {
        console.error('❌ PSP API response not OK from Clients:', response.status);
        throw new Error('Failed to fetch PSP data');
      }
    } catch (error) {
      console.error('❌ Error refreshing PSP data from Clients:', error);
      throw error;
    }
  };

  // Bulk delete functions
  const handleSelectTransaction = (transactionId: number, checked: boolean) => {
    if (checked) {
      setSelectedTransactions(prev => [...prev, transactionId]);
    } else {
      setSelectedTransactions(prev => prev.filter(id => id !== transactionId));
    }
  };

  const handleSelectAllTransactions = (checked: boolean) => {
    if (checked) {
      const allTransactionIds = transactions.map(t => t.id);
      setSelectedTransactions(allTransactionIds);
    } else {
      setSelectedTransactions([]);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedTransactions.length === 0) {
      alert(t('transactions.select_transactions_delete'));
      return;
    }

    const confirmMessage = `${t('transactions.confirm_bulk_delete').replace('{count}', selectedTransactions.length)}\n\n${t('transactions.action_cannot_undone')}`;

    if (confirm(confirmMessage)) {
      try {
        setBulkDeleteLoading(true);

        // Delete transactions one by one
        const deletePromises = selectedTransactions.map(async transactionId => {
          try {
            const response = await api.delete(
              `/transactions/${transactionId}`
            );
            return { id: transactionId, success: response.ok };
          } catch (error) {
            return { id: transactionId, success: false, error };
          }
        });

        const results = await Promise.all(deletePromises);
        const successful = results.filter(r => r.success);
        const failed = results.filter(r => !r.success);

        // Remove successful deletions from local state
        setTransactions(prev =>
          prev.filter(t => !successful.some(s => s.id === t.id))
        );

        // Clear selection
        setSelectedTransactions([]);
        setShowBulkDeleteModal(false);

        // Wait a moment for backend to process all deletions, then refresh
        setTimeout(async () => {
          await fetchTransactions();

          // Refresh PSP data after bulk deletion
          try {
            await refreshPSPData();
            console.log('PSP data refreshed after bulk deletion');
          } catch (pspError) {
            console.warn(
              'Failed to refresh PSP data after bulk deletion:',
              pspError
            );
            // Don't fail the bulk deletion if PSP refresh fails
          }
        }, 500);

        // Show results
        if (successful.length > 0 && failed.length === 0) {
          alert(t('transactions.deleted_success').replace('{count}', successful.length));
        } else if (successful.length > 0 && failed.length > 0) {
          alert(
            t('transactions.bulk_delete_partial')
              .replace('{success}', successful.length)
              .replace('{failed}', failed.length)
          );
        } else {
          alert(t('transactions.bulk_delete_none'));
        }
      } catch (error) {
        console.error('Error in bulk delete:', error);
        alert(t('transactions.bulk_delete_error'));
      } finally {
        setBulkDeleteLoading(false);
      }
    }
  };

  const confirmDeleteClient = async () => {
    if (!selectedClient) return;

    try {
      setDeleteLoading(true);

      // Note: You'll need to implement the actual delete endpoint
      // For now, we'll simulate the deletion
      const response = await api.delete(
        `/clients/${encodeURIComponent(selectedClient.client_name)}`
      );

      if (response.ok) {
        // Remove client from local state
        setClients(prev =>
          prev.filter(
            client => client.client_name !== selectedClient.client_name
          )
        );
        setShowDeleteModal(false);
        setSelectedClient(null);
      } else {
        const data = await api.parseResponse(response);
        alert(data?.message || t('transactions.failed_delete_client'));
      }
    } catch (error) {
      console.error('Error deleting client:', error);
      alert(t('transactions.failed_delete_client'));
    } finally {
      setDeleteLoading(false);
    }
  };

  const closeModal = () => {
    setShowViewModal(false);
    setShowEditModal(false);
    setShowDeleteModal(false);
    setShowBulkDeleteModal(false);
    setSelectedClient(null);
  };




  const filteredClients = Array.isArray(clients)
    ? clients.filter(client => {
        const matchesSearch =
          !filters.search ||
          client.client_name
            .toLowerCase()
            .includes(filters.search.toLowerCase()) ||
          (client.company_name &&
            client.company_name
              .toLowerCase()
              .includes(filters.search.toLowerCase()));

        const matchesClientName =
          !filters.client_name ||
          client.client_name
            .toLowerCase()
            .includes(filters.client_name.toLowerCase());

        const matchesPaymentMethod =
          !filters.payment_method || filters.payment_method === 'all' ||
          (client.payment_method &&
            client.payment_method
              .toLowerCase()
              .includes(filters.payment_method.toLowerCase()));

        const matchesCategory =
          !filters.category || filters.category === 'all' ||
          (client.category &&
            client.category
              .toLowerCase()
              .includes(filters.category.toLowerCase()));

        const matchesPSP =
          !filters.psp || filters.psp === 'all' ||
          (Array.isArray(client.psps) &&
            client.psps.some(psp =>
              psp.toLowerCase().includes(filters.psp.toLowerCase())
            ));

        const matchesCurrency =
          !filters.currency || filters.currency === 'all' ||
          (Array.isArray(client.currencies) &&
            client.currencies.some(currency =>
              currency.toLowerCase().includes(filters.currency.toLowerCase())
            ));

        return (
          matchesSearch &&
          matchesClientName &&
          matchesPaymentMethod &&
          matchesCategory &&
          matchesPSP &&
          matchesCurrency
        );
      })
    : [];

  // Clients are displayed in chronological order (newest transactions first)
  const sortedClients = filteredClients;

  // Calculate summary metrics - use data when available, regardless of loading state
  const totalVolume = Array.isArray(filteredClients) && filteredClients.length > 0
    ? filteredClients.reduce((sum, client) => sum + client.total_amount, 0)
    : Array.isArray(clients) && clients.length > 0
    ? clients.reduce((sum, client) => sum + client.total_amount, 0)
    : 0;
  
  const totalCommissions = Array.isArray(filteredClients) && filteredClients.length > 0
    ? filteredClients.reduce((sum, client) => sum + client.total_commission, 0)
    : Array.isArray(clients) && clients.length > 0
    ? clients.reduce((sum, client) => sum + client.total_commission, 0)
    : 0;
    
  const totalTransactions = Array.isArray(filteredClients) && filteredClients.length > 0
    ? filteredClients.reduce((sum, client) => sum + client.transaction_count, 0)
    : Array.isArray(clients) && clients.length > 0
    ? clients.reduce((sum, client) => sum + client.transaction_count, 0)
    : 0;

  // Debug logging for commission calculation
  console.log('🔍 Commission Debug:', {
    activeTab,
    clientsLength: clients.length,
    filteredClientsLength: filteredClients.length,
    totalCommissions,
    sampleClient: filteredClients[0] ? {
      name: filteredClients[0].client_name,
      commission: filteredClients[0].total_commission,
      total_amount: filteredClients[0].total_amount
    } : 'No clients',
    allCommissions: filteredClients.map(c => ({ name: c.client_name, commission: c.total_commission }))
  });

  const avgTransactionValue =
    totalTransactions > 0 ? totalVolume / totalTransactions : 0;

  // State for dashboard financial data
  const [dashboardFinancialData, setDashboardFinancialData] = useState<{
    total_revenue: number;
    total_commission: number;
    net_cash: number;  // Degistirildi: Net Cash = Deposits - Withdrawals (dogru formul)
    total_deposits: number;
    total_withdrawals: number;
  } | null>(null);

  // State for payment method data
  const [paymentMethodData, setPaymentMethodData] = useState<{
    [key: string]: { deposits: number; withdrawals: number; total: number; count: number };
  } | null>(null);
  
  // Track total transaction count for change detection
  const [paymentMethodTransactionCount, setPaymentMethodTransactionCount] = useState<number>(0);

  // Fetch dashboard financial data for accurate calculations
  const fetchDashboardFinancialData = useCallback(async () => {
    try {
      const response = await api.get('/analytics/dashboard/stats?range=all');
      if (response.ok) {
        const data = await api.parseResponse(response);
        setDashboardFinancialData({
          total_revenue: data.summary?.total_revenue || 0,
          total_commission: data.summary?.total_commission || 0,
          // DUZELTME: net_cash kullan (deposits - withdrawals), total_net degil (komisyon sonrasi tutar)
          net_cash: data.summary?.net_cash || 0,  // Dogru formul: Deposits - Withdrawals
          total_deposits: data.summary?.total_deposits || 0,
          total_withdrawals: data.summary?.total_withdrawals || 0,
        });
        console.log('🔄 Clients: Dashboard financial data loaded:', data.summary);
      }
    } catch (error) {
      console.error('Error fetching dashboard financial data:', error);
    }
  }, []);

  // Normalize payment method names for display
  const normalizePaymentMethodName = (rawMethod: string): string => {
    const methodMap: { [key: string]: string } = {
      'KK': 'Credit Card',
      'BANKA': 'Bank',
      'Banka': 'Bank',
      'BANK': 'Bank',
      'CC': 'Credit Card',
      'CARD': 'Credit Card',
      'CREDIT CARD': 'Credit Card',
      'CASH': 'Cash',
      'WIRE': 'Wire Transfer',
      'TRANSFER': 'Transfer',
      'PAYPAL': 'PayPal',
      'STRIPE': 'Stripe',
      'SQUARE': 'Square',
      'TETHER': 'Tether',
      'USDT': 'Tether',
      'UNKNOWN': 'Unknown'
    };
    
    // First try exact match
    if (methodMap[rawMethod]) {
      return methodMap[rawMethod];
    }
    
    // Then try uppercase match
    const upperMethod = rawMethod.toUpperCase();
    if (methodMap[upperMethod]) {
      return methodMap[upperMethod];
    }
    
    // Handle case variations for common methods
    if (upperMethod.includes('CREDIT') && upperMethod.includes('CARD')) {
      return 'Credit Card';
    }
    if (upperMethod.includes('BANK')) {
      return 'Bank';
    }
    if (upperMethod.includes('TETHER') || upperMethod.includes('USDT')) {
      return 'Tether';
    }
    
    // Return original if no match found
    return rawMethod;
  };

  // Fetch payment method data for accurate analysis
  const fetchPaymentMethodData = useCallback(async () => {
    try {
      // Get transactions for payment method analysis
      // Note: Using pagination limit of 500. For complete analysis of very large datasets,
      // consider using analytics endpoints that aggregate payment method stats server-side
      const response = await api.get('/transactions/?per_page=500&page=1');
      if (response.status === 200) {
        const data = api.parseResponse(response);
        const allTransactions = data && (data as any).transactions && Array.isArray((data as any).transactions) 
          ? (data as any).transactions 
          : [];
        
        console.log('🔄 Clients: Fetched all transactions for payment method analysis:', allTransactions.length);
        
        const breakdown: { [key: string]: { deposits: number; withdrawals: number; total: number; count: number } } = {};
        
        allTransactions.forEach((transaction: any) => {
          const rawMethod = transaction.payment_method || 'Unknown';
          
          // Normalize payment method names for display
          const method = normalizePaymentMethodName(rawMethod);
          
          if (!breakdown[method]) {
            breakdown[method] = { deposits: 0, withdrawals: 0, total: 0, count: 0 };
          }
          
          // For Tether, use original USD amount; for others, use converted TRY amount
          const isTether = rawMethod && (rawMethod.toLowerCase().includes('tether') || rawMethod === 'TETHER');
          const amount = isTether 
            ? (transaction.amount || 0)  // Use original USD amount for Tether
            : (transaction.amount_tl !== null && transaction.amount_tl !== undefined ? transaction.amount_tl : transaction.amount || 0);  // Use converted TRY amount for others
          
          breakdown[method].count += 1;
          
          if (transaction.category === 'DEP' || transaction.category === 'Deposit' || transaction.category === 'Investment') {
            breakdown[method].deposits += amount;
            breakdown[method].total += amount;
          } else if (transaction.category === 'WD' || transaction.category === 'Withdraw' || transaction.category === 'Withdrawal') {
            breakdown[method].withdrawals += amount;
            breakdown[method].total -= amount;
          }
        });
        
        setPaymentMethodData(breakdown);
        setPaymentMethodTransactionCount(allTransactions.length);
        console.log('🔄 Clients: Payment method data calculated from all transactions:', Object.keys(breakdown).length, 'methods');
        console.log('🔄 Clients: Payment method breakdown details:', breakdown);
      }
    } catch (error) {
      console.error('Error fetching payment method data:', error);
    }
  }, []);

  // Fetch dashboard data when component mounts
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      fetchDashboardFinancialData();
      fetchPaymentMethodData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, authLoading]);  // SADECE auth - function references EKLEME!

  // Refresh payment method data when transactions change significantly (DISABLED - causes infinite loop)
  // useEffect(() => {
  //   if (isAuthenticated && !authLoading && transactions && transactions.length > 0) {
  //     // If we have transactions but no payment method data, or if transaction count changed significantly
  //     const hasPaymentData = paymentMethodData ? Object.keys(paymentMethodData).length > 0 : false;
  //     const currentTransactionCount = transactions.length;
  //     const transactionCountChanged = Math.abs(paymentMethodTransactionCount - currentTransactionCount) > 10;
  //     
  //     if (!hasPaymentData || transactionCountChanged) {
  //       console.log('🔄 Clients: Refreshing payment method data due to transaction changes');
  //       fetchPaymentMethodData();
  //     }
  //   }
  // }, [isAuthenticated, authLoading]);  // DISABLED transactions dependency - causes infinite loop!

  // Calculate deposit and withdrawal metrics using dashboard data
  const depositWithdrawMetrics = useMemo(() => {
    if (dashboardFinancialData) {
      // Use dashboard data for accurate calculations
      console.log('🔄 Clients: Using dashboard financial data for calculations');
      return {
        totalDeposits: dashboardFinancialData.total_deposits,
        totalWithdrawals: dashboardFinancialData.total_withdrawals,
      };
    }
    
    // Fallback to paginated transactions
    console.log('🔄 Clients: Using paginated transactions as fallback (may be inaccurate)');
    
    if (!Array.isArray(transactions)) {
      console.log('🔄 Clients: No transactions array available for deposit/withdrawal calculation');
      return { totalDeposits: 0, totalWithdrawals: 0 };
    }
    
    // Handle both category formats: 'DEP'/'WD' and 'Deposit'/'Withdraw'
    const deposits = transactions.filter(t => 
      t.category === 'DEP' || t.category === 'Deposit' || t.category === 'Investment'
    );
    const withdrawals = transactions.filter(t => 
      t.category === 'WD' || t.category === 'Withdraw' || t.category === 'Withdrawal'
    );
    
    console.log('🔄 Clients: Found', deposits.length, 'deposits and', withdrawals.length, 'withdrawals in paginated data');
    
    // Use converted amounts (amount_tl) for proper currency conversion
    const totalDeposits = deposits.reduce((sum, t) => {
      // Use amount_tl if available (converted amount), otherwise fallback to amount
      const amount = t.amount_tl !== null && t.amount_tl !== undefined ? t.amount_tl : t.amount || 0;
      return sum + amount;
    }, 0);
    const totalWithdrawals = withdrawals.reduce((sum, t) => {
      // Use amount_tl if available (converted amount), otherwise fallback to amount
      const amount = t.amount_tl !== null && t.amount_tl !== undefined ? t.amount_tl : t.amount || 0;
      return sum + amount;
    }, 0);
    
    console.log('🔄 Clients: Calculated totals from paginated data - Deposits:', totalDeposits, 'Withdrawals:', totalWithdrawals);
    console.log('⚠️  NOTE: These values are from paginated data and may not represent the full financial picture');
    
    return { totalDeposits, totalWithdrawals };
  }, [dashboardFinancialData, transactions]); // Make it reactive to dashboard data and transactions changes

  const { totalDeposits, totalWithdrawals } = depositWithdrawMetrics;

  // Debug logging for overview cards
  console.log('🔄 Clients: Overview cards data:', {
    transactionsLength: transactions.length,
    totalDeposits: dashboardFinancialData?.total_deposits || totalDeposits,
    totalWithdrawals: dashboardFinancialData?.total_withdrawals || totalWithdrawals,
    netCash: (dashboardFinancialData?.total_deposits || totalDeposits) - (dashboardFinancialData?.total_withdrawals || totalWithdrawals),
    clientsLength: clients.length,
    totalTransactions,
    activeTab
  });

  // Calculate payment method breakdown - use all transactions data for accuracy
  const paymentMethodBreakdown = useMemo(() => {
    console.log('🔄 Clients: Payment method breakdown calculation - paymentMethodData:', !!paymentMethodData, 'transactions length:', transactions?.length);
    
    if (paymentMethodData && Object.keys(paymentMethodData).length > 0) {
      // Use complete payment method data from all transactions
      console.log('🔄 Clients: Using complete payment method data from all transactions');
      console.log('🔄 Clients: Payment method data keys:', Object.keys(paymentMethodData));
      return paymentMethodData;
    }
    
    // Fallback to paginated transactions
    console.log('🔄 Clients: Using paginated transactions as fallback for payment method analysis');
    
    if (!Array.isArray(transactions)) return {};
    
    const breakdown: { [key: string]: { deposits: number; withdrawals: number; total: number; count: number } } = {};
    
    transactions.forEach(transaction => {
      const rawMethod = transaction.payment_method || 'Unknown';
      
      // Normalize payment method names for display
      const method = normalizePaymentMethodName(rawMethod);
      
      if (!breakdown[method]) {
        breakdown[method] = { deposits: 0, withdrawals: 0, total: 0, count: 0 };
      }
      
      // For Tether, use original USD amount; for others, use converted TRY amount
      const isTether = rawMethod && (rawMethod.toLowerCase().includes('tether') || rawMethod === 'TETHER');
      const amount = isTether 
        ? (transaction.amount || 0)  // Use original USD amount for Tether
        : (transaction.amount_tl !== null && transaction.amount_tl !== undefined ? transaction.amount_tl : transaction.amount || 0);  // Use converted TRY amount for others
      
      breakdown[method].count += 1;
      
      if (transaction.category === 'DEP' || transaction.category === 'Deposit' || transaction.category === 'Investment') {
        breakdown[method].deposits += amount;
        breakdown[method].total += amount;
      } else if (transaction.category === 'WD' || transaction.category === 'Withdraw' || transaction.category === 'Withdrawal') {
        breakdown[method].withdrawals += amount;
        breakdown[method].total -= amount;
      }
    });
    
    console.log('🔄 Clients: Payment method breakdown calculated from', transactions.length, 'paginated transactions');
    console.log('⚠️  NOTE: This breakdown may be incomplete due to pagination');
    
    return breakdown;
  }, [paymentMethodData, transactions]); // Make it reactive to payment method data and transactions changes

  // Calculate daily deposit and withdrawal metrics for the selected date
  const calculateDailyDepositWithdrawMetrics = (date: string) => {
    // First, try to calculate from local transactions (more reliable)
    if (Array.isArray(transactions)) {
      const dateTransactions = transactions.filter(t => {
        const transactionDate = t.date ? t.date.split('T')[0] : null;
        return transactionDate === date;
      });
      
      // Handle both category formats: 'DEP'/'WD' and 'Deposit'/'Withdraw'
      const deposits = dateTransactions.filter(t => 
        t.category === 'DEP' || t.category === 'Deposit' || t.category === 'Investment'
      );
      const withdrawals = dateTransactions.filter(t => 
        t.category === 'WD' || t.category === 'Withdraw' || t.category === 'Withdrawal'
      );
      
      // Use converted amounts (amount_tl) for proper currency conversion
      const totalDeposits = deposits.reduce((sum, t) => {
        const amount = t.amount_tl !== null && t.amount_tl !== undefined ? t.amount_tl : t.amount || 0;
        return sum + Math.abs(amount); // Ensure positive for deposits
      }, 0);
      const totalWithdrawals = withdrawals.reduce((sum, t) => {
        const amount = t.amount_tl !== null && t.amount_tl !== undefined ? t.amount_tl : t.amount || 0;
        return sum + Math.abs(amount); // Ensure positive for withdrawals
      }, 0);
      
      // Calculate transaction count and unique clients from the same filtered transactions
      const transactionCount = dateTransactions.length;
      const uniqueClients = new Set(dateTransactions.map(t => t.client_name).filter(name => name)).size;
      
      // If we have data from local calculation, use it (more reliable)
      if (transactionCount > 0) {
        console.log('📊 Using local calculation for daily metrics:', { totalDeposits, totalWithdrawals, transactionCount, uniqueClients });
        return { totalDeposits, totalWithdrawals, transactionCount, uniqueClients };
      }
    }
    
    // Fallback to backend data if local calculation has no data
    if (dailySummaryData && dailySummaryData.date === date) {
      const backendDeposits = dailySummaryData.total_deposits_tl || 0;
      const backendWithdrawals = dailySummaryData.total_withdrawals_tl || 0;
      const backendCount = dailySummaryData.transaction_count || 0;
      const backendClients = dailySummaryData.unique_clients || 0;
      
      console.log('📊 Using backend data for daily metrics:', { backendDeposits, backendWithdrawals, backendCount, backendClients });
      
      return {
        totalDeposits: backendDeposits,
        totalWithdrawals: backendWithdrawals,
        transactionCount: backendCount,
        uniqueClients: backendClients
      };
    }
    
    // Final fallback
    return { totalDeposits: 0, totalWithdrawals: 0, transactionCount: 0, uniqueClients: 0 };
  };

  // Calculate daily payment method breakdown for the selected date
  const calculateDailyPaymentMethodBreakdown = (date: string) => {
    if (!Array.isArray(transactions)) return {};
    
    const dateTransactions = transactions.filter(t => {
      const transactionDate = t.date ? t.date.split('T')[0] : null;
      return transactionDate === date;
    });
    
    const breakdown: { [key: string]: { deposits: number; withdrawals: number; total: number } } = {};
    
    dateTransactions.forEach(transaction => {
      const rawMethod = transaction.payment_method || 'Unknown';
      
      // Normalize payment method names for display
      const method = normalizePaymentMethodName(rawMethod);
      
      const amount = transaction.amount || 0; // Use original amount since we have automatic conversion
      
      if (!breakdown[method]) {
        breakdown[method] = { deposits: 0, withdrawals: 0, total: 0 };
      }
      
      if (transaction.category === 'DEP' || transaction.category === 'Deposit' || transaction.category === 'Investment') {
        breakdown[method].deposits += amount;
        breakdown[method].total += amount;
      } else if (transaction.category === 'WD' || transaction.category === 'Withdraw' || transaction.category === 'Withdrawal') {
        breakdown[method].withdrawals += amount;
        breakdown[method].total -= amount;
      }
    });
    
    return breakdown;
  };


  // Exchange Rate Edit Functions
  const openRateEditModal = (date: string, currentRate: number) => {
    setEditingDate(date);
    setEditingRate(currentRate.toString());
    setShowRateEditModal(true);
  };
  
  const closeRateEditModal = () => {
    setShowRateEditModal(false);
    setEditingDate('');
    setEditingRate('');
  };
  
  const handleFetchRate = () => {
    // Open calendar for date selection
    setShowCalendar(true);
    setSelectedCalendarDate(editingDate); // Pre-select current date
  };

  const handleCalendarDateSelect = async (selectedDate: string) => {
    if (!selectedDate) return;
    
    try {
      setRateEditLoading(true);
      setShowCalendar(false);
      
      // Fetch rate from yfinance for selected date
      const response = await api.post(`/exchange-rates/${selectedDate}/fetch`);
      
      if (response.ok) {
        const result = await api.parseResponse(response);
        if (result.success && result.data) {
          const fetchedRate = result.data.rate;
          setEditingRate(fetchedRate.toString());
          // Update the editing date to the selected date
          setEditingDate(selectedDate);
        } else {
          console.error('Failed to fetch rate from yfinance');
          alert(t('transactions.yfinance_failed'));
        }
      } else {
        console.error('Failed to fetch rate from yfinance');
        alert(t('transactions.yfinance_failed'));
      }
    } catch (err: any) {
      console.error('Error fetching rate from yfinance:', err);
      alert(t('transactions.yfinance_error'));
    } finally {
      setRateEditLoading(false);
    }
  };

  const handleRateSave = async () => {
    if (!editingDate || !editingRate) return;
    
    try {
      setRateEditLoading(true);
      
      // Validate rate
      const rateValue = parseFloat(editingRate);
      if (isNaN(rateValue) || rateValue <= 0) {
        alert(t('transactions.invalid_rate'));
        return;
      }
      
      // Optimistically update the local state for immediate UI feedback
      setDailyGrossBalances(prev => ({
        ...prev,
        [editingDate]: {
          ...prev[editingDate],
          rate: rateValue
        }
      }));
      
      // Call API to update rate
      const response = await api.put(`/exchange-rates/${editingDate}`, {
        rate: rateValue
      });
      
      if (response.ok) {
        const result = await api.parseResponse(response);
        console.log('Rate updated successfully:', result);
        
        // Refresh the transactions data
        await fetchTransactions();
        
        // Immediately refresh the daily gross balances to reflect the new rate
        await fetchDailyGrossBalances(transactions);
        
        closeRateEditModal();
        alert(t('transactions.rate_updated_success').replace('{date}', editingDate));
      } else {
        // Revert optimistic update on error
        await fetchDailyGrossBalances(transactions);
        const error = await api.parseResponse(response);
        alert(`${t('transactions.failed_update_rate')}: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error saving exchange rate:', error);
      // Revert optimistic update on error
      await fetchDailyGrossBalances(transactions);
      alert(t('transactions.failed_save_rate'));
    } finally {
      setRateEditLoading(false);
    }
  };

  // Daily Summary Functions
  const fetchDailySummary = async (date: string) => {
    try {
      setDailySummaryLoading(true);
      setSelectedDate(date);
      
      const response = await api.get(`/api/summary/${date}`);
      
      if (response.ok) {
        const data = await api.parseResponse(response) as any;
        console.log('🔍 Daily Summary Data Received:', data);
        console.log('🔍 PSP Summary Data:', data.psp_summary);
        console.log('🔍 Deposits/Withdrawals from Backend:', {
          total_deposits_tl: data.total_deposits_tl,
          total_withdrawals_tl: data.total_withdrawals_tl,
          total_deposits_usd: data.total_deposits_usd,
          total_withdrawals_usd: data.total_withdrawals_usd,
          transaction_count: data.transaction_count,
          unique_clients: data.unique_clients
        });
        
        // Normalize usd_rate - backend may return Decimal, convert to number
        const normalizedData: DailySummary = {
          ...data,
          usd_rate: data.usd_rate !== null && data.usd_rate !== undefined 
            ? (typeof data.usd_rate === 'number' ? data.usd_rate : Number(data.usd_rate))
            : null,
          // Ensure all numeric fields are numbers
          gross_balance_tl: data.gross_balance_tl !== undefined ? Number(data.gross_balance_tl) : undefined,
          gross_balance_usd: data.gross_balance_usd !== undefined ? Number(data.gross_balance_usd) : undefined,
          total_deposits_tl: data.total_deposits_tl !== undefined ? Number(data.total_deposits_tl) : 0,
          total_deposits_usd: data.total_deposits_usd !== undefined ? Number(data.total_deposits_usd) : 0,
          total_withdrawals_tl: data.total_withdrawals_tl !== undefined ? Number(data.total_withdrawals_tl) : 0,
          total_withdrawals_usd: data.total_withdrawals_usd !== undefined ? Number(data.total_withdrawals_usd) : 0,
        };
        
        console.log('🔍 Normalized Daily Summary Data:', {
          total_deposits_tl: normalizedData.total_deposits_tl,
          total_withdrawals_tl: normalizedData.total_withdrawals_tl,
          transaction_count: normalizedData.transaction_count
        });
        
        setDailySummaryData(normalizedData);
        setShowDailySummaryModal(true);
      } else {
        // Handle non-200 responses
        console.warn('⚠️ Daily Summary API returned non-OK status:', response.status);
        try {
          const errorData = await api.parseResponse(response);
          console.error('❌ Error data:', errorData);
        } catch (parseError) {
          console.error('❌ Failed to parse error response:', parseError);
        }
        
        // Create empty summary for dates without data
        const emptySummary: DailySummary = {
          date: date,
          date_str: new Date(date).toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          }),
          usd_rate: null,
          total_amount_tl: 0,
          total_amount_usd: 0,
          total_commission_tl: 0,
          total_commission_usd: 0,
          total_net_tl: 0,
          total_net_usd: 0,
          transaction_count: 0,
          unique_clients: 0,
          psp_summary: [],
          category_summary: [],
          payment_method_summary: [],
          transactions: []
        };
        setDailySummaryData(emptySummary);
        setShowDailySummaryModal(true);
      }
    } catch (error) {
      console.error('❌ Error fetching daily summary:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('❌ Error details:', errorMessage);
      
      // Show empty summary on error
      const emptySummary: DailySummary = {
        date: date,
        date_str: new Date(date).toLocaleDateString('en-US', { 
          weekday: 'long', 
          year: 'numeric', 
          month: 'long', 
          day: 'numeric' 
        }),
        usd_rate: null,
        total_amount_tl: 0,
        total_amount_usd: 0,
        total_commission_tl: 0,
        total_commission_usd: 0,
        total_net_tl: 0,
        total_net_usd: 0,
        transaction_count: 0,
        unique_clients: 0,
        psp_summary: [],
        category_summary: [],
        payment_method_summary: [],
        transactions: []
      };
      setDailySummaryData(emptySummary);
      setShowDailySummaryModal(true);
    } finally {
      setDailySummaryLoading(false);
    }
  };

  const closeDailySummaryModal = () => {
    setShowDailySummaryModal(false);
    setDailySummaryData(null);
    setSelectedDate('');
  };

  // Function to detect foreign currencies in daily transactions
  // const detectForeignCurrencies = (date: string): string[] => { ... }
  // Function to check if exchange rates are needed
  // const needsExchangeRates = (date: string): boolean => { ... }
  // Function to get missing exchange rates
  // const getMissingExchangeRates = (date: string): string[] => { ... }
  // Function to save exchange rates
  // const saveExchangeRates = async () => { ... }
  // Function to calculate amounts with exchange rates
  // const calculateAmountWithRates = (amount: number, currency: string): number => { ... }
  // Function to calculate daily metrics with exchange rates
  // const calculateDailyMetricsWithRates = (date: string) => { ... }

  // Chart data preparation functions
  const prepareTransactionVolumeData = () => {
    const monthlyData = transactions.reduce((acc, transaction) => {
      if (!transaction.date) return acc; // Skip transactions without dates
      
      const date = new Date(transaction.date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      
      if (!acc[monthKey]) {
        acc[monthKey] = {
          month: monthKey,
          deposits: 0,
          withdrawals: 0,
          net: 0,
          count: 0
        };
      }
      
      if (transaction.amount > 0) {
        acc[monthKey].deposits += transaction.amount;
      } else {
        acc[monthKey].withdrawals += Math.abs(transaction.amount);
      }
      acc[monthKey].net += transaction.amount;
      acc[monthKey].count += 1;
      
      return acc;
    }, {} as Record<string, any>);

    return Object.values(monthlyData)
      .sort((a, b) => a.month.localeCompare(b.month))
      .slice(-6); // Last 6 months
  };

  const preparePaymentMethodChartData = () => {
    const methodData = transactions.reduce((acc, transaction) => {
      const rawMethod = transaction.payment_method || 'Unknown';
      const method = normalizePaymentMethodName(rawMethod);
      if (!acc[method]) {
        acc[method] = { method, volume: 0, count: 0 };
      }
      acc[method].volume += Math.abs(transaction.amount);
      acc[method].count += 1;
      return acc;
    }, {} as Record<string, any>);

    return Object.values(methodData)
      .sort((a, b) => b.volume - a.volume)
      .slice(0, 5); // Top 5 methods
  };

  const prepareClientPerformanceData = () => {
    return clients
      .map(client => ({
        name: client.client_name,
        volume: client.total_amount,
        transactions: client.transaction_count,
        avgTransaction: client.avg_transaction,
        commission: client.total_commission
      }))
      .sort((a, b) => b.volume - a.volume)
      .slice(0, 10); // Top 10 clients
  };

  const prepareCurrencyDistributionData = () => {
    const currencyData = transactions.reduce((acc, transaction) => {
      const currency = transaction.currency || 'Unknown';
      if (!acc[currency]) {
        acc[currency] = { currency, volume: 0, count: 0 };
      }
      acc[currency].volume += Math.abs(transaction.amount);
      acc[currency].count += 1;
      return acc;
    }, {} as Record<string, any>);

    return Object.values(currencyData)
      .sort((a, b) => b.volume - a.volume);
  };

  const preparePSPPerformanceData = () => {
    const pspData = transactions.reduce((acc, transaction) => {
      const psp = transaction.psp || 'Unknown';
      if (!acc[psp]) {
        acc[psp] = { psp, volume: 0, count: 0, success: 0 };
      }
      acc[psp].volume += Math.abs(transaction.amount);
      acc[psp].count += 1;
      // Assume successful if amount is not zero
      if (transaction.amount !== 0) {
        acc[psp].success += 1;
      }
      return acc;
    }, {} as Record<string, any>);

    return Object.values(pspData)
      .map(item => ({
        ...item,
        successRate: item.count > 0 ? (item.success / item.count) * 100 : 0
      }))
      .sort((a, b) => b.volume - a.volume)
      .slice(0, 5); // Top 5 PSPs
  };

  // Chart colors
  const chartColors = {
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    light: '#f3f4f6',
    dark: '#1f2937'
  };

  const pieChartColors = [
    chartColors.primary,
    chartColors.secondary,
    chartColors.success,
    chartColors.warning,
    chartColors.danger,
    chartColors.info
  ];

  // Enhanced loading state
  if (authLoading) {
    return <ClientsPageSkeleton />;
  }

  // Error boundary for critical errors
  if (error && !clientsError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <AlertCircle className="h-16 w-16 mx-auto" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Application Error
          </h3>
          <p className="text-gray-600 mb-6">{error}</p>
          <Button
            variant="default"
            onClick={() => window.location.reload()}
            className="inline-flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Reload Page
          </Button>
        </div>
      </div>
    );
  }

  const fetchClientTransactions = async (clientName: string) => {
    if (clientTransactions[clientName]) return; // Already loaded
    
    setLoadingClientTransactions(prev => ({ ...prev, [clientName]: true }));
    
    try {
      const params = new URLSearchParams();
      params.append('client', clientName);
      params.append('per_page', '100'); // Get all transactions for this client
      
      const response = await api.get(`/transactions/?${params.toString()}`);
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data?.transactions) {
          setClientTransactions(prev => ({ ...prev, [clientName]: data.transactions }));
        }
      }
    } catch (error) {
      console.error('Error fetching client transactions:', error);
    } finally {
      setLoadingClientTransactions(prev => ({ ...prev, [clientName]: false }));
    }
  };

  const toggleClientExpansion = (clientName: string) => {
    const newExpanded = new Set(expandedClients);
    if (newExpanded.has(clientName)) {
      newExpanded.delete(clientName);
    } else {
      newExpanded.add(clientName);
      fetchClientTransactions(clientName);
    }
    setExpandedClients(newExpanded);
  };

  const renderGroupedTransactions = () => {
    // First, flatten all transactions from grouped data to apply display limit
    const allGroupedTransactions = groupTransactionsByDate(transactions);
    
    // Flatten transactions while preserving order
    let flattenedTransactions: Transaction[] = [];
    allGroupedTransactions.forEach(group => {
      flattenedTransactions = [...flattenedTransactions, ...group.transactions];
    });
    
    // Apply display limit
    const limitedTransactions = flattenedTransactions.slice(0, displayLimit);
    
    // Re-group the limited transactions
    const groupedTransactions = groupTransactionsByDate(limitedTransactions);

    if (groupedTransactions.length === 0) {
      return (
        <div className='p-8 text-center text-gray-500'>
          No transactions to group by date
        </div>
      );
    }

    return groupedTransactions.map((dateGroup, groupIndex) => (
      <div key={dateGroup.dateKey} className='border-b border-gray-100 last:border-b-0'>
        {/* Date Header - Professional & Minimal */}
        <div className='px-6 py-3 bg-slate-100 border-b border-slate-300'>
          <div className='flex items-center justify-between'>
            <div className='flex items-center gap-3'>
              {/* Simplified Icon */}
              <div className='w-8 h-8 bg-slate-700 rounded-lg flex items-center justify-center'>
                <Calendar className='h-4 w-4 text-white' />
              </div>
              
              <div className='space-y-0.5'>
                {/* Date Title - Reduced Size */}
                <div className='flex items-center gap-2'>
                  <h4 className='text-lg font-semibold text-slate-900 tracking-tight'>
                    {formatDateHeader(dateGroup.date)}
                  </h4>
                  <span className='inline-flex items-center px-2 py-0.5 text-xs font-medium text-slate-700 bg-slate-200 rounded'>
                    {new Date(dateGroup.date).toLocaleDateString('en-US', { weekday: 'short' })}
                  </span>
                </div>
                
                {/* Stats - Tabular Numbers */}
                <div className='flex items-center gap-3 text-sm tabular-nums'>
                  <div className='flex items-center gap-1.5 text-slate-700'>
                    <span className='font-medium'>{dateGroup.transactions.length}</span>
                    <span className='text-slate-600'>transaction{dateGroup.transactions.length !== 1 ? 's' : ''}</span>
                  </div>
                  <span className='text-slate-400'>|</span>
                  <div className='flex items-center gap-2 text-slate-700'>
                    {dateGroup.grossBalance && dateGroup.grossBalance.tl !== undefined ? (
                      // Show both TRY and USD from backend data with exchange rate
                      <div className='flex items-center gap-3 tabular-nums'>
                        <span className='font-medium text-slate-900'>{formatCurrency(dateGroup.grossBalance.tl, '₺')}</span>
                        <span className='text-slate-400'>|</span>
                        <span className='font-medium text-slate-900'>{formatCurrency(dateGroup.grossBalance.usd, '$')}</span>
                        {dateGroup.grossBalance.rate > 0 && (
                          <span className='text-xs text-slate-600'>
                            @{dateGroup.grossBalance.rate.toFixed(2)}
                          </span>
                        )}
                        <span className='text-slate-600 text-xs'>gross</span>
                      </div>
                    ) : (
                      // Fallback: Calculate using NEW USD-first logic (matching backend)
                      (() => {
                        // Step 1: Calculate net amounts for each currency
                        let tryNet = 0;
                        let usdNet = 0;
                        
                        dateGroup.transactions.forEach(t => {
                          const amount = t.amount || 0;
                          const isWithdrawal = t.category && t.category.toUpperCase() === 'WD';
                          const signedAmount = isWithdrawal ? -Math.abs(amount) : amount;
                          
                          // DEBUG: Log transaction details for September 30th
                          if (dateGroup.dateKey.includes('2025-09-30')) {
                            console.log('🔍 Transaction Debug:', {
                              client: t.client_name,
                              amount: amount,
                              netAmount: t.net_amount,
                              currency: t.currency,
                              category: t.category,
                              isWithdrawal: isWithdrawal,
                              signedAmount: signedAmount
                            });
                          }
                          
                          if (t.currency === 'TRY' || t.currency === 'TL') {
                            tryNet += signedAmount;
                          } else if (t.currency === 'USD') {
                            usdNet += signedAmount;
                          }
                        });
                        
                        // Step 2: Calculate USD Gross Balance FIRST
                        // Formula: (TRY_net / rate) + USD_net
                        const usdGross = (tryNet / currentUsdRate) + usdNet;
                        
                        // Step 3: Calculate TRY Gross Balance from USD
                        // Formula: USD_gross * rate
                        const tryGross = usdGross * currentUsdRate;
                        
                        // DEBUG: Log final calculation for September 30th
                        if (dateGroup.dateKey.includes('2025-09-30')) {
                          console.log('🔍 Final Calculation Debug:', {
                            tryNet: tryNet,
                            usdNet: usdNet,
                            currentUsdRate: currentUsdRate,
                            usdGross: usdGross,
                            tryGross: tryGross
                          });
                        }
                        
                        return (
                          <div className='flex items-center gap-3 tabular-nums'>
                            <span className='font-medium text-slate-900'>{formatCurrency(tryGross, '₺')}</span>
                            <span className='text-slate-400'>|</span>
                            <span className='font-medium text-slate-900'>{formatCurrency(usdGross, '$')}</span>
                            <span className='text-xs text-slate-600'>@{currentUsdRate.toFixed(2)}</span>
                            <span className='text-slate-600 text-xs'>calc</span>
                          </div>
                        );
                      })()
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Action Buttons - Simplified */}
            <div className='flex items-center gap-2'>
              <Button
                onClick={() => fetchDailySummary(dateGroup.date)}
                disabled={dailySummaryLoading}
                variant="outline"
                size="sm"
                className="inline-flex items-center gap-1.5"
              >
                <BarChart className='h-3.5 w-3.5' />
                {dailySummaryLoading && selectedDate === dateGroup.date ? 'Loading...' : 'Summary'}
              </Button>
              
              {/* Quick Edit Rate Button */}
              {/* Show Edit Rate button if we have gross balance data with rate OR if we have transactions for this date (especially USD transactions) */}
              {(dateGroup.grossBalance && dateGroup.grossBalance.rate > 0) || 
               (dateGroup.transactions && dateGroup.transactions.length > 0 && 
                dateGroup.transactions.some((t: Transaction) => t.currency === 'USD' || t.currency === 'EUR')) ? (
                <Button
                  onClick={() => openRateEditModal(
                    dateGroup.date, 
                    dateGroup.grossBalance?.rate || currentUsdRate || 48.0
                  )}
                  variant="outline"
                  size="sm"
                  className="inline-flex items-center gap-1.5"
                  title={`Edit exchange rate for ${dateGroup.date}`}
                >
                  <Edit className='h-3.5 w-3.5' />
                  Edit Rate
                </Button>
              ) : null}
            </div>
          </div>
        </div>

        {/* Transactions Table for this date */}
        <div className='overflow-x-auto border border-gray-200 rounded-lg bg-white shadow-sm'>
          <table className='min-w-full divide-y divide-gray-200' style={{ borderCollapse: 'separate', borderSpacing: 0 }}>
            <thead className='bg-gray-50 sticky top-0 z-10 shadow-sm'>
              <tr>
                <th className='px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200'>
                  Client
                </th>
                <th className='px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200'>
                  Company
                </th>

                <th className='px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200'>
                  Payment Method
                </th>
                <th className='px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200'>
                  Category
                </th>
                <th className='px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200 tabular-nums'>
                  Amount
                </th>
                <th className='px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200 tabular-nums'>
                  Commission
                </th>
                <th className='px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200 tabular-nums'>
                  Net Amount
                </th>
                <th className='px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200'>
                  Currency
                </th>
                <th className='px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200'>
                  PSP
                </th>
                <th className='px-6 py-4 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider w-1/12 border-b border-gray-200'>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className='bg-white divide-y divide-gray-200'>
              {dateGroup.transactions.map((transaction) => (
                <TransactionRow
                  key={transaction.id}
                  transaction={transaction}
                  onView={handleViewTransaction}
                  onEdit={handleEditTransaction}
                  onDelete={handleDeleteTransaction}
                  normalizePaymentMethodName={normalizePaymentMethodName}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    ));
  };

  // Template download function
  const downloadTemplate = (type: 'essential' | 'full', format: 'csv' | 'xlsx') => {
    if (type === 'essential') {
      if (format === 'csv') {
        // Download essential CSV template
        const csvContent = `Client,Company,Payment Method,Category,Amount,Currency,PSP,Date
John Doe,ABC Corporation,Credit Card,DEP,1000.50,USD,Stripe,2025-08-18
Jane Smith,XYZ Ltd,Bank Transfer,WIT,2500.00,EUR,PayPal,2025-08-19
Mike Johnson,Global Inc,TR1122334455,Wire Transfer,DEP,5000.00,GBP,Bank of America,2025-08-20`;
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'essential_transaction_template.csv';
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        // Download essential Excel template
        const essentialData = [
          ['Client', 'Company', 'Payment Method', 'Category', 'Amount', 'Currency', 'PSP', 'Date'],
          ['John Doe', 'ABC Corporation', 'Credit Card', 'DEP', 1000.50, 'USD', 'Stripe', '2025-08-18'],
          ['Jane Smith', 'XYZ Ltd', 'Bank Transfer', 'WIT', 2500.00, 'EUR', 'PayPal', '2025-08-19'],
          ['Mike Johnson', 'Global Inc', 'TR1122334455', 'Wire Transfer', 'DEP', 5000.00, 'GBP', 'Bank of America', '2025-08-20']
        ];
        
        const worksheet = XLSX.utils.aoa_to_sheet(essentialData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Transactions');
        
        XLSX.writeFile(workbook, 'essential_transaction_template.xlsx');
      }
    } else {
      if (format === 'csv') {
        // Download full CSV template
        const csvContent = `Client,Company,Payment Method,Category,Amount,Commission,Net Amount,Currency,PSP,Date,Notes
John Doe,ABC Corporation,Credit Card,DEP,1000.50,25.00,975.50,USD,Stripe,2025-08-18,Monthly payment
Jane Smith,XYZ Ltd,Bank Transfer,WIT,2500.00,50.00,2450.00,EUR,PayPal,2025-08-19,Quarterly transfer
Mike Johnson,Global Inc,TR1122334455,Wire Transfer,DEP,5000.00,100.00,4900.00,GBP,Bank of America,2025-08-20,Annual deposit`;
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'full_transaction_template.csv';
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        // Download full Excel template
        const fullData = [
          ['Client', 'Company', 'Payment Method', 'Category', 'Amount', 'Commission', 'Net Amount', 'Currency', 'PSP', 'Date', 'Notes'],
          ['John Doe', 'ABC Corporation', 'Credit Card', 'DEP', 1000.50, 25.00, 975.50, 'USD', 'Stripe', '2025-08-18', 'Monthly payment'],
          ['Jane Smith', 'XYZ Ltd', 'Bank Transfer', 'WIT', 2500.00, 50.00, 2450.00, 'EUR', 'PayPal', '2025-08-19', 'Quarterly transfer'],
          ['Mike Johnson', 'Global Inc', 'TR1122334455', 'Wire Transfer', 'DEP', 5000.00, 100.00, 4900.00, 'GBP', 'Bank of America', '2025-08-20', 'Annual deposit']
        ];
        
        const worksheet = XLSX.utils.aoa_to_sheet(fullData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Transactions');
        
        XLSX.writeFile(workbook, 'full_transaction_template.xlsx');
      }
    }
  };

  // Handle tab change with custom logic
  const handleTabChange = (value: string) => {
    const newTab = value as 'overview' | 'transactions' | 'analytics' | 'clients';
    console.log('🔄 Clients page - Tab change:', newTab, 'Previous tab:', activeTab);
    
    // Call the base handler from the hook (handles localStorage and URL persistence)
    handleTabChangeBase(value);
    
    // Reset display limit when navigating away from transactions tab
    if (activeTab === 'transactions' && newTab !== 'transactions') {
      console.log('🔄 Resetting display limit to 100');
      setDisplayLimit(100);
    }
  };

  // Handle Load More button click
  const handleLoadMore = async () => {
    if (loadMoreState.loading) return;
    
    console.log('🔄 Clients page - Load More clicked', {
      currentDisplayLimit: displayLimit,
      totalTransactions: transactions.length,
      needsFetch: displayLimit >= transactions.length
    });
    
    // First, increase display limit
    const newDisplayLimit = displayLimit + 100;
    setDisplayLimit(newDisplayLimit);
    
    // If we've displayed all loaded transactions and there might be more on server, fetch more
    if (newDisplayLimit >= transactions.length && loadMoreState.hasMore) {
      setLoadMoreState(prev => ({ ...prev, loading: true }));
      
      try {
        await fetchTransactionsData(false, true);
      } catch (error) {
        console.error('❌ Error loading more transactions:', error);
      } finally {
        setLoadMoreState(prev => ({ ...prev, loading: false }));
      }
    }
  };

  // Handle page change with loading state (kept for compatibility)
  const handlePageChange = (newPage: number) => {
    console.log('🔄 Clients page - Page change:', newPage);
    // This function is kept for compatibility but Load More is now used instead
    console.log('⚠️ Page change not supported with Load More functionality');
  };

  // Handle items per page change
  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    console.log('🔄 Clients page - Items per page change:', newItemsPerPage);
    // Update load more state with new items per page
    setLoadMoreState(prev => ({ 
      ...prev, 
      itemsPerLoad: newItemsPerPage,
      currentOffset: 0,
      hasMore: true,
      oldestDate: null
    }));
  };

  // Loading state
  if (loading) {
    return (
      <div className='min-h-screen flex items-center justify-center bg-gray-50'>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto'></div>
          <p className='mt-4 text-gray-600'>Loading clients...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">

      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Users className="h-8 w-8 text-gray-600" />
              {t('clients.title')}
              </h1>
              <p className="text-gray-600">{t('clients.description')}</p>
            </div>
            <div className="flex items-center gap-3">
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={handleExportAllTransactions}
                disabled={exporting}
                icon={exporting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                ) : (
                  <Download className="h-4 w-4" />
                )}
                iconPosition="left"
                className="bg-blue-50 border-blue-300 text-blue-700 hover:bg-blue-100"
              >
                {exporting ? t('common.loading') : t('clients.export_all_transactions')}
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={triggerFileInput}
                disabled={importing}
                icon={<Upload className="h-4 w-4" />}
                iconPosition="left"
                className="bg-green-50 border-green-300 text-green-700 hover:bg-green-100"
              >
                {importing ? t('common.loading') : t('clients.import')}
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => setShowPasteImport(true)}
                disabled={importing}
                icon={<FileText className="h-4 w-4" />}
                iconPosition="left"
                className="bg-purple-50 border-purple-300 text-purple-700 hover:bg-purple-100"
              >
                Paste & Import
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => setShowImportGuide(true)}
                icon={<Info className="h-4 w-4" />}
                iconPosition="left"
                className="bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100"
              >
                {t('clients.guide')}
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => setShowBulkDeleteModal(true)}
                icon={<Trash2 className="h-4 w-4" />}
                iconPosition="left"
                className="bg-red-50 border-red-300 text-red-700 hover:bg-red-100"
              >
                {t('clients.bulk')}
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => {
                  // BRate functionality removed - button kept for visual consistency
                }}
                icon={<TrendingUp className="h-4 w-4" />}
                iconPosition="left"
                className="bg-gray-50 border-gray-300 text-gray-500 cursor-not-allowed opacity-60"
                disabled
              >
                {t('clients.brate')}
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    console.log('🔄 Starting data refresh...');
                    
                    // Refresh all data from database sequentially to avoid conflicts
                    console.log('📊 Fetching clients...');
                    await fetchClients();
                    
                    console.log('💳 Fetching transactions...');
                    await fetchTransactions();
                    
                    console.log('🏦 Refreshing PSP data...');
                    await refreshPSPData();
                    
                    console.log('✅ Data refreshed successfully');
                    alert(t('transactions.data_refreshed'));
                  } catch (error: unknown) {
                    console.error('❌ Error refreshing data:', error);
                    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
                    console.error('❌ Error details:', errorMessage);
                    alert(`${t('transactions.error_refreshing_data')}: ${errorMessage}`);
                  }
                }}
                icon={<RefreshCw className="h-4 w-4" />}
                iconPosition="left"
                className="bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100"
              >
                {t('clients.fetch')}
              </UnifiedButton>
              <UnifiedButton
                variant="primary"
                size="sm"
                onClick={() => navigate('/transactions/add')}
                icon={<Plus className="h-4 w-4" />}
                iconPosition="left"
              >
                {t('clients.add_transaction')}
              </UnifiedButton>
            </div>
          </div>
        </div>

      <div className="space-y-6">

      

      {/* Status Indicators */}
      <div className="bg-gray-50/50 border border-gray-200/60 rounded-xl p-4">
        <div className='flex items-center gap-6 text-sm text-gray-700'>
          <div className='flex items-center gap-2'>
            <div className='w-2 h-2 bg-green-500 rounded-full'></div>
                            <span className="font-medium">{t('dashboard.active_clients')}: {clients.length}</span>
          </div>
          <div className='flex items-center gap-2'>
            <div className='w-2 h-2 bg-gray-400 rounded-full'></div>
            <span className="font-medium">{t('clients.total_volume')}: {formatCurrency(totalVolume, '₺')}</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-gray-50/80 border border-gray-200/60 rounded-lg shadow-sm">
          <TabsTrigger value="overview" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:border data-[state=active]:border-gray-200">
            <BarChart3 className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('tabs.overview')}</span>
          </TabsTrigger>
          <TabsTrigger value="clients" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:border data-[state=active]:border-gray-200">
            <Users className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('navigation.clients')}</span>
          </TabsTrigger>
          <TabsTrigger value="transactions" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:border data-[state=active]:border-gray-200">
            <FileText className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('navigation.transactions')}</span>
          </TabsTrigger>
          <TabsTrigger value="analytics" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:border data-[state=active]:border-gray-200">
            <LineChart className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('tabs.analytics')}</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab Content */}
        <TabsContent value="overview" className="mt-6">
          {/* Professional Financial Metrics Section */}
          <div className="mb-6">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-gray-600" />
                {t('clients.financial_overview')}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {t('clients.key_financial_metrics')}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <MetricCard
                title={t('ledger.total_deposits')}
                value={formatCurrency(dashboardFinancialData?.total_deposits || totalDeposits, '₺')}
                subtitle={t('clients.all_dep_transactions')}
                icon={TrendingUp}
                color="green"
                animated={true}
                animationDuration={500}
                showGlass={true}
              />
              
              <MetricCard
                title={t('ledger.total_withdrawals')}
                value={formatCurrency(Math.abs(dashboardFinancialData?.total_withdrawals || totalWithdrawals), '₺')}
                subtitle={t('clients.all_wd_transactions')}
                icon={TrendingDown}
                color="red"
                animated={true}
                animationDuration={500}
                showGlass={true}
              />
              
              <MetricCard
                title={t('dashboard.net_cash')}
                value={formatCurrency((dashboardFinancialData?.total_deposits || totalDeposits) - (dashboardFinancialData?.total_withdrawals || totalWithdrawals), '₺')}
                subtitle={t('clients.all_transactions_net')}
                icon={DollarSign}
                color={((dashboardFinancialData?.total_deposits || totalDeposits) - (dashboardFinancialData?.total_withdrawals || totalWithdrawals)) >= 0 ? "gray" : "red"}
                animated={true}
                animationDuration={500}
              />
              
              <MetricCard
                title={t('dashboard.total_commissions')}
                value={formatCurrency(dashboardFinancialData?.total_commission || totalCommissions, '₺')}
                subtitle={t('clients.all_transactions_commission')}
                icon={FileText}
                color="purple"
                animated={true}
                animationDuration={500}
              />
            </div>
          </div>

          {/* Client Distribution and Top Performers - ENHANCED */}
          <div className="mb-6">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Users className="h-5 w-5 text-gray-600" />
                {t('clients.client_insights')}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {t('clients.distribution_top_performers')}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Client Distribution Card */}
              <UnifiedCard variant="elevated" className="relative overflow-hidden">
                <div className="absolute top-4 right-4 w-20 h-20 bg-gray-100 rounded-full opacity-20" />
                <CardContent className="p-6 relative">
                  <div className="flex items-start gap-4">
                    <div className="bg-gray-100 p-3 rounded-lg">
                      <Users className="h-6 w-6 text-gray-700" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-gray-600 mb-2">Client Distribution</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-2">
                        {clientsSummary?.total_clients || clients.length}
                      </div>
                      <p className="text-sm text-gray-500 mb-4">
                        {clientsSummary?.multi_currency_count || clients.filter(c => Array.isArray(c.currencies) && c.currencies.length > 1).length} multi-currency
                      </p>
                      
                      {/* New Metrics */}
                      <div className="space-y-2 pt-3 border-t border-gray-100">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-600 flex items-center gap-1">
                            <TrendingUp className="h-3 w-3" />
                            New This Month
                          </span>
                          <span className="text-sm font-semibold text-emerald-600">
                            +{clientsSummary?.new_clients_this_month || 0}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-600 flex items-center gap-1">
                            <DollarSign className="h-3 w-3" />
                            Avg Transaction
                          </span>
                          <span className="text-sm font-semibold text-gray-700">
                            {formatCurrency(clientsSummary?.avg_transaction_value || 0, '₺')}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </UnifiedCard>

              {/* Top Performers Card */}
              <UnifiedCard variant="elevated" className="relative overflow-hidden">
                <div className="absolute top-4 right-4 w-20 h-20 bg-purple-100 rounded-full opacity-20" />
                <CardContent className="p-6 relative">
                  <div className="flex items-start gap-4">
                    <div className="bg-purple-100 p-3 rounded-lg">
                      <Award className="h-6 w-6 text-purple-700" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-gray-600 mb-2">Top Performers</h3>
                      <div className="text-2xl font-bold text-gray-900 mb-1 truncate">
                        {clientsSummary?.most_active?.client_name || (clients.length > 0 ? clients.reduce((max, client) => client.transaction_count > max.transaction_count ? client : max).client_name : 'N/A')}
                      </div>
                      <p className="text-sm text-gray-500 mb-4">
                        Most transactions: {clientsSummary?.most_active?.transaction_count || (clients.length > 0 ? clients.reduce((max, client) => client.transaction_count > max.transaction_count ? client : max).transaction_count : 0)} txns
                      </p>
                      
                      {/* New Metrics */}
                      <div className="space-y-2 pt-3 border-t border-gray-100">
                        <div className="flex items-center justify-between">
                          <div className="flex flex-col">
                            <span className="text-xs text-gray-600 flex items-center gap-1">
                              <TrendingUp className="h-3 w-3" />
                              Top by Volume
                            </span>
                            <span className="text-xs font-medium text-gray-800 mt-0.5 truncate max-w-[120px]">
                              {clientsSummary?.top_by_volume?.client_name || 'N/A'}
                            </span>
                          </div>
                          <span className="text-sm font-semibold text-emerald-600">
                            {formatCurrency(clientsSummary?.top_by_volume?.total_amount || 0, '₺')}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex flex-col">
                            <span className="text-xs text-gray-600 flex items-center gap-1">
                              <Star className="h-3 w-3" />
                              Highest Commission
                            </span>
                            <span className="text-xs font-medium text-gray-800 mt-0.5 truncate max-w-[120px]">
                              {clientsSummary?.top_by_commission?.client_name || 'N/A'}
                            </span>
                          </div>
                          <span className="text-sm font-semibold text-purple-600">
                            {formatCurrency(clientsSummary?.top_by_commission?.total_commission || 0, '₺')}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </UnifiedCard>
            </div>
          </div>


        </TabsContent>

        <TabsContent value="transactions" className="mt-6">
          {/* Transactions Header Section */}
          <UnifiedCard>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div>
                    <CardTitle className="flex items-center gap-3">
                      Transaction Management
                      <UnifiedBadge variant="secondary" size="sm" className="bg-gray-100 text-gray-800">
                        Enhanced Filters Available
                      </UnifiedBadge>
                    </CardTitle>
              <CardDescription>All transaction records</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {/* Prominent Filter Button */}
                  <UnifiedButton
                    variant={showFilters ? "primary" : "outline"}
                    onClick={() => setShowFilters(!showFilters)}
                    icon={<Filter className="h-4 w-4" />}
                    className={`transition-all duration-200 ${
                      showFilters 
                        ? 'bg-gray-600 hover:bg-gray-700 text-white shadow-lg' 
                        : 'border-gray-300 text-gray-600 hover:bg-gray-50 hover:border-gray-400'
                    }`}
                  >
                    {showFilters ? 'Hide Filters' : `Show Filters${getActiveFilterCount() > 0 ? ` (${getActiveFilterCount()})` : ''}`}
                  </UnifiedButton>
                </div>
              </div>
            </CardHeader>
            <CardContent>
            
            {/* Comprehensive Filter Card */}
            {showFilters && (
              <div className="mb-6 animate-in slide-in-from-top-4 duration-300">
                <TransactionFilterPanel
                  filters={filters}
                  dropdownOptions={dropdownOptions}
                  expandedFilterSections={expandedFilterSections}
                  displayLimit={displayLimit}
                  transactionsLength={transactions.length}
                  exporting={exporting}
                  onFilterChange={handleFilterChange}
                  onToggleFilterSection={toggleFilterSection}
                  onClearAllFilters={clearAllFilters}
                  onApplyFilters={() => {
                    setLoadMoreState(prev => ({ ...prev, currentOffset: 0, hasMore: true, oldestDate: null }));
                    fetchTransactions();
                  }}
                  onExportDisplayed={handleExportDisplayedTransactions}
                  onExportAll={handleExportAllTransactions}
                  onApplyQuickFilter={applyQuickFilter}
                />
              </div>
            )}
            {/* Legacy filter code removed - using TransactionFilterPanel component above */}
            {loading ? (
              <div className='p-12 text-center'>
                <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-gray-600 mx-auto mb-4'></div>
                <p className='text-gray-600 text-lg'>Loading transactions...</p>
              </div>
            ) : error ? (
              <div className='p-12 text-center'>
                <div className='text-red-500 mb-4'>
                  <AlertCircle className='h-16 w-16 mx-auto' />
                </div>
                <h3 className='text-xl font-semibold text-gray-900 mb-2'>
                  Error Loading Transactions
                </h3>
                <p className='text-gray-600 mb-6'>{error}</p>
                <Button
                  variant="default"
                  onClick={fetchTransactions}
                  className="flex items-center gap-2"
                >
                  Try Again
                </Button>
              </div>
            ) : transactions.length === 0 ? (
              <div className='p-12 text-center'>
                <div className='text-gray-400 mb-4'>
                  <FileText className='h-16 w-16 mx-auto' />
                </div>
                <h3 className='text-xl font-semibold text-gray-900 mb-2'>
                  No Transactions Found
                </h3>
                <p className='text-gray-600'>
                  No transactions are currently available.
                </p>
              </div>
            ) : (
              <div className='overflow-x-auto'>
                {renderGroupedTransactions()}

                {/* Summary Footer */}
                <div className='px-6 py-4 border-t border-gray-200 bg-gray-50'>
                  <div className='flex items-center justify-between text-sm text-gray-700'>
                    <div className='flex items-center gap-4'>
                      <span className='font-medium'>
                        {transactions.length} {t('dashboard.total_transactions').toLowerCase()}
                      </span>
                      <span className='text-gray-500'>
                        across {groupTransactionsByDate(transactions).length} date{groupTransactionsByDate(transactions).length !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <span className='font-semibold text-gray-900'>
                      Total: {formatCurrency(
                        transactions.reduce((sum, t) => sum + (t.amount || 0), 0),
                        'TL'
                      )}
                    </span>
                  </div>
                </div>

                {/* Pagination Info & Load More Section */}
                <div className="border-t border-gray-200 bg-gradient-to-b from-white to-gray-50">
                  {/* Pagination Stats */}
                  <div className="px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-gray-500" />
                          <span className="text-sm font-medium text-gray-700">
                            Showing {transactions.length.toLocaleString()} {transactions.length === 1 ? 'transaction' : 'transactions'}
                          </span>
                        </div>
                        {loadMoreState.total > 0 && (
                          <div className="flex items-center gap-2">
                            <BarChart className="h-4 w-4 text-blue-500" />
                            <span className="text-sm text-gray-600">
                              Total: <span className="font-semibold text-gray-900">{loadMoreState.total.toLocaleString()}</span>
                            </span>
                          </div>
                        )}
                        {loadMoreState.oldestDate && (
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-purple-500" />
                            <span className="text-sm text-gray-600">
                              Oldest: <span className="font-semibold text-gray-900">{new Date(loadMoreState.oldestDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-3">
                        {/* Display Info */}
                        <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                          Displaying: {Math.min(displayLimit, transactions.length)}/{transactions.length} | 
                          hasMore: {loadMoreState.hasMore ? 'true' : 'false'} | 
                          Total: {loadMoreState.total}
                        </div>
                        
                        {displayLimit < transactions.length && (
                          <div className="flex items-center gap-2 bg-blue-50 px-3 py-1.5 rounded-lg">
                            <div className="flex items-center gap-1.5">
                              <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                              <span className="text-xs font-medium text-blue-700">
                                {Math.round((displayLimit / transactions.length) * 100)}% displayed
                              </span>
                            </div>
                            <div className="w-24 h-1.5 bg-blue-100 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-blue-500 rounded-full transition-all duration-300"
                                style={{ width: `${Math.min((displayLimit / transactions.length) * 100, 100)}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Load More Button */}
                  {(() => {
                    // Show button if there are more transactions to display (either already loaded or on server)
                    const hasMoreToDisplay = displayLimit < transactions.length;
                    const hasMoreOnServer = loadMoreState.hasMore;
                    const showButton = hasMoreToDisplay || hasMoreOnServer;
                    
                    console.log('🔍 Load More Debug:', {
                      displayLimit,
                      transactionsLength: transactions.length,
                      hasMoreToDisplay,
                      hasMoreOnServer,
                      showButton,
                      loading: loadMoreState.loading
                    });
                    
                    return showButton;
                  })() && (
                    <div className="flex justify-center pb-6 px-6">
                      <UnifiedButton
                        variant="outline"
                        size="lg"
                        onClick={handleLoadMore}
                        disabled={loadMoreState.loading}
                        icon={loadMoreState.loading ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        ) : (
                          <RefreshCw className="h-4 w-4" />
                        )}
                        iconPosition="left"
                        className="min-w-[280px] border-blue-200 text-blue-700 hover:bg-blue-50 hover:border-blue-300 transition-all duration-200 shadow-sm hover:shadow-md"
                      >
                        {loadMoreState.loading ? (
                          <span>Loading older transactions...</span>
                        ) : (
                          <span>Load {loadMoreState.itemsPerLoad} More Transactions</span>
                        )}
                      </UnifiedButton>
                    </div>
                  )}
                  
                  {/* All Loaded Status */}
                  {!loadMoreState.hasMore && transactions.length > 0 && (
                    <div className="flex justify-center pb-6 px-6">
                      <div className="flex items-center gap-3 bg-green-50 border border-green-200 text-green-700 px-6 py-3 rounded-lg shadow-sm">
                        <CheckCircle className="h-5 w-5" />
                        <span className="font-medium">
                          All transactions loaded ({transactions.length.toLocaleString()} total)
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            </CardContent>
          </UnifiedCard>

        </TabsContent>

        <TabsContent value="analytics" className="mt-6">
          {/* Analytics Dashboard Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
                <p className="text-gray-600 mt-1">Comprehensive insights and performance metrics</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-gray-700">Live Data</span>
                </div>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export Report
                </Button>
              </div>
            </div>
          </div>

          {/* Key Metrics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Total Revenue */}
            <UnifiedCard className="hover:shadow-lg transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{t('clients.total_revenue')}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {formatCurrency(
                        clients.reduce((sum, client) => sum + client.total_amount, 0),
                        '₺'
                      )}
                    </p>
                    <p className="text-sm text-green-600 mt-1 flex items-center">
                      <TrendingUp className="h-4 w-4 mr-1" />
                      +12.5% from last month
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                    <DollarSign className="h-6 w-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </UnifiedCard>

            {/* Active Clients */}
            <UnifiedCard className="hover:shadow-lg transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{t('clients.active_clients')}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {clients.filter(client => client.transaction_count > 0).length}
                    </p>
                    <p className="text-sm text-blue-600 mt-1 flex items-center">
                      <Users className="h-4 w-4 mr-1" />
                      {clients.length} total clients
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Users className="h-6 w-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </UnifiedCard>

            {/* Average Transaction */}
            <UnifiedCard className="hover:shadow-lg transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{t('clients.avg_transaction')}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {formatCurrency(
                        clients.reduce((sum, client) => sum + client.total_amount, 0) / 
                        clients.reduce((sum, client) => sum + client.transaction_count, 0) || 0,
                        '₺'
                      )}
                    </p>
                    <p className="text-sm text-purple-600 mt-1 flex items-center">
                      <BarChart3 className="h-4 w-4 mr-1" />
                      Per transaction
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                    <BarChart3 className="h-6 w-6 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </UnifiedCard>

            {/* Commission Earned */}
            <UnifiedCard className="hover:shadow-lg transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{t('clients.commission')}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {formatCurrency(
                        clients.reduce((sum, client) => sum + client.total_commission, 0),
                        '₺'
                      )}
                    </p>
                    <p className="text-sm text-orange-600 mt-1 flex items-center">
                      <CreditCard className="h-4 w-4 mr-1" />
                      8.5% avg rate
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                    <CreditCard className="h-6 w-6 text-orange-600" />
                  </div>
                </div>
              </CardContent>
            </UnifiedCard>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Transaction Volume Trend */}
            <UnifiedCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LineChart className="h-5 w-5 text-blue-600" />
                  Transaction Volume Trend
                </CardTitle>
                <CardDescription>Monthly deposits and withdrawals over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsLineChart data={prepareTransactionVolumeData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                      <XAxis 
                        dataKey="month" 
                        stroke="#6b7280"
                        fontSize={12}
                        tickFormatter={(value) => {
                          const [year, month] = value.split('-');
                          return `${month}/${year.slice(2)}`;
                        }}
                      />
                      <YAxis 
                        stroke="#6b7280"
                        fontSize={12}
                        tickFormatter={(value) => formatCurrency(value, '₺')}
                      />
                      <Tooltip 
                        formatter={(value: any) => [formatCurrency(value, '₺'), '']}
                        labelFormatter={(label) => {
                          const [year, month] = label.split('-');
                          return `${month}/${year}`;
                        }}
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="deposits" 
                        stroke="#10b981" 
                        strokeWidth={3}
                        dot={{ fill: "#10b981", strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6, stroke: "#10b981", strokeWidth: 2 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="withdrawals" 
                        stroke="#ef4444" 
                        strokeWidth={3}
                        dot={{ fill: "#ef4444", strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6, stroke: "#ef4444", strokeWidth: 2 }}
                      />
                    </RechartsLineChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex items-center justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-gray-600">Deposits</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <span className="text-sm text-gray-600">Withdrawals</span>
                  </div>
                </div>
              </CardContent>
            </UnifiedCard>

            {/* Payment Method Distribution */}
            <UnifiedCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChartIcon className="h-5 w-5 text-purple-600" />
                  Payment Method Distribution
                </CardTitle>
                <CardDescription>Volume breakdown by payment method</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <Pie
                        data={preparePaymentMethodChartData()}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        paddingAngle={5}
                        dataKey="volume"
                      >
                        {preparePaymentMethodChartData().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={pieChartColors[index % pieChartColors.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value: any) => [formatCurrency(value, '₺'), 'Volume']}
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Legend 
                        verticalAlign="bottom" 
                        height={36}
                        formatter={(value) => <span className="text-sm text-gray-700">{value}</span>}
                      />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </UnifiedCard>
          </div>

          {/* Performance Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Top Clients Performance */}
            <UnifiedCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-green-600" />
                  Top Client Performance
                </CardTitle>
                <CardDescription>Volume by client ranking</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsBarChart data={prepareClientPerformanceData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                      <XAxis 
                        dataKey="name" 
                        stroke="#6b7280"
                        fontSize={10}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        tickFormatter={(value) => value.length > 12 ? value.substring(0, 12) + '...' : value}
                      />
                      <YAxis 
                        stroke="#6b7280"
                        fontSize={12}
                        tickFormatter={(value) => formatCurrency(value, '₺')}
                      />
                      <Tooltip 
                        formatter={(value: any) => [formatCurrency(value, '₺'), 'Volume']}
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Bar 
                        dataKey="volume" 
                        fill="#3b82f6"
                        radius={[4, 4, 0, 0]}
                      />
                    </RechartsBarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </UnifiedCard>

            {/* Currency Distribution */}
            <UnifiedCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5 text-blue-600" />
                  Currency Distribution
                </CardTitle>
                <CardDescription>Volume breakdown by currency</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsBarChart data={prepareCurrencyDistributionData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                      <XAxis 
                        dataKey="currency"
                        stroke="#6b7280"
                        fontSize={12}
                      />
                      <YAxis 
                        stroke="#6b7280"
                        fontSize={12}
                        tickFormatter={(value) => formatCurrency(value, '₺')}
                      />
                      <Tooltip 
                        formatter={(value: any) => [formatCurrency(value, '₺'), 'Volume']}
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Bar 
                        dataKey="volume" 
                        fill="#8b5cf6"
                        radius={[4, 4, 0, 0]}
                      />
                    </RechartsBarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </UnifiedCard>
          </div>

      </TabsContent>

      <TabsContent value="clients" className="mt-6">
          {/* Clients Table */}
          <div className='bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden'>
            <div className='px-8 py-6 border-b border-gray-100'>
              <div className='flex items-center justify-between'>
                <div className='flex items-center gap-3'>
                  <div className='w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center'>
                    <Users className='w-5 h-5 text-gray-600' />
                  </div>
                  <div>
                    <h2 className='text-xl font-semibold text-gray-900'>Client Information</h2>
                    <p className='text-sm text-gray-500'>Manage your client relationships and details</p>
                  </div>
                </div>
                <div className='flex items-center gap-3'>
                  <Button
                    onClick={() => setShowAddModal(true)}
                    className='bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center gap-2'
                  >
                    <Plus className='w-4 h-4' />
                    Add Client
                  </Button>
                </div>
              </div>
            </div>
            <div className='p-8'>
              {loading ? (
                <div className='flex items-center justify-center py-12'>
                  <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600'></div>
                </div>
              ) : (
                <div className='overflow-x-auto'>
                  <table className='w-full'>
                    <thead>
                      <tr className='border-b border-gray-100'>
                        <th className='text-left py-3 px-4 font-medium text-gray-600'>Client</th>
                        <th className='text-left py-3 px-4 font-medium text-gray-600'>Company</th>
                        <th className='text-left py-3 px-4 font-medium text-gray-600'>{t('clients.total_amount')}</th>
                        <th className='text-left py-3 px-4 font-medium text-gray-600'>Transactions</th>
                        <th className='text-left py-3 px-4 font-medium text-gray-600'>Last Transaction</th>
                        <th className='text-left py-3 px-4 font-medium text-gray-600'>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {clients.map((client, index) => (
                        <React.Fragment key={index}>
                          <tr className='border-b border-gray-50 hover:bg-gray-50 hover:scale-[1.01] transition-all duration-300 ease-in-out cursor-pointer'>
                            <td className='py-4 px-4'>
                              <div className='flex items-center gap-3'>
                                <div className='w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center'>
                                  <span className='text-sm font-medium text-gray-600'>
                                    {client.client_name.charAt(0).toUpperCase()}
                                  </span>
                                </div>
                                <div>
                                  <div className='font-medium text-gray-900'>{client.client_name}</div>
                                  <div className='text-sm text-gray-500'>{client.company_name || 'N/A'}</div>
                                </div>
                              </div>
                            </td>
                            <td className='py-4 px-4'>
                              <div className='text-sm text-gray-900'>{client.company_name || 'N/A'}</div>
                            </td>
                            <td className='py-4 px-4'>
                              <div className='text-sm font-medium text-gray-900'>
                                {formatCurrency(client.total_amount, 'TL')}
                              </div>
                            </td>
                            <td className='py-4 px-4'>
                              <div className='text-sm text-gray-600'>{client.transaction_count}</div>
                            </td>
                            <td className='py-4 px-4'>
                              <div className='text-sm text-gray-600'>
                                {client.last_transaction ? 
                                  new Date(client.last_transaction).toLocaleDateString() : 
                                  'N/A'
                                }
                              </div>
                            </td>
                            <td className='py-4 px-4'>
                              <div className='flex items-center gap-2'>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleViewClient(client)}
                                  className='text-gray-600 hover:text-gray-700'
                                >
                                  <Eye className='w-4 h-4' />
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleEditClient(client)}
                                  className='text-green-600 hover:text-green-700'
                                >
                                  <Edit className='w-4 h-4' />
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleDeleteClient(client)}
                                  className='text-red-600 hover:text-red-700'
                                >
                                  <Trash2 className='w-4 h-4' />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        </React.Fragment>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>


      </TabsContent>
      </Tabs>

      {/* View Client Modal */}
      {showViewModal && selectedClient && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'>
          <div className='bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto'>
            <div className='p-6 border-b border-gray-100'>
              <div className='flex items-center justify-between'>
                <h3 className='text-xl font-semibold text-gray-900'>
                  Client Details
                </h3>
                <Button
                  onClick={closeModal}
                  variant="ghost"
                  size="icon-sm"
                  className='text-gray-400 hover:text-gray-600'
                >
                  <X className='h-5 w-5' />
                </Button>
              </div>
            </div>
            <div className='p-6 space-y-6'>
              {/* Client Info */}
              <div className='flex items-center gap-4'>
                <div className='w-16 h-16 bg-accent-100 rounded-full flex items-center justify-center'>
                  <User className='h-8 w-8 text-accent-600' />
                </div>
                <div>
                  <h4 className='text-xl font-semibold text-gray-900'>
                    {selectedClient.client_name}
                  </h4>
                  <p className='text-gray-600'>
                    {selectedClient.company_name || 'No Company'}
                  </p>
                </div>
              </div>

              {/* Financial Summary */}
              <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <p className='text-sm text-gray-600'>{t('clients.total_volume')}</p>
                  <p className='text-xl font-bold text-gray-900'>
                    {formatCurrency(
                      selectedClient.total_amount,
                      Array.isArray(selectedClient.currencies) &&
                      selectedClient.currencies.length > 0
                        ? selectedClient.currencies[0]
                        : 'USD'
                    )}
                  </p>
                </div>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <p className='text-sm text-gray-600'>Commissions</p>
                  <p className='text-xl font-bold text-success-600'>
                    {formatCurrency(
                      selectedClient.total_commission,
                      Array.isArray(selectedClient.currencies) &&
                      selectedClient.currencies.length > 0
                        ? selectedClient.currencies[0]
                        : 'USD'
                    )}
                  </p>
                </div>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <p className='text-sm text-gray-600'>Net Amount</p>
                  <p className='text-xl font-bold text-accent-600'>
                    {formatCurrency(
                      selectedClient.total_net,
                      Array.isArray(selectedClient.currencies) &&
                      selectedClient.currencies.length > 0
                        ? selectedClient.currencies[0]
                        : 'USD'
                    )}
                  </p>
                </div>
              </div>

              {/* Transaction Details */}
              <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <p className='text-sm text-gray-600'>Transaction Count</p>
                  <p className='text-2xl font-bold text-gray-900'>
                    {selectedClient.transaction_count}
                  </p>
                </div>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <p className='text-sm text-gray-600'>{t('clients.avg_transaction')}</p>
                  <p className='text-2xl font-bold text-gray-900'>
                    {formatCurrency(
                      selectedClient.avg_transaction,
                      Array.isArray(selectedClient.currencies) &&
                      selectedClient.currencies.length > 0
                        ? selectedClient.currencies[0]
                        : 'USD'
                    )}
                  </p>
                </div>
              </div>

              {/* Additional Details */}
              <div className='space-y-4'>
                {selectedClient.payment_method && (
                  <div className='flex items-center gap-3'>
                    <Globe className='h-5 w-5 text-gray-400' />
                    <div>
                      <p className='text-sm font-medium text-gray-900'>
                        Payment Method
                      </p>
                      <p className='text-sm text-gray-600'>
                        {selectedClient.payment_method}
                      </p>
                    </div>
                  </div>
                )}

                {selectedClient.currencies &&
                  selectedClient.currencies.length > 0 && (
                    <div>
                      <p className='text-sm font-medium text-gray-900 mb-2'>
                        Currencies
                      </p>
                      <div className='flex flex-wrap gap-2'>
                        {selectedClient.currencies.map(currency => (
                          <span
                            key={currency}
                            className='inline-flex px-3 py-1 text-sm font-medium rounded-full bg-accent-100 text-accent-800'
                          >
                            {currency}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                {selectedClient.psps && selectedClient.psps.length > 0 && (
                  <div>
                    <p className='text-sm font-medium text-gray-900 mb-2'>
                      Payment Service Providers
                    </p>
                    <div className='flex flex-wrap gap-2'>
                      {selectedClient.psps.map(psp => (
                        <span
                          key={psp}
                          className='inline-flex px-3 py-1 text-sm font-medium rounded-full bg-success-100 text-success-800'
                        >
                          {psp}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className='flex items-center gap-3'>
                  <Calendar className='h-5 w-5 text-gray-400' />
                  <div>
                    <p className='text-sm font-medium text-gray-900'>
                      Last Transaction
                    </p>
                    <p className='text-sm text-gray-600'>
                      {selectedClient.last_transaction
                        ? formatDate(selectedClient.last_transaction)
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className='p-6 border-t border-gray-100'>
              <Button
                onClick={closeModal}
                variant="outline"
                className='w-full'
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Client Modal */}
      {showEditModal && selectedClient && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'>
          <div className='bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto'>
            <div className='p-6 border-b border-gray-100'>
              <div className='flex items-center justify-between'>
                <h3 className='text-xl font-semibold text-gray-900'>
                  Edit Client
                </h3>
                <button
                  onClick={closeModal}
                  className='p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200'
                >
                  <X className='h-5 w-5' />
                </button>
              </div>
            </div>
            <div className='p-6'>
              <p className='text-gray-600 mb-6'>
                Edit functionality will be implemented here. This would include
                forms for updating client information.
              </p>
              <div className='flex gap-3'>
                <button
                  onClick={closeModal}
                  className='flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200'
                >
                  Cancel
                </button>
                <button
                  onClick={closeModal}
                  className='flex-1 px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 transition-colors duration-200'
                >
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedClient && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'>
          <div className='bg-white rounded-xl max-w-md w-full'>
            <div className='p-6 border-b border-gray-100'>
              <div className='flex items-center justify-between'>
                <h3 className='text-xl font-semibold text-gray-900'>
                  Delete Client
                </h3>
                <button
                  onClick={closeModal}
                  className='p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200'
                >
                  <X className='h-5 w-5' />
                </button>
              </div>
            </div>
            <div className='p-6'>
              <div className='flex items-center gap-4 mb-4'>
                <div className='w-12 h-12 bg-danger-100 rounded-full flex items-center justify-center'>
                  <Trash2 className='h-6 w-6 text-danger-600' />
                </div>
                <div>
                  <p className='text-lg font-semibold text-gray-900'>
                    Are you sure?
                  </p>
                  <p className='text-gray-600'>This action cannot be undone.</p>
                </div>
              </div>
              <p className='text-gray-600 mb-6'>
                You are about to delete{' '}
                <strong>{selectedClient.client_name}</strong>. This will
                permanently remove all associated data.
              </p>
              <div className='flex gap-3'>
                <button
                  onClick={closeModal}
                  disabled={deleteLoading}
                  className='flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 disabled:opacity-50'
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDeleteClient}
                  disabled={deleteLoading}
                  className='flex-1 px-4 py-2 bg-danger-600 text-white rounded-lg hover:bg-danger-700 transition-colors duration-200 disabled:opacity-50'
                >
                  {deleteLoading ? 'Deleting...' : 'Delete Client'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Daily Summary Modal */}
      {showDailySummaryModal && dailySummaryData && (
        <div className='fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4'>
          <div className='bg-white rounded-2xl shadow-lg max-w-5xl w-full max-h-[85vh] overflow-hidden border border-gray-100'>
            {/* Modal Header */}
            <div className='bg-gray-50 border-b border-gray-200 p-6'>
              <div className='flex items-center justify-between'>
                <div className='flex items-center gap-4'>
                  <div className='w-10 h-10 bg-gray-200 rounded-xl flex items-center justify-center'>
                    <Calendar className='h-5 w-5 text-gray-600' />
                  </div>
                  <div>
                    <h2 className='text-xl font-semibold text-gray-900'>Daily Summary</h2>
                    <p className='text-gray-500 text-sm'>
                      {dailySummaryData.date_str}
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeDailySummaryModal}
                  className='w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center hover:bg-gray-200 transition-colors duration-200'
                >
                  <X className='h-4 w-4 text-gray-600' />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className='p-6 overflow-y-auto max-h-[calc(85vh-120px)]'>
              {dailySummaryLoading ? (
                <div className='flex items-center justify-center py-12'>
                  <div className='text-center'>
                    <div className='animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-gray-600 mx-auto mb-3'></div>
                    <p className='text-gray-600 text-sm'>Loading summary...</p>
                  </div>
                </div>
              ) : (
                <div className='space-y-6'>
                  {/* Key Metrics Section */}
                  {(() => {
                    const dailyMetrics = calculateDailyDepositWithdrawMetrics(dailySummaryData.date);
                    return (
                      <div className='space-y-4'>
                        <div className='flex items-center gap-3'>
                          <div className='w-1 h-6 bg-gray-400 rounded-full'></div>
                          <h3 className='text-lg font-medium text-gray-900'>Overview</h3>
                        </div>
                        
                        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4'>
                          {/* Deposits */}
                          <div className='bg-white border border-gray-200 rounded-xl p-4 hover:shadow-sm transition-shadow duration-200'>
                            <div className='flex items-center justify-between mb-3'>
                              <div className='w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center'>
                                <TrendingUp className='h-4 w-4 text-green-600' />
                              </div>
                              <span className='text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full'>
                                Deposits
                              </span>
                            </div>
                            <p className='text-2xl font-semibold text-gray-900 mb-1'>
                              {formatCurrency(dailyMetrics.totalDeposits, '₺')}
                            </p>
                            <p className='text-xs text-gray-500'>{t('clients.total_incoming')}</p>
                          </div>

                          {/* Withdrawals */}
                          <div className='bg-white border border-gray-200 rounded-xl p-4 hover:shadow-sm transition-shadow duration-200'>
                            <div className='flex items-center justify-between mb-3'>
                              <div className='w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center'>
                                <TrendingUp className='h-4 w-4 text-red-600 rotate-180' />
                              </div>
                              <span className='text-xs font-medium text-red-600 bg-red-50 px-2 py-1 rounded-full'>
                                Withdrawals
                              </span>
                            </div>
                            <p className='text-2xl font-semibold text-gray-900 mb-1'>
                              {formatCurrency(dailyMetrics.totalWithdrawals, '₺')}
                            </p>
                            <p className='text-xs text-gray-500'>{t('clients.total_outgoing')}</p>
                          </div>

                          {/* Net Flow */}
                          <div className='bg-white border border-gray-200 rounded-xl p-4 hover:shadow-sm transition-shadow duration-200'>
                            <div className='flex items-center justify-between mb-3'>
                              <div className='w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center'>
                                <Activity className='h-4 w-4 text-gray-600' />
                              </div>
                              <span className='text-xs font-medium text-gray-600 bg-gray-50 px-2 py-1 rounded-full'>
                                Net
                              </span>
                            </div>
                            <p className={`text-2xl font-semibold mb-1 ${(dailySummaryData?.gross_balance_tl || dailyMetrics.totalDeposits - dailyMetrics.totalWithdrawals) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatCurrency(dailySummaryData?.gross_balance_tl || dailyMetrics.totalDeposits - dailyMetrics.totalWithdrawals, '₺')}
                            </p>
                            <p className='text-xs text-gray-500'>Balance</p>
                          </div>

                          {/* Statistics */}
                          <div className='bg-white border border-gray-200 rounded-xl p-4 hover:shadow-sm transition-shadow duration-200'>
                            <div className='flex items-center justify-between mb-3'>
                              <div className='w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center'>
                                <BarChart3 className='h-4 w-4 text-gray-600' />
                              </div>
                              <span className='text-xs font-medium text-gray-600 bg-gray-50 px-2 py-1 rounded-full'>
                                Stats
                              </span>
                            </div>
                            <div className='space-y-2'>
                              <div className='flex justify-between items-center text-sm'>
                                <span className='text-gray-600'>Transactions</span>
                                <span className='font-semibold text-gray-900'>{dailyMetrics.transactionCount}</span>
                              </div>
                              <div className='flex justify-between items-center text-sm'>
                                <span className='text-gray-600'>Clients</span>
                                <span className='font-semibold text-gray-900'>{dailyMetrics.uniqueClients}</span>
                              </div>
                              {dailyMetrics.transactionCount > 0 && (
                                <div className='flex justify-between items-center text-sm'>
                                  <span className='text-gray-600'>{t('common.average')}</span>
                                  <span className='font-semibold text-gray-900'>
                                    {formatCurrency((dailyMetrics.totalDeposits + dailyMetrics.totalWithdrawals) / dailyMetrics.transactionCount)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })()}

                  {/* USD Rate */}
                  {dailySummaryData.usd_rate !== null && dailySummaryData.usd_rate !== undefined && (
                    <div className='bg-gray-50 border border-gray-200 rounded-xl p-4'>
                      <div className='flex items-center gap-3'>
                        <div className='w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center'>
                          <DollarSign className='h-4 w-4 text-gray-600' />
                        </div>
                        <div>
                          <p className='text-sm font-medium text-gray-700'>USD Rate</p>
                          <p className='text-xl font-semibold text-gray-900'>${Number(dailySummaryData.usd_rate).toFixed(2)}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Payment Methods Breakdown */}
                  {(() => {
                    const dailyPaymentBreakdown = calculateDailyPaymentMethodBreakdown(dailySummaryData.date);
                    return Object.keys(dailyPaymentBreakdown).length > 0 ? (
                      <div className='space-y-4'>
                        <div className='flex items-center gap-3'>
                          <div className='w-1 h-6 bg-gray-400 rounded-full'></div>
                          <h3 className='text-lg font-medium text-gray-900'>Payment Methods</h3>
                        </div>
                        
                        <div className='grid grid-cols-1 lg:grid-cols-2 gap-4'>
                          {Object.entries(dailyPaymentBreakdown)
                            .sort(([, a], [, b]) => Math.abs(b.total) - Math.abs(a.total))
                            .map(([method, data]) => (
                              <div key={method} className='bg-white border border-gray-200 rounded-xl p-4 hover:shadow-sm transition-shadow duration-200'>
                                <div className='flex items-center justify-between mb-3'>
                                  <h4 className='text-sm font-medium text-gray-900'>{method}</h4>
                                  <div className={`text-sm font-semibold px-2 py-1 rounded-full ${data.total >= 0 ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'}`}>
                                    {formatCurrency(Math.abs(data.total), '₺')}
                                  </div>
                                </div>
                                
                                <div className='grid grid-cols-2 gap-3'>
                                  <div className='bg-green-50 border border-green-100 rounded-lg p-3'>
                                    <div className='flex items-center gap-2 mb-1'>
                                      <TrendingUp className='h-3 w-3 text-green-600' />
                                      <span className='text-xs font-medium text-green-700'>Deposits</span>
                                    </div>
                                    <p className='text-lg font-semibold text-green-900'>
                                      {formatCurrency(data.deposits, '₺')}
                                    </p>
                                  </div>
                                  
                                  <div className='bg-red-50 border border-red-100 rounded-lg p-3'>
                                    <div className='flex items-center gap-2 mb-1'>
                                      <TrendingUp className='h-3 w-3 text-red-600 rotate-180' />
                                      <span className='text-xs font-medium text-red-700'>Withdrawals</span>
                                    </div>
                                    <p className='text-lg font-semibold text-red-900'>
                                      {formatCurrency(data.withdrawals, '₺')}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    ) : null;
                  })()}

                  {/* Distribution Summary */}
                  {dailySummaryData.transaction_count > 0 && (
                    <div className='space-y-4'>
                      <div className='flex items-center gap-3'>
                        <div className='w-1 h-6 bg-gray-400 rounded-full'></div>
                        <h3 className='text-lg font-medium text-gray-900'>Breakdown</h3>
                      </div>
                      
                      <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
                        {/* PSP Distribution */}
                        {dailySummaryData.psp_summary.length > 0 && (
                          <div className='bg-white border border-gray-200 rounded-xl p-4'>
                            <div className='flex items-center gap-3 mb-3'>
                              <div className='w-6 h-6 bg-gray-100 rounded-lg flex items-center justify-center'>
                                <Building2 className='h-3 w-3 text-gray-600' />
                              </div>
                              <h4 className='text-sm font-medium text-gray-900'>PSPs</h4>
                            </div>
                            <div className='space-y-3'>
                              {dailySummaryData.psp_summary.slice(0, 4).map((psp, idx) => {
                                // Use backend-provided is_tether flag or fallback to name check
                                const isTether = psp.is_tether || (psp.name && (psp.name.toLowerCase().includes('tether') || psp.name === 'TETHER'));
                                const grossAmount = isTether ? (psp.gross_usd || psp.amount_usd || 0) : (psp.gross_tl || psp.amount_tl || 0);
                                const commission = isTether ? psp.commission_usd : psp.commission_tl;
                                const netAmount = isTether ? psp.net_usd : psp.net_tl;
                                const currencySymbol = isTether ? '$' : '₺';
                                
                                return (
                                  <div key={idx} className='bg-gray-50 rounded-lg p-3'>
                                    <div className='flex justify-between items-center mb-2'>
                                      <span className='text-sm font-medium text-gray-700 truncate'>{psp.name}</span>
                                      <span className='text-xs text-gray-500'>{psp.count} tx</span>
                                    </div>
                                    <div className='space-y-1.5 text-xs'>
                                      <div className='flex justify-between items-center'>
                                        <span className='text-gray-600'>Gross</span>
                                        <span className='font-semibold text-blue-600'>
                                          {currencySymbol}{grossAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </span>
                                      </div>
                                      <div className='flex justify-between items-center'>
                                        <span className='text-gray-600'>Commission</span>
                                        <span className='font-semibold text-orange-600'>
                                          {currencySymbol}{commission.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </span>
                                      </div>
                                      <div className='flex justify-between items-center pt-1 border-t border-gray-200'>
                                        <span className='text-gray-600'>Net</span>
                                        <span className='font-bold text-green-600'>
                                          {currencySymbol}{netAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                              {dailySummaryData.psp_summary.length > 4 && (
                                <div className='text-center pt-2 border-t border-gray-100'>
                                  <span className='text-xs text-gray-500'>
                                    +{dailySummaryData.psp_summary.length - 4} more
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Category Distribution */}
                        {dailySummaryData.category_summary.length > 0 && (
                          <div className='bg-white border border-gray-200 rounded-xl p-4'>
                            <div className='flex items-center gap-3 mb-3'>
                              <div className='w-6 h-6 bg-gray-100 rounded-lg flex items-center justify-center'>
                                <FileText className='h-3 w-3 text-gray-600' />
                              </div>
                              <h4 className='text-sm font-medium text-gray-900'>Categories</h4>
                            </div>
                            <div className='space-y-2'>
                              {dailySummaryData.category_summary.slice(0, 4).map((category, idx) => (
                                <div key={idx} className='flex justify-between items-center text-sm'>
                                  <span className='text-gray-600 truncate'>{category.name}</span>
                                  <span className='font-medium text-gray-900'>{category.count}</span>
                                </div>
                              ))}
                              {dailySummaryData.category_summary.length > 4 && (
                                <div className='text-center pt-2 border-t border-gray-100'>
                                  <span className='text-xs text-gray-500'>
                                    +{dailySummaryData.category_summary.length - 4} more
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Payment Methods */}
                        {dailySummaryData.payment_method_summary.length > 0 && (
                          <div className='bg-white border border-gray-200 rounded-xl p-4'>
                            <div className='flex items-center gap-3 mb-3'>
                              <div className='w-6 h-6 bg-gray-100 rounded-lg flex items-center justify-center'>
                                <CreditCard className='h-3 w-3 text-gray-600' />
                              </div>
                              <h4 className='text-sm font-medium text-gray-900'>Payment Methods</h4>
                            </div>
                            <div className='space-y-3'>
                              {dailySummaryData.payment_method_summary.slice(0, 4).map((method, idx) => {
                                // Check if this payment method is Tether to show USD
                                const isTether = method.name && (method.name.toLowerCase().includes('tether') || method.name === 'TETHER');
                                const grossAmount = isTether ? (method.gross_usd || method.amount_usd || 0) : (method.gross_tl || method.amount_tl || 0);
                                const commission = isTether ? method.commission_usd : method.commission_tl;
                                const netAmount = isTether ? method.net_usd : method.net_tl;
                                const currencySymbol = isTether ? '$' : '₺';
                                
                                return (
                                  <div key={idx} className='bg-gray-50 rounded-lg p-3'>
                                    <div className='flex justify-between items-center mb-2'>
                                      <span className='text-sm font-medium text-gray-700'>{normalizePaymentMethodName(method.name)}</span>
                                      <span className='text-xs text-gray-500'>{method.count} tx</span>
                                    </div>
                                    <div className='space-y-1.5 text-xs'>
                                      <div className='flex justify-between items-center'>
                                        <span className='text-gray-600'>Gross (Before Comm.)</span>
                                        <span className='font-semibold text-blue-600'>
                                          {currencySymbol}{grossAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </span>
                                      </div>
                                      <div className='flex justify-between items-center'>
                                        <span className='text-gray-600'>Commission</span>
                                        <span className='font-semibold text-orange-600'>
                                          {currencySymbol}{commission.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </span>
                                      </div>
                                      <div className='flex justify-between items-center pt-1 border-t border-gray-200'>
                                        <span className='text-gray-600'>Net (After Comm.)</span>
                                        <span className='font-bold text-green-600'>
                                          {currencySymbol}{netAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                              {dailySummaryData.payment_method_summary.length > 4 && (
                                <div className='text-center pt-2 border-t border-gray-100'>
                                  <span className='text-xs text-gray-500'>
                                    +{dailySummaryData.payment_method_summary.length - 4} more
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modals Section */}

      {/* Transaction View Modal */}
      {showViewTransactionModal && selectedTransaction && (
        <Modal
          isOpen={showViewTransactionModal}
          onClose={() => setShowViewTransactionModal(false)}
          title={t('transactions.view_transaction')}
        >
          <TransactionDetailView transaction={selectedTransaction} />
        </Modal>
      )}

      {/* Transaction Edit Modal */}
      {showEditTransactionModal && selectedTransaction && (
        <Modal
          isOpen={showEditTransactionModal}
          onClose={() => setShowEditTransactionModal(false)}
          title={t('transactions.edit_transaction')}
        >
          <TransactionEditForm
            transaction={selectedTransaction}
            onSave={(updatedTransaction) => {
              console.log('🔄 Transaction updated, refreshing local state...', updatedTransaction.id);
              
              // Update the transaction in the local state
              setTransactions(prev => 
                prev.map(t => t.id === updatedTransaction.id ? updatedTransaction : t)
              );
              
              // Update in client transactions if it exists
              if (clientTransactions[updatedTransaction.client_name]) {
                setClientTransactions(prev => ({
                  ...prev,
                  [updatedTransaction.client_name]: prev[updatedTransaction.client_name].map(t => 
                    t.id === updatedTransaction.id ? updatedTransaction : t
                  )
                }));
              }
              
              // Refresh daily summary if it's currently open for the same date
              if (dailySummaryData && dailySummaryData.date === updatedTransaction.date) {
                fetchDailySummary(updatedTransaction.date);
              }
              
              // Close the modal first
              setShowEditTransactionModal(false);
              
              // Dispatch event to refresh transaction lists in other components (but not this one)
              window.dispatchEvent(new CustomEvent('transactionsUpdated', {
                detail: { 
                  action: 'update',
                  transactionId: updatedTransaction.id,
                  skipCurrentPage: true // Flag to skip refresh on current page
                }
              }));
            }}
            onCancel={() => setShowEditTransactionModal(false)}
            dropdownOptions={dropdownOptions}
          />
        </Modal>
      )}

               {/* Import Guide Modal */}
         {showImportGuide && (
           <Modal
             isOpen={showImportGuide}
             onClose={() => setShowImportGuide(false)}
             title={t('transactions.import_guide')}
             size="lg"
           >
          <div className="space-y-6 max-h-96 overflow-y-auto">
            {/* File Format Support */}
            <div>
              <h5 className="text-sm font-medium text-gray-800 mb-2">✅ Supported File Formats:</h5>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">CSV (Fully Supported)</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">XLSX (Fully Supported)</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">XLS (Fully Supported)</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">XLSM (Fully Supported)</span>
              </div>
            </div>

            {/* Essential vs Optional Fields */}
            <div>
              <h5 className="text-sm font-medium text-gray-800 mb-2">🎯 Essential vs Optional Fields:</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <h6 className="font-medium text-green-700 mb-1">✅ Essential Fields (Recommended):</h6>
                  <ul className="text-green-600 space-y-1">
                    <li>• <strong>Client</strong> - Client's full name</li>
                    <li>• <strong>Amount</strong> - Transaction amount</li>
                    <li>• <strong>Company</strong> - Company name</li>
                    <li>• <strong>Payment Method</strong> - How payment was made</li>
                    <li>• <strong>Category</strong> - Transaction category</li>
                    <li>• <strong>Currency</strong> - Transaction currency</li>
                    <li>• <strong>PSP</strong> - Payment service provider</li>
                    <li>• <strong>Date</strong> - Transaction date</li>
                  </ul>
                </div>
                <div>
                  <h6 className="font-medium text-gray-700 mb-1">❓ Optional Fields:</h6>
                  <ul className="text-gray-600 space-y-1">
                    <li>• <strong>Commission</strong> - Auto-calculated if not provided</li>
                    <li>• <strong>Net Amount</strong> - Auto-calculated if not provided</li>
                    <li>• <strong>Notes</strong> - Additional transaction details</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Column Structure */}
            <div>
              <h5 className="text-sm font-medium text-gray-800 mb-2">📋 Essential Column Structure (in exact order):</h5>
              <div className="bg-white border border-gray-200 rounded-lg p-3 text-xs font-mono text-gray-700 overflow-x-auto">
                <div className="grid grid-cols-9 gap-1 text-center font-medium text-gray-600 mb-2">
                  <div className="col-span-1">1</div>
                  <div className="col-span-1">2</div>
                  <div className="col-span-1">3</div>
                  <div className="col-span-1">4</div>
                  <div className="col-span-1">5</div>
                  <div className="col-span-1">6</div>
                  <div className="col-span-1">7</div>
                  <div className="col-span-1">8</div>
                  <div className="col-span-1">9</div>
                </div>
                <div className="grid grid-cols-9 gap-1 text-center">
                  <div className="col-span-1">Client</div>
                  <div className="col-span-1">Company</div>
                  
                  <div className="col-span-1">Payment</div>
                  <div className="col-span-1">Category</div>
                  <div className="col-span-1">Amount</div>
                  <div className="col-span-1">Currency</div>
                  <div className="col-span-1">PSP</div>
                  <div className="col-span-1">Date</div>
                </div>
                
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="text-xs text-gray-600 text-center mb-2">Optional Columns (if needed):</div>
                  <div className="grid grid-cols-3 gap-1 text-center text-xs">
                    <div className="col-span-1">10</div>
                    <div className="col-span-1">11</div>
                    <div className="col-span-1">12</div>
                  </div>
                  <div className="grid grid-cols-3 gap-1 text-center text-xs">
                    <div className="col-span-1">Commission</div>
                    <div className="col-span-1">Net Amount</div>
                    <div className="col-span-1">Notes</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Example Formats */}
            <div>
              <h5 className="text-sm font-medium text-gray-800 mb-2">💡 Example File Formats:</h5>
              
              {/* CSV Format */}
              <div className="mb-3">
                <h6 className="text-sm font-medium text-gray-700 mb-2">📄 CSV Format (Essential Columns):</h6>
                <div className="bg-white border border-gray-200 rounded-lg p-3 text-xs font-mono text-gray-700 overflow-x-auto">
                  <div className="text-gray-600 font-medium mb-1">Essential Header Row:</div>
                  <div className="text-gray-800">Client,Company,Payment Method,Category,Amount,Currency,PSP,Date</div>
                  <div className="text-gray-600 font-medium mt-2 mb-1">Essential Data Row (Example):</div>
                  <div className="text-gray-800">John Doe,ABC Corp,Credit Card,DEP,1000.50,USD,Stripe,2025-08-18</div>
                  
                  <div className="mt-3 pt-2 border-t border-gray-200">
                    <div className="text-gray-600 font-medium mb-1">Full Header Row (with optional columns):</div>
                    <div className="text-gray-800">Client,Company,Payment Method,Category,Amount,Commission,Net Amount,Currency,PSP,Date,Notes</div>
                    <div className="text-gray-600 font-medium mt-2 mb-1">Full Data Row (Example):</div>
                    <div className="text-gray-800">John Doe,ABC Corp,Credit Card,DEP,1000.50,25.00,975.50,USD,Stripe,2025-08-18,Monthly payment</div>
                  </div>
                </div>
              </div>
              
              {/* Excel Format */}
              <div>
                <h6 className="text-sm font-medium text-gray-700 mb-2">📊 Excel Format (XLSX/XLS/XLSM):</h6>
                <div className="bg-white border border-gray-200 rounded-lg p-3 text-xs font-mono text-gray-700 overflow-x-auto">
                  <div className="text-gray-600 font-medium mb-1">Essential Column Structure:</div>
                  <div className="text-gray-800">Column A: Client | Column B: Company | Column C: Payment Method</div>
                  <div className="text-gray-800">Column D: Category | Column E: Amount | Column F: Currency | Column G: PSP | Column H: Date</div>
                  
                  <div className="mt-3 pt-2 border-t border-gray-200">
                    <div className="text-gray-600 font-medium mb-1">Optional Columns (if needed):</div>
                    <div className="text-gray-800">Column J: Commission | Column K: Net Amount | Column L: Notes</div>
                  </div>
                  
                  <div className="text-gray-600 font-medium mt-2 mb-1">💡 Tip: Excel files are automatically parsed - just ensure your first row contains headers!</div>
                </div>
              </div>
            </div>

            {/* Downloadable Template Examples */}
            <div>
              <h5 className="text-sm font-medium text-gray-800 mb-2">📥 Download Template Examples:</h5>
              
              {/* Essential Template */}
              <div className="mb-3">
                <h6 className="text-sm font-medium text-green-700 mb-2">✅ Essential Template (9 columns):</h6>
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <div className="text-sm text-green-800 mb-2">
                    <strong>Perfect for most imports:</strong> Contains only the essential columns needed for complete transaction data.
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => downloadTemplate('essential', 'csv')}
                      className="px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition-colors duration-200 flex items-center gap-1"
                    >
                      <Download className="w-3 h-3" />
                      Download CSV Template
                    </button>
                    <button
                      onClick={() => downloadTemplate('essential', 'xlsx')}
                      className="px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition-colors duration-200 flex items-center gap-1"
                    >
                      <Download className="w-3 h-3" />
                      Download Excel Template
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Full Template */}
              <div>
                <h6 className="text-sm font-medium text-gray-700 mb-2">📋 Full Template (12 columns):</h6>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <div className="text-sm text-gray-800 mb-2">
                    <strong>Complete template:</strong> Includes all columns including commission, net amount, and notes for advanced users.
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => downloadTemplate('full', 'csv')}
                      className="px-3 py-1.5 bg-gray-600 text-white text-xs rounded-lg hover:bg-gray-700 transition-colors duration-200 flex items-center gap-1"
                    >
                      <Download className="w-3 h-3" />
                      Download CSV Template
                    </button>
                    <button
                      onClick={() => downloadTemplate('full', 'xlsx')}
                      className="px-3 py-1.5 bg-gray-600 text-white text-xs rounded-lg hover:bg-gray-700 transition-colors duration-200 flex items-center gap-1"
                    >
                      <Download className="w-3 h-3" />
                      Download Excel Template
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Smart Import Note */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <h6 className="text-sm font-medium text-green-800 mb-1">🧮 Smart Import Features:</h6>
              <ul className="text-sm text-green-700 space-y-1">
                <li>• <strong>Essential 9 columns</strong> provide complete transaction data</li>
                <li>• <strong>Commission & Net Amount</strong> are auto-calculated if not provided</li>
                <li>• <strong>Transaction summaries</strong> are automatically generated</li>
                <li>• <strong>Client statistics</strong> are updated in real-time</li>
                <li>• <strong>Flexible import</strong> - use 9 essential columns or all 12 columns</li>
                <li>• Only import <strong>raw data</strong> - let the system handle calculations!</li>
              </ul>
            </div>
          </div>
        </Modal>
      )}

         {/* Import Preview Modal */}
         {showImportPreview && (
           <Modal
             isOpen={showImportPreview}
             onClose={() => setShowImportPreview(false)}
             title={t('transactions.import_preview')}
             size="lg"
           >
             <div className="space-y-6">
               {/* Summary */}
               <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                 <h5 className="text-sm font-medium text-gray-800 mb-2">📊 Import Summary:</h5>
                 <div className="grid grid-cols-2 gap-4 text-sm">
                   <div>
                     <span className="text-gray-600 font-medium">{t('clients.total_transactions')}:</span>
                     <span className="ml-2 text-gray-800">{importData.length}</span>
                   </div>
                   <div>
                     <span className="text-gray-600 font-medium">File Type:</span>
                     <span className="ml-2 text-gray-800">CSV</span>
                   </div>
                 </div>
               </div>

               {/* Preview Table */}
               <div>
                 <h5 className="text-sm font-medium text-gray-800 mb-3">👀 Preview (First 5 transactions):</h5>
                 <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                   <table className="min-w-full divide-y divide-gray-200">
                     <thead className="bg-gray-50">
                       <tr>
                         <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client</th>
                         <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                         <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                         <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Currency</th>
                         <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                       </tr>
                     </thead>
                     <tbody className="bg-white divide-y divide-gray-200">
                       {importPreview.map((transaction, index) => (
                         <tr key={index} className="hover:bg-gray-50">
                           <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{transaction.client_name}</td>
                           <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{transaction.company || '-'}</td>
                           <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{transaction.amount}</td>
                           <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{transaction.currency}</td>
                           <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{transaction.category}</td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 </div>
               </div>

               {/* Action Buttons */}
               <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                 <button
                   onClick={() => setShowImportPreview(false)}
                   className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                 >
                   Cancel
                 </button>
                 <button
                   onClick={handleFinalImport}
                   disabled={importing}
                   className="px-4 py-2 text-sm font-medium text-white bg-gray-600 border border-transparent rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                 >
                   {importing ? 'Importing...' : `Import ${importData.length} Transactions`}
                 </button>
               </div>
             </div>
           </Modal>
         )}

         {/* Paste Import Modal */}
         {showPasteImport && (
           <Modal
             isOpen={showPasteImport}
             onClose={() => {
               setShowPasteImport(false);
               setPasteData('');
             }}
             title="Paste & Import Transactions"
             size="lg"
           >
             <div className="space-y-4">
               <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                 <p className="text-sm text-blue-800">
                   <strong>Format:</strong> Tab-separated values (her satır bir transaction)<br/>
                   <strong>Kolonlar:</strong> Müşteri Adı | Ödeme Yöntemi | Şirket | ORDER | Tarih (DD.MM.YYYY) | Kategori (YATIRIM/ÇEKME) | Tutar | Komisyon | Net Tutar | Para Birimi | PSP | MÜŞTERİ
                 </p>
               </div>
               
               <div>
                 <label htmlFor="pasteData" className="block text-sm font-medium text-gray-700 mb-2">
                   Transaction Verileri (Tab-separated):
                 </label>
                 <textarea
                   id="pasteData"
                   value={pasteData}
                   onChange={(e) => setPasteData(e.target.value)}
                   placeholder="Verileri buraya yapıştırın..."
                   className="w-full h-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 font-mono text-sm"
                 />
                 <p className="text-xs text-gray-500 mt-1">
                   {pasteData.split('\n').filter(l => l.trim()).length} satır tespit edildi
                 </p>
               </div>

               <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                 <button
                   onClick={() => {
                     setShowPasteImport(false);
                     setPasteData('');
                   }}
                   className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                 >
                   İptal
                 </button>
                 <button
                   onClick={handlePasteImport}
                   disabled={importing || !pasteData.trim()}
                   className="px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                 >
                   {importing ? 'Importing...' : 'Import Et'}
                 </button>
               </div>
             </div>
           </Modal>
         )}

         {/* Bulk Delete Modal */}
         {showBulkDeleteModal && (
           <Modal
             isOpen={showBulkDeleteModal}
             onClose={() => setShowBulkDeleteModal(false)}
             title={t('transactions.bulk_delete_all')}
             size="md"
           >
             <div className="space-y-6">
               {/* Warning */}
               <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                 <div className="flex items-center gap-2 mb-2">
                   <AlertCircle className="w-5 h-5 text-red-600" />
                   <h5 className="text-sm font-medium text-red-800">⚠️ DANGER ZONE</h5>
                 </div>
                 <p className="text-sm text-red-700">
                   This action will <strong>permanently delete ALL transactions</strong> from the system. 
                   This action cannot be undone and will affect all client data, reports, and analytics.
                 </p>
               </div>

               {/* Confirmation Code Input */}
               <div>
                 <label htmlFor="confirmationCode" className="block text-sm font-medium text-gray-700 mb-2">
                   Enter Confirmation Code:
                 </label>
                 <input
                   type="text"
                   id="confirmationCode"
                   value={confirmationCode}
                   onChange={(e) => setConfirmationCode(e.target.value)}
                   placeholder="Enter 4-digit code"
                   className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
                   maxLength={4}
                   autoComplete="off"
                 />
                 <p className="text-xs text-gray-500 mt-1">
                   You must enter the exact 4-digit confirmation code to proceed with deletion.
                 </p>
               </div>

               {/* Action Buttons */}
               <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                 <button
                   onClick={() => setShowBulkDeleteModal(false)}
                   className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                 >
                   Cancel
                 </button>
                 <button
                   onClick={handleBulkDeleteAll}
                   disabled={deleting || confirmationCode !== '4561'}
                   className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                 >
                   {deleting ? 'Deleting...' : 'Delete All Transactions'}
                 </button>
               </div>
             </div>
           </Modal>
         )}

         {/* Exchange Rate Edit Modal */}
         {showRateEditModal && (
           <Modal
             isOpen={showRateEditModal}
             onClose={closeRateEditModal}
             title={`${t('exchange_rates.edit_rate')} - ${editingDate}`}
             size="md"
           >
             <div className="space-y-6">
               {/* Info Section */}
               <UnifiedCard className="p-4">
                 <div className="flex items-start gap-3">
                   <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                     <Info className="w-4 h-4 text-gray-600" />
                   </div>
                   <div className="flex-1">
                     <h5 className="text-sm font-medium text-gray-900 mb-1">USD/TRY Exchange Rate</h5>
                     <p className="text-sm text-gray-600 leading-relaxed">
                       This rate is used to calculate gross balances for {editingDate}.
                       Changing this rate will recalculate all balances for this date.
                     </p>
                   </div>
                 </div>
               </UnifiedCard>

               {/* Rate Input */}
               <div className="space-y-3">
                 <label className="block text-sm font-medium text-gray-700">
                   Exchange Rate (USD/TRY)
                 </label>
                 <div className="flex gap-3">
                   <Input
                     type="number"
                     step="0.0001"
                     min="0"
                     value={editingRate}
                     onChange={(e) => setEditingRate(e.target.value)}
                     className="flex-1"
                     placeholder="Enter exchange rate (e.g., 48.3900)"
                     disabled={rateEditLoading}
                   />
                   <UnifiedButton
                     onClick={handleFetchRate}
                     disabled={rateEditLoading}
                     variant="secondary"
                     className="flex items-center gap-2 whitespace-nowrap"
                   >
                     <CalendarDays className="w-4 h-4" />
                     Select Date
                   </UnifiedButton>
                 </div>
                 <p className="text-xs text-gray-500">
                   Example: 48.3900 means 1 USD = 48.39 TRY
                 </p>
               </div>

               {/* Preview Section */}
               {editingRate && parseFloat(editingRate) > 0 && (
                 <UnifiedCard className="p-4">
                   <h5 className="text-sm font-medium text-gray-900 mb-3">Preview</h5>
                   <div className="space-y-3">
                     <div className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                       <span className="text-sm text-gray-600">New Rate:</span>
                       <span className="text-sm font-medium text-gray-900">1 USD = {parseFloat(editingRate).toFixed(4)} TRY</span>
                     </div>
                     <div className="flex justify-between items-center py-2">
                       <span className="text-sm text-gray-600">Inverse:</span>
                       <span className="text-sm font-medium text-gray-900">1 TRY = {(1 / parseFloat(editingRate)).toFixed(6)} USD</span>
                     </div>
                   </div>
                 </UnifiedCard>
               )}

               {/* Action Buttons */}
               <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                 <UnifiedButton
                   onClick={closeRateEditModal}
                   disabled={rateEditLoading}
                   variant="outline"
                 >
                   Cancel
                 </UnifiedButton>
                 <UnifiedButton
                   onClick={handleRateSave}
                   disabled={rateEditLoading || !editingRate || parseFloat(editingRate) <= 0}
                   variant="primary"
                 >
                   {rateEditLoading ? 'Saving...' : 'Save Rate'}
                 </UnifiedButton>
               </div>
             </div>
           </Modal>
         )}

         {/* Calendar Date Picker Modal */}
         {showCalendar && (
           <Modal
             isOpen={showCalendar}
             onClose={() => setShowCalendar(false)}
             title={t('exchange_rates.select_date')}
             size="sm"
           >
             <div className="space-y-6">
               <UnifiedCard className="p-4 text-center">
                 <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 rounded-full bg-gray-100">
                   <CalendarDays className="w-6 h-6 text-gray-600" />
                 </div>
                 <h5 className="text-sm font-medium text-gray-900 mb-2">Choose Date</h5>
                 <p className="text-sm text-gray-600 mb-4">
                   Select a date to fetch the USD/TRY exchange rate from yfinance
                 </p>
                 
                 <Input
                   type="date"
                   value={selectedCalendarDate}
                   onChange={(e) => setSelectedCalendarDate(e.target.value)}
                   className="w-full max-w-xs mx-auto"
                   max={new Date().toISOString().split('T')[0]} // Don't allow future dates
                 />
               </UnifiedCard>
               
               <div className="flex justify-center gap-3">
                 <UnifiedButton
                   onClick={() => setShowCalendar(false)}
                   variant="outline"
                 >
                   Cancel
                 </UnifiedButton>
                 <UnifiedButton
                   onClick={() => handleCalendarDateSelect(selectedCalendarDate)}
                   disabled={!selectedCalendarDate || rateEditLoading}
                   variant="primary"
                 >
                   {rateEditLoading ? 'Fetching...' : 'Get Rate'}
                 </UnifiedButton>
               </div>
             </div>
           </Modal>
         )}

      </div>
      {/* End Modals Container */}

    </div>
  );
}