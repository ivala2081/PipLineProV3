import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTabPersistence } from '../hooks/useTabPersistence';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  CreditCard,
  Building2,
  Calendar,
  Eye,
  Edit,
  Trash2,
  Filter,
  Search,
  Download,
  AlertCircle,
  Award,
  BarChart,
  User,
  Building,
  Plus,
  LineChart,
  Activity,
  X,
  Globe,
  RefreshCw,
  CheckCircle,
  Clock,
  PieChart,
  MoreHorizontal,
  Upload,
  ChevronLeft,
  ChevronRight,
  Info,
  Calculator,
  Receipt,
  Banknote,
  ShoppingCart,
  XCircle,
  Check,
  Shield,
  Wallet,
  Lock,
  Unlock,
  Save
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../hooks/useNotifications';
import { api } from '../utils/apiClient';
import { logger } from '../utils/logger';
import { formatCurrency as formatCurrencyUtil } from '../utils/currencyUtils';
import { 
  UnifiedCard, 
  UnifiedButton, 
  UnifiedBadge, 
  UnifiedSection, 
  UnifiedGrid 
} from '../design-system';
import { Breadcrumb } from '../components/ui';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { SectionHeader } from '../components/ui/SectionHeader';
import StandardMetricsCard from '../components/StandardMetricsCard';
import MetricCard from '../components/MetricCard';

interface Expense {
  id: number;
  description: string;  // Açıklama
  detail: string;  // Detay
  category: 'inflow' | 'outflow';  // Giren / Çıkan
  type: 'payment' | 'transfer';  // Ödeme / Transfer
  amount_try: number;  // TRY
  amount_usd: number;  // USD
  amount_usdt: number;  // USDT
  mount_currency: string;  // TRY, USD, or USDT - which currency was entered
  status: 'paid' | 'pending' | 'cancelled';  // Durum
  cost_period: string;  // Maliyet Dönemi (e.g., "2025-01" or "Ocak 2025")
  payment_date: string;  // Ödeme Tarihi
  payment_period: string;  // Ödeme Dönemi
  source: string;  // Kaynak
  created_at: string;
  updated_at: string;
}

/**
 * Accounting Component - Optimized for Performance
 * 
 * Performance Optimizations:
 * - useMemo: Memoized filtered expenses and totals to prevent recalculation
 * - useCallback: Wrapped event handlers to prevent child re-renders
 * - Debouncing: 300ms debounce on search input to reduce filter operations
 * - Lazy Loading: Analytics tab loads only when active
 */
export default function Accounting() {
  // #region agent log
  useEffect(() => {
    fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'Accounting.tsx:component',message:'Accounting component mounted',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
  }, []);
  // #endregion
  
  // Hooks must be called unconditionally at the top
  const { t, currentLanguage } = useLanguage();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { success, error, info } = useNotifications();
  const navigate = useNavigate();
  const [activeTab, handleTabChange] = useTabPersistence<'overview' | 'expenses' | 'analytics' | 'net'>('overview');
  const [expensesView, setExpensesView] = useState<'all' | 'daily' | 'internal_revenue'>('all');
  const [netView, setNetView] = useState<'calculator' | 'daily'>('calculator');
  
  // State for loading record from Daily Net to Calculator
  const [recordToLoad, setRecordToLoad] = useState<any | null>(null);
  
  // Month/Year filter for daily summary
  const [selectedMonth, setSelectedMonth] = useState<number>(new Date().getMonth() + 1); // Current month (1-12)
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear()); // Current year
  
  // Sort order for daily summary (ascending/descending)
  const [dailySummarySortOrder, setDailySummarySortOrder] = useState<'asc' | 'desc'>('desc');
  
  // Expanded daily details
  const [expandedDate, setExpandedDate] = useState<string | null>(null);
  
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [expenseStatusFilter, setExpenseStatusFilter] = useState<'all' | 'paid' | 'pending' | 'cancelled'>('all');
  const [expenseCategoryFilter, setExpenseCategoryFilter] = useState<'all' | 'inflow' | 'outflow'>('all');
  const [expenseTypeFilter, setExpenseTypeFilter] = useState<'all' | 'payment' | 'transfer'>('all');
  const [expenseDateFrom, setExpenseDateFrom] = useState('');
  const [expenseDateTo, setExpenseDateTo] = useState('');
  const [expenseCostPeriod, setExpenseCostPeriod] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  
  // Analytics & Budget state
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [showBudget, setShowBudget] = useState(false);
  const [analytics, setAnalytics] = useState<any>(null);
  const [budgets, setBudgets] = useState<any[]>([]);
  const [budgetStatus, setBudgetStatus] = useState<any>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [loadingBudgets, setLoadingBudgets] = useState(false);
  
  // Internal Revenue sub-tab state
  const [internalRevenueView, setInternalRevenueView] = useState<'currency_summary'>('currency_summary');
  
  // Monthly Currency Summary state
  const [selectedMonthPeriod, setSelectedMonthPeriod] = useState<string>(
    new Date().toISOString().slice(0, 7) // Current month: "YYYY-MM"
  );
  const [savedMonths, setSavedMonths] = useState<Array<{month_period: string; is_locked: boolean}>>([]);
  const [isMonthLocked, setIsMonthLocked] = useState(false);
  const [isSavingMonth, setIsSavingMonth] = useState(false);
  const [isLoadingMonth, setIsLoadingMonth] = useState(false);
  
  // Editable exchange rates (temporary, not auto-saved)
  const [tempExchangeRates, setTempExchangeRates] = useState<{[key: string]: string}>({
    TRY: ''
  });
  
  // Temporary carryover values (not auto-saved)
  const [tempCarryoverValues, setTempCarryoverValues] = useState<{
    TRY: number;
    USD: number;
    USDT: number;
  }>({
    TRY: 0,
    USD: 0,
    USDT: 0
  });
  
  // DEVİR (Carryover) values - user can edit manually
  // Initialize carryover values from localStorage or default to SİMÜLASYON sheet values
  const [carryoverValues, setCarryoverValues] = useState<{
    TRY: number;
    USD: number;
    USDT: number;
  }>(() => {
    // Try to load from localStorage first
    const saved = localStorage.getItem('expense_carryover_values');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed.TRY === 'number' && typeof parsed.USD === 'number' && typeof parsed.USDT === 'number') {
          return parsed;
        }
      } catch (e) {
        console.warn('Failed to parse saved carryover values:', e);
      }
    }
    // Default to SİMÜLASYON sheet values if not found
    return {
      TRY: 750000,  // From SİMÜLASYON sheet
      USD: 5000,    // From SİMÜLASYON sheet
      USDT: 168000  // From SİMÜLASYON sheet
    };
  });
  
  // Pagination state for All Expenses view
  const [currentExpensePage, setCurrentExpensePage] = useState(1);
  const EXPENSES_PER_PAGE = 50;
  // Stabilize inner Net component to avoid remounts (preserve its state across parent re-renders)
  // Note: We use the component directly now since we need to pass dynamic props (recordToLoad)
  
  // Expense modal states
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [viewingExpense, setViewingExpense] = useState<Expense | null>(null);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [isViewMode, setIsViewMode] = useState(false);
  const [showAddAnother, setShowAddAnother] = useState(false);
  const [formData, setFormData] = useState({
    description: '',
    detail: '',
    category: 'inflow' as 'inflow' | 'outflow',
    type: 'payment' as 'payment' | 'transfer',
    amount: '',  // Single amount field - user enters amount here
    mount_currency: 'TRY' as 'TRY' | 'USD' | 'USDT',  // Selected currency
    status: 'pending' as 'paid' | 'pending' | 'cancelled',
    cost_period: '',
    payment_date: '',
    payment_period: '',
    source: ''
  });
  
  // Calculated amounts (read-only, shown to user)
  const [calculatedAmounts, setCalculatedAmounts] = useState({
    amount_try: 0,
    amount_usd: 0,
    amount_usdt: 0
  });
  
  // Exchange rate auto-conversion state
  const [currentRate, setCurrentRate] = useState<number | null>(null);
  const [fetchingRate, setFetchingRate] = useState(false);
  
  // Converter toggle state (default: on)
  const [converterEnabled, setConverterEnabled] = useState<boolean>(true);
  
  // Calculate amounts based on selected currency and entered amount
  useEffect(() => {
    const amount = parseFloat(formData.amount) || 0;
    
    let calculated = {
      amount_try: 0,
      amount_usd: 0,
      amount_usdt: 0
    };
    
    // If converter is disabled, only set the entered currency amount
    if (!converterEnabled) {
      if (formData.mount_currency === 'TRY') {
        calculated.amount_try = amount;
      } else if (formData.mount_currency === 'USD') {
        calculated.amount_usd = amount;
      } else if (formData.mount_currency === 'USDT') {
        calculated.amount_usdt = amount;
      }
      setCalculatedAmounts(calculated);
      return;
    }
    
    // Converter is enabled - perform conversion using API rate
    // Default exchange rate - should be fetched from API when available
    const DEFAULT_EXCHANGE_RATE = 42.00;
    const exchangeRate = currentRate || DEFAULT_EXCHANGE_RATE;
    
    if (formData.mount_currency === 'TRY') {
      calculated.amount_try = amount;
      calculated.amount_usd = exchangeRate > 0 ? amount / exchangeRate : 0;
      calculated.amount_usdt = calculated.amount_usd; // USDT = USD (1:1)
    } else if (formData.mount_currency === 'USD') {
      calculated.amount_usd = amount;
      calculated.amount_try = amount * exchangeRate;
      calculated.amount_usdt = amount; // USDT = USD (1:1)
    } else if (formData.mount_currency === 'USDT') {
      calculated.amount_usdt = amount;
      calculated.amount_usd = amount; // USDT = USD (1:1)
      calculated.amount_try = amount * exchangeRate;
    }
    
    setCalculatedAmounts(calculated);
  }, [formData.amount, formData.mount_currency, currentRate, converterEnabled]);

  // --- Net Tab inner component ---
  function NetCalculatorInner({ expenses, recordToLoad, onRecordLoaded, validatePin }: { expenses: Expense[]; recordToLoad: any | null; onRecordLoaded: () => void; validatePin: (pin: string) => Promise<boolean> }) {
    // Helper function to get localStorage key for date-specific values
    const getStorageKey = (date: string) => `net_tab_values_${date}`;
    
    // Helper function to save values to localStorage
    const saveValuesToStorage = (date: string, values: {
      expensesUsd: string;
      rolloverUsd: string;
      netCashUsd: string;
      commissionUsd: string;
      oncekiKapanisUsd: string;
      companyCashUsd: string;
      cryptoBalanceUsd: string;
      anlikKasaUsd: string;
      bekleyenTahsilatUsd: string;
      anlikKasaManual: boolean;
    }) => {
      try {
        const key = getStorageKey(date);
        localStorage.setItem(key, JSON.stringify(values));
        logger.info('[Net Tab] Saved values to localStorage for date:', date);
      } catch (e) {
        logger.error('[Net Tab] Failed to save values to localStorage:', e);
      }
    };
    
    // Helper function to load values from localStorage
    const loadValuesFromStorage = (date: string): {
      expensesUsd: string;
      rolloverUsd: string;
      netCashUsd: string;
      commissionUsd: string;
      oncekiKapanisUsd: string;
      companyCashUsd: string;
      cryptoBalanceUsd: string;
      anlikKasaUsd: string;
      bekleyenTahsilatUsd: string;
      anlikKasaManual: boolean;
    } | null => {
      try {
        const key = getStorageKey(date);
        const saved = localStorage.getItem(key);
        if (saved) {
          const parsed = JSON.parse(saved);
          logger.info('[Net Tab] Loaded values from localStorage for date:', date);
          return parsed;
        }
      } catch (e) {
        logger.error('[Net Tab] Failed to load values from localStorage:', e);
      }
      return null;
    };
    
    // Use localStorage to persist date across remounts
    const [date, setDateState] = useState<string>(() => {
      const saved = localStorage.getItem('net_tab_date');
      if (saved) {
        logger.info('[Net Tab] Loaded date from localStorage:', saved);
        return saved;
      }
      const today = new Date().toISOString().slice(0, 10);
      logger.info('[Net Tab] Initial date set to:', today);
      return today;
    });
    
    // Load saved values for initial date
    const getInitialValues = () => {
      const saved = localStorage.getItem('net_tab_date');
      const dateToLoad = saved || new Date().toISOString().slice(0, 10);
      return loadValuesFromStorage(dateToLoad);
    };
    
    const initialSavedValues = getInitialValues();
    
    const [expensesUsd, setExpensesUsd] = useState<string>(() => initialSavedValues?.expensesUsd || '0');
    const [rolloverUsd, setRolloverUsd] = useState<string>(() => initialSavedValues?.rolloverUsd || '0');
    const [netCashUsd, setNetCashUsd] = useState<string>(() => initialSavedValues?.netCashUsd || '0');
    const [commissionUsd, setCommissionUsd] = useState<string>(() => initialSavedValues?.commissionUsd || '0');
    
    // New fields
    const [oncekiKapanisUsd, setOncekiKapanisUsd] = useState<string>(() => initialSavedValues?.oncekiKapanisUsd || '0');
    const [companyCashUsd, setCompanyCashUsd] = useState<string>(() => initialSavedValues?.companyCashUsd || '0');
    const [cryptoBalanceUsd, setCryptoBalanceUsd] = useState<string>(() => initialSavedValues?.cryptoBalanceUsd || '0');
    const [anlikKasaUsd, setAnlikKasaUsd] = useState<string>(() => initialSavedValues?.anlikKasaUsd || '0');
    const [bekleyenTahsilatUsd, setBekleyenTahsilatUsd] = useState<string>(() => initialSavedValues?.bekleyenTahsilatUsd || '0');
    const [anlikKasaManual, setAnlikKasaManual] = useState<boolean>(() => initialSavedValues?.anlikKasaManual || false);
    
    // Wrapper to persist date changes and load values for new date
    const setDate = (newDate: string) => {
      logger.info('[Net Tab] Date being changed to:', newDate);
      
      // Save current values before switching dates
      saveValuesToStorage(date, {
        expensesUsd,
        rolloverUsd,
        netCashUsd,
        commissionUsd,
        oncekiKapanisUsd,
        companyCashUsd,
        cryptoBalanceUsd,
        anlikKasaUsd,
        bekleyenTahsilatUsd,
        anlikKasaManual
      });
      
      localStorage.setItem('net_tab_date', newDate);
      setDateState(newDate);
      
      // Load values for the new date
      const savedValues = loadValuesFromStorage(newDate);
      if (savedValues) {
        setExpensesUsd(savedValues.expensesUsd || '0');
        setRolloverUsd(savedValues.rolloverUsd || '0');
        setNetCashUsd(savedValues.netCashUsd || '0');
        setCommissionUsd(savedValues.commissionUsd || '0');
        setOncekiKapanisUsd(savedValues.oncekiKapanisUsd || '0');
        setCompanyCashUsd(savedValues.companyCashUsd || '0');
        setCryptoBalanceUsd(savedValues.cryptoBalanceUsd || '0');
        setAnlikKasaUsd(savedValues.anlikKasaUsd || '0');
        setBekleyenTahsilatUsd(savedValues.bekleyenTahsilatUsd || '0');
        setAnlikKasaManual(savedValues.anlikKasaManual || false);
      } else {
        // Reset to defaults if no saved values
        setExpensesUsd('0');
        setRolloverUsd('0');
        setNetCashUsd('0');
        setCommissionUsd('0');
        setOncekiKapanisUsd('0');
        setCompanyCashUsd('0');
        setCryptoBalanceUsd('0');
        setAnlikKasaUsd('0');
        setBekleyenTahsilatUsd('0');
        setAnlikKasaManual(false);
      }
    };
    const [showManualCodeModal, setShowManualCodeModal] = useState<boolean>(false);
    const [manualConfirmationCode, setManualConfirmationCode] = useState<string>('');
    const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
    const [deleteSecurityCode, setDeleteSecurityCode] = useState<string>('');
    
    const [result, setResult] = useState<any | null>(null);
    const [loadingNet, setLoadingNet] = useState<boolean>(false);
    const [errorNet, setErrorNet] = useState<string | null>(null);
    const [savingNet, setSavingNet] = useState<boolean>(false);
    const [isSaved, setIsSaved] = useState<boolean>(false);
    const [showCalendar, setShowCalendar] = useState<boolean>(false);
    const [fetchingExpenses, setFetchingExpenses] = useState<boolean>(false);
    const [fetchingCryptoBalance, setFetchingCryptoBalance] = useState<boolean>(false);
    const [justFetchedData, setJustFetchedData] = useState<boolean>(false);
    const [currentMonth, setCurrentMonth] = useState<Date>(() => {
      return date ? new Date(date) : new Date();
    });
    const isInitialMount = React.useRef(true);

    const fetchNet = async () => {
      try {
        setLoadingNet(true);
        setErrorNet(null);
        const params: Record<string, string> = {
          date,
          expenses_usd: expensesUsd || '0',
          rollover_usd: rolloverUsd || '0',
          net_cash_usd: netCashUsd || '0',
          commissions_usd: commissionUsd || '0',
          onceki_kapanis_usd: oncekiKapanisUsd || '0',
          company_cash_usd: companyCashUsd || '0',
          crypto_balance_usd: cryptoBalanceUsd || '0',
          anlik_kasa_usd: anlikKasaUsd || '0',
          anlik_kasa_manual: anlikKasaManual ? 'true' : 'false',
          bekleyen_tahsilat_usd: bekleyenTahsilatUsd || '0',
        };
        const query = new URLSearchParams(params).toString();
        const resp = await api.get(`/accounting/net?${query}`);
        const data = await api.parseResponse(resp);
        if (data && data.success) {
          setResult(data.data);
          setIsSaved(data.is_saved || false);
          
          // DON'T load saved values if we just fetched data - this prevents overwriting freshly fetched values
          if (!justFetchedData && data.is_saved && data.data) {
            // Only load if inputs are at default values
            if (netCashUsd === '0' && commissionUsd === '0' && expensesUsd === '0' && rolloverUsd === '0' 
                && oncekiKapanisUsd === '0' && companyCashUsd === '0' && cryptoBalanceUsd === '0' && anlikKasaUsd === '0' && bekleyenTahsilatUsd === '0') {
              logger.info('[fetchNet] Loading saved values from database');
              setExpensesUsd(String(data.data.expenses_usd || '0'));
              setRolloverUsd(String(data.data.rollover_usd || '0'));
              setNetCashUsd(String(data.data.net_cash_usd || '0'));
              setCommissionUsd(String(data.data.commissions_usd || '0'));
              setOncekiKapanisUsd(String(data.data.onceki_kapanis_usd || '0'));
          setCompanyCashUsd(String(data.data.company_cash_usd || '0'));
          setCryptoBalanceUsd(String(data.data.crypto_balance_usd || '0'));
          setAnlikKasaUsd(String(data.data.anlik_kasa_usd || '0'));
          setAnlikKasaManual(data.data.anlik_kasa_manual || false);
          setBekleyenTahsilatUsd(String(data.data.bekleyen_tahsilat_usd || '0'));
            }
          } else if (justFetchedData) {
            logger.info('[fetchNet] Skipping saved value load - just fetched data (protection active)');
          }
        } else {
          setErrorNet(t('accounting.net.calculation_failed'));
        }
      } catch (e: any) {
        setErrorNet(e?.message || t('accounting.net.calculation_failed'));
      } finally {
        setLoadingNet(false);
      }
    };

    // Helper: fetch net with explicit overrides (avoids race with setState)
    const fetchNetWithParams = async (overrides: Partial<Record<'expenses_usd' | 'rollover_usd' | 'net_cash_usd' | 'commissions_usd' | 'onceki_kapanis_usd' | 'company_cash_usd' | 'crypto_balance_usd' | 'anlik_kasa_usd' | 'bekleyen_tahsilat_usd', string>> = {}) => {
      try {
        setLoadingNet(true);
        setErrorNet(null);
        const params: Record<string, string> = {
          date,
          expenses_usd: overrides.expenses_usd ?? (expensesUsd || '0'),
          rollover_usd: overrides.rollover_usd ?? (rolloverUsd || '0'),
          net_cash_usd: overrides.net_cash_usd ?? (netCashUsd || '0'),
          commissions_usd: overrides.commissions_usd ?? (commissionUsd || '0'),
          onceki_kapanis_usd: overrides.onceki_kapanis_usd ?? (oncekiKapanisUsd || '0'),
          company_cash_usd: overrides.company_cash_usd ?? (companyCashUsd || '0'),
          crypto_balance_usd: overrides.crypto_balance_usd ?? (cryptoBalanceUsd || '0'),
          anlik_kasa_usd: overrides.anlik_kasa_usd ?? (anlikKasaUsd || '0'),
          bekleyen_tahsilat_usd: overrides.bekleyen_tahsilat_usd ?? (bekleyenTahsilatUsd || '0'),
        };
        const query = new URLSearchParams(params).toString();
        const resp = await api.get(`/accounting/net?${query}`);
        const data = await api.parseResponse(resp);
        if (data && data.success) {
          setResult(data.data);
          setIsSaved(data.is_saved || false);
        } else {
          setErrorNet(t('accounting.net.calculation_failed'));
        }
      } catch (e: any) {
        setErrorNet(e?.message || t('accounting.net.calculation_failed'));
      } finally {
        setLoadingNet(false);
      }
    };

    const fetchDailyExpenses = () => {
      try {
        setFetchingExpenses(true);
        logger.info(`[Expenses Fetch] Starting for date: ${date}`);
        
        // Validate date
        if (!date) {
          error(t('accounting.net.error_no_date'));
          logger.error('[Expenses Fetch] No date selected');
          return;
        }
        
        // Calculate total expenses in USD for the selected date from expenses state
        const filteredExpenses = expenses.filter(exp => exp.payment_date === date && exp.status === 'paid');
        logger.info(`[Expenses Fetch] Found ${filteredExpenses.length} paid expenses for ${date}`);
        
        if (filteredExpenses.length === 0) {
          info(t('accounting.net.info_no_expenses_found'));
          logger.info('[Expenses Fetch] No paid expenses found for this date');
          setExpensesUsd('0');
          setIsSaved(false);
          setJustFetchedData(true);
          setTimeout(() => fetchNet(), 100);
          return;
        }
        
        const dailyTotal = filteredExpenses.reduce((sum, exp) => {
          const amount = exp.amount_usd || 0;
          // Validate amount is a valid number
          if (isNaN(amount) || amount < 0) {
            logger.warn(`[Expenses Fetch] Invalid amount for expense ID ${exp.id}: ${amount}`);
            return sum;
          }
          return sum + amount;
        }, 0);
        
        // Validate calculated total
        if (isNaN(dailyTotal)) {
          error(t('accounting.net.error_invalid_calculation'));
          logger.error('[Expenses Fetch] Calculated total is NaN');
          return;
        }
        
        const formattedTotal = dailyTotal.toFixed(2);
        logger.info(`[Expenses Fetch] Total calculated: $${formattedTotal}`);
        setExpensesUsd(String(formattedTotal));
        setIsSaved(false);
        setJustFetchedData(true); // Prevent fetchNet from overwriting
        
        // Show success with actual value
        if (dailyTotal > 0) {
          success(`${t('accounting.net.success_expenses_fetched')}: $${formattedTotal}`);
        } else {
          info(`${t('accounting.net.info_expenses_zero')}: $${formattedTotal}`);
        }
        
        // Recalculate result immediately with explicit overrides (no race)
        fetchNetWithParams({ expenses_usd: formattedTotal });
        // Clear protection shortly after
        setTimeout(() => {
          setJustFetchedData(false);
          logger.info('[Expenses Fetch] Protection flag cleared');
        }, 500);
      } catch (e: any) {
        const errorMsg = e?.message || 'Unknown error';
        logger.error('[Expenses Fetch] Failed to calculate daily expenses:', {
          error: errorMsg,
          date,
          expensesCount: expenses.length
        });
        error(t('accounting.net.error_fetch_expenses'));
      } finally {
        setFetchingExpenses(false);
      }
    };

    const fetchDailyNetCash = async () => {
      try {
        setFetchingExpenses(true);
        logger.info(`[Net Cash Fetch] Starting for date: ${date}`);
        
        // Validate date
        if (!date) {
          error(t('accounting.net.error_no_date'));
          logger.error('[Net Cash Fetch] No date selected');
          return;
        }
        
        // Load transactions from localStorage
        const savedTransactions = localStorage.getItem('pipeline_transactions_data');
        if (!savedTransactions) {
          info(t('accounting.net.info_no_transactions_found'));
          logger.info('[Net Cash Fetch] No transactions found in localStorage');
          setNetCashUsd('0');
          setIsSaved(false);
          setJustFetchedData(true);
          setTimeout(() => fetchNet(), 100);
          return;
        }
        
        let transactions;
        try {
          transactions = JSON.parse(savedTransactions);
          if (!Array.isArray(transactions)) {
            throw new Error('Invalid transactions data format');
          }
        } catch (parseError) {
          error(t('accounting.net.error_invalid_data'));
          logger.error('[Net Cash Fetch] Failed to parse transactions:', parseError);
          return;
        }
        
        // Filter all transactions for the selected date (all currencies)
        const dailyTransactions = transactions.filter((txn: any) => txn.date === date);
        
        logger.info(`[Net Cash Fetch] Found ${dailyTransactions.length} transactions for ${date}`);
        
        if (dailyTransactions.length === 0) {
          info(t('accounting.net.info_no_transactions_for_date'));
          logger.info('[Net Cash Fetch] No transactions found for this date');
          setNetCashUsd('0');
          setIsSaved(false);
          setJustFetchedData(true);
          setTimeout(() => fetchNet(), 100);
          return;
        }
        
        // Get exchange rate for the date (try to get from API or use default)
        let exchangeRate = 42.00; // Default fallback
        let rateSource = 'default';
        
        try {
          const rateResp = await api.get(`/api/v1/exchange-rates/historical?date=${date}&pair=USDTRY`);
          const rateData = await api.parseResponse(rateResp);
          if (rateData && rateData.rate) {
            exchangeRate = parseFloat(rateData.rate);
            if (isNaN(exchangeRate) || exchangeRate <= 0) {
              logger.warn('[Net Cash Fetch] Invalid exchange rate from API, using default');
              exchangeRate = 42.00;
            } else {
              rateSource = 'api';
            }
          }
        } catch (e) {
          logger.warn('[Net Cash Fetch] Failed to fetch exchange rate, using default:', exchangeRate);
          info(t('accounting.net.info_using_default_rate'));
        }
        
        logger.info(`[Net Cash Fetch] Using exchange rate: ${exchangeRate} (source: ${rateSource})`);
        
        let totalUSD = 0;
        let invalidTransactions = 0;
        
        // Calculate gross amount for each transaction
        dailyTransactions.forEach((txn: any) => {
          const amount = txn.amount || 0;
          const currency = txn.currency || 'TL';
          
          // Validate amount
          if (isNaN(amount)) {
            invalidTransactions++;
            logger.warn(`[Net Cash Fetch] Invalid amount in transaction:`, txn);
            return;
          }
          
          let amountInUSD = 0;
          
          if (currency === 'USD') {
            amountInUSD = amount;
          } else if (currency === 'TL' || currency === 'TRY') {
            // Convert TRY to USD
            amountInUSD = amount / exchangeRate;
          } else if (currency === 'EUR') {
            // For EUR, approximate conversion (can be improved later)
            amountInUSD = amount * 1.1; // Rough EUR to USD
          } else {
            logger.warn(`[Net Cash Fetch] Unknown currency: ${currency}, skipping transaction`);
            invalidTransactions++;
            return;
          }
          
          totalUSD += amountInUSD;
        });
        
        if (invalidTransactions > 0) {
          logger.warn(`[Net Cash Fetch] Skipped ${invalidTransactions} invalid transactions`);
        }
        
        // Validate total
        if (isNaN(totalUSD)) {
          error(t('accounting.net.error_invalid_calculation'));
          logger.error('[Net Cash Fetch] Calculated total is NaN');
          return;
        }
        
        const formattedTotal = totalUSD.toFixed(2);
        logger.info(`[Net Cash Fetch] Calculated Total USD (gross): $${formattedTotal}`);
        
        setNetCashUsd(String(formattedTotal));
        setIsSaved(false);
        setJustFetchedData(true); // Prevent fetchNet from overwriting
        
        // Show success with actual value
        if (totalUSD !== 0) {
          success(`${t('accounting.net.success_net_cash_fetched')}: $${formattedTotal} (${dailyTransactions.length} transactions)`);
        } else {
          info(`${t('accounting.net.info_net_cash_zero')}: ${dailyTransactions.length} transactions found but total is $0.00`);
        }
        
        // Recalculate with explicit overrides (avoid race)
        fetchNetWithParams({ net_cash_usd: formattedTotal });
        setTimeout(() => {
          setJustFetchedData(false);
          logger.info('[Net Cash Fetch] Protection flag cleared');
        }, 500);
      } catch (e: any) {
        const errorMsg = e?.message || 'Unknown error';
        logger.error('[Net Cash Fetch] Failed to calculate daily net cash:', {
          error: errorMsg,
          date
        });
        error(t('accounting.net.error_fetch_net_cash'));
      } finally {
        setFetchingExpenses(false);
      }
    };

    const fetchDailyCommission = async () => {
      try {
        setFetchingExpenses(true);
        logger.info(`[Commission Fetch] Starting for date: ${date}`);
        
        // Validate date
        if (!date) {
          error(t('accounting.net.error_no_date'));
          logger.error('[Commission Fetch] No date selected');
          return;
        }
        
        // Load transactions from localStorage
        const savedTransactions = localStorage.getItem('pipeline_transactions_data');
        if (!savedTransactions) {
          info(t('accounting.net.info_no_transactions_found'));
          logger.info('[Commission Fetch] No transactions found in localStorage');
          setCommissionUsd('0');
          setIsSaved(false);
          setJustFetchedData(true);
          setTimeout(() => fetchNet(), 100);
          return;
        }
        
        let transactions;
        try {
          transactions = JSON.parse(savedTransactions);
          if (!Array.isArray(transactions)) {
            throw new Error('Invalid transactions data format');
          }
        } catch (parseError) {
          error(t('accounting.net.error_invalid_data'));
          logger.error('[Commission Fetch] Failed to parse transactions:', parseError);
          return;
        }
        
        // Filter all transactions for the selected date
        const dailyTransactions = transactions.filter((txn: any) => txn.date === date);
        
        logger.info(`[Commission Fetch] Found ${dailyTransactions.length} transactions for ${date}`);
        
        if (dailyTransactions.length === 0) {
          info(t('accounting.net.info_no_transactions_for_date'));
          logger.info('[Commission Fetch] No transactions found for this date');
          setCommissionUsd('0');
          setIsSaved(false);
          setJustFetchedData(true);
          setTimeout(() => fetchNet(), 100);
          return;
        }
        
        // Get exchange rate for the date
        let exchangeRate = 42.00; // Default fallback
        let rateSource = 'default';
        
        try {
          const rateResp = await api.get(`/api/v1/exchange-rates/historical?date=${date}&pair=USDTRY`);
          const rateData = await api.parseResponse(rateResp);
          if (rateData && rateData.rate) {
            exchangeRate = parseFloat(rateData.rate);
            if (isNaN(exchangeRate) || exchangeRate <= 0) {
              logger.warn('[Commission Fetch] Invalid exchange rate from API, using default');
              exchangeRate = 42.00;
            } else {
              rateSource = 'api';
            }
          }
        } catch (e) {
          logger.warn('[Commission Fetch] Failed to fetch exchange rate, using default:', exchangeRate);
          info(t('accounting.net.info_using_default_rate'));
        }
        
        logger.info(`[Commission Fetch] Using exchange rate: ${exchangeRate} (source: ${rateSource})`);
        
        let totalCommissionUSD = 0;
        let invalidTransactions = 0;
        let transactionsWithCommission = 0;
        
        // Calculate total commission for each transaction
        dailyTransactions.forEach((txn: any) => {
          const commission = txn.commission || 0;
          const currency = txn.currency || 'TL';
          
          // Validate commission
          if (isNaN(commission)) {
            invalidTransactions++;
            logger.warn(`[Commission Fetch] Invalid commission in transaction:`, txn);
            return;
          }
          
          // Skip if no commission
          if (commission === 0) {
            return;
          }
          
          transactionsWithCommission++;
          let commissionInUSD = 0;
          
          if (currency === 'USD') {
            commissionInUSD = Math.abs(commission);
          } else if (currency === 'TL' || currency === 'TRY') {
            // Convert TRY commission to USD
            commissionInUSD = Math.abs(commission) / exchangeRate;
          } else if (currency === 'EUR') {
            // For EUR, approximate conversion
            commissionInUSD = Math.abs(commission) * 1.1;
          } else {
            logger.warn(`[Commission Fetch] Unknown currency: ${currency}, skipping transaction`);
            invalidTransactions++;
            return;
          }
          
          totalCommissionUSD += commissionInUSD;
        });
        
        if (invalidTransactions > 0) {
          logger.warn(`[Commission Fetch] Skipped ${invalidTransactions} invalid transactions`);
        }
        
        logger.info(`[Commission Fetch] ${transactionsWithCommission} transactions had commissions out of ${dailyTransactions.length}`);
        
        // Validate total
        if (isNaN(totalCommissionUSD)) {
          error(t('accounting.net.error_invalid_calculation'));
          logger.error('[Commission Fetch] Calculated total is NaN');
          return;
        }
        
        const formattedTotal = totalCommissionUSD.toFixed(2);
        logger.info(`[Commission Fetch] Calculated Total Commission USD: $${formattedTotal}`);
        
        setCommissionUsd(String(formattedTotal));
        setIsSaved(false);
        setJustFetchedData(true); // Prevent fetchNet from overwriting
        
        // Show success with actual value
        if (totalCommissionUSD > 0) {
          success(`${t('accounting.net.success_commission_fetched')}: $${formattedTotal} (${transactionsWithCommission} txns with commission)`);
        } else {
          info(`${t('accounting.net.info_commission_zero')}: No commissions found in ${dailyTransactions.length} transactions`);
        }
        
        // Recalculate with explicit overrides (avoid race)
        fetchNetWithParams({ commissions_usd: formattedTotal });
        setTimeout(() => {
          setJustFetchedData(false);
          logger.info('[Commission Fetch] Protection flag cleared');
        }, 500);
      } catch (e: any) {
        const errorMsg = e?.message || 'Unknown error';
        logger.error('[Commission Fetch] Failed to calculate daily commission:', {
          error: errorMsg,
          date
        });
        error(t('accounting.net.error_fetch_commission'));
      } finally {
        setFetchingExpenses(false);
      }
    };

    const fetchAllData = async () => {
      if (!date) {
        error(t('accounting.net.error_no_date'));
        return;
      }
      
      setFetchingExpenses(true);
      logger.info(`[Fetch All] Starting auto-fetch for date: ${date}`);
      
      const results = {
        expenses: { success: false, value: '0', message: '' },
        netCash: { success: false, value: '0', message: '' },
        commission: { success: false, value: '0', message: '' }
      };
      
      // Fetch Expenses
      try {
        const filteredExpenses = expenses.filter(exp => exp.payment_date === date && exp.status === 'paid');
        if (filteredExpenses.length === 0) {
          results.expenses = { success: true, value: '0', message: t('accounting.net.info_no_expenses_found') };
          setExpensesUsd('0'); // Always update state
        } else {
          const dailyTotal = filteredExpenses.reduce((sum, exp) => sum + (exp.amount_usd || 0), 0);
          const formattedTotal = dailyTotal.toFixed(2);
          results.expenses = { success: true, value: formattedTotal, message: `${filteredExpenses.length} expense(s): $${formattedTotal}` };
          setExpensesUsd(formattedTotal); // Update state with calculated value
          logger.info(`[Fetch All] Expenses state updated to: $${formattedTotal}`);
        }
      } catch (e: any) {
        results.expenses = { success: false, value: '0', message: 'Failed to fetch expenses' };
        setExpensesUsd('0'); // Reset on error
        logger.error('[Fetch All] Expenses fetch failed:', e);
      }
      
      // Fetch Net Cash
      try {
        const savedTransactions = localStorage.getItem('pipeline_transactions_data');
        if (!savedTransactions) {
          results.netCash = { success: true, value: '0', message: t('accounting.net.info_no_transactions_found') };
          setNetCashUsd('0'); // Always update state
        } else {
          const transactions = JSON.parse(savedTransactions);
          const dailyTransactions = transactions.filter((txn: any) => txn.date === date);
          
          if (dailyTransactions.length === 0) {
            results.netCash = { success: true, value: '0', message: t('accounting.net.info_no_transactions_for_date') };
            setNetCashUsd('0'); // Always update state
          } else {
            let exchangeRate = 42.00;
            try {
              const rateResp = await api.get(`/api/v1/exchange-rates/historical?date=${date}&pair=USDTRY`);
              const rateData = await api.parseResponse(rateResp);
              if (rateData && rateData.rate && !isNaN(parseFloat(rateData.rate))) {
                exchangeRate = parseFloat(rateData.rate);
              }
            } catch (e) {
              // Use default rate
            }
            
            let totalUSD = 0;
            dailyTransactions.forEach((txn: any) => {
              const amount = txn.amount || 0;
              const currency = txn.currency || 'TL';
              let amountInUSD = 0;
              
              if (currency === 'USD') amountInUSD = amount;
              else if (currency === 'TL' || currency === 'TRY') amountInUSD = amount / exchangeRate;
              else if (currency === 'EUR') amountInUSD = amount * 1.1;
              
              totalUSD += amountInUSD;
            });
            
            const formattedTotal = totalUSD.toFixed(2);
            results.netCash = { success: true, value: formattedTotal, message: `${dailyTransactions.length} transaction(s): $${formattedTotal}` };
            setNetCashUsd(formattedTotal); // Update state with calculated value
            logger.info(`[Fetch All] Net Cash state updated to: $${formattedTotal}`);
          }
        }
      } catch (e: any) {
        results.netCash = { success: false, value: '0', message: 'Failed to fetch net cash' };
        setNetCashUsd('0'); // Reset on error
        logger.error('[Fetch All] Net cash fetch failed:', e);
      }
      
      // Fetch Commission
      try {
        const savedTransactions = localStorage.getItem('pipeline_transactions_data');
        if (!savedTransactions) {
          results.commission = { success: true, value: '0', message: t('accounting.net.info_no_transactions_found') };
          setCommissionUsd('0'); // Always update state
        } else {
          const transactions = JSON.parse(savedTransactions);
          const dailyTransactions = transactions.filter((txn: any) => txn.date === date);
          
          if (dailyTransactions.length === 0) {
            results.commission = { success: true, value: '0', message: t('accounting.net.info_no_transactions_for_date') };
            setCommissionUsd('0'); // Always update state
          } else {
            let exchangeRate = 42.00;
            try {
              const rateResp = await api.get(`/api/v1/exchange-rates/historical?date=${date}&pair=USDTRY`);
              const rateData = await api.parseResponse(rateResp);
              if (rateData && rateData.rate && !isNaN(parseFloat(rateData.rate))) {
                exchangeRate = parseFloat(rateData.rate);
              }
            } catch (e) {
              // Use default rate
            }
            
            let totalCommissionUSD = 0;
            let transactionsWithCommission = 0;
            
            dailyTransactions.forEach((txn: any) => {
              const commission = txn.commission || 0;
              const currency = txn.currency || 'TL';
              
              if (commission === 0) return;
              transactionsWithCommission++;
              
              let commissionInUSD = 0;
              if (currency === 'USD') commissionInUSD = Math.abs(commission);
              else if (currency === 'TL' || currency === 'TRY') commissionInUSD = Math.abs(commission) / exchangeRate;
              else if (currency === 'EUR') commissionInUSD = Math.abs(commission) * 1.1;
              
              totalCommissionUSD += commissionInUSD;
            });
            
            const formattedTotal = totalCommissionUSD.toFixed(2);
            results.commission = { success: true, value: formattedTotal, message: `${transactionsWithCommission} txn(s) with commission: $${formattedTotal}` };
            setCommissionUsd(formattedTotal); // Update state with calculated value
            logger.info(`[Fetch All] Commission state updated to: $${formattedTotal}`);
          }
        }
      } catch (e: any) {
        results.commission = { success: false, value: '0', message: 'Failed to fetch commission' };
        setCommissionUsd('0'); // Reset on error
        logger.error('[Fetch All] Commission fetch failed:', e);
      }
      
      setFetchingExpenses(false);
      setIsSaved(false);
      setJustFetchedData(true); // Prevent fetchNet from overriding freshly fetched values
      logger.info('[Fetch All] Protection flag SET - values will be protected from overwrite');
      
      // Build notification message
      const successCount = [results.expenses.success, results.netCash.success, results.commission.success].filter(Boolean).length;
      
      logger.info('[Fetch All] Completed:', results);
      logger.info('[Fetch All] Final state values that were SET:', {
        expensesUsd: results.expenses.value,
        netCashUsd: results.netCash.value,
        commissionUsd: results.commission.value
      });

      // Recalculate with explicit overrides to reflect values immediately
      fetchNetWithParams({
        expenses_usd: results.expenses.value,
        net_cash_usd: results.netCash.value,
        commissions_usd: results.commission.value,
      });
      // Clear protection shortly after
      setTimeout(() => {
        setJustFetchedData(false);
        logger.info('[Fetch All] Protection flag cleared');
      }, 500);
      
      if (successCount === 3) {
        // All successful
        const messages = [
          `✓ Expenses: ${results.expenses.message}`,
          `✓ Net Cash: ${results.netCash.message}`,
          `✓ Commission: ${results.commission.message}`
        ];
        success(`${t('accounting.net.fetch_all_success')}\n${messages.join('\n')}\n\n${t('accounting.net.click_calculate_to_proceed')}`);
      } else if (successCount > 0) {
        // Partial success
        const successMsgs = [];
        const failMsgs = [];
        
        if (results.expenses.success) successMsgs.push(`✓ Expenses: ${results.expenses.message}`);
        else failMsgs.push(`✗ Expenses: ${results.expenses.message}`);
        
        if (results.netCash.success) successMsgs.push(`✓ Net Cash: ${results.netCash.message}`);
        else failMsgs.push(`✗ Net Cash: ${results.netCash.message}`);
        
        if (results.commission.success) successMsgs.push(`✓ Commission: ${results.commission.message}`);
        else failMsgs.push(`✗ Commission: ${results.commission.message}`);
        
        info(`${t('accounting.net.fetch_all_partial')}\n${successMsgs.join('\n')}\n${failMsgs.join('\n')}\n\n${t('accounting.net.click_calculate_to_proceed')}`);
      } else {
        // All failed
        error(`${t('accounting.net.fetch_all_failed')}\n✗ Expenses: ${results.expenses.message}\n✗ Net Cash: ${results.netCash.message}\n✗ Commission: ${results.commission.message}`);
      }
    };

    const fetchCryptoBalance = async (isAutoFetch: boolean = false) => {
      try {
        setFetchingCryptoBalance(true);
        logger.info(`[Crypto Balance] ${isAutoFetch ? 'Auto-fetching' : 'Fetching'} total balance from all active wallets`);
        
        const resp = await api.get('/accounting/crypto-balance');
        const data = await api.parseResponse(resp);
        
        if (data && data.success) {
          const totalUsd = data.data.total_usd || 0;
          const formattedTotal = totalUsd.toFixed(2);
          logger.info(`[Crypto Balance] Total fetched: $${formattedTotal}`);
          
          setCryptoBalanceUsd(formattedTotal);
          setIsSaved(false);
          
          // Auto-calculate anlikKasaUsd = companyCashUsd + cryptoBalanceUsd
          const newAnlikKasa = (parseFloat(companyCashUsd || '0') + parseFloat(formattedTotal)).toFixed(2);
          setAnlikKasaUsd(newAnlikKasa);
          
          // Only show success message on manual fetch
          if (!isAutoFetch) {
            success(`Crypto Balance Fetched: $${formattedTotal} (${data.data.wallet_count} wallets)`);
          }
          
          // Recalculate with new values
          fetchNetWithParams({ 
            crypto_balance_usd: formattedTotal,
            anlik_kasa_usd: newAnlikKasa
          });
        } else {
          if (!isAutoFetch) {
            error('Failed to fetch crypto balance');
          }
        }
      } catch (e: any) {
        logger.error('[Crypto Balance] Failed to fetch:', e);
        // Only show error on manual fetch
        if (!isAutoFetch) {
          error(e?.message || 'Failed to fetch crypto balance');
        }
      } finally {
        setFetchingCryptoBalance(false);
      }
    };

    const loadPreviousClosing = async () => {
      try {
        logger.info('[Previous Closing] Loading from previous day');
        
        // Calculate previous day
        const currentDate = new Date(date);
        currentDate.setDate(currentDate.getDate() - 1);
        const previousDate = currentDate.toISOString().slice(0, 10);
        
        logger.info(`[Previous Closing] Previous date: ${previousDate}`);
        
        const resp = await api.get(`/accounting/net?date=${previousDate}`);
        const data = await api.parseResponse(resp);
        
        if (data && data.success && data.data) {
          const previousAnlikKasa = data.data.anlik_kasa_usd || 0;
          const formattedValue = previousAnlikKasa.toFixed(2);
          logger.info(`[Previous Closing] Loaded: $${formattedValue}`);
          
          setOncekiKapanisUsd(formattedValue);
          setIsSaved(false);
          
          success(`Previous Closing Loaded: $${formattedValue}`);
          
          // Recalculate with new value
          fetchNetWithParams({ onceki_kapanis_usd: formattedValue });
        } else {
          info('No data found for previous day');
          setOncekiKapanisUsd('0');
        }
      } catch (e: any) {
        logger.error('[Previous Closing] Failed to load:', e);
        error(e?.message || 'Failed to load previous closing');
      }
    };

    // Auto-calculate anlikKasaUsd when companyCashUsd or cryptoBalanceUsd changes (only if not in manual mode)
    React.useEffect(() => {
      if (anlikKasaManual) {
        // Skip auto-calculation when manual mode is enabled
        return;
      }
      const companyCash = parseFloat(companyCashUsd || '0');
      const cryptoBalance = parseFloat(cryptoBalanceUsd || '0');
      const calculatedAnlikKasa = (companyCash + cryptoBalance).toFixed(2);
      
      if (anlikKasaUsd !== calculatedAnlikKasa) {
        logger.info(`[Auto Calculate] Updating Anlik Kasa: ${companyCash} + ${cryptoBalance} = ${calculatedAnlikKasa}`);
        setAnlikKasaUsd(calculatedAnlikKasa);
      }
    }, [companyCashUsd, cryptoBalanceUsd, anlikKasaManual]);

    const handleToggleManualMode = () => {
      if (!anlikKasaManual) {
        // Enable manual mode - show confirmation code modal
        setShowManualCodeModal(true);
      } else {
        // Disable manual mode - reset to auto-calculated
        setAnlikKasaManual(false);
        setManualConfirmationCode('');
        // Recalculate based on company cash + crypto balance
        const calculated = (parseFloat(companyCashUsd) || 0) + (parseFloat(cryptoBalanceUsd) || 0);
        setAnlikKasaUsd(String(calculated));
        setIsSaved(false);
      }
    };

    const handleConfirmManualMode = async () => {
      const isValid = await validatePin(manualConfirmationCode);
      if (isValid) {
        setAnlikKasaManual(true);
        setShowManualCodeModal(false);
        setManualConfirmationCode('');
        setIsSaved(false);
      } else {
        error(t('accounting.net.invalid_confirmation_code') || 'Invalid confirmation code. Please enter the correct 4-digit code.');
        setManualConfirmationCode('');
      }
    };

    const handleDeleteAll = () => {
      setShowDeleteModal(true);
    };

    const handleConfirmDelete = async () => {
      const isValid = await validatePin(deleteSecurityCode);
      if (isValid) {
        // Clear all input values
        setExpensesUsd('0');
        setRolloverUsd('0');
        setNetCashUsd('0');
        setCommissionUsd('0');
        setOncekiKapanisUsd('0');
        setCompanyCashUsd('0');
        setCryptoBalanceUsd('0');
        setAnlikKasaUsd('0');
        setBekleyenTahsilatUsd('0');
        setAnlikKasaManual(false);
        setIsSaved(false);
        setResult(null);
        setShowDeleteModal(false);
        setDeleteSecurityCode('');
        
        // Clear localStorage for current date
        saveValuesToStorage(date, {
          expensesUsd: '0',
          rolloverUsd: '0',
          netCashUsd: '0',
          commissionUsd: '0',
          oncekiKapanisUsd: '0',
          companyCashUsd: '0',
          cryptoBalanceUsd: '0',
          anlikKasaUsd: '0',
          bekleyenTahsilatUsd: '0',
          anlikKasaManual: false
        });
        
        success(t('accounting.net.all_values_deleted'));
        // Recalculate with cleared values
        setTimeout(() => fetchNet(), 100);
      } else {
        error(t('accounting.net.invalid_confirmation_code') || 'Invalid confirmation code. Please enter the correct 4-digit code.');
        setDeleteSecurityCode('');
      }
    };

    const saveNet = async () => {
      if (!result) {
        setErrorNet(t('accounting.net.please_calculate_first'));
        return;
      }
      
      try {
        setSavingNet(true);
        setErrorNet(null);
        const resp = await api.post(`/accounting/net`, {
          date: result.date,
          net_cash_usd: result.net_cash_usd,
          expenses_usd: result.expenses_usd,
          commissions_usd: result.commissions_usd,
          rollover_usd: result.rollover_usd,
          net_saglama_usd: result.net_saglama_usd,
          onceki_kapanis_usd: result.onceki_kapanis_usd,
          company_cash_usd: result.company_cash_usd,
          crypto_balance_usd: result.crypto_balance_usd,
          anlik_kasa_usd: anlikKasaUsd || result.anlik_kasa_usd,
          anlik_kasa_manual: anlikKasaManual,
          confirmation_code: anlikKasaManual ? '4561' : '',
          bekleyen_tahsilat_usd: result.bekleyen_tahsilat_usd,
          fark_usd: result.fark_usd,
          fark_bottom_usd: result.fark_bottom_usd,
        });
        const data = await api.parseResponse(resp);
        if (data && data.success) {
          setIsSaved(true);
          success(t('accounting.net.saved_successfully'));
        } else {
          setErrorNet(t('accounting.net.calculation_failed'));
        }
      } catch (e: any) {
        setErrorNet(e?.message || t('accounting.net.calculation_failed'));
      } finally {
        setSavingNet(false);
      }
    };

    useEffect(() => {
      if (isInitialMount.current) {
        isInitialMount.current = false;
        logger.info('[Net Tab] Initial mount - fetching net data for date:', date);
        setIsSaved(false);
        fetchNet();
        // Auto-fetch crypto balance on initial load
        fetchCryptoBalance(true);
      } else {
        logger.info('[Net Tab] Date changed to:', date);
        setIsSaved(false);
        // DON'T clear justFetchedData here - it should only be cleared manually
        fetchNet();
        // Auto-fetch crypto balance when date changes
        fetchCryptoBalance(true);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [date]);

    // Sync calendar month when date changes externally
    useEffect(() => {
      if (date) {
        const dateObj = new Date(date);
        setCurrentMonth(new Date(dateObj.getFullYear(), dateObj.getMonth(), 1));
      }
    }, [date]);

    // Load record from Daily Net when recordToLoad is set
    useEffect(() => {
      if (recordToLoad) {
        logger.info('[Load Record] Loading record into calculator:', recordToLoad);
        
        // First, save the record values to localStorage for the target date
        // This ensures when we change the date, the values will be loaded from localStorage
        const recordValues = {
          expensesUsd: String(recordToLoad.expenses_usd || '0'),
          rolloverUsd: String(recordToLoad.rollover_usd || '0'),
          netCashUsd: String(recordToLoad.net_cash_usd || '0'),
          commissionUsd: String(recordToLoad.commissions_usd || '0'),
          oncekiKapanisUsd: String(recordToLoad.onceki_kapanis_usd || '0'),
          companyCashUsd: String(recordToLoad.company_cash_usd || '0'),
          cryptoBalanceUsd: String(recordToLoad.crypto_balance_usd || '0'),
          anlikKasaUsd: String(recordToLoad.anlik_kasa_usd || '0'),
          bekleyenTahsilatUsd: String(recordToLoad.bekleyen_tahsilat_usd || '0'),
          anlikKasaManual: recordToLoad.anlik_kasa_manual || false
        };
        
        // Save to localStorage first
        saveValuesToStorage(recordToLoad.date, recordValues);
        
        // Now set the date - this will trigger the date useEffect which will load from localStorage
        setDate(recordToLoad.date);
        
        // Mark as not saved (user can modify and re-save)
        setIsSaved(false);
        
        // Notify parent that record has been loaded
        onRecordLoaded();
        
        success(`Loaded record for ${recordToLoad.date}`);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [recordToLoad]);

    // Save values to localStorage whenever they change (debounced)
    useEffect(() => {
      // Skip saving on initial mount
      if (isInitialMount.current) {
        return;
      }
      
      // Debounce saving to avoid too many writes
      const timeoutId = setTimeout(() => {
        saveValuesToStorage(date, {
          expensesUsd,
          rolloverUsd,
          netCashUsd,
          commissionUsd,
          oncekiKapanisUsd,
          companyCashUsd,
          cryptoBalanceUsd,
          anlikKasaUsd,
          bekleyenTahsilatUsd,
          anlikKasaManual
        });
      }, 500); // Save 500ms after user stops typing
      
      return () => clearTimeout(timeoutId);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [date, expensesUsd, rolloverUsd, netCashUsd, commissionUsd, oncekiKapanisUsd, companyCashUsd, cryptoBalanceUsd, anlikKasaUsd, bekleyenTahsilatUsd, anlikKasaManual]);

    // Auto-save draft to database every 15 minutes
    useEffect(() => {
      // Skip if no result calculated yet or if already saved
      if (!result || isSaved) {
        return;
      }

      const autoSaveInterval = setInterval(async () => {
        // Only auto-save if there's a valid result and it's not already saved
        if (result && !isSaved) {
          try {
            logger.info('[Auto-save] Saving draft to database...');
            await saveNet();
            info('Draft auto-saved successfully');
          } catch (e) {
            logger.error('[Auto-save] Failed to save draft:', e);
          }
        }
      }, 15 * 60 * 1000); // 15 minutes in milliseconds

      return () => clearInterval(autoSaveInterval);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [result, isSaved]);

    // Calendar functions
    const getDaysInMonth = (date: Date): number => {
      return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
    };

    const getFirstDayOfMonth = (date: Date): number => {
      return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
    };

    const formatDateForInput = (selectedDate: Date): string => {
      const year = selectedDate.getFullYear();
      const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
      const day = String(selectedDate.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    const handleDateSelect = (day: number) => {
      const selectedDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
      setDate(formatDateForInput(selectedDate));
      setShowCalendar(false);
    };

    const navigateMonth = (direction: 'prev' | 'next') => {
      setCurrentMonth(prev => {
        const newDate = new Date(prev);
        if (direction === 'prev') {
          newDate.setMonth(prev.getMonth() - 1);
        } else {
          newDate.setMonth(prev.getMonth() + 1);
        }
        return newDate;
      });
    };

    const selectedDateObj = date ? new Date(date) : new Date();
    const daysInMonth = getDaysInMonth(currentMonth);
    const firstDay = getFirstDayOfMonth(currentMonth);
    const monthName = currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const days: (number | null)[] = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }
    
    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(day);
    }

    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        const target = event.target as HTMLElement;
        if (showCalendar && !target.closest('.calendar-container')) {
          setShowCalendar(false);
        }
      };
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showCalendar]);

    return (
      <div className="space-y-5">
        {/* Header Section with Date and Actions */}
        <UnifiedCard variant="flat">
          <div className="p-5">
            <div className="flex items-center justify-between gap-6">
              {/* Left: Title and Date Selector */}
              <div className="flex items-center gap-4 flex-1">
                <div className="p-2.5 bg-gray-100 rounded-lg">
                  <Calendar className="h-5 w-5 text-gray-700" />
                </div>
                <div className="flex items-center gap-4 flex-1">
                  <div className="min-w-[140px]">
                    <h3 className="text-sm font-semibold text-gray-900 mb-0.5">{t('accounting.net.calculation_date')}</h3>
                    <p className="text-xs text-gray-500">{t('accounting.net.calculation_date_desc')}</p>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="relative calendar-container">
                      <div className="relative">
                        <Input 
                          type="date" 
                          value={date} 
                          onChange={(e) => setDate(e.target.value)} 
                          className="w-[200px] pl-3 pr-10 py-2.5 text-sm border border-gray-200 rounded-lg bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none transition-all [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none [&::-webkit-inner-spin-button]:hidden [&::-webkit-outer-spin-button]:hidden"
                          style={{ colorScheme: 'light' }}
                        />
                        <button
                          type="button"
                          onClick={() => setShowCalendar(!showCalendar)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded transition-colors"
                        >
                          <Calendar className="h-4 w-4 text-gray-400" />
                        </button>
                      </div>
                    
                      {showCalendar && (
                        <div className="absolute z-50 mt-2 bg-white border border-gray-200 rounded-xl shadow-xl p-4 w-72">
                          <div className="flex items-center justify-between mb-4">
                            <button type="button" onClick={() => navigateMonth('prev')} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
                              <ChevronLeft className="h-4 w-4 text-gray-600" />
                            </button>
                            <h3 className="text-sm font-semibold text-gray-900">{monthName}</h3>
                            <button type="button" onClick={() => navigateMonth('next')} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
                              <ChevronRight className="h-4 w-4 text-gray-600" />
                            </button>
                          </div>
                          <div className="grid grid-cols-7 gap-1 mb-2">
                            {weekDays.map(day => (
                              <div key={day} className="text-xs font-medium text-gray-500 text-center py-1">{day}</div>
                            ))}
                          </div>
                          <div className="grid grid-cols-7 gap-1">
                            {days.map((day, index) => {
                              if (day === null) return <div key={index} className="h-8"></div>;
                              const isSelected = selectedDateObj.getFullYear() === currentMonth.getFullYear() && selectedDateObj.getMonth() === currentMonth.getMonth() && selectedDateObj.getDate() === day;
                              const isToday = new Date().getFullYear() === currentMonth.getFullYear() && new Date().getMonth() === currentMonth.getMonth() && new Date().getDate() === day;
                              return (
                                <button key={index} type="button" onClick={() => handleDateSelect(day)} 
                                  className={`h-8 text-sm rounded-lg transition-colors ${isSelected ? 'bg-gray-900 text-white font-semibold' : isToday ? 'bg-gray-100 text-gray-900 font-medium border border-gray-300' : 'text-gray-700 hover:bg-gray-50'}`}>
                                  {day}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* Today Button */}
                    <UnifiedButton
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const today = new Date().toISOString().slice(0, 10);
                        setDate(today);
                        logger.info('[Today Button] Date set to today:', today);
                      }}
                      disabled={fetchingExpenses}
                      className="whitespace-nowrap border-gray-300 text-gray-700 hover:bg-gray-50"
                      icon={<Calendar className="h-4 w-4" />}
                      iconPosition="left"
                    >
                      {t('accounting.net.today')}
                    </UnifiedButton>
                    
                    {/* Fetch All Button */}
                    <UnifiedButton
                      variant="primary"
                      size="sm"
                      onClick={fetchAllData}
                      disabled={fetchingExpenses || !date}
                      className="whitespace-nowrap"
                      icon={<Download className={`h-4 w-4 ${fetchingExpenses ? 'animate-pulse' : ''}`} />}
                      iconPosition="left"
                    >
                      {fetchingExpenses ? t('accounting.net.fetching_all') : t('accounting.net.fetch_all')}
                    </UnifiedButton>
                  </div>
                </div>
              </div>

              {/* Right: Saved Status */}
              {isSaved && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium text-green-700">{t('accounting.net.saved')}</span>
                </div>
              )}
            </div>
          </div>
        </UnifiedCard>

        {errorNet && (
          <UnifiedCard variant="flat">
            <div className="p-4 bg-red-50 border-l-4 border-red-500">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-red-900">{t('accounting.net.calculation_error')}</h4>
                  <p className="text-sm text-red-700 mt-1">{errorNet}</p>
                </div>
              </div>
            </div>
          </UnifiedCard>
        )}

        {/* Input Section */}
        <UnifiedCard variant="elevated">
          <div className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Receipt className="h-5 w-5 text-gray-700" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900">{t('accounting.net.transaction_data')}</h3>
                <p className="text-xs text-gray-500">{t('accounting.net.transaction_data_desc')}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Primary Inputs */}
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">{t('accounting.net.expenses')}</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <Input type="number" min="0" step="0.01" value={expensesUsd} onChange={(e) => { setExpensesUsd(e.target.value); setIsSaved(false); setJustFetchedData(false); }} onBlur={() => { if (!justFetchedData) fetchNet(); }} 
                      className="pl-8 pr-12 h-11 border-gray-200 focus:outline-none" placeholder="0.00" />
                    <button
                      type="button"
                      onClick={fetchDailyExpenses}
                      disabled={fetchingExpenses}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
                      title={t('accounting.net.auto_fill_expenses')}
                    >
                      <Download className={`h-4 w-4 text-gray-600 ${fetchingExpenses ? 'animate-pulse' : ''}`} />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">{t('accounting.net.expenses_desc')}</p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">{t('accounting.net.rollover_collection')}</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <Input type="number" min="0" step="0.01" value={rolloverUsd} onChange={(e) => { setRolloverUsd(e.target.value); setIsSaved(false); }} onBlur={fetchNet} 
                      className="pl-8 h-11 border-gray-200 focus:outline-none" placeholder="0.00" />
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">{t('accounting.net.rollover_collection_desc')}</p>
                </div>
              </div>

              {/* Override Inputs */}
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">{t('accounting.net.net_cash_override')}</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <Input type="number" min="0" step="0.01" value={netCashUsd} onChange={(e) => { setNetCashUsd(e.target.value); setIsSaved(false); setJustFetchedData(false); }} onBlur={() => { if (!justFetchedData) fetchNet(); }} 
                      className="pl-8 pr-12 h-11 border-gray-200 focus:outline-none" placeholder="0.00" />
                    <button
                      type="button"
                      onClick={fetchDailyNetCash}
                      disabled={fetchingExpenses}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
                      title={t('accounting.net.auto_fill_net_cash')}
                    >
                      <Download className={`h-4 w-4 text-gray-600 ${fetchingExpenses ? 'animate-pulse' : ''}`} />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">{t('accounting.net.net_cash_override_desc')}</p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">{t('accounting.net.commission_override')}</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <Input type="number" min="0" step="0.01" value={commissionUsd} onChange={(e) => { setCommissionUsd(e.target.value); setIsSaved(false); setJustFetchedData(false); }} onBlur={() => { if (!justFetchedData) fetchNet(); }} 
                      className="pl-8 pr-12 h-11 border-gray-200 focus:outline-none" placeholder="0.00" />
                    <button
                      type="button"
                      onClick={fetchDailyCommission}
                      disabled={fetchingExpenses}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
                      title={t('accounting.net.auto_fill_commission')}
                    >
                      <Download className={`h-4 w-4 text-gray-600 ${fetchingExpenses ? 'animate-pulse' : ''}`} />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">{t('accounting.net.commission_override_desc')}</p>
                </div>
              </div>
            </div>
          </div>
        </UnifiedCard>

        {/* Cash Balance Input Section */}
        <UnifiedCard variant="elevated">
          <div className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Wallet className="h-5 w-5 text-gray-700" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900">{t('accounting.net.cash_balance_data')}</h3>
                <p className="text-xs text-gray-500">{t('accounting.net.cash_balance_data_desc')}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-4">
                {/* Previous Closing */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">{t('accounting.net.previous_closing')}</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <Input 
                      type="number"
                      min="0"
                      step="0.01"
                      value={oncekiKapanisUsd} 
                      onChange={(e) => { setOncekiKapanisUsd(e.target.value); setIsSaved(false); }} 
                      onBlur={fetchNet} 
                      className="pl-8 pr-12 h-11 border-gray-200 focus:outline-none" 
                      placeholder="0.00" 
                    />
                    <button
                      type="button"
                      onClick={loadPreviousClosing}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 hover:bg-gray-100 rounded transition-colors"
                      title="Load from previous day"
                    >
                      <ChevronLeft className="h-4 w-4 text-gray-600" />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">{t('accounting.net.previous_closing_desc')}</p>
                </div>

                {/* Company Cash */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">Company Cash (USD)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <Input 
                      type="number"
                      min="0"
                      step="0.01"
                      value={companyCashUsd} 
                      onChange={(e) => { setCompanyCashUsd(e.target.value); setIsSaved(false); }} 
                      onBlur={fetchNet} 
                      className="pl-8 h-11 border-gray-200 focus:outline-none" 
                      placeholder="0.00" 
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">Physical cash and bank balance</p>
                </div>

                {/* Crypto Wallets Balance */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">Crypto Wallets Balance (USD)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <Input 
                      type="number"
                      min="0"
                      step="0.01"
                      value={cryptoBalanceUsd} 
                      readOnly
                      className="pl-8 pr-12 h-11 border-gray-200 bg-gray-50 focus:outline-none cursor-not-allowed" 
                      placeholder="0.00" 
                    />
                    <button
                      type="button"
                      onClick={() => fetchCryptoBalance(false)}
                      disabled={fetchingCryptoBalance}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
                      title="Refresh crypto balance"
                    >
                      <RefreshCw className={`h-4 w-4 text-gray-600 ${fetchingCryptoBalance ? 'animate-spin' : ''}`} />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">Auto-fetched from Trust wallets • Click refresh to update</p>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-4">
                {/* Current Cash (Auto-calculated or Manual) */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">
                    <div className="flex items-center justify-between">
                      <span>{t('accounting.net.current_cash')}</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-normal normal-case ${anlikKasaManual ? 'text-orange-600' : 'text-gray-500'}`}>
                          {anlikKasaManual ? 'Manual' : 'Auto'}
                        </span>
                        <button
                          type="button"
                          onClick={handleToggleManualMode}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            anlikKasaManual 
                              ? 'bg-orange-600 focus:ring-orange-500' 
                              : 'bg-gray-200 focus:ring-gray-400'
                          }`}
                          title={anlikKasaManual ? 'Switch to Auto-calculated' : 'Switch to Manual'}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                              anlikKasaManual ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                    </div>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <Input 
                      type="number"
                      min="0"
                      step="0.01"
                      value={anlikKasaUsd} 
                      readOnly={!anlikKasaManual}
                      onChange={(e) => {
                        if (anlikKasaManual) {
                          setAnlikKasaUsd(e.target.value);
                          setIsSaved(false);
                        }
                      }}
                      onBlur={() => {
                        if (anlikKasaManual) {
                          fetchNet();
                        }
                      }}
                      className={`pl-8 h-11 border-gray-200 focus:outline-none font-medium ${
                        anlikKasaManual 
                          ? 'bg-white border-orange-300 focus:border-orange-500 cursor-text' 
                          : 'bg-gray-50 cursor-not-allowed'
                      }`}
                      placeholder="0.00" 
                    />
                  </div>
                  <p className={`text-xs mt-1.5 ${anlikKasaManual ? 'text-orange-600' : 'text-gray-500'}`}>
                    {anlikKasaManual 
                      ? 'Manual override active - Enter value directly'
                      : `Company Cash + Crypto Balance = $${anlikKasaUsd || '0.00'}`
                    }
                  </p>
                </div>

                {/* Pending Collection */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">{t('accounting.net.pending_collection')}</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <Input 
                      type="number"
                      min="0"
                      step="0.01"
                      value={bekleyenTahsilatUsd} 
                      onChange={(e) => { setBekleyenTahsilatUsd(e.target.value); setIsSaved(false); }} 
                      onBlur={fetchNet} 
                      className="pl-8 h-11 border-gray-200 focus:outline-none" 
                      placeholder="0.00" 
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">{t('accounting.net.pending_collection_desc')}</p>
                </div>
              </div>
            </div>
          </div>
        </UnifiedCard>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3">
          <UnifiedButton 
            variant="outline" 
            onClick={handleDeleteAll} 
            className="min-w-[140px] text-red-600 hover:text-red-700 hover:border-red-300 border-red-300"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </UnifiedButton>
          <UnifiedButton variant="outline" onClick={() => { setJustFetchedData(false); fetchNet(); }} disabled={loadingNet} className="min-w-[140px]">
            <RefreshCw className={`h-4 w-4 mr-2 ${loadingNet ? 'animate-spin' : ''}`} />
            {loadingNet ? t('accounting.net.calculating') : t('accounting.net.calculate')}
          </UnifiedButton>
          {result && (
            <UnifiedButton variant="primary" onClick={saveNet} disabled={savingNet || loadingNet} className="min-w-[140px]">
              <CheckCircle className="h-4 w-4 mr-2" />
              {savingNet ? t('accounting.net.saving') : isSaved ? t('accounting.net.update') : t('accounting.net.save')}
            </UnifiedButton>
          )}
        </div>

        {/* Confirmation Code Modal for Manual Override */}
        {showManualCodeModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {t('accounting.net.enable_manual_mode')}
                </h3>
                <button
                  onClick={() => {
                    setShowManualCodeModal(false);
                    setManualConfirmationCode('');
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                {t('accounting.net.enter_confirmation_code')}
              </p>
              <div className="mb-4">
                <Input
                  type="text"
                  value={manualConfirmationCode}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, '').slice(0, 4);
                    setManualConfirmationCode(value);
                  }}
                  placeholder="----"
                  className="text-center text-lg font-mono tracking-widest"
                  maxLength={4}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleConfirmManualMode();
                    }
                  }}
                />
              </div>
              <div className="flex gap-3 justify-end">
                <UnifiedButton
                  variant="outline"
                  onClick={() => {
                    setShowManualCodeModal(false);
                    setManualConfirmationCode('');
                  }}
                >
                  {t('common.cancel') || 'Cancel'}
                </UnifiedButton>
                <UnifiedButton
                  variant="primary"
                  onClick={handleConfirmManualMode}
                  disabled={manualConfirmationCode.length !== 4}
                >
                  {t('common.confirm') || 'Confirm'}
                </UnifiedButton>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Delete All Values
                </h3>
                <button
                  onClick={() => {
                    setShowDeleteModal(false);
                    setDeleteSecurityCode('');
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Please enter the security code to delete all values on this page.
              </p>
              <div className="mb-4">
                <Input
                  type="text"
                  value={deleteSecurityCode}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, '').slice(0, 4);
                    setDeleteSecurityCode(value);
                  }}
                  placeholder="----"
                  className="text-center text-lg font-mono tracking-widest"
                  maxLength={4}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleConfirmDelete();
                    }
                  }}
                />
              </div>
              <div className="flex gap-3 justify-end">
                <UnifiedButton
                  variant="outline"
                  onClick={() => {
                    setShowDeleteModal(false);
                    setDeleteSecurityCode('');
                  }}
                >
                  {t('common.cancel') || 'Cancel'}
                </UnifiedButton>
                <UnifiedButton
                  variant="primary"
                  onClick={handleConfirmDelete}
                  disabled={deleteSecurityCode.length !== 4}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Delete
                </UnifiedButton>
              </div>
            </div>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <div className="space-y-5">
            {/* Components Section */}
            <UnifiedSection title={t('accounting.net.calculation_components')} description={t('accounting.net.calculation_components_desc')}>
              <UnifiedGrid cols={4} gap="md">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">{t('accounting.net.net_cash')}</p>
                      <p className="text-xl font-bold text-gray-900">${Number(result.net_cash_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</p>
                    </div>
                    <div className="p-1.5 bg-gray-100 rounded">
                      <CreditCard className="h-4 w-4 text-gray-700" />
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">{t('accounting.net.expenses')}</p>
                      <p className="text-xl font-bold text-gray-900">${Number(result.expenses_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</p>
                    </div>
                    <div className="p-1.5 bg-gray-100 rounded">
                      <ShoppingCart className="h-4 w-4 text-gray-700" />
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">{t('accounting.net.commission')}</p>
                      <p className="text-xl font-bold text-gray-900">${Number(result.commissions_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</p>
                    </div>
                    <div className="p-1.5 bg-gray-100 rounded">
                      <Award className="h-4 w-4 text-gray-700" />
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">{t('accounting.net.rollover')}</p>
                      <p className="text-xl font-bold text-gray-900">${Number(result.rollover_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</p>
                    </div>
                    <div className="p-1.5 bg-gray-100 rounded">
                      <RefreshCw className="h-4 w-4 text-gray-700" />
                    </div>
                  </div>
                </div>
              </UnifiedGrid>
            </UnifiedSection>

            {/* Net Result */}
            <UnifiedCard variant="elevated" className="overflow-hidden">
              <div className="bg-gray-50 p-6 border-l-4 border-gray-600">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-gray-100 rounded-xl">
                      <TrendingUp className="h-6 w-6 text-gray-700" />
                    </div>
                    <div>
                      <p className="text-xs font-medium text-green-700 uppercase tracking-wider mb-1">{t('accounting.net.net_result')}</p>
                      <h3 className="text-3xl font-bold text-green-900">${Number(result.net_saglama_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</h3>
                      <p className="text-xs text-green-600 mt-1">{t('accounting.net.net_saglama')}</p>
                    </div>
                  </div>
                </div>
              </div>
            </UnifiedCard>

            {/* Cash Balance Section */}
            <UnifiedSection title={t('accounting.net.cash_balance_analysis')} description={t('accounting.net.cash_balance_analysis_desc')}>
              <UnifiedGrid cols={4} gap="md">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">{t('accounting.net.previous_close')}</p>
                      <p className="text-xl font-bold text-gray-900">${Number(result.onceki_kapanis_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</p>
                    </div>
                    <div className="p-1.5 bg-gray-100 rounded">
                      <CreditCard className="h-4 w-4 text-gray-700" />
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">{t('accounting.net.current_cash_balance')}</p>
                      <p className="text-xl font-bold text-gray-900">${Number(result.anlik_kasa_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</p>
                    </div>
                    <div className="p-1.5 bg-gray-100 rounded">
                      <Wallet className="h-4 w-4 text-gray-700" />
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">{t('accounting.net.pending')}</p>
                      <p className="text-xl font-bold text-gray-900">${Number(result.bekleyen_tahsilat_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</p>
                    </div>
                    <div className="p-1.5 bg-gray-100 rounded">
                      <Clock className="h-4 w-4 text-gray-700" />
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">{t('accounting.net.difference')}</p>
                      <p className="text-xl font-bold text-gray-900">${Number(result.fark_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</p>
                    </div>
                    <div className="p-1.5 bg-gray-100 rounded">
                      <TrendingUp className="h-4 w-4 text-gray-700" />
                    </div>
                  </div>
                </div>
              </UnifiedGrid>
            </UnifiedSection>

            {/* Reconciliation */}
            <UnifiedCard variant="elevated" className="overflow-hidden">
              <div className={`p-6 border-l-4 ${Number(result.fark_bottom_usd) === 0 ? 'bg-gray-50 border-gray-600' : 'bg-gray-50 border-gray-600'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-xl ${Number(result.fark_bottom_usd) === 0 ? 'bg-gray-100' : 'bg-gray-100'}`}>
                      <AlertCircle className={`h-6 w-6 ${Number(result.fark_bottom_usd) === 0 ? 'text-gray-700' : 'text-gray-700'}`} />
                    </div>
                    <div>
                      <p className={`text-xs font-medium uppercase tracking-wider mb-1 ${Number(result.fark_bottom_usd) === 0 ? 'text-green-700' : 'text-red-700'}`}>
                        {Number(result.fark_bottom_usd) === 0 ? t('accounting.net.balanced_no_discrepancy') : t('accounting.net.reconciliation_required')}
                      </p>
                      <h3 className={`text-3xl font-bold ${Number(result.fark_bottom_usd) === 0 ? 'text-green-900' : 'text-red-900'}`}>
                        ${Number(result.fark_bottom_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                      </h3>
                      <p className={`text-xs mt-1 ${Number(result.fark_bottom_usd) === 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {t('accounting.net.reconciliation_difference_desc')}
                      </p>
                    </div>
                  </div>
                  {Number(result.fark_bottom_usd) === 0 && (
                    <div className="px-4 py-2 bg-green-100 border border-green-300 rounded-lg">
                      <span className="text-sm font-semibold text-green-800">{t('accounting.net.perfect_match')}</span>
                    </div>
                  )}
                </div>
              </div>
            </UnifiedCard>
          </div>
        )}
      </div>
    );
  }

  // Daily Net Component - Historical Records Table with Advanced Features
  function DailyNetView({ onLoadRecord, validatePin }: { onLoadRecord: (record: any) => void; validatePin: (pin: string) => Promise<boolean> }) {
    // Historical records state
    const [allRecords, setAllRecords] = useState<any[]>([]);
    const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
    const [showEditModal, setShowEditModal] = useState<boolean>(false);
    const [editingRecord, setEditingRecord] = useState<any | null>(null);
    const [editSecurityCode, setEditSecurityCode] = useState<string>('');
    
    // Filter & Search state
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [dateFrom, setDateFrom] = useState<string>('');
    const [dateTo, setDateTo] = useState<string>('');
    const [statusFilter, setStatusFilter] = useState<'all' | 'balanced' | 'unbalanced'>('all');
    
    // Sorting state
    const [sortColumn, setSortColumn] = useState<string>('date');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
    
    // Pagination state
    const [currentPage, setCurrentPage] = useState<number>(1);
    const RECORDS_PER_PAGE = 50;
    
    // Comparison state
    const [showComparisonModal, setShowComparisonModal] = useState<boolean>(false);
    const [comparisonDate1, setComparisonDate1] = useState<any>(null);
    const [comparisonDate2, setComparisonDate2] = useState<any>(null);

    const loadHistoricalRecords = async () => {
      try {
        setLoadingHistory(true);
        const resp = await api.get('/accounting/net/history');
        const data = await api.parseResponse(resp);
        if (data && data.success) {
          setAllRecords(data.data || []);
        }
      } catch (e: any) {
        error(e?.message || 'Failed to load historical records');
      } finally {
        setLoadingHistory(false);
      }
    };

    // Filter and search logic
    const filteredRecords = useMemo(() => {
      let filtered = [...allRecords];
      
      // Date range filter
      if (dateFrom) {
        filtered = filtered.filter(record => record.date >= dateFrom);
      }
      if (dateTo) {
        filtered = filtered.filter(record => record.date <= dateTo);
      }
      
      // Status filter
      if (statusFilter === 'balanced') {
        filtered = filtered.filter(record => Number(record.fark_bottom_usd) === 0);
      } else if (statusFilter === 'unbalanced') {
        filtered = filtered.filter(record => Number(record.fark_bottom_usd) !== 0);
      }
      
      // Search term (searches date, amounts)
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        filtered = filtered.filter(record => 
          record.date.includes(term) ||
          String(record.net_cash_usd).includes(term) ||
          String(record.net_saglama_usd).includes(term) ||
          String(record.fark_bottom_usd).includes(term)
        );
      }
      
      return filtered;
    }, [allRecords, dateFrom, dateTo, statusFilter, searchTerm]);

    // Sorting logic
    const sortedRecords = useMemo(() => {
      const sorted = [...filteredRecords];
      
      sorted.sort((a, b) => {
        let aVal, bVal;
        
        switch (sortColumn) {
          case 'date':
            aVal = a.date;
            bVal = b.date;
            break;
          case 'net_cash':
            aVal = Number(a.net_cash_usd);
            bVal = Number(b.net_cash_usd);
            break;
          case 'expenses':
            aVal = Number(a.expenses_usd);
            bVal = Number(b.expenses_usd);
            break;
          case 'commission':
            aVal = Number(a.commissions_usd);
            bVal = Number(b.commissions_usd);
            break;
          case 'net_saglama':
            aVal = Number(a.net_saglama_usd);
            bVal = Number(b.net_saglama_usd);
            break;
          case 'fark':
            aVal = Number(a.fark_bottom_usd);
            bVal = Number(b.fark_bottom_usd);
            break;
          default:
            aVal = a.date;
            bVal = b.date;
        }
        
        if (sortDirection === 'asc') {
          return aVal > bVal ? 1 : -1;
        } else {
          return aVal < bVal ? 1 : -1;
        }
      });
      
      return sorted;
    }, [filteredRecords, sortColumn, sortDirection]);

    // Pagination logic
    const paginatedRecords = useMemo(() => {
      const startIndex = (currentPage - 1) * RECORDS_PER_PAGE;
      const endIndex = startIndex + RECORDS_PER_PAGE;
      return sortedRecords.slice(startIndex, endIndex);
    }, [sortedRecords, currentPage]);

    const totalPages = Math.ceil(sortedRecords.length / RECORDS_PER_PAGE);

    // Handle column sort
    const handleSort = (column: string) => {
      if (sortColumn === column) {
        setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
      } else {
        setSortColumn(column);
        setSortDirection('desc');
      }
      setCurrentPage(1); // Reset to first page when sorting
    };

    // Monthly summary calculations
    const monthlySummary = useMemo(() => {
      if (sortedRecords.length === 0) return null;
      
      const totalNetSaglama = sortedRecords.reduce((sum, r) => sum + Number(r.net_saglama_usd), 0);
      const totalExpenses = sortedRecords.reduce((sum, r) => sum + Number(r.expenses_usd), 0);
      const totalNetCash = sortedRecords.reduce((sum, r) => sum + Number(r.net_cash_usd), 0);
      const balancedCount = sortedRecords.filter(r => Number(r.fark_bottom_usd) === 0).length;
      const avgNetSaglama = totalNetSaglama / sortedRecords.length;
      
      return {
        totalNetSaglama,
        totalExpenses,
        totalNetCash,
        avgNetSaglama,
        balancedCount,
        totalRecords: sortedRecords.length,
        balancedPercentage: (balancedCount / sortedRecords.length) * 100
      };
    }, [sortedRecords]);

    // Variance analysis
    const varianceAnalysis = useMemo(() => {
      if (sortedRecords.length < 2) return null;
      
      const sortedByDate = [...sortedRecords].sort((a, b) => a.date.localeCompare(b.date));
      const variances = [];
      
      for (let i = 1; i < sortedByDate.length; i++) {
        const prev = sortedByDate[i - 1];
        const curr = sortedByDate[i];
        
        const netSaglamaChange = Number(curr.net_saglama_usd) - Number(prev.net_saglama_usd);
        const netSaglamaChangePercent = (netSaglamaChange / Number(prev.net_saglama_usd)) * 100;
        
        variances.push({
          date: curr.date,
          netSaglamaChange,
          netSaglamaChangePercent: isFinite(netSaglamaChangePercent) ? netSaglamaChangePercent : 0
        });
      }
      
      return variances;
    }, [sortedRecords]);

    const handleEditRecord = (record: any) => {
      setEditingRecord(record);
      setShowEditModal(true);
    };

    const handleDeleteRecord = async () => {
      const isValid = await validatePin(editSecurityCode);
      if (!isValid) {
        error(t('accounting.net.invalid_confirmation_code') || 'Invalid confirmation code. Please enter the correct 4-digit code.');
        setEditSecurityCode('');
        return;
      }

      try {
        const resp = await api.delete(`/accounting/net/${editingRecord.date}`, {
          confirmation_code: editSecurityCode
        });
        const data = await api.parseResponse(resp) as { success?: boolean };
        if (data && data.success) {
          success('Record deleted successfully');
          loadHistoricalRecords();
          setShowEditModal(false);
          setEditingRecord(null);
          setEditSecurityCode('');
        }
      } catch (e: any) {
        error(e?.message || 'Failed to delete record');
      }
    };

    const handleLoadRecord = (record: any) => {
      // Call parent's callback to load the record
      onLoadRecord(record);
    };

    const exportToExcel = () => {
      if (sortedRecords.length === 0) return;
      
      // CSV export with filtered/sorted data
      const headers = ['Date', 'Net Cash', 'Expenses', 'Commission', 'Rollover', 'Net Sağlama', 'Current Cash', 'FARK'];
      const rows = sortedRecords.map(record => [
        new Date(record.date).toLocaleDateString(),
        Number(record.net_cash_usd).toFixed(2),
        Number(record.expenses_usd).toFixed(2),
        Number(record.commissions_usd).toFixed(2),
        Number(record.rollover_usd).toFixed(2),
        Number(record.net_saglama_usd).toFixed(2),
        Number(record.anlik_kasa_usd).toFixed(2),
        Number(record.fark_bottom_usd).toFixed(2)
      ]);
      
      const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `net_calculations_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      success(`Exported ${sortedRecords.length} records`);
    };

    const handleResetFilters = () => {
      setSearchTerm('');
      setDateFrom('');
      setDateTo('');
      setStatusFilter('all');
      setCurrentPage(1);
    };

    const handleSelectForComparison = (record: any) => {
      if (!comparisonDate1) {
        setComparisonDate1(record);
        info('Select second date to compare');
      } else if (!comparisonDate2 && record.date !== comparisonDate1.date) {
        setComparisonDate2(record);
        setShowComparisonModal(true);
      } else if (record.date === comparisonDate1.date) {
        info('Please select a different date');
      } else {
        // Reset and start over
        setComparisonDate1(record);
        setComparisonDate2(null);
        info('Select second date to compare');
      }
    };

    const resetComparison = () => {
      setComparisonDate1(null);
      setComparisonDate2(null);
      setShowComparisonModal(false);
    };

    React.useEffect(() => {
      loadHistoricalRecords();
    }, []);

    return (
      <div className="space-y-6">
        {/* Filter Bar */}
        <UnifiedCard variant="elevated">
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div>
                <label className="text-xs font-medium text-gray-700 mb-1.5 block">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    type="text"
                    placeholder="Search records..."
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="pl-10"
                  />
              </div>
              </div>

              {/* Date From */}
              <div>
                <label className="text-xs font-medium text-gray-700 mb-1.5 block">From Date</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => {
                    setDateFrom(e.target.value);
                    setCurrentPage(1);
                  }}
                />
              </div>

              {/* Date To */}
              <div>
                <label className="text-xs font-medium text-gray-700 mb-1.5 block">To Date</label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => {
                    setDateTo(e.target.value);
                    setCurrentPage(1);
                  }}
                />
              </div>

              {/* Status Filter */}
              <div>
                <label className="text-xs font-medium text-gray-700 mb-1.5 block">{t('accounting.status')}</label>
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value as 'all' | 'balanced' | 'unbalanced');
                    setCurrentPage(1);
                  }}
                  className="w-full h-10 px-3 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">{t('accounting.all_status')}</option>
                  <option value="balanced">{t('accounting.net.balanced')}</option>
                  <option value="unbalanced">{t('accounting.net.unbalanced')}</option>
                </select>
              </div>
            </div>

            {/* Filter Actions */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
              <div className="text-sm text-gray-600">
                Showing {paginatedRecords.length} of {sortedRecords.length} records
                {sortedRecords.length !== allRecords.length && ` (filtered from ${allRecords.length})`}
              </div>
              <div className="flex gap-2">
                {comparisonDate1 && (
                  <UnifiedButton variant="outline" size="sm" onClick={resetComparison}>
                    <X className="h-4 w-4 mr-1" />
                    Reset Comparison
                  </UnifiedButton>
                )}
                <UnifiedButton variant="outline" size="sm" onClick={handleResetFilters}>
                  <Filter className="h-4 w-4 mr-1" />
                  Reset Filters
                </UnifiedButton>
                <UnifiedButton variant="outline" size="sm" onClick={exportToExcel} disabled={sortedRecords.length === 0}>
                  <Download className="h-4 w-4 mr-1" />
                  Export
                </UnifiedButton>
                <UnifiedButton variant="outline" size="sm" onClick={loadHistoricalRecords} disabled={loadingHistory}>
                  <RefreshCw className={`h-4 w-4 mr-1 ${loadingHistory ? 'animate-spin' : ''}`} />
                  Refresh
                </UnifiedButton>
              </div>
            </div>
          </div>
        </UnifiedCard>

        {/* Monthly Summary Cards */}
        {monthlySummary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <UnifiedCard variant="elevated" className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600 uppercase tracking-wider">Total Net Sağlama</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">
                    ${monthlySummary.totalNetSaglama.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Across {monthlySummary.totalRecords} records</p>
                </div>
                <div className="p-2 bg-green-100 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                </div>
              </div>
            </UnifiedCard>

            <UnifiedCard variant="elevated" className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600 uppercase tracking-wider">Avg Net Sağlama</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">
                    ${monthlySummary.avgNetSaglama.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Per day average</p>
                </div>
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Activity className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            </UnifiedCard>

            <UnifiedCard variant="elevated" className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600 uppercase tracking-wider">Total Expenses</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">
                    ${monthlySummary.totalExpenses.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Total spent</p>
                </div>
                <div className="p-2 bg-red-100 rounded-lg">
                  <TrendingDown className="h-5 w-5 text-red-600" />
                </div>
              </div>
            </UnifiedCard>

            <UnifiedCard variant="elevated" className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600 uppercase tracking-wider">Balanced Days</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">
                    {monthlySummary.balancedPercentage.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{monthlySummary.balancedCount} of {monthlySummary.totalRecords} days</p>
                </div>
                <div className="p-2 bg-purple-100 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-purple-600" />
                </div>
              </div>
            </UnifiedCard>
          </div>
        )}

        {/* Charts Section */}
        {sortedRecords.length >= 2 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Net Trends Chart */}
            <UnifiedCard variant="elevated">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h4 className="text-base font-semibold text-gray-900">Net Sağlama Trends</h4>
                    <p className="text-xs text-gray-500 mt-1">Historical Net Sağlama over time</p>
                  </div>
                  <div className="p-2 bg-green-100 rounded-lg">
                    <LineChart className="h-5 w-5 text-green-600" />
                  </div>
                </div>
                <div className="h-64">
                  <p className="text-sm text-gray-500 text-center py-20">Chart visualization coming soon with Recharts</p>
                </div>
              </div>
            </UnifiedCard>

            {/* Expense vs Revenue Chart */}
            <UnifiedCard variant="elevated">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h4 className="text-base font-semibold text-gray-900">Expenses vs Net Cash</h4>
                    <p className="text-xs text-gray-500 mt-1">Comparison of expenses and revenue</p>
                  </div>
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-blue-600" />
                  </div>
                </div>
                <div className="h-64">
                  <p className="text-sm text-gray-500 text-center py-20">Chart visualization coming soon with Recharts</p>
                </div>
              </div>
            </UnifiedCard>

            {/* Variance Analysis Chart */}
            {varianceAnalysis && varianceAnalysis.length > 0 && (
              <UnifiedCard variant="elevated" className="lg:col-span-2">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h4 className="text-base font-semibold text-gray-900">Variance Analysis</h4>
                      <p className="text-xs text-gray-500 mt-1">Day-over-day Net Sağlama changes</p>
                    </div>
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Activity className="h-5 w-5 text-purple-600" />
                    </div>
                  </div>
                  
                  {/* Variance Table */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">{t('common.date')}</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-600 uppercase">Change (USD)</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-600 uppercase">Change (%)</th>
                          <th className="px-4 py-2 text-center text-xs font-medium text-gray-600 uppercase">Trend</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {varianceAnalysis.slice(0, 10).map((variance, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-2 whitespace-nowrap text-gray-900 font-medium">
                              {new Date(variance.date).toLocaleDateString()}
                            </td>
                            <td className={`px-4 py-2 whitespace-nowrap text-right font-semibold ${
                              variance.netSaglamaChange > 0 ? 'text-green-600' : variance.netSaglamaChange < 0 ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {variance.netSaglamaChange > 0 ? '+' : ''}${variance.netSaglamaChange.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                            </td>
                            <td className={`px-4 py-2 whitespace-nowrap text-right font-semibold ${
                              variance.netSaglamaChangePercent > 0 ? 'text-green-600' : variance.netSaglamaChangePercent < 0 ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {variance.netSaglamaChangePercent > 0 ? '+' : ''}{variance.netSaglamaChangePercent.toFixed(2)}%
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-center">
                              {variance.netSaglamaChange > 0 ? (
                                <TrendingUp className="h-4 w-4 text-green-600 mx-auto" />
                              ) : variance.netSaglamaChange < 0 ? (
                                <TrendingDown className="h-4 w-4 text-red-600 mx-auto" />
                              ) : (
                                <Activity className="h-4 w-4 text-gray-400 mx-auto" />
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {varianceAnalysis.length > 10 && (
                    <p className="text-xs text-gray-500 text-center mt-3">
                      Showing latest 10 changes out of {varianceAnalysis.length}
                    </p>
                  )}
                </div>
              </UnifiedCard>
            )}
          </div>
        )}

        {/* Historical Records Table */}
        <UnifiedCard variant="elevated">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-base font-semibold text-gray-900">Saved Net Calculations</h3>
                <p className="text-xs text-gray-500 mt-1">View and manage historical net calculation records</p>
              </div>
            </div>

            {loadingHistory ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="h-6 w-6 text-gray-400 animate-spin" />
                <span className="ml-2 text-sm text-gray-500">Loading records...</span>
              </div>
            ) : sortedRecords.length === 0 ? (
              <div className="text-center py-12">
                <Calculator className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">
                  {allRecords.length === 0 ? 'No saved records found' : 'No records match your filters'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {allRecords.length === 0 ? 'Calculate and save to see records here' : 'Try adjusting your filter criteria'}
                </p>
              </div>
            ) : (
              <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                          <button
                            onClick={() => handleSort('date')}
                            className="flex items-center gap-1 hover:text-gray-900 transition-colors"
                          >
                            Date
                            {sortColumn === 'date' && (
                              sortDirection === 'asc' ? <ChevronRight className="h-3 w-3 rotate-[-90deg]" /> : <ChevronRight className="h-3 w-3 rotate-90" />
                            )}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">
                          <button
                            onClick={() => handleSort('net_cash')}
                            className="flex items-center justify-end gap-1 hover:text-gray-900 transition-colors ml-auto"
                          >
                            Net Cash
                            {sortColumn === 'net_cash' && (
                              sortDirection === 'asc' ? <ChevronRight className="h-3 w-3 rotate-[-90deg]" /> : <ChevronRight className="h-3 w-3 rotate-90" />
                            )}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">
                          <button
                            onClick={() => handleSort('expenses')}
                            className="flex items-center justify-end gap-1 hover:text-gray-900 transition-colors ml-auto"
                          >
                            Expenses
                            {sortColumn === 'expenses' && (
                              sortDirection === 'asc' ? <ChevronRight className="h-3 w-3 rotate-[-90deg]" /> : <ChevronRight className="h-3 w-3 rotate-90" />
                            )}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">
                          <button
                            onClick={() => handleSort('commission')}
                            className="flex items-center justify-end gap-1 hover:text-gray-900 transition-colors ml-auto"
                          >
                            Commission
                            {sortColumn === 'commission' && (
                              sortDirection === 'asc' ? <ChevronRight className="h-3 w-3 rotate-[-90deg]" /> : <ChevronRight className="h-3 w-3 rotate-90" />
                            )}
                          </button>
                        </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">Rollover</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider font-semibold">
                          <button
                            onClick={() => handleSort('net_saglama')}
                            className="flex items-center justify-end gap-1 hover:text-gray-900 transition-colors ml-auto font-semibold"
                          >
                            Net Sağlama
                            {sortColumn === 'net_saglama' && (
                              sortDirection === 'asc' ? <ChevronRight className="h-3 w-3 rotate-[-90deg]" /> : <ChevronRight className="h-3 w-3 rotate-90" />
                            )}
                          </button>
                        </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">Current Cash</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">
                          <button
                            onClick={() => handleSort('fark')}
                            className="flex items-center justify-end gap-1 hover:text-gray-900 transition-colors ml-auto"
                          >
                            FARK
                            {sortColumn === 'fark' && (
                              sortDirection === 'asc' ? <ChevronRight className="h-3 w-3 rotate-[-90deg]" /> : <ChevronRight className="h-3 w-3 rotate-90" />
                            )}
                          </button>
                        </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-600 uppercase tracking-wider">{t('common.actions')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                      {paginatedRecords.map((record) => (
                        <tr 
                          key={record.id} 
                          className={`hover:bg-gray-50 transition-colors ${
                            comparisonDate1?.date === record.date || comparisonDate2?.date === record.date
                              ? 'bg-blue-50 border-l-4 border-blue-500'
                              : ''
                          }`}
                        >
                        <td className="px-4 py-3 whitespace-nowrap text-gray-900 font-medium">
                          {new Date(record.date).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-gray-900">
                          ${Number(record.net_cash_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-gray-900">
                          ${Number(record.expenses_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-gray-900">
                          ${Number(record.commissions_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-gray-900">
                          ${Number(record.rollover_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right font-semibold text-green-700">
                          ${Number(record.net_saglama_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-gray-900">
                          ${Number(record.anlik_kasa_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                          {record.anlik_kasa_manual && <span className="ml-1 text-xs text-orange-600">(M)</span>}
                        </td>
                        <td className={`px-4 py-3 whitespace-nowrap text-right font-medium ${Number(record.fark_bottom_usd) === 0 ? 'text-green-700' : 'text-red-700'}`}>
                          ${Number(record.fark_bottom_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-center">
                          <div className="flex items-center justify-center gap-1">
                              <button
                                onClick={() => handleSelectForComparison(record)}
                                className={`p-1.5 hover:bg-gray-100 rounded transition-colors ${
                                  comparisonDate1?.date === record.date || comparisonDate2?.date === record.date ? 'bg-blue-100' : ''
                                }`}
                                title="Compare"
                              >
                                <BarChart className="h-4 w-4 text-purple-600" />
                              </button>
                            <button
                              onClick={() => handleLoadRecord(record)}
                              className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                                title="Load to calculator"
                            >
                                <Upload className="h-4 w-4 text-blue-600" />
                            </button>
                            <button
                              onClick={() => handleEditRecord(record)}
                              className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                              title="Delete this record"
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-200">
                    <div className="text-sm text-gray-600">
                      Page {currentPage} of {totalPages}
                    </div>
                    <div className="flex gap-2">
                      <UnifiedButton
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(1)}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4 mr-1" />
                        First
                      </UnifiedButton>
                      <UnifiedButton
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </UnifiedButton>
                      <div className="flex items-center gap-1">
                        {[...Array(Math.min(5, totalPages))].map((_, i) => {
                          let pageNum;
                          if (totalPages <= 5) {
                            pageNum = i + 1;
                          } else if (currentPage <= 3) {
                            pageNum = i + 1;
                          } else if (currentPage >= totalPages - 2) {
                            pageNum = totalPages - 4 + i;
                          } else {
                            pageNum = currentPage - 2 + i;
                          }
                          
                          return (
                            <button
                              key={pageNum}
                              onClick={() => setCurrentPage(pageNum)}
                              className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                                currentPage === pageNum
                                  ? 'bg-green-600 text-white'
                                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                              }`}
                            >
                              {pageNum}
                            </button>
                          );
                        })}
                      </div>
                      <UnifiedButton
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </UnifiedButton>
                      <UnifiedButton
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(totalPages)}
                        disabled={currentPage === totalPages}
                      >
                        Last
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </UnifiedButton>
                    </div>
              </div>
                )}
              </>
            )}
          </div>
        </UnifiedCard>

        {/* Edit/Delete Modal */}
        {showEditModal && editingRecord && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Delete Record
                </h3>
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingRecord(null);
                    setEditSecurityCode('');
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Are you sure you want to delete the record for:
              </p>
              <p className="text-sm font-semibold text-gray-900 mb-4">
                {new Date(editingRecord.date).toLocaleDateString()} - Net Sağlama: ${Number(editingRecord.net_saglama_usd).toFixed(2)}
              </p>
              <p className="text-sm text-gray-600 mb-4">
                Enter security code to confirm deletion:
              </p>
              <div className="mb-4">
                <Input
                  type="text"
                  value={editSecurityCode}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, '').slice(0, 4);
                    setEditSecurityCode(value);
                  }}
                  placeholder="----"
                  className="text-center text-lg font-mono tracking-widest"
                  maxLength={4}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && editSecurityCode.length === 4) {
                      handleDeleteRecord();
                    }
                  }}
                />
              </div>
              <div className="flex gap-3 justify-end">
                <UnifiedButton
                  variant="outline"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingRecord(null);
                    setEditSecurityCode('');
                  }}
                >
                  Cancel
                </UnifiedButton>
                <UnifiedButton
                  variant="primary"
                  onClick={handleDeleteRecord}
                  disabled={editSecurityCode.length !== 4}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Delete
                </UnifiedButton>
              </div>
            </div>
          </div>
        )}

        {/* Comparison Modal */}
        {showComparisonModal && comparisonDate1 && comparisonDate2 && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
              <div className="bg-gray-50 px-6 py-5 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                      <BarChart className="h-6 w-6 text-purple-600" />
                      Date Comparison
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Comparing {new Date(comparisonDate1.date).toLocaleDateString()} vs {new Date(comparisonDate2.date).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    onClick={() => setShowComparisonModal(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="h-5 w-5 text-gray-500" />
                  </button>
                </div>
              </div>

              <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                <div className="grid grid-cols-2 gap-6">
                  {/* Date 1 Column */}
                  <div className="space-y-4">
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <h4 className="text-lg font-semibold text-purple-900 mb-1">
                        {new Date(comparisonDate1.date).toLocaleDateString()}
                      </h4>
                      <p className="text-xs text-purple-600">Date 1</p>
                    </div>

                    <div className="space-y-3">
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Net Cash</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate1.net_cash_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Expenses</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate1.expenses_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Commission</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate1.commissions_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Rollover</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate1.rollover_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <p className="text-xs font-medium text-green-700 uppercase">Net Sağlama</p>
                        <p className="text-2xl font-bold text-green-900 mt-1">
                          ${Number(comparisonDate1.net_saglama_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Current Cash</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate1.anlik_kasa_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className={`rounded-lg p-3 ${Number(comparisonDate1.fark_bottom_usd) === 0 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                        <p className={`text-xs font-medium uppercase ${Number(comparisonDate1.fark_bottom_usd) === 0 ? 'text-green-700' : 'text-red-700'}`}>FARK</p>
                        <p className={`text-lg font-bold mt-1 ${Number(comparisonDate1.fark_bottom_usd) === 0 ? 'text-green-900' : 'text-red-900'}`}>
                          ${Number(comparisonDate1.fark_bottom_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Date 2 Column */}
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="text-lg font-semibold text-blue-900 mb-1">
                        {new Date(comparisonDate2.date).toLocaleDateString()}
                      </h4>
                      <p className="text-xs text-blue-600">Date 2</p>
                    </div>

                    <div className="space-y-3">
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Net Cash</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate2.net_cash_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                        <p className={`text-xs mt-1 font-medium ${
                          Number(comparisonDate2.net_cash_usd) > Number(comparisonDate1.net_cash_usd) 
                            ? 'text-green-600' 
                            : Number(comparisonDate2.net_cash_usd) < Number(comparisonDate1.net_cash_usd)
                            ? 'text-red-600'
                            : 'text-gray-600'
                        }`}>
                          {Number(comparisonDate2.net_cash_usd) > Number(comparisonDate1.net_cash_usd) && '↑ '}
                          {Number(comparisonDate2.net_cash_usd) < Number(comparisonDate1.net_cash_usd) && '↓ '}
                          ${Math.abs(Number(comparisonDate2.net_cash_usd) - Number(comparisonDate1.net_cash_usd)).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Expenses</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate2.expenses_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                        <p className={`text-xs mt-1 font-medium ${
                          Number(comparisonDate2.expenses_usd) > Number(comparisonDate1.expenses_usd) 
                            ? 'text-red-600' 
                            : Number(comparisonDate2.expenses_usd) < Number(comparisonDate1.expenses_usd)
                            ? 'text-green-600'
                            : 'text-gray-600'
                        }`}>
                          {Number(comparisonDate2.expenses_usd) > Number(comparisonDate1.expenses_usd) && '↑ '}
                          {Number(comparisonDate2.expenses_usd) < Number(comparisonDate1.expenses_usd) && '↓ '}
                          ${Math.abs(Number(comparisonDate2.expenses_usd) - Number(comparisonDate1.expenses_usd)).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Commission</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate2.commissions_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                        <p className={`text-xs mt-1 font-medium ${
                          Number(comparisonDate2.commissions_usd) > Number(comparisonDate1.commissions_usd) 
                            ? 'text-red-600' 
                            : Number(comparisonDate2.commissions_usd) < Number(comparisonDate1.commissions_usd)
                            ? 'text-green-600'
                            : 'text-gray-600'
                        }`}>
                          {Number(comparisonDate2.commissions_usd) > Number(comparisonDate1.commissions_usd) && '↑ '}
                          {Number(comparisonDate2.commissions_usd) < Number(comparisonDate1.commissions_usd) && '↓ '}
                          ${Math.abs(Number(comparisonDate2.commissions_usd) - Number(comparisonDate1.commissions_usd)).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Rollover</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate2.rollover_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                        <p className={`text-xs mt-1 font-medium ${
                          Number(comparisonDate2.rollover_usd) > Number(comparisonDate1.rollover_usd) 
                            ? 'text-green-600' 
                            : Number(comparisonDate2.rollover_usd) < Number(comparisonDate1.rollover_usd)
                            ? 'text-red-600'
                            : 'text-gray-600'
                        }`}>
                          {Number(comparisonDate2.rollover_usd) > Number(comparisonDate1.rollover_usd) && '↑ '}
                          {Number(comparisonDate2.rollover_usd) < Number(comparisonDate1.rollover_usd) && '↓ '}
                          ${Math.abs(Number(comparisonDate2.rollover_usd) - Number(comparisonDate1.rollover_usd)).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <p className="text-xs font-medium text-green-700 uppercase">Net Sağlama</p>
                        <p className="text-2xl font-bold text-green-900 mt-1">
                          ${Number(comparisonDate2.net_saglama_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                        <p className={`text-sm mt-1 font-medium ${
                          Number(comparisonDate2.net_saglama_usd) > Number(comparisonDate1.net_saglama_usd) 
                            ? 'text-green-600' 
                            : Number(comparisonDate2.net_saglama_usd) < Number(comparisonDate1.net_saglama_usd)
                            ? 'text-red-600'
                            : 'text-gray-600'
                        }`}>
                          {Number(comparisonDate2.net_saglama_usd) > Number(comparisonDate1.net_saglama_usd) && '↑ '}
                          {Number(comparisonDate2.net_saglama_usd) < Number(comparisonDate1.net_saglama_usd) && '↓ '}
                          ${Math.abs(Number(comparisonDate2.net_saglama_usd) - Number(comparisonDate1.net_saglama_usd)).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                          {' '}
                          ({((Math.abs(Number(comparisonDate2.net_saglama_usd) - Number(comparisonDate1.net_saglama_usd)) / Number(comparisonDate1.net_saglama_usd)) * 100).toFixed(1)}%)
                        </p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs font-medium text-gray-600 uppercase">Current Cash</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          ${Number(comparisonDate2.anlik_kasa_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                        <p className={`text-xs mt-1 font-medium ${
                          Number(comparisonDate2.anlik_kasa_usd) > Number(comparisonDate1.anlik_kasa_usd) 
                            ? 'text-green-600' 
                            : Number(comparisonDate2.anlik_kasa_usd) < Number(comparisonDate1.anlik_kasa_usd)
                            ? 'text-red-600'
                            : 'text-gray-600'
                        }`}>
                          {Number(comparisonDate2.anlik_kasa_usd) > Number(comparisonDate1.anlik_kasa_usd) && '↑ '}
                          {Number(comparisonDate2.anlik_kasa_usd) < Number(comparisonDate1.anlik_kasa_usd) && '↓ '}
                          ${Math.abs(Number(comparisonDate2.anlik_kasa_usd) - Number(comparisonDate1.anlik_kasa_usd)).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                      </div>

                      <div className={`rounded-lg p-3 ${Number(comparisonDate2.fark_bottom_usd) === 0 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                        <p className={`text-xs font-medium uppercase ${Number(comparisonDate2.fark_bottom_usd) === 0 ? 'text-green-700' : 'text-red-700'}`}>FARK</p>
                        <p className={`text-lg font-bold mt-1 ${Number(comparisonDate2.fark_bottom_usd) === 0 ? 'text-green-900' : 'text-red-900'}`}>
                          ${Number(comparisonDate2.fark_bottom_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                        </p>
                        <p className={`text-xs mt-1 font-medium ${
                          Math.abs(Number(comparisonDate2.fark_bottom_usd)) < Math.abs(Number(comparisonDate1.fark_bottom_usd)) 
                            ? 'text-green-600' 
                            : Math.abs(Number(comparisonDate2.fark_bottom_usd)) > Math.abs(Number(comparisonDate1.fark_bottom_usd))
                            ? 'text-red-600'
                            : 'text-gray-600'
                        }`}>
                          {Math.abs(Number(comparisonDate2.fark_bottom_usd)) < Math.abs(Number(comparisonDate1.fark_bottom_usd)) && '✓ Better '}
                          {Math.abs(Number(comparisonDate2.fark_bottom_usd)) > Math.abs(Number(comparisonDate1.fark_bottom_usd)) && '⚠ Worse '}
                          {Math.abs(Number(comparisonDate2.fark_bottom_usd)) === Math.abs(Number(comparisonDate1.fark_bottom_usd)) && '= Same '}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Date 2 Column - Mirror of Date 1 */}
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="text-lg font-semibold text-blue-900 mb-1">
                        {new Date(comparisonDate2.date).toLocaleDateString()}
                      </h4>
                      <p className="text-xs text-blue-600">Date 2</p>
                    </div>

                    {/* Summary Comparison */}
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <h5 className="text-sm font-semibold text-gray-900 mb-3">Overall Comparison</h5>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">Net Sağlama Change:</span>
                          <span className={`font-bold ${
                            Number(comparisonDate2.net_saglama_usd) > Number(comparisonDate1.net_saglama_usd) ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {Number(comparisonDate2.net_saglama_usd) > Number(comparisonDate1.net_saglama_usd) ? '+' : ''}
                            ${(Number(comparisonDate2.net_saglama_usd) - Number(comparisonDate1.net_saglama_usd)).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">Percentage Change:</span>
                          <span className={`font-bold ${
                            Number(comparisonDate2.net_saglama_usd) > Number(comparisonDate1.net_saglama_usd) ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {Number(comparisonDate2.net_saglama_usd) > Number(comparisonDate1.net_saglama_usd) ? '+' : ''}
                            {(((Number(comparisonDate2.net_saglama_usd) - Number(comparisonDate1.net_saglama_usd)) / Number(comparisonDate1.net_saglama_usd)) * 100).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">Expense Change:</span>
                          <span className={`font-bold ${
                            Number(comparisonDate2.expenses_usd) < Number(comparisonDate1.expenses_usd) ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {Number(comparisonDate2.expenses_usd) > Number(comparisonDate1.expenses_usd) ? '+' : ''}
                            ${(Number(comparisonDate2.expenses_usd) - Number(comparisonDate1.expenses_usd)).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">{t('accounting.status_comparison')}:</span>
                          <span className="font-bold">
                            {Number(comparisonDate1.fark_bottom_usd) === 0 ? '✓' : '✗'} → {Number(comparisonDate2.fark_bottom_usd) === 0 ? '✓' : '✗'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
                <UnifiedButton variant="outline" onClick={resetComparison}>
                  Close Comparison
                </UnifiedButton>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }
  
  // Security PIN for editing
  const [securityPin, setSecurityPin] = useState('');
  const [showPinModal, setShowPinModal] = useState(false);
  const [pinModalCallback, setPinModalCallback] = useState<(() => void) | null>(null);
  const [pinError, setPinError] = useState('');
  const [validatingPin, setValidatingPin] = useState(false);

  // Validate PIN via API
  const validatePinViaApi = useCallback(async (pin: string): Promise<boolean> => {
    try {
      setValidatingPin(true);
      const response = await api.post('/accounting/validate-pin', { pin });
      const data = await api.parseResponse(response);
      return data?.valid === true;
    } catch (err) {
      logger.error('PIN validation error:', err);
      return false;
    } finally {
      setValidatingPin(false);
    }
  }, []);

  // Handle PIN submission
  const handlePinSubmit = useCallback(async () => {
    if (securityPin.length !== 4) {
      setPinError(t('accounting.pin_must_be_4_digits'));
      return;
    }
    
    const isValid = await validatePinViaApi(securityPin);
    if (isValid) {
      setPinError('');
      setShowPinModal(false);
      if (pinModalCallback) {
        pinModalCallback();
        setPinModalCallback(null);
      }
    } else {
      setPinError(t('accounting.invalid_security_pin'));
      setSecurityPin('');
    }
  }, [securityPin, pinModalCallback, validatePinViaApi, t]);

  // Request PIN validation with callback
  const requestPinValidation = useCallback((callback: () => void) => {
    setPinModalCallback(() => callback);
    setSecurityPin('');
    setPinError('');
    setShowPinModal(true);
  }, []);

  // Load expenses from API on component mount
  useEffect(() => {
    const loadExpenses = async () => {
      // #region agent log (dev only)
      if (import.meta.env.DEV) {
        try {
          fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              location: 'Accounting.tsx:3233',
              message: 'loadExpenses useEffect triggered',
              data: { isAuthenticated, authLoading, activeTab },
              timestamp: Date.now(),
              sessionId: 'debug-session',
              runId: 'run2',
              hypothesisId: 'C'
            })
          }).catch(() => {});
        } catch {}
      }
      // #endregion
      
      if (!isAuthenticated || authLoading) {
        // #region agent log (dev only)
        if (import.meta.env.DEV) {
          try {
            fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                location: 'Accounting.tsx:3234',
                message: 'Skipping expense load - not authenticated or loading',
                data: { isAuthenticated, authLoading },
                timestamp: Date.now(),
                sessionId: 'debug-session',
                runId: 'run2',
                hypothesisId: 'C'
              })
            }).catch(() => {});
          } catch {}
        }
        // #endregion
        return;
      }
      
      try {
        setLoading(true);
        setLoadError(null);
        logger.debug('Loading expenses from API...');
        
        // #region agent log (dev only)
        if (import.meta.env.DEV) {
          try {
            fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                location: 'Accounting.tsx:3258',
                message: 'About to call api.get(/accounting/expenses)',
                data: {},
                timestamp: Date.now(),
                sessionId: 'debug-session',
                runId: 'run2',
                hypothesisId: 'C'
              })
            }).catch(() => {});
          } catch {}
        }
        // #endregion
        const response = await api.get('/accounting/expenses');
        
        // #region agent log (dev only)
        if (import.meta.env.DEV) {
          try {
            fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                location: 'Accounting.tsx:3258',
                message: 'API response received',
                data: { ok: response.ok, status: (response as any).status },
                timestamp: Date.now(),
                sessionId: 'debug-session',
                runId: 'run2',
                hypothesisId: 'C'
              })
            }).catch(() => {});
          } catch {}
        }
        // #endregion
        
        if (response.ok) {
          const data: any = await api.parseResponse(response);
          logger.debug('Expenses loaded:', data);
          
          // #region agent log (dev only)
          if (import.meta.env.DEV) {
            try {
              fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  location: 'Accounting.tsx:3265',
                  message: 'Expenses API response parsed',
                  data: { success: data.success, expensesCount: Array.isArray(data.expenses) ? data.expenses.length : 0, message: data.message, error: data.error },
                  timestamp: Date.now(),
                  sessionId: 'debug-session',
                  runId: 'run2',
                  hypothesisId: 'C'
                })
              }).catch(() => {});
            } catch {}
          }
          // #endregion
          
          if (data.success && Array.isArray(data.expenses)) {
            setExpenses(data.expenses);
          } else {
            logger.warn('Invalid expenses response structure:', data);
            setLoadError(data.error || 'Invalid response format');
            setExpenses([]);
          }
        } else {
          logger.error('HTTP error loading expenses:', response.status);
          setLoadError('Failed to load expenses');
          setExpenses([]);
        }
      } catch (err) {
        logger.error('Error loading expenses:', err);
        // #region agent log (dev only)
        if (import.meta.env.DEV) {
          try {
            fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                location: 'Accounting.tsx:3280',
                message: 'Error loading expenses (catch block)',
                data: { error: err instanceof Error ? err.message : String(err) },
                timestamp: Date.now(),
                sessionId: 'debug-session',
                runId: 'run2',
                hypothesisId: 'C'
              })
            }).catch(() => {});
          } catch {}
        }
        // #endregion
        setLoadError('Error loading expenses: ' + (err instanceof Error ? err.message : String(err)));
        setExpenses([]);
      } finally {
        setLoading(false);
      }
    };
    
    loadExpenses();
  }, [isAuthenticated, authLoading, activeTab]);

  // Debounce search term for better performance
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300); // 300ms delay

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // ============================================================================
  // MONTHLY CURRENCY SUMMARY FUNCTIONS
  // ============================================================================
  
  // Load saved months list
  const loadSavedMonths = useCallback(async () => {
    try {
      const response = await api.get('/accounting/currency-summary/months');
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          setSavedMonths(data.months || []);
        }
      }
    } catch (err) {
      console.error('Error loading saved months:', err);
    }
  }, []);
  
  // Load month data
  const loadMonthData = useCallback(async (monthPeriod: string) => {
    try {
      setIsLoadingMonth(true);
      setSelectedMonthPeriod(monthPeriod);
      
      const response = await api.get(`/accounting/currency-summary/${monthPeriod}`);
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success && data.is_saved && data.currencies.length > 0) {
          // Load saved data
          setIsMonthLocked(data.is_locked);
          
          // Populate DEVİR and KUR from saved data
          const savedCarryover: any = { TRY: 0, USD: 0, USDT: 0 };
          const savedRates: any = { TRY: '' };
          
          data.currencies.forEach((curr: any) => {
            savedCarryover[curr.currency] = curr.devir || 0;
            if (curr.currency === 'TRY' && curr.exchange_rate) {
              savedRates.TRY = curr.exchange_rate.toString();
            }
          });
          
          setTempCarryoverValues(savedCarryover);
          setTempExchangeRates(savedRates);
          
          info(`Loaded data for ${monthPeriod}`);
        } else {
          // No saved data - current month or new month
          setIsMonthLocked(false);
          
          // Use current exchange rate for TRY
          if (currentRate && currentRate > 0) {
            setTempExchangeRates({ TRY: currentRate.toFixed(2) });
          }
          
          // Check if we have localStorage values for current month
          const currentMonth = new Date().toISOString().slice(0, 7);
          if (monthPeriod === currentMonth) {
            const saved = localStorage.getItem('expense_carryover_values');
            if (saved) {
              try {
                const parsed = JSON.parse(saved);
                setTempCarryoverValues(parsed);
              } catch (e) {
                // Use defaults
                setTempCarryoverValues({ TRY: 750000, USD: 5000, USDT: 168000 });
              }
            } else {
              setTempCarryoverValues({ TRY: 750000, USD: 5000, USDT: 168000 });
            }
          } else {
            // For other months, start with zeros
            setTempCarryoverValues({ TRY: 0, USD: 0, USDT: 0 });
          }
        }
      }
    } catch (err) {
      console.error('Error loading month data:', err);
      error('Failed to load month data');
    } finally {
      setIsLoadingMonth(false);
    }
  }, [currentRate, info, error]);
  
  // Currency-based summary (like SİMÜLASYON sheet) - moved here before handleSaveCurrencySummary
  const currencySummary = useMemo(() => {
    // Always show all three currencies (company cash/assets)
    const summary: Record<string, {
      currency: string;
      carryover: number; // DEVİR - opening balance (user can edit)
      inflow: number; // GİREN - total inflow
      outflow: number; // ÇIKAN - total outflow
      net: number; // NET = carryover + inflow - outflow
      usdEquivalent: number; // USD conversion
    }> = {
      'TRY': { currency: 'TRY', carryover: tempCarryoverValues.TRY, inflow: 0, outflow: 0, net: 0, usdEquivalent: 0 },
      'USD': { currency: 'USD', carryover: tempCarryoverValues.USD, inflow: 0, outflow: 0, net: 0, usdEquivalent: 0 },
      'USDT': { currency: 'USDT', carryover: tempCarryoverValues.USDT, inflow: 0, outflow: 0, net: 0, usdEquivalent: 0 }
    };

    // Safety check - if no expenses, return empty summary with carryover values
    if (!expenses || expenses.length === 0) {
      // Still calculate net and USD equivalent even with no expenses
      // Use temp exchange rate if available, otherwise fall back to currentRate
      const exchangeRate = (tempExchangeRates.TRY && parseFloat(tempExchangeRates.TRY) > 0) 
        ? parseFloat(tempExchangeRates.TRY)
        : (currentRate && currentRate > 0) ? currentRate : 42.00;
      Object.keys(summary).forEach(key => {
        const item = summary[key];
        item.net = item.carryover + item.inflow - item.outflow;
        if (key === 'USD' || key === 'USDT') {
          item.usdEquivalent = item.net;
        } else if (key === 'TRY') {
          item.usdEquivalent = exchangeRate > 0 ? item.net / exchangeRate : 0;
        }
      });
      // Return currencies in SİMÜLASYON order: USD, TRY, USDT
      return [
        summary['USD'],
        summary['TRY'],
        summary['USDT']
      ];
    }

    // Calculate totals per currency
    expenses.forEach(expense => {
      if (!expense) return; // Safety check
      
      const currency = expense.mount_currency || 'TRY';
      const currencyKey = currency === 'TRY' ? 'TRY' : currency === 'USD' ? 'USD' : 'USDT';
      
      if (!summary[currencyKey]) {
        summary[currencyKey] = { currency: currencyKey, carryover: 0, inflow: 0, outflow: 0, net: 0, usdEquivalent: 0 };
      }

      // Get amount based on currency
      let amount = 0;
      if (currency === 'TRY') {
        amount = expense.amount_try || 0;
      } else if (currency === 'USD') {
        amount = expense.amount_usd || 0;
      } else if (currency === 'USDT') {
        amount = expense.amount_usdt || 0;
      }

      // Add to inflow or outflow based on category
      if (expense.category === 'inflow') {
        summary[currencyKey].inflow += amount;
      } else if (expense.category === 'outflow') {
        summary[currencyKey].outflow += amount;
      }
    });

    // Calculate net and USD equivalent (using temp exchange rate if available)
    const exchangeRate = (tempExchangeRates.TRY && parseFloat(tempExchangeRates.TRY) > 0) 
      ? parseFloat(tempExchangeRates.TRY)
      : (currentRate && currentRate > 0) ? currentRate : 42.00; // Use temp rate, fetched rate, or default
    
    Object.keys(summary).forEach(key => {
      const item = summary[key];
      item.net = item.carryover + item.inflow - item.outflow;
      
      // Convert to USD
      if (key === 'USD' || key === 'USDT') {
        item.usdEquivalent = item.net; // Already in USD
      } else if (key === 'TRY') {
        item.usdEquivalent = exchangeRate > 0 ? item.net / exchangeRate : 0; // Convert TRY to USD
      }
    });

    // Return currencies in SİMÜLASYON order: USD, TRY, USDT
    return [
      summary['USD'],
      summary['TRY'],
      summary['USDT']
    ];
  }, [expenses, currentRate, tempCarryoverValues, tempExchangeRates]);

  // Save month data
  const handleSaveCurrencySummary = useCallback(async () => {
    try {
      setIsSavingMonth(true);
      
      // Prepare data from current currencySummary calculation
      const currencies = currencySummary.map(item => ({
        currency: item.currency,
        devir: tempCarryoverValues[item.currency as 'TRY' | 'USD' | 'USDT'] || 0,
        exchange_rate: item.currency === 'TRY' && tempExchangeRates.TRY ? parseFloat(tempExchangeRates.TRY) : null,
        inflow: item.inflow,
        outflow: item.outflow,
        net: item.net,
        usd_equivalent: item.usdEquivalent
      }));
      
      const response = await api.post('/accounting/currency-summary', {
        month_period: selectedMonthPeriod,
        currencies
      });
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          success('Month data saved successfully!');
          loadSavedMonths(); // Refresh month list
          
          // Save to localStorage for current month
          const currentMonth = new Date().toISOString().slice(0, 7);
          if (selectedMonthPeriod === currentMonth) {
            localStorage.setItem('expense_carryover_values', JSON.stringify(tempCarryoverValues));
          }
        } else {
          error(data.error || 'Failed to save month data');
        }
      } else {
        error('Failed to save month data');
      }
    } catch (err) {
      console.error('Error saving month data:', err);
      error('Failed to save month data');
    } finally {
      setIsSavingMonth(false);
    }
  }, [selectedMonthPeriod, currencySummary, tempCarryoverValues, tempExchangeRates, success, error, loadSavedMonths]);
  
  // Lock month
  const handleLockMonth = useCallback(async () => {
    if (!confirm(`Lock ${selectedMonthPeriod}? You won't be able to edit it without unlocking.`)) {
      return;
    }
    
    try {
      const response = await api.post(`/accounting/currency-summary/${selectedMonthPeriod}/lock`);
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          setIsMonthLocked(true);
          success('Month locked successfully');
          loadSavedMonths();
        } else {
          error(data.error || 'Failed to lock month');
        }
      }
    } catch (err) {
      console.error('Error locking month:', err);
      error('Failed to lock month');
    }
  }, [selectedMonthPeriod, success, error, loadSavedMonths]);
  
  // Unlock month
  const handleUnlockMonth = useCallback(async () => {
    try {
      const response = await api.post(`/accounting/currency-summary/${selectedMonthPeriod}/unlock`);
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          setIsMonthLocked(false);
          success('Month unlocked successfully');
          loadSavedMonths();
        } else {
          error(data.error || 'Failed to unlock month');
        }
      }
    } catch (err) {
      console.error('Error unlocking month:', err);
      error('Failed to unlock month');
    }
  }, [selectedMonthPeriod, success, error, loadSavedMonths]);
  
  // Load saved months on mount
  useEffect(() => {
    loadSavedMonths();
  }, [loadSavedMonths]);
  
  // Load current month data on mount
  useEffect(() => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    loadMonthData(currentMonth);
  }, [loadMonthData]);

// Optimized expense modal handlers with useCallback
  const handleOpenAddExpense = useCallback(() => {
    setEditingExpense(null);
    setViewingExpense(null);
    setIsViewMode(false);
    setShowAddAnother(false);
    setConverterEnabled(true); // Reset converter toggle to default (on)
    setFormData({
      description: '',
      detail: '',
      category: 'inflow',
      type: 'payment',
      amount: '',
      mount_currency: 'TRY',
      status: 'pending',
      cost_period: '',
      payment_date: '',
      payment_period: '',
      source: ''
    });
    setCalculatedAmounts({ amount_try: 0, amount_usd: 0, amount_usdt: 0 });
    setShowExpenseModal(true);
  }, []);

  const handleOpenViewExpense = useCallback((expense: Expense) => {
    setViewingExpense(expense);
    setEditingExpense(null);
    setIsViewMode(true);
    // Determine which amount to show based on mount_currency
    const mountCurrency = expense.mount_currency || 'TRY';
    let amount = '0';
    if (mountCurrency === 'TRY') {
      amount = expense.amount_try?.toString() || '0';
    } else if (mountCurrency === 'USD') {
      amount = expense.amount_usd?.toString() || '0';
    } else if (mountCurrency === 'USDT') {
      amount = expense.amount_usdt?.toString() || '0';
    }
    
    setFormData({
      description: expense.description,
      detail: expense.detail,
      category: expense.category || 'inflow',
      type: expense.type || 'payment',
      amount: amount,
      mount_currency: mountCurrency,
      status: expense.status,
      cost_period: expense.cost_period,
      payment_date: expense.payment_date,
      payment_period: expense.payment_period,
      source: expense.source
    });
    
    // Set calculated amounts from expense data
    setCalculatedAmounts({
      amount_try: expense.amount_try || 0,
      amount_usd: expense.amount_usd || 0,
      amount_usdt: expense.amount_usdt || 0
    });
    setShowExpenseModal(true);
  }, []);

  const handleOpenEditExpense = useCallback((expense: Expense) => {
    // Request PIN validation before opening edit modal
    requestPinValidation(() => {
      setEditingExpense(expense);
      setViewingExpense(null);
      setIsViewMode(false);
      // Determine which amount to show based on mount_currency
      const mountCurrency = expense.mount_currency || 'TRY';
      let amount = '0';
      if (mountCurrency === 'TRY') {
        amount = expense.amount_try?.toString() || '0';
      } else if (mountCurrency === 'USD') {
        amount = expense.amount_usd?.toString() || '0';
      } else if (mountCurrency === 'USDT') {
        amount = expense.amount_usdt?.toString() || '0';
      }
      
      setFormData({
        description: expense.description,
        detail: expense.detail,
        category: expense.category || 'inflow',
        type: expense.type || 'payment',
        amount: amount,
        mount_currency: mountCurrency,
        status: expense.status,
        cost_period: expense.cost_period,
        payment_date: expense.payment_date,
        payment_period: expense.payment_period,
        source: expense.source
      });
      
      // Set calculated amounts from expense data
      setCalculatedAmounts({
        amount_try: expense.amount_try || 0,
        amount_usd: expense.amount_usd || 0,
        amount_usdt: expense.amount_usdt || 0
      });
      setShowExpenseModal(true);
    });
  }, [requestPinValidation]);

  const handleCloseExpenseModal = useCallback(() => {
    setShowExpenseModal(false);
    setEditingExpense(null);
    setViewingExpense(null);
    setIsViewMode(false);
    setShowAddAnother(false);
    setCurrentRate(null);
    setSecurityPin('');
    setConverterEnabled(true); // Reset converter toggle to default (on)
    setFormData({
      description: '',
      detail: '',
      category: 'inflow',
      type: 'payment',
      amount: '',
      mount_currency: 'TRY',
      status: 'pending',
      cost_period: '',
      payment_date: '',
      payment_period: '',
      source: ''
    });
    setCalculatedAmounts({ amount_try: 0, amount_usd: 0, amount_usdt: 0 });
  }, []);

  // Fetch current exchange rate
  const fetchCurrentRate = useCallback(async () => {
    setFetchingRate(true);
    try {
      logger.debug('Fetching current exchange rate...');
      const response = await api.get('/exchange-rates/current');
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        logger.debug('Exchange rate response:', data);
        
        // API returns: { success: true, rate: { rate: number, ... } }
        if (data.success && data.rate && data.rate.rate) {
          const rateValue = parseFloat(data.rate.rate);
          logger.debug('Exchange rate fetched:', rateValue);
          setCurrentRate(rateValue);
          success(t('accounting.rate_fetched').replace('{rate}', rateValue.toFixed(4)));
          return rateValue;
        } else {
          logger.error('Invalid exchange rate response structure:', data);
          error(t('accounting.rate_fetch_failed'));
          return null;
        }
      } else {
        logger.error('HTTP error fetching exchange rate:', response.status);
        error(t('accounting.rate_fetch_failed'));
        return null;
      }
    } catch (err) {
      logger.error('Error fetching exchange rate:', err);
      error(t('accounting.rate_fetch_error'));
      return null;
    } finally {
      setFetchingRate(false);
    }
  }, [t, success, error]);

  // Fetch exchange rate on mount for currency summary (moved here after fetchCurrentRate definition)
  useEffect(() => {
    if (isAuthenticated && !authLoading && activeTab === 'expenses' && !currentRate) {
      fetchCurrentRate().catch(() => {
        // Silently fail - will use default rate
      });
    }
  }, [isAuthenticated, authLoading, activeTab, currentRate, fetchCurrentRate]);

  // Auto-conversion is now handled automatically via useEffect based on mount_currency

  const handleSaveExpense = useCallback(async () => {
    // #region agent log
    try {
      fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: 'Accounting.tsx:3425',
          message: 'handleSaveExpense called',
          data: { isEdit: !!editingExpense, expensesCount: expenses.length },
          timestamp: Date.now(),
          sessionId: 'debug-session',
          runId: 'run2',
          hypothesisId: 'A'
        })
      }).catch(() => {});
    } catch {}
    // #endregion
    
    try {
      setLoading(true);
      
      if (editingExpense) {
        // #region agent log
        try {
          fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              location: 'Accounting.tsx:3428',
              message: 'Updating expense via API',
              data: { expenseId: editingExpense.id },
              timestamp: Date.now(),
              sessionId: 'debug-session',
              runId: 'run2',
              hypothesisId: 'A'
            })
          }).catch(() => {});
        } catch {}
        // #endregion
        
        // Update existing expense via API
        const response = await api.put(`/accounting/expenses/${editingExpense.id}`, {
          description: formData.description,
          detail: formData.detail,
          category: formData.category,
          type: formData.type,
          amount_try: calculatedAmounts.amount_try,
          amount_usd: calculatedAmounts.amount_usd,
          amount_usdt: calculatedAmounts.amount_usdt,
          mount_currency: formData.mount_currency,
          status: formData.status,
          cost_period: formData.cost_period,
          payment_date: formData.payment_date || null,
          payment_period: formData.payment_period,
          source: formData.source
        });
        
        if (response.ok) {
          const data: any = await api.parseResponse(response);
          if (data.success && data.expense) {
            // Update local state with server response
            setExpenses(expenses.map(exp => 
              exp.id === editingExpense.id ? data.expense : exp
            ));
            success(t('accounting.expense_updated_success'));
            // Close modal after update (no "Add Another" for updates)
            handleCloseExpenseModal();
          } else {
            error(data.error || t('accounting.failed_to_update_expense'));
          }
        } else {
          error(t('accounting.failed_to_update_expense'));
        }
      } else {
        // #region agent log
        try {
          fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              location: 'Accounting.tsx:3448',
              message: 'Adding new expense via API',
              data: { expensesCount: expenses.length },
              timestamp: Date.now(),
              sessionId: 'debug-session',
              runId: 'run2',
              hypothesisId: 'A'
            })
          }).catch(() => {});
        } catch {}
        // #endregion
        
        // Create new expense via API
        const response = await api.post('/accounting/expenses', {
          description: formData.description,
          detail: formData.detail,
          category: formData.category,
          type: formData.type,
          amount_try: calculatedAmounts.amount_try,
          amount_usd: calculatedAmounts.amount_usd,
          amount_usdt: calculatedAmounts.amount_usdt,
          mount_currency: formData.mount_currency,
          status: formData.status,
          cost_period: formData.cost_period,
          payment_date: formData.payment_date || null,
          payment_period: formData.payment_period,
          source: formData.source
        });
        
        if (response.ok) {
          const data: any = await api.parseResponse(response);
          console.log('[Accounting] Add expense response:', { ok: response.ok, status: response.status, data });
          if (data.success && data.expense) {
            // Add new expense to local state
            setExpenses([...expenses, data.expense]);
            success(t('accounting.expense_added_success'));
            console.log('[Accounting] Closing modal after successful add');
            // Close modal after successful add
            handleCloseExpenseModal();
          } else {
            console.error('[Accounting] Response missing success or expense:', data);
            error(data.error || 'Failed to create expense');
          }
        } else {
          console.error('[Accounting] Response not ok:', response.status);
          error('Failed to create expense');
        }
      }
    } catch (err) {
      logger.error('Error saving expense:', err);
      error('Error saving expense. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [editingExpense, expenses, formData, calculatedAmounts, handleCloseExpenseModal, success, error, t]);

  const handleDeleteExpense = useCallback(async (id: number) => {
    // #region agent log
    try {
      fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: 'Accounting.tsx:3469',
          message: 'handleDeleteExpense called',
          data: { expenseId: id },
          timestamp: Date.now(),
          sessionId: 'debug-session',
          runId: 'run2',
          hypothesisId: 'A'
        })
      }).catch(() => {});
    } catch {}
    // #endregion
    
    if (!confirm(t('accounting.confirm_delete_expense'))) {
      return;
    }
    
    try {
      setLoading(true);
      
      // Delete expense via API
      const response = await api.delete(`/accounting/expenses/${id}`);
      
      if (response.ok) {
        const data: any = await api.parseResponse(response);
        if (data.success) {
          // Remove from local state
          setExpenses(expenses.filter(exp => exp.id !== id));
          success(t('accounting.expense_deleted_success'));
        } else {
          error(data.error || 'Failed to delete expense');
        }
      } else {
        error('Failed to delete expense');
      }
    } catch (err) {
      logger.error('Error deleting expense:', err);
      error('Error deleting expense. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [expenses, success, error, t]);

  // Memoized filtered expenses for performance (using debounced search)
  const filteredExpenses = useMemo(() => {
    return expenses.filter(expense => {
      const matchesSearch = 
        expense.description.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
        expense.detail.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
        expense.source.toLowerCase().includes(debouncedSearchTerm.toLowerCase());
      
      const matchesStatus = expenseStatusFilter === 'all' || expense.status === expenseStatusFilter;
      const matchesCategory = expenseCategoryFilter === 'all' || expense.category === expenseCategoryFilter;
      
      return matchesSearch && matchesStatus && matchesCategory;
    });
  }, [expenses, debouncedSearchTerm, expenseStatusFilter, expenseCategoryFilter]);

  // Paginated expenses for All Expenses view
  const paginatedExpenses = useMemo(() => {
    const startIndex = (currentExpensePage - 1) * EXPENSES_PER_PAGE;
    const endIndex = startIndex + EXPENSES_PER_PAGE;
    return filteredExpenses.slice(startIndex, endIndex);
  }, [filteredExpenses, currentExpensePage, EXPENSES_PER_PAGE]);

  const totalExpensePages = Math.ceil(filteredExpenses.length / EXPENSES_PER_PAGE);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentExpensePage(1);
  }, [debouncedSearchTerm, expenseStatusFilter, expenseCategoryFilter]);

  // Memoized totals for performance
  const expenseTotals = useMemo(() => {
    return {
      totalTRY: expenses.reduce((sum, exp) => sum + exp.amount_try, 0),
      totalUSD: expenses.reduce((sum, exp) => sum + exp.amount_usd, 0),
      count: expenses.length
    };
  }, [expenses]);

  // Memoized daily summary grouped by payment_date for selected month/year
  const dailySummary = useMemo(() => {
    // Filter expenses with valid payment_date, paid status, and matching month/year
    const expensesWithDate = expenses.filter(exp => {
      if (!exp.payment_date || exp.payment_date.trim() === '' || exp.status !== 'paid') {
        return false;
      }
      
      // Parse the payment date and check if it matches selected month/year
      const paymentDate = new Date(exp.payment_date);
      const expenseMonth = paymentDate.getMonth() + 1; // getMonth() returns 0-11, we need 1-12
      const expenseYear = paymentDate.getFullYear();
      
      return expenseMonth === selectedMonth && expenseYear === selectedYear;
    });
    
    // Group by payment_date
    const grouped = expensesWithDate.reduce((acc, expense) => {
      const date = expense.payment_date;
      if (!acc[date]) {
        acc[date] = {
          date,
          totalTRY: 0,
          totalUSD: 0,
          count: 0,
          expenses: []
        };
      }
      acc[date].totalTRY += expense.amount_try;
      acc[date].totalUSD += expense.amount_usd;
      acc[date].count += 1;
      acc[date].expenses.push(expense);
      return acc;
    }, {} as Record<string, { date: string; totalTRY: number; totalUSD: number; count: number; expenses: Expense[] }>);
    
    // Convert to array and sort by date (based on sort order)
    return Object.values(grouped).sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return dailySummarySortOrder === 'desc' ? dateB - dateA : dateA - dateB;
    });
  }, [expenses, selectedMonth, selectedYear, dailySummarySortOrder]);

  // Export to CSV functionality
  const handleExportCSV = useCallback(() => {
    const csvHeaders = 'Description,Detail,TRY Amount,USD Amount,Status,Cost Period,Payment Date,Payment Period,Source\n';
    const csvData = filteredExpenses.map(exp => 
      `"${exp.description}","${exp.detail}",${exp.amount_try},${exp.amount_usd},"${exp.status}","${exp.cost_period}","${exp.payment_date}","${exp.payment_period}","${exp.source}"`
    ).join('\n');
    
    const csv = csvHeaders + csvData;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `expenses_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    success(t('accounting.exported_expenses').replace('{count}', String(filteredExpenses.length)));
  }, [filteredExpenses, success, t]);

  // Scroll to top on mount to prevent auto-scroll down
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, []);

  // Save expenses to localStorage whenever they change (optional)
  useEffect(() => {
    if (expenses.length > 0) {
      localStorage.setItem('accounting_expenses', JSON.stringify(expenses));
    }
  }, [expenses]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Ctrl+K or Cmd+K: Focus search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[placeholder*="Search expenses"]') as HTMLInputElement;
        searchInput?.focus();
        info('Search activated (Ctrl+K)');
      }
      
      // Ctrl+N or Cmd+N: New expense
      if ((e.ctrlKey || e.metaKey) && e.key === 'n' && !showExpenseModal) {
        e.preventDefault();
        handleOpenAddExpense();
        info('New expense form opened (Ctrl+N)');
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showExpenseModal, handleOpenAddExpense]);

if (authLoading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <div className="h-10 w-64 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-4 w-96 bg-gray-100 rounded animate-pulse mt-2"></div>
        </div>
        <div className="space-y-6">
          <div className="h-12 bg-gray-100 rounded animate-pulse"></div>
          <div className="h-96 bg-gray-50 rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 animate-in fade-in duration-300">

      {/* Page Header */}
      <div className="mb-6">
        <SectionHeader
          title="Accounting"
          description="Financial records and accounting management"
          icon={Calculator}
          actions={
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded border border-gray-200 font-mono">Ctrl+K</span>
              <span className="text-xs text-gray-500">Search</span>
              <span className="text-gray-300">•</span>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded border border-gray-200 font-mono">Ctrl+N</span>
              <span className="text-xs text-gray-500">New Expense</span>
            </div>
          }
        />
      </div>

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-gray-50/80 border border-gray-200/60 rounded-lg shadow-sm">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            {t('tabs.overview')}
          </TabsTrigger>
          <TabsTrigger value="expenses" className="flex items-center gap-2">
            <Receipt className="h-4 w-4" />
            {t('tabs.expenses')}
          </TabsTrigger>
          <TabsTrigger value="net" className="flex items-center gap-2">
            <Calculator className="h-4 w-4" />
            {t('tabs.net')}
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <LineChart className="h-4 w-4" />
            {t('tabs.analytics')}
          </TabsTrigger>
        </TabsList>

        {/* Tab Content */}
        <TabsContent value="overview" className="mt-6">
          <div className="p-6">
            <UnifiedCard variant="elevated">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-blue-600" />
                  Accounting Overview
                </CardTitle>
                <CardDescription>
                  Your accounting dashboard overview
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12">
                  <Calculator className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-600">Welcome to the Accounting section</p>
                  <p className="text-sm text-gray-500 mt-2">Select a tab above to get started</p>
                </div>
              </CardContent>
            </UnifiedCard>
                        </div>
        </TabsContent>

        <TabsContent value="expenses" className="mt-6">
          <div className="space-y-6">
            {/* Sub-Navigation for Expenses */}
            {/* Creative Sub-Tab Navigation */}
            <div className="relative w-full">
              {/* Background */}
              <div className="relative bg-gray-50 border border-gray-200 rounded-lg p-1.5">
                {/* Animated background indicator */}
                <div 
                  className={`absolute top-1.5 bottom-1.5 w-[calc(33.333%-0.5rem)] bg-white border border-gray-300 rounded-md transition-all duration-300 ease-out ${
                    expensesView === 'all' 
                      ? 'left-1.5' 
                      : expensesView === 'daily'
                      ? 'left-[calc(33.333%+0.25rem)]'
                      : 'left-[calc(66.666%+1rem)]'
                  }`}
                />
                
                {/* Tab buttons */}
                <div className="relative grid grid-cols-3 gap-1.5">
                  <button
                    onClick={() => setExpensesView('all')}
                    className={`group relative flex items-center justify-center gap-2.5 px-5 py-3.5 rounded-md font-semibold text-sm transition-all duration-300 ease-out outline-none focus:outline-none focus:ring-0 ${
                      expensesView === 'all'
                        ? 'text-gray-900'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {/* Icon */}
                    <Receipt className={`h-4 w-4 transition-all duration-300 ${
                      expensesView === 'all' 
                        ? 'text-gray-900' 
                        : 'text-gray-500 group-hover:text-gray-700'
                    }`} />
                    
                    {/* Text */}
                    <span className="relative z-10 transition-all duration-300">
                      {t('accounting.all_expenses')}
                    </span>
                  </button>
                  
                  <button
                    onClick={() => setExpensesView('daily')}
                    className={`group relative flex items-center justify-center gap-2.5 px-5 py-3.5 rounded-md font-semibold text-sm transition-all duration-300 ease-out outline-none focus:outline-none focus:ring-0 ${
                      expensesView === 'daily'
                        ? 'text-gray-900'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {/* Icon */}
                    <Calendar className={`h-4 w-4 transition-all duration-300 ${
                      expensesView === 'daily' 
                        ? 'text-gray-900' 
                        : 'text-gray-500 group-hover:text-gray-700'
                    }`} />
                    
                    {/* Text */}
                    <span className="relative z-10 transition-all duration-300">
                      {t('accounting.daily_summary')}
                    </span>
                  </button>
                  
                  <button
                    onClick={() => setExpensesView('internal_revenue')}
                    className={`group relative flex items-center justify-center gap-2.5 px-5 py-3.5 rounded-md font-semibold text-sm transition-all duration-300 ease-out outline-none focus:outline-none focus:ring-0 ${
                      expensesView === 'internal_revenue'
                        ? 'text-gray-900'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {/* Icon */}
                    <Calculator className={`h-4 w-4 transition-all duration-300 ${
                      expensesView === 'internal_revenue' 
                        ? 'text-gray-900' 
                        : 'text-gray-500 group-hover:text-gray-700'
                    }`} />
                    
                    {/* Text */}
                    <span className="relative z-10 transition-all duration-300">
                      Internal Revenue
                    </span>
                  </button>
                </div>
              </div>
            </div>

            {/* All Expenses View */}
            {expensesView === 'all' && (
              <>
            {/* Modern Header Card */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 px-6 py-5 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200">
                        <Receipt className="h-5 w-5 text-gray-700" />
                      </div>
                      {t('accounting.company_expenses')}
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">{t('accounting.track_manage_expenses')}</p>
                  </div>
                  <Button
                    onClick={handleOpenAddExpense}
                    className="bg-gray-900 hover:bg-gray-800 text-white px-4 py-2 rounded-lg flex items-center gap-2 border border-gray-900 transition-all"
                  >
                    <Plus className="h-4 w-4" />
                    {t('accounting.add_expense')}
                  </Button>
                </div>
              </div>
              
              {/* Modern Filter Section */}
              <div className="p-6 border-b border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                  {/* Search */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                      <Search className="h-4 w-4 text-gray-500" />
                      Search
                    </label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        type="text"
                        placeholder={t('accounting.search_placeholder')}
                        className="pl-10 w-full border-gray-200 focus:border-gray-500 focus:ring-gray-500"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                      />
                      {searchTerm && (
                        <button
                          onClick={() => setSearchTerm('')}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                          title={t('accounting.clear_search')}
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {/* Status Filter */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                      <Filter className="h-4 w-4 text-gray-500" />
                      {t('accounting.status')}
                    </label>
                    <div className="relative">
                      <select
                        value={expenseStatusFilter}
                        onChange={(e) => setExpenseStatusFilter(e.target.value as 'all' | 'paid' | 'pending' | 'cancelled')}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 bg-white appearance-none text-sm"
                      >
                        <option value="all">{t('accounting.all_status')}</option>
                        <option value="paid">{t('accounting.status_paid')}</option>
                        <option value="pending">{t('accounting.status_pending')}</option>
                        <option value="cancelled">{t('accounting.status_cancelled')}</option>
                      </select>
                    </div>
                  </div>
                  
                  {/* Category Filter */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                      <Filter className="h-4 w-4 text-gray-500" />
                      {t('accounting.category')}
                    </label>
                    <div className="relative">
                      <select
                        value={expenseCategoryFilter}
                        onChange={(e) => setExpenseCategoryFilter(e.target.value as 'all' | 'inflow' | 'outflow')}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 bg-white appearance-none text-sm"
                      >
                        <option value="all">{t('accounting.all_categories')}</option>
                        <option value="inflow">{t('accounting.category_inflow')}</option>
                        <option value="outflow">{t('accounting.category_outflow')}</option>
                      </select>
                    </div>
                  </div>
                  
                  {/* Active Filters Indicator */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Active Filters</label>
                    <div className="flex items-center gap-2 min-h-[40px]">
                      {(searchTerm || expenseStatusFilter !== 'all' || expenseCategoryFilter !== 'all') && (
                        <div className="flex items-center gap-2 flex-wrap">
                          {searchTerm && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-md border border-gray-200">
                              Search: "{searchTerm.substring(0, 20)}{searchTerm.length > 20 ? '...' : ''}"
                              <button
                                onClick={() => setSearchTerm('')}
                                className="hover:text-gray-900"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          )}
                          {expenseStatusFilter !== 'all' && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-md border border-gray-200">
                              {t('accounting.status')}: {expenseStatusFilter === 'paid' ? t('accounting.status_paid') : expenseStatusFilter === 'pending' ? t('accounting.status_pending') : t('accounting.status_cancelled')}
                              <button
                                onClick={() => setExpenseStatusFilter('all')}
                                className="hover:text-gray-900"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          )}
                          {expenseCategoryFilter !== 'all' && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-md border border-gray-200">
                              {t('accounting.category')}: {expenseCategoryFilter === 'inflow' ? t('accounting.category_inflow') : t('accounting.category_outflow')}
                              <button
                                onClick={() => setExpenseCategoryFilter('all')}
                                className="hover:text-gray-900"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          )}
                        </div>
                      )}
                      {!searchTerm && expenseStatusFilter === 'all' && expenseCategoryFilter === 'all' && (
                        <span className="text-xs text-gray-400">No active filters</span>
                      )}
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Actions</label>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleExportCSV}
                        variant="outline"
                        className="flex-1 border-gray-200 hover:border-gray-300 hover:bg-gray-50 flex items-center justify-center gap-2"
                        disabled={filteredExpenses.length === 0}
                        size="sm"
                      >
                        <Download className="h-4 w-4" />
                        Export
                      </Button>
                      {(searchTerm || expenseStatusFilter !== 'all' || expenseCategoryFilter !== 'all') && (
                        <Button
                          onClick={() => {
                            setSearchTerm('');
                            setExpenseStatusFilter('all');
                            setExpenseCategoryFilter('all');
                          }}
                          variant="outline"
                          className="border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                          size="sm"
                          title="Clear all filters"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Modern Table Card */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                      <Activity className="h-5 w-5 text-gray-700" />
                      Expense Records
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Showing {((currentExpensePage - 1) * EXPENSES_PER_PAGE) + 1} to {Math.min(currentExpensePage * EXPENSES_PER_PAGE, filteredExpenses.length)} of {filteredExpenses.length} {filteredExpenses.length === 1 ? 'expense' : 'expenses'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.description')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.detail')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.category')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.type')}</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.mount')}</th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.status')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.cost_period')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.payment_date')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.payment_period')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('accounting.source')}</th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.actions')}</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {paginatedExpenses.map((expense, index) => (
                      <tr key={expense.id} className="hover:bg-gray-50 transition-colors group">
                          <td className="py-5 px-6 text-center">
                            <span className="text-sm font-medium text-gray-600">
                              {(currentExpensePage - 1) * EXPENSES_PER_PAGE + index + 1}
                            </span>
                          </td>
                          <td className="py-5 px-6">
                            <p className="font-semibold text-gray-900 group-hover:text-gray-700 transition-colors">{expense.description}</p>
                          </td>
                          <td className="py-5 px-6">
                            <p className="text-sm text-gray-600 max-w-xs truncate" title={expense.detail}>
                              {expense.detail}
                            </p>
                          </td>
                          <td className="py-5 px-6">
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                              expense.category === 'inflow' 
                                ? 'bg-gray-100 text-gray-700 border border-gray-300' :
                                'bg-gray-200 text-gray-800 border border-gray-300'
                            }`}>
                              {expense.category === 'inflow' ? t('accounting.category_inflow') : t('accounting.category_outflow')}
                            </span>
                          </td>
                          <td className="py-5 px-6">
                            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-gray-50 text-gray-700 border border-gray-200">
                              {expense.type === 'payment' ? t('accounting.type_payment') : t('accounting.type_transfer')}
                            </span>
                          </td>
                          <td className="py-5 px-6 text-right">
                            <p className="font-bold text-gray-900 font-mono">
                              {expense.mount_currency === 'USD' 
                                ? `$${expense.amount_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                : expense.mount_currency === 'USDT'
                                ? `₮${expense.amount_usdt.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                : formatCurrencyUtil(expense.amount_try, '₺')}
                            </p>
                            <p className="text-xs text-gray-500 mt-0.5">
                              {expense.mount_currency || 'TRY'}
                            </p>
                          </td>
                          <td className="py-5 px-6 text-center">
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                              expense.status === 'paid' 
                                ? 'bg-gray-100 text-gray-700 border border-gray-300' :
                              expense.status === 'pending'
                                ? 'bg-gray-50 text-gray-600 border border-gray-200' :
                                'bg-gray-200 text-gray-800 border border-gray-300'
                            }`}>
                              {expense.status === 'paid' && <CheckCircle className="h-3.5 w-3.5" />}
                              {expense.status === 'pending' && <Clock className="h-3.5 w-3.5" />}
                              {expense.status === 'cancelled' && <XCircle className="h-3.5 w-3.5" />}
                              {expense.status === 'paid' ? 'Ödendi' : 
                               expense.status === 'pending' ? 'Beklemede' : 
                               'İptal'}
                            </span>
                          </td>
                          <td className="py-5 px-6">
                            <p className="text-sm text-gray-700">{expense.cost_period}</p>
                          </td>
                          <td className="py-5 px-6">
                            <p className="text-sm text-gray-700">
                              {expense.payment_date ? new Date(expense.payment_date).toLocaleDateString('tr-TR') : '-'}
                            </p>
                          </td>
                          <td className="py-5 px-6">
                            <p className="text-sm text-gray-700">{expense.payment_period}</p>
                          </td>
                          <td className="py-5 px-6">
                            <p className="text-sm text-gray-700">{expense.source}</p>
                          </td>
                          <td className="py-5 px-6">
                            <div className="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenViewExpense(expense)}
                                className="h-9 w-9 p-0 hover:bg-gray-100 hover:text-gray-700 rounded-lg transition-all"
                                title="View expense details (read-only)"
                                aria-label="View expense"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenEditExpense(expense)}
                                className="h-9 w-9 p-0 hover:bg-gray-100 hover:text-gray-700 rounded-lg transition-all"
                                title="Edit this expense"
                                aria-label="Edit expense"
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteExpense(expense.id)}
                                className="h-9 w-9 p-0 hover:bg-gray-200 hover:text-gray-900 rounded-lg transition-all"
                                title="Delete this expense (cannot be undone)"
                                aria-label="Delete expense"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
                
                {filteredExpenses.length === 0 && (
                  <div className="text-center py-16">
                    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                      <ShoppingCart className="h-10 w-10 text-gray-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No expenses found</h3>
                    <p className="text-sm text-gray-600 max-w-md mx-auto mb-6">
                      {searchTerm || expenseStatusFilter !== 'all' || expenseCategoryFilter !== 'all'
                        ? 'No expenses match your current search or filter criteria. Try adjusting your filters to see more results.' 
                        : 'You haven\'t added any expenses yet. Start tracking your company expenses by adding your first entry.'}
                    </p>
                    {!searchTerm && expenseStatusFilter === 'all' && expenseCategoryFilter === 'all' && (
                      <Button
                        onClick={handleOpenAddExpense}
                        className="bg-gray-900 hover:bg-gray-800 text-white px-4 py-2 rounded-lg flex items-center gap-2 mx-auto border border-gray-900 transition-all"
                      >
                        <Plus className="h-4 w-4" />
                        Add Your First Expense
                      </Button>
                    )}
                    {(searchTerm || expenseStatusFilter !== 'all' || expenseCategoryFilter !== 'all') && (
                      <Button
                        variant="outline"
                        onClick={() => {
                          setSearchTerm('');
                          setExpenseStatusFilter('all');
                          setExpenseCategoryFilter('all');
                        }}
                        className="border-gray-200 hover:border-gray-300 hover:bg-gray-50 px-4 py-2 rounded-lg flex items-center gap-2 mx-auto"
                      >
                        <X className="h-4 w-4" />
                        Clear Filters
                      </Button>
                    )}
                  </div>
                )}

                {/* Pagination Controls */}
                {filteredExpenses.length > EXPENSES_PER_PAGE && (
                  <div className="bg-gray-50 border-t border-gray-200 px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        Page {currentExpensePage} of {totalExpensePages}
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentExpensePage(prev => Math.max(prev - 1, 1))}
                          disabled={currentExpensePage === 1}
                          className="flex items-center gap-2"
                        >
                          <ChevronLeft className="h-4 w-4" />
                          Previous
                        </Button>
                        
                        <div className="flex items-center gap-1">
                          {Array.from({ length: Math.min(5, totalExpensePages) }, (_, i) => {
                            let pageNum;
                            if (totalExpensePages <= 5) {
                              pageNum = i + 1;
                            } else if (currentExpensePage <= 3) {
                              pageNum = i + 1;
                            } else if (currentExpensePage >= totalExpensePages - 2) {
                              pageNum = totalExpensePages - 4 + i;
                            } else {
                              pageNum = currentExpensePage - 2 + i;
                            }
                            
                            return (
                              <Button
                                key={pageNum}
                                variant={currentExpensePage === pageNum ? "default" : "outline"}
                                size="sm"
                                onClick={() => setCurrentExpensePage(pageNum)}
                                className="min-w-[40px] h-9"
                              >
                                {pageNum}
                              </Button>
                            );
                          })}
                        </div>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentExpensePage(prev => Math.min(prev + 1, totalExpensePages))}
                          disabled={currentExpensePage === totalExpensePages}
                          className="flex items-center gap-2"
                        >
                          Next
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Business-Oriented Summary Cards */}
            {expenses.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Turkish Lira Card */}
                <div className="bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 group">
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div className="w-14 h-14 bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-center group-hover:bg-gray-100 transition-all duration-200">
                        <Banknote className="h-7 w-7 text-gray-700 group-hover:text-gray-900 transition-colors" />
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total TRY</p>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <p className="text-3xl font-bold text-slate-900 font-mono tracking-tight">
                        {formatCurrencyUtil(expenseTotals.totalTRY, '₺')}
                      </p>
                      <p className="text-sm text-slate-600 font-medium">Turkish Lira</p>
                    </div>
                  </div>
                </div>

                {/* US Dollar Card */}
                <div className="bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 group">
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div className="w-14 h-14 bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-center group-hover:bg-gray-100 transition-all duration-200">
                        <CreditCard className="h-7 w-7 text-gray-700 group-hover:text-gray-900 transition-colors" />
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total USD</p>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <p className="text-3xl font-bold text-slate-900 font-mono tracking-tight">
                        ${expenseTotals.totalUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </p>
                      <p className="text-sm text-slate-600 font-medium">US Dollar</p>
                    </div>
                  </div>
                </div>

                {/* Expense Records Card */}
                <div className="bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 group">
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div className="w-14 h-14 bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-center group-hover:bg-gray-100 transition-all duration-200">
                        <Receipt className="h-7 w-7 text-gray-700 group-hover:text-gray-900 transition-colors" />
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Entries</p>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <p className="text-3xl font-bold text-slate-900 tracking-tight">
                        {expenseTotals.count}
                      </p>
                      <p className="text-sm text-slate-600 font-medium">Expense Records</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

              </>
            )}

            {/* Daily Summary View */}
            {expensesView === 'daily' && (
              <div className="space-y-6">
                {/* Header Card */}
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <div className="bg-gray-50 px-6 py-5 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-3">
                          <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200">
                            <Calendar className="h-5 w-5 text-gray-700" />
                          </div>
                          {t('accounting.daily_expenses')}
                        </h2>
                        <p className="text-sm text-gray-600 mt-1">{t('accounting.daily_breakdown')}</p>
                      </div>
                      <UnifiedBadge variant="info" size="md">
                        {t('accounting.payment_date_grouped')}
                      </UnifiedBadge>
                    </div>
                  </div>

                  {/* Clean Period Selection */}
                  <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Calendar className="h-5 w-5 text-gray-600" />
                        <div>
                          <h3 className="text-sm font-semibold text-gray-900">{t('accounting.select_period')}</h3>
                          <p className="text-xs text-gray-600">Choose month and year for analysis</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        {/* Month Selector */}
                        <div className="flex flex-col gap-1">
                          <label className="text-xs font-medium text-gray-700 uppercase tracking-wide">Month</label>
                          <select
                            value={selectedMonth}
                            onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                            className="px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-gray-500 focus:border-gray-500 font-medium min-w-[120px]"
                          >
                            <option value={1}>{t('accounting.january')}</option>
                            <option value={2}>{t('accounting.february')}</option>
                            <option value={3}>{t('accounting.march')}</option>
                            <option value={4}>{t('accounting.april')}</option>
                            <option value={5}>{t('accounting.may')}</option>
                            <option value={6}>{t('accounting.june')}</option>
                            <option value={7}>{t('accounting.july')}</option>
                            <option value={8}>{t('accounting.august')}</option>
                            <option value={9}>{t('accounting.september')}</option>
                            <option value={10}>{t('accounting.october')}</option>
                            <option value={11}>{t('accounting.november')}</option>
                            <option value={12}>{t('accounting.december')}</option>
                          </select>
                        </div>
                        
                        {/* Year Selector */}
                        <div className="flex flex-col gap-1">
                          <label className="text-xs font-medium text-gray-700 uppercase tracking-wide">Year</label>
                          <select
                            value={selectedYear}
                            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                            className="px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-gray-500 focus:border-gray-500 font-medium min-w-[100px]"
                          >
                            {Array.from({ length: 5 }, (_, i) => {
                              const year = new Date().getFullYear() - 2 + i;
                              return (
                                <option key={year} value={year}>
                                  {year}
                                </option>
                              );
                            })}
                          </select>
                        </div>
                        
                        {/* Current Month Button */}
                        <div className="flex flex-col gap-1">
                          <label className="text-xs font-medium text-gray-700 uppercase tracking-wide opacity-0">Action</label>
                          <button
                            onClick={() => {
                              setSelectedMonth(new Date().getMonth() + 1);
                              setSelectedYear(new Date().getFullYear());
                            }}
                            className="px-4 py-2 text-sm bg-gray-800 text-white rounded-md hover:bg-gray-900 transition-colors font-medium"
                          >
                            {t('accounting.current_month')}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Daily Summary Table */}
                  <div className="overflow-x-auto">
                    {dailySummary.length > 0 ? (
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                          <tr>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                              <div className="flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-gray-500" />
                                {t('accounting.payment_date')}
                                <button
                                  onClick={() => setDailySummarySortOrder(dailySummarySortOrder === 'desc' ? 'asc' : 'desc')}
                                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                                  title={dailySummarySortOrder === 'desc' ? t('accounting.sort_ascending') : t('accounting.sort_descending')}
                                >
                                  {dailySummarySortOrder === 'desc' ? (
                                    <svg className="h-3 w-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                  ) : (
                                    <svg className="h-3 w-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                    </svg>
                                  )}
                                </button>
                              </div>
                            </th>
                            <th className="px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                              <div className="flex items-center justify-end gap-2">
                                <Banknote className="h-4 w-4 text-gray-500" />
                                TRY
                              </div>
                            </th>
                            <th className="px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                              <div className="flex items-center justify-end gap-2">
                                <Banknote className="h-4 w-4 text-gray-500" />
                                USD
                              </div>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {dailySummary.map((day, index) => (
                            <React.Fragment key={day.date}>
                              <tr 
                                key={day.date} 
                                onClick={() => setExpandedDate(expandedDate === day.date ? null : day.date)}
                                className="hover:bg-gray-50 transition-colors group cursor-pointer"
                              >
                                <td className="px-6 py-4">
                                  <div className="flex items-center gap-3">
                                    <Calendar className="h-5 w-5 text-gray-400" />
                                    <div>
                                      <p className="font-semibold text-gray-900 text-base">
                                        {new Date(day.date).toLocaleDateString(
                                          currentLanguage === 'tr' ? 'tr-TR' : 'en-US', 
                                          { 
                                            day: '2-digit', 
                                            month: 'long', 
                                            year: 'numeric' 
                                          }
                                        )}
                                      </p>
                                      <p className="text-sm text-gray-600 mt-0.5">
                                        {day.count} {day.count === 1 ? 'transaction' : 'transactions'}
                                      </p>
                                    </div>
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-right">
                                  <p className="text-lg font-semibold text-gray-900 font-mono">
                                    {formatCurrencyUtil(day.totalTRY, '₺')}
                                  </p>
                                </td>
                                <td className="px-6 py-4 text-right">
                                  <div className="flex items-center justify-end gap-2">
                                    <p className="text-lg font-semibold text-gray-900 font-mono">
                                      ${day.totalUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                    </p>
                                    <div className={`transition-transform duration-200 ${expandedDate === day.date ? 'rotate-180' : ''}`}>
                                      <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                      </svg>
                                    </div>
                                  </div>
                                </td>
                              </tr>
                              
                              {/* Professional Expanded Details */}
                              {expandedDate === day.date && (
                                <tr className="bg-slate-50">
                                  <td colSpan={3} className="px-6 py-6">
                                    <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                                      {/* Header */}
                                      <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
                                        <div className="flex items-center justify-between">
                                          <div className="flex items-center gap-3">
                                            <div className="w-9 h-9 bg-slate-100 rounded-lg flex items-center justify-center">
                                              <Receipt className="h-5 w-5 text-slate-700" />
                                            </div>
                                            <div>
                                              <h4 className="font-semibold text-slate-900 text-sm">
                                                {t('accounting.expenses_for_date').replace('{count}', day.count.toString())}
                                              </h4>
                                              <p className="text-xs text-slate-600 mt-0.5">
                                                Detailed transaction breakdown
                                              </p>
                                            </div>
                                          </div>
                                          <div className="flex items-center gap-6 text-xs">
                                            <div className="text-right">
                                              <p className="text-slate-500 font-medium uppercase tracking-wide">Total TRY</p>
                                              <p className="text-slate-900 font-semibold text-sm mt-0.5 font-mono">
                                                {formatCurrencyUtil(day.totalTRY, '₺')}
                                              </p>
                                            </div>
                                            <div className="text-right">
                                              <p className="text-slate-500 font-medium uppercase tracking-wide">Total USD</p>
                                              <p className="text-slate-900 font-semibold text-sm mt-0.5 font-mono">
                                                ${day.totalUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                              </p>
                                            </div>
                                          </div>
                                        </div>
                                      </div>

                                      {/* Professional Table Layout */}
                                      <div className="overflow-hidden">
                                        <table className="w-full">
                                          <thead className="bg-slate-50 border-b border-slate-200">
                                            <tr>
                                              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider w-[40%]">
                                                Description
                                              </th>
                                              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider w-[30%]">
                                                Details
                                              </th>
                                              <th className="px-4 py-3 text-right text-xs font-semibold text-slate-700 uppercase tracking-wider w-[12%]">
                                                TRY
                                              </th>
                                              <th className="px-4 py-3 text-right text-xs font-semibold text-slate-700 uppercase tracking-wider w-[12%]">
                                                USD
                                              </th>
                                              <th className="px-6 py-3 text-center text-xs font-semibold text-slate-700 uppercase tracking-wider w-[6%]">
                                                {t('accounting.status')}
                                              </th>
                                            </tr>
                                          </thead>
                                          <tbody className="bg-white divide-y divide-slate-100">
                                            {day.expenses.map((expense, idx) => (
                                              <tr 
                                                key={expense.id} 
                                                className="hover:bg-slate-50 transition-colors"
                                              >
                                                <td className="px-6 py-4">
                                                  <div className="flex items-start gap-3">
                                                    <div className="mt-0.5">
                                                      <Receipt className="h-4 w-4 text-slate-400" />
                                                    </div>
                                                    <div className="min-w-0 flex-1">
                                                      <p className="font-semibold text-slate-900 text-sm leading-tight">
                                                        {expense.description}
                                                      </p>
                                                      <p className="text-xs text-slate-500 mt-1 font-medium">
                                                        ID: {expense.id}
                                                      </p>
                                                    </div>
                                                  </div>
                                                </td>
                                                <td className="px-4 py-4">
                                                  <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
                                                    {expense.detail}
                                                  </p>
                                                </td>
                                                <td className="px-4 py-4 text-right">
                                                  <p className="text-sm font-semibold text-slate-900 font-mono tabular-nums">
                                                    {formatCurrencyUtil(expense.amount_try, '₺')}
                                                  </p>
                                                </td>
                                                <td className="px-4 py-4 text-right">
                                                  <p className="text-sm font-semibold text-slate-900 font-mono tabular-nums">
                                                    ${expense.amount_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                                  </p>
                                                </td>
                                                <td className="px-6 py-4">
                                                  <div className="flex justify-center">
                                                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wide ${
                                                      expense.status === 'paid' 
                                                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                                                        : expense.status === 'pending'
                                                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                                                    }`}>
                                                      {expense.status === 'paid' ? t('accounting.paid') : 
                                                       expense.status === 'pending' ? t('accounting.pending') : 
                                                       t('accounting.cancelled')}
                                                    </span>
                                                  </div>
                                                </td>
                                              </tr>
                                            ))}
                                          </tbody>
                                        </table>
                                      </div>
                                    </div>
                                  </td>
                                </tr>
                              )}
                            </React.Fragment>
                          ))}
                        </tbody>
                        <tfoot className="bg-gray-100 border-t border-gray-300">
                          <tr>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                </svg>
                                <div>
                                  <p className="font-semibold text-gray-900 text-lg">
                                    Grand Total
                                  </p>
                                  <p className="text-sm text-gray-600 mt-0.5">
                                    {dailySummary.length} {dailySummary.length === 1 ? 'day' : 'days'} • {dailySummary.reduce((sum, day) => sum + day.count, 0)} total transactions
                                  </p>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <p className="text-xl font-semibold text-gray-900 font-mono">
                                {formatCurrencyUtil(
                                  dailySummary.reduce((sum, day) => sum + day.totalTRY, 0),
                                  '₺'
                                )}
                              </p>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <p className="text-xl font-semibold text-gray-900 font-mono">
                                ${dailySummary.reduce((sum, day) => sum + day.totalUSD, 0).toLocaleString('en-US', { 
                                  minimumFractionDigits: 2, 
                                  maximumFractionDigits: 2 
                                })}
                              </p>
                            </td>
                          </tr>
                        </tfoot>
                      </table>
                    ) : (
                      <div className="text-center py-16">
                        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                          <Calendar className="h-10 w-10 text-gray-600" />
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">{t('accounting.no_daily_data')}</h3>
                        <p className="text-sm text-gray-600 max-w-md mx-auto mb-6">
                          {t('accounting.no_daily_data_desc')}
                        </p>
                        <Button
                          onClick={() => setExpensesView('all')}
                          className="bg-gray-900 hover:bg-gray-800 text-white px-4 py-2 rounded-lg flex items-center gap-2 mx-auto border border-gray-900 transition-all"
                        >
                          <Receipt className="h-4 w-4" />
                          {t('accounting.all_expenses')}
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            {/* Internal Revenue View */}
            {expensesView === 'internal_revenue' && (
              <div className="space-y-6">
                {/* Currency Summary */}
                {currencySummary.length > 0 && (
                  <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                    <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                      {/* Month Selector Row */}
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-4">
                          <label className="text-sm font-medium text-gray-700">Month:</label>
                          <select
                            value={selectedMonthPeriod}
                            onChange={(e) => loadMonthData(e.target.value)}
                            disabled={isLoadingMonth}
                            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 bg-white text-sm"
                          >
                            <option value={new Date().toISOString().slice(0, 7)}>
                              Current Month ({new Date().toISOString().slice(0, 7)})
                            </option>
                            {savedMonths.map(month => (
                              <option key={month.month_period} value={month.month_period}>
                                {month.month_period} {month.is_locked ? '🔒' : ''}
                              </option>
                            ))}
                          </select>
                          
                          {isMonthLocked && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-orange-100 text-orange-700 border border-orange-200">
                              <Lock className="h-3 w-3 mr-1" />
                              Locked
                            </span>
                          )}
                          
                          {isLoadingMonth && (
                            <span className="text-sm text-gray-500">Loading...</span>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <Button
                            onClick={handleSaveCurrencySummary}
                            disabled={isMonthLocked || isSavingMonth || isLoadingMonth}
                            className="bg-gray-900 hover:bg-gray-800 text-white disabled:opacity-50"
                            size="sm"
                          >
                            <Save className="h-4 w-4 mr-2" />
                            {isSavingMonth ? 'Saving...' : 'Save Month Data'}
                          </Button>
                          
                          {!isMonthLocked && selectedMonthPeriod !== new Date().toISOString().slice(0, 7) && (
                            <Button
                              onClick={handleLockMonth}
                              variant="outline"
                              size="sm"
                              className="border-orange-500 text-orange-600 hover:bg-orange-50"
                            >
                              <Lock className="h-4 w-4 mr-2" />
                              Lock Month
                            </Button>
                          )}
                          
                          {isMonthLocked && (
                            <Button
                              onClick={handleUnlockMonth}
                              variant="outline"
                              size="sm"
                              className="border-green-500 text-green-600 hover:bg-green-50"
                            >
                              <Unlock className="h-4 w-4 mr-2" />
                              Unlock
                            </Button>
                          )}
                        </div>
                      </div>
                      
                      {/* Title Row */}
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                            <Calculator className="h-5 w-5 text-gray-700" />
                            Currency Summary
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            Summary grouped by currency with inflow/outflow calculations. 
                            {isMonthLocked ? ' (Read-only - month is locked)' : ' Edit DEVİR and KUR, then click Save.'}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Currency</th>
                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">DEVİR<br/>(Carryover)</th>
                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">GİREN<br/>(Inflow)</th>
                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">ÇIKAN<br/>(Outflow)</th>
                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">NET</th>
                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">USD ÇEVRİM<br/>(USD Conversion)</th>
                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">KUR<br/>(Rate)</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {currencySummary.map((item, index) => {
                            const exchangeRate = (currentRate && currentRate > 0) ? currentRate : 42.00;
                            return (
                            <tr key={item.currency} className="hover:bg-gray-50 transition-colors">
                              <td className="px-6 py-4">
                                <span className="font-semibold text-gray-900">{item.currency}</span>
                              </td>
                              <td className="px-6 py-4 text-right">
                                <div className="flex items-center justify-end gap-2">
                                  {item.currency === 'TRY' ? (
                                    <span className="text-gray-500 text-sm">₺</span>
                                  ) : (
                                    <span className="text-gray-500 text-sm">$</span>
                                  )}
                                  <Input
                                    type="number"
                                    step="0.01"
                                    value={tempCarryoverValues[item.currency as 'TRY' | 'USD' | 'USDT'] || 0}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value) || 0;
                                      setTempCarryoverValues({
                                        ...tempCarryoverValues,
                                        [item.currency]: value
                                      });
                                      // NO auto-save! User must click "Save Month Data" button
                                    }}
                                    disabled={isMonthLocked}
                                    className={`w-32 h-9 text-sm font-mono text-right border-gray-300 focus:border-gray-500 focus:ring-gray-500 ${
                                      isMonthLocked ? 'bg-gray-100 cursor-not-allowed' : ''
                                    }`}
                                    placeholder="0.00"
                                  />
                                </div>
                              </td>
                              <td className="px-6 py-4 text-right">
                                <span className="text-sm font-mono text-gray-700">
                                  {item.currency === 'TRY' 
                                    ? formatCurrencyUtil(item.inflow, '₺')
                                    : item.currency === 'USD'
                                    ? `$${item.inflow.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                    : `$${item.inflow.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-right">
                                <span className="text-sm font-mono text-gray-700">
                                  {item.currency === 'TRY' 
                                    ? formatCurrencyUtil(item.outflow, '₺')
                                    : item.currency === 'USD'
                                    ? `$${item.outflow.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                    : `$${item.outflow.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-right">
                                <span className={`text-sm font-bold font-mono ${
                                  item.net >= 0 ? 'text-gray-900' : 'text-red-600'
                                }`}>
                                  {item.currency === 'TRY' 
                                    ? formatCurrencyUtil(item.net, '₺')
                                    : item.currency === 'USD'
                                    ? `$${item.net.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                    : `$${item.net.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-right">
                                <span className="text-sm font-bold font-mono text-gray-900">
                                  ${item.usdEquivalent.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-right">
                                {item.currency === 'TRY' ? (
                                  <div className="flex items-center justify-end gap-2">
                                    <Input
                                      type="number"
                                      step="0.01"
                                      value={tempExchangeRates.TRY || ''}
                                      onChange={(e) => {
                                        setTempExchangeRates({
                                          ...tempExchangeRates,
                                          TRY: e.target.value
                                        });
                                      }}
                                      disabled={isMonthLocked}
                                      className={`w-24 h-9 text-sm font-mono text-right border-gray-300 focus:border-gray-500 focus:ring-gray-500 ${
                                        isMonthLocked ? 'bg-gray-100 cursor-not-allowed' : ''
                                      }`}
                                      placeholder="0.00"
                                    />
                                  </div>
                                ) : (
                                  <span className="text-sm font-mono text-gray-700">-</span>
                                )}
                              </td>
                            </tr>
                            );
                          })}
                          {/* KASA TOPLAM Row */}
                          <tr className="bg-gray-50 font-semibold">
                            <td className="px-6 py-4">
                              <span className="font-bold text-gray-900">KASA TOPLAM</span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <span className="text-sm font-mono text-gray-700">-</span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <span className="text-sm font-mono text-gray-700">-</span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <span className="text-sm font-mono text-gray-700">-</span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <span className="text-sm font-mono text-gray-700">-</span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <span className="text-sm font-bold font-mono text-gray-900">
                                ${currencySummary.reduce((sum, item) => sum + item.usdEquivalent, 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <span className="text-sm font-mono text-gray-700">-</span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="mt-6">
          {activeTab === 'analytics' && (
            <div className="p-6 animate-in fade-in duration-300">
              <UnifiedCard variant="elevated">
                <CardHeader>
                  <CardTitle>Accounting Analytics</CardTitle>
                  <CardDescription>Financial analytics and reporting</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">Accounting analytics will be displayed here.</p>
                </CardContent>
              </UnifiedCard>
            </div>
          )}
        </TabsContent>

        <TabsContent value="net" className="mt-6">
          <div className="space-y-6">
            {/* Sub-Navigation for Net */}
            <div className="relative w-full">
              {/* Background with glassmorphism effect */}
              <div className="relative bg-gradient-to-r from-slate-50/90 via-white/80 to-slate-50/90 backdrop-blur-sm border border-slate-200/60 rounded-xl shadow-lg shadow-slate-200/20 p-1.5">
                {/* Animated background indicator */}
                <div 
                  className={`absolute top-1.5 bottom-1.5 w-[calc(50%-0.375rem)] bg-gray-100/50 backdrop-blur-sm border border-gray-200/40 rounded-lg shadow-sm transition-all duration-300 ease-out ${
                    netView === 'calculator' 
                      ? 'left-1.5' 
                      : 'right-1.5'
                  }`}
                />
                
                {/* Tab buttons */}
                <div className="relative grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => setNetView('calculator')}
                    className={`group relative flex items-center justify-center gap-2.5 px-5 py-3.5 rounded-lg font-semibold text-sm transition-all duration-300 ease-out outline-none focus:outline-none focus:ring-0 ${
                      netView === 'calculator'
                        ? 'text-green-700 shadow-sm'
                        : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50/50'
                    }`}
                  >
                    {/* Icon with subtle animation */}
                    <Calculator className={`h-4 w-4 transition-all duration-300 ${
                      netView === 'calculator' 
                        ? 'text-green-600 scale-110' 
                        : 'text-slate-500 group-hover:text-slate-700 group-hover:scale-105'
                    }`} />
                    
                    {/* Text with smooth transitions */}
                    <span className="relative z-10 transition-all duration-300">
                      Net Calculator
                    </span>
                    
                    {/* Subtle glow effect for active state */}
                    {netView === 'calculator' && (
                      <div className="absolute inset-0 rounded-lg bg-gray-100/20 animate-pulse" />
                    )}
                  </button>
                  
                  <button
                    onClick={() => setNetView('daily')}
                    className={`group relative flex items-center justify-center gap-2.5 px-5 py-3.5 rounded-lg font-semibold text-sm transition-all duration-300 ease-out outline-none focus:outline-none focus:ring-0 ${
                      netView === 'daily'
                        ? 'text-green-700 shadow-sm'
                        : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50/50'
                    }`}
                  >
                    {/* Icon with subtle animation */}
                    <Calendar className={`h-4 w-4 transition-all duration-300 ${
                      netView === 'daily' 
                        ? 'text-green-600 scale-110' 
                        : 'text-slate-500 group-hover:text-slate-700 group-hover:scale-105'
                    }`} />
                    
                    {/* Text with smooth transitions */}
                    <span className="relative z-10 transition-all duration-300">
                      Daily Net
                    </span>
                    
                    {/* Subtle glow effect for active state */}
                    {netView === 'daily' && (
                      <div className="absolute inset-0 rounded-lg bg-gray-100/20 animate-pulse" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Calculator View */}
            {netView === 'calculator' && (
              <div className="animate-in fade-in duration-300">
              <UnifiedCard variant="elevated">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calculator className="h-5 w-5 text-green-700" />
                    {t('accounting.net.title')}
                  </CardTitle>
                  <CardDescription>{t('accounting.net.subtitle')}</CardDescription>
                </CardHeader>
                <CardContent>
                    <NetCalculatorInner 
                      expenses={expenses} 
                      recordToLoad={recordToLoad}
                      onRecordLoaded={() => setRecordToLoad(null)}
                      validatePin={validatePinViaApi}
                    />
                </CardContent>
              </UnifiedCard>
            </div>
          )}

            {/* Daily Net View */}
            {netView === 'daily' && (
              <div className="animate-in fade-in duration-300">
                <DailyNetView 
                  onLoadRecord={(record) => {
                    setRecordToLoad(record);
                    setNetView('calculator');
                  }}
                  validatePin={validatePinViaApi}
                />
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Security PIN Modal */}
      {showPinModal && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[60] p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowPinModal(false);
              setPinModalCallback(null);
              setSecurityPin('');
              setPinError('');
            }
          }}
        >
          <div className="bg-white rounded-xl border border-gray-200 max-w-sm w-full shadow-2xl">
            <div className="bg-gray-50 px-6 py-5 border-b border-gray-200 rounded-t-xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                  <Shield className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{t('accounting.security_verification')}</h3>
                  <p className="text-sm text-gray-600">{t('accounting.enter_pin_to_continue')}</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('accounting.security_pin')}
                  </label>
                  <Input
                    type="password"
                    value={securityPin}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '').slice(0, 4);
                      setSecurityPin(value);
                      setPinError('');
                    }}
                    placeholder="••••"
                    className="text-center text-2xl font-mono tracking-[0.5em] h-14"
                    maxLength={4}
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && securityPin.length === 4) {
                        handlePinSubmit();
                      }
                    }}
                  />
                  {pinError && (
                    <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="h-4 w-4" />
                      {pinError}
                    </p>
                  )}
                </div>
                <div className="flex gap-3 pt-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => {
                      setShowPinModal(false);
                      setPinModalCallback(null);
                      setSecurityPin('');
                      setPinError('');
                    }}
                  >
                    {t('common.cancel')}
                  </Button>
                  <Button
                    className="flex-1 bg-gray-900 hover:bg-gray-800 text-white"
                    onClick={handlePinSubmit}
                    disabled={securityPin.length !== 4 || validatingPin}
                  >
                    {validatingPin ? (
                      <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Check className="h-4 w-4 mr-2" />
                    )}
                    {validatingPin ? t('common.validating') : t('common.confirm')}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modern Expense Modal */}
      {showExpenseModal && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) handleCloseExpenseModal();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Escape') handleCloseExpenseModal();
          }}
          tabIndex={-1}
        >
          <div className="bg-white rounded-lg border border-gray-200 max-w-2xl w-full max-h-[90vh] overflow-hidden">
            <div className="bg-gray-50 px-6 py-5 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200">
                    <Receipt className="h-5 w-5 text-gray-700" />
                  </div>
                  {isViewMode ? t('accounting.view_expense') : editingExpense ? t('accounting.edit_expense') : t('accounting.add_new_expense')}
                </h2>
                <button
                  onClick={handleCloseExpenseModal}
                  className="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition-colors"
                >
                  <X className="h-5 w-5 text-gray-500" />
                </button>
              </div>
            </div>

            <div className="overflow-y-auto max-h-[calc(90vh-140px)]">
              <div className="p-6 space-y-6">
              
              {/* Basic Information Section */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide flex items-center gap-2">
                  <div className="w-1 h-4 bg-gray-700 rounded-full"></div>
                  {t('accounting.basic_information')}
                </h3>
                <div className="pl-4 space-y-4">
                  {/* Description */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      {t('accounting.description')} {!isViewMode && <span className="text-red-500">*</span>}
                    </label>
                    <Input
                      type="text"
                      placeholder={t('accounting.description_placeholder')}
                      value={formData.description}
                      onChange={(e) => setFormData({...formData, description: e.target.value})}
                      className="w-full h-11 text-base"
                      disabled={isViewMode}
                    />
                  </div>

                  {/* Detail */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      {t('accounting.detail')}
                    </label>
                    <Input
                      type="text"
                      placeholder={t('accounting.detail_placeholder')}
                      value={formData.detail}
                      onChange={(e) => setFormData({...formData, detail: e.target.value})}
                      className="w-full h-11 text-base"
                      disabled={isViewMode}
                    />
                  </div>

                  {/* Category */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      {t('accounting.category')} {!isViewMode && <span className="text-red-500">*</span>}
                    </label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({...formData, category: e.target.value as 'inflow' | 'outflow'})}
                      className="w-full h-11 px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 disabled:bg-gray-100 disabled:cursor-not-allowed text-base"
                      disabled={isViewMode}
                    >
                      <option value="inflow">{t('accounting.category_inflow')}</option>
                      <option value="outflow">{t('accounting.category_outflow')}</option>
                    </select>
                  </div>

                  {/* Type */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      {t('accounting.type')} {!isViewMode && <span className="text-red-500">*</span>}
                    </label>
                    <select
                      value={formData.type}
                      onChange={(e) => setFormData({...formData, type: e.target.value as 'payment' | 'transfer'})}
                      className="w-full h-11 px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 disabled:bg-gray-100 disabled:cursor-not-allowed text-base"
                      disabled={isViewMode}
                    >
                      <option value="payment">{t('accounting.type_payment')}</option>
                      <option value="transfer">{t('accounting.type_transfer')}</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Financial Details Section */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide flex items-center gap-2">
                  <div className="w-1 h-4 bg-gray-700 rounded-full"></div>
                  {t('accounting.financial_details')}
                </h3>
                <div className="pl-4 space-y-4">
                  {/* Amount - Radio buttons + single input */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        {t('accounting.mount')} {!isViewMode && <span className="text-red-500">*</span>}
                      </label>
                      
                      {/* Converter Toggle */}
                      {!isViewMode && (
                        <div className="flex items-center gap-3 mb-3 p-3 bg-gray-50 border border-gray-200 rounded-md">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={converterEnabled}
                              onChange={(e) => setConverterEnabled(e.target.checked)}
                              className="w-4 h-4 rounded border-gray-300 text-gray-700 focus:ring-gray-500 focus:ring-2"
                            />
                            <span className="text-sm font-medium text-gray-700">Converter</span>
                          </label>
                          <span className={`text-xs px-2 py-1 rounded ${
                            converterEnabled 
                              ? 'bg-gray-200 text-gray-700' 
                              : 'bg-gray-100 text-gray-500'
                          }`}>
                            {converterEnabled ? 'ON' : 'OFF'}
                          </span>
                        </div>
                      )}
                      
                      {/* Currency Selection - Radio Buttons */}
                      {!isViewMode && (
                        <div className="flex items-center gap-4 mb-3 p-3 bg-gray-50 border border-gray-200 rounded-md">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              value="TRY"
                              checked={formData.mount_currency === 'TRY'}
                              onChange={(e) => setFormData({...formData, mount_currency: e.target.value as 'TRY' | 'USD' | 'USDT'})}
                              className="w-4 h-4 text-gray-700"
                            />
                            <span className="font-medium text-sm">₺ TRY</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              value="USD"
                              checked={formData.mount_currency === 'USD'}
                              onChange={(e) => setFormData({...formData, mount_currency: e.target.value as 'TRY' | 'USD' | 'USDT'})}
                              className="w-4 h-4 text-gray-700"
                            />
                            <span className="font-medium text-sm">$ USD</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              value="USDT"
                              checked={formData.mount_currency === 'USDT'}
                              onChange={(e) => setFormData({...formData, mount_currency: e.target.value as 'TRY' | 'USD' | 'USDT'})}
                              className="w-4 h-4 text-gray-700"
                            />
                            <span className="font-medium text-sm">₮ USDT</span>
                          </label>
                        </div>
                      )}
                      
                      {/* Single Amount Input */}
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-semibold">
                          {formData.mount_currency === 'TRY' ? '₺' : formData.mount_currency === 'USD' ? '$' : '₮'}
                        </span>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          max="999999999"
                          placeholder="0.00"
                          value={formData.amount}
                          onChange={(e) => setFormData({...formData, amount: e.target.value})}
                          className="w-full h-11 pl-8 text-base font-mono"
                          disabled={isViewMode}
                        />
                      </div>
                      
                      {/* Calculated Amounts (Read-only) */}
                      {!isViewMode && formData.amount && parseFloat(formData.amount) > 0 && (
                        <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-md space-y-2">
                          {converterEnabled ? (
                            <>
                              <div className="text-xs font-semibold text-gray-600 mb-2">{t('accounting.calculated_amounts')}:</div>
                              <div className="grid grid-cols-3 gap-2 text-sm">
                                <div className="flex items-center gap-1.5">
                                  <span className="text-gray-500">₺</span>
                                  <span className="font-mono text-gray-700">{calculatedAmounts.amount_try.toFixed(2)} TRY</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <span className="text-gray-500">$</span>
                                  <span className="font-mono text-gray-700">{calculatedAmounts.amount_usd.toFixed(2)} USD</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <span className="text-gray-500">₮</span>
                                  <span className="font-mono text-gray-700">{calculatedAmounts.amount_usdt.toFixed(2)} USDT</span>
                                </div>
                              </div>
                              {currentRate && formData.mount_currency !== 'USDT' && (
                                <div className="text-xs text-gray-500 mt-2">
                                  {t('accounting.rate')}: 1 USD = {currentRate.toFixed(4)} TRY
                                </div>
                              )}
                            </>
                          ) : (
                            <div className="text-xs text-gray-500">
                              Converter is OFF - Only {formData.mount_currency === 'TRY' ? '₺ TRY' : formData.mount_currency === 'USD' ? '$ USD' : '₮ USDT'} amount will be saved
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* View Mode - Show all amounts */}
                      {isViewMode && (
                        <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-md space-y-2">
                          <div className="grid grid-cols-3 gap-2 text-sm">
                            <div className="flex items-center gap-1.5">
                              <span className="text-gray-500">₺</span>
                              <span className="font-mono text-gray-700">{calculatedAmounts.amount_try.toFixed(2)} TRY</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className="text-gray-500">$</span>
                              <span className="font-mono text-gray-700">{calculatedAmounts.amount_usd.toFixed(2)} USD</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className="text-gray-500">₮</span>
                              <span className="font-mono text-gray-700">{calculatedAmounts.amount_usdt.toFixed(2)} USDT</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Status */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      {t('accounting.status')}
                    </label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({...formData, status: e.target.value as 'paid' | 'pending' | 'cancelled'})}
                      className="w-full h-11 px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 disabled:bg-gray-100 disabled:cursor-not-allowed text-base"
                      disabled={isViewMode}
                    >
                      <option value="pending">{t('accounting.status_pending')}</option>
                      <option value="paid">{t('accounting.status_paid')}</option>
                      <option value="cancelled">{t('accounting.status_cancelled')}</option>
                    </select>
                  </div>

                  {/* Source */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      {t('accounting.source')}
                    </label>
                    <Input
                      type="text"
                      placeholder={t('accounting.source_placeholder')}
                      value={formData.source}
                      onChange={(e) => setFormData({...formData, source: e.target.value})}
                      className="w-full h-11 text-base"
                      disabled={isViewMode}
                    />
                  </div>
                </div>
              </div>

              {/* Period Information Section */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide flex items-center gap-2">
                  <div className="w-1 h-4 bg-gray-700 rounded-full"></div>
                  {t('accounting.period_information')}
                </h3>
                <div className="pl-4 space-y-4">
                  {/* Cost Period */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      {t('accounting.cost_period')}
                    </label>
                    <Input
                      type="text"
                      placeholder={t('accounting.period_placeholder')}
                      value={formData.cost_period}
                      onChange={(e) => setFormData({...formData, cost_period: e.target.value})}
                      className="w-full h-11 text-base"
                      disabled={isViewMode}
                    />
                  </div>

                  {/* Payment Date and Period */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        {t('accounting.payment_date')}
                      </label>
                      <Input
                        type="date"
                        value={formData.payment_date}
                        onChange={(e) => setFormData({...formData, payment_date: e.target.value})}
                        className="w-full h-11 text-base"
                        disabled={isViewMode}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        {t('accounting.payment_period')}
                      </label>
                      <Input
                        type="text"
                        placeholder={t('accounting.period_placeholder')}
                        value={formData.payment_period}
                        onChange={(e) => setFormData({...formData, payment_period: e.target.value})}
                        className="w-full h-11 text-base"
                        disabled={isViewMode}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            </div>

            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
              {showAddAnother ? (
                <>
                  <div className="flex-1">
                    <p className="text-sm text-gray-700 font-medium">{t('accounting.expense_added_success')}</p>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleOpenAddExpense}
                    className="px-4 py-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    {t('accounting.add_another')}
                  </Button>
                  <Button
                    onClick={handleCloseExpenseModal}
                    className="px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white border border-gray-900"
                  >
                    {t('accounting.close')}
                  </Button>
                </>
              ) : !isViewMode ? (
                <>
                  <Button
                    variant="outline"
                    onClick={handleCloseExpenseModal}
                    className="px-4 py-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  >
                    <X className="h-4 w-4 mr-2" />
                    {t('common.cancel')}
                  </Button>
                  <Button
                    onClick={handleSaveExpense}
                    disabled={!formData.description || !formData.category || !formData.type || !formData.amount || parseFloat(formData.amount) <= 0}
                    className="px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white disabled:opacity-50 disabled:cursor-not-allowed border border-gray-900"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    {editingExpense ? t('accounting.update_expense') : t('accounting.add_expense')}
                  </Button>
                </>
              ) : null}
              {isViewMode && (
                <Button
                  variant="outline"
                  onClick={handleCloseExpenseModal}
                  className="px-4 py-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                >
                  <X className="h-4 w-4 mr-2" />
                  {t('accounting.close')}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
