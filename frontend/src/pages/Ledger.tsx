import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useTabPersistence } from '../hooks/useTabPersistence';
import {
  Building,
  Search,
  Filter,
  Download,
  Eye,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Calendar,
  CreditCard,
  Activity,
  BarChart3,
  PieChart,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap,
  LayoutGrid,
  Table,
  LineChart,
  Save,
  AlertTriangle,
  Shield,
  X,
  Target,
  ChevronDown,
  Wallet,
  ChevronRight,
  Edit,
  Save as SaveIcon,
  X as XIcon,
  ChevronLeft,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { api } from '../utils/apiClient';
import { formatCurrency, formatTetherCurrency } from '../utils/currencyUtils';
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
import StandardMetricsCard from '../components/StandardMetricsCard';
import MetricCard from '../components/MetricCard';
import { LedgerPageSkeleton } from '../components/EnhancedSkeletonLoaders';
import TrustTabContent from '../components/trust/TrustTabContent';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  LineChart as RechartsLineChart, 
  Line, 
  PieChart as RechartsPieChart, 
  Pie, 
  Cell,
  AreaChart,
  Area,
  ScatterChart,
  Scatter
} from 'recharts';

interface PSPData {
  psp: string;
  total_amount: number;
  total_commission: number;
  total_net: number;
  total_allocations: number;
  total_deposits: number;
  total_withdrawals: number;
  transaction_count: number;
  commission_rate: number;
}

interface PSPOverviewData {
  psp: string;
  total_deposits: number;
  total_withdrawals: number;
  total_net: number;
  total_allocations: number;
  total_rollover: number;
  transaction_count: number;
  average_transaction: number;
  last_activity: string;
}

interface PSPLedgerData {
  deposit: number;        // Backend uses 'deposit' not 'deposits'
  withdraw: number;       // Backend uses 'withdraw' not 'withdrawals'
  toplam: number;         // Backend uses 'toplam' not 'total'
  komisyon: number;       // Backend uses 'komisyon' not 'commission'
  net: number;
  allocation: number;
  rollover: number;
  transaction_count: number;
}

interface DayData {
  date: string;
  date_str: string;
  psps: { [key: string]: PSPLedgerData };
  totals: {
    total_psp: number;
    total: number;
    net: number;
    commission: number;
    carry_over: number;
  };
}

interface UnifiedHistoryEntry {
  id: string;
  type: string;
  type_code: string;
  date: string;
  psp_name: string;
  amount: number;
  created_at: string;
  updated_at: string;
}

interface HistoryPagination {
  page: number;
  per_page: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// Helper function to get commission rate color
const getCommissionRateColor = (rate: number) => {
  if (rate === 0) return 'text-gray-500';
  if (rate <= 2) return 'text-green-600';
  if (rate <= 5) return 'text-yellow-600';
  if (rate <= 10) return 'text-orange-600';
  return 'text-red-600';
};

// Helper function to get commission rate background color
const getCommissionRateBgColor = (rate: number) => {
  if (rate === 0) return 'bg-gray-100 text-gray-600';
  if (rate <= 2) return 'bg-green-100 text-green-800';
  if (rate <= 5) return 'bg-yellow-100 text-yellow-800';
  if (rate <= 10) return 'bg-orange-100 text-orange-800';
  return 'bg-red-100 text-red-800';
};

export default function Ledger() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { t } = useLanguage();

  // Helper function to format currency based on PSP type
  const formatPSPCurrency = (amount: number, pspName: string) => {
    if (pspName.toUpperCase() === 'TETHER') {
      return formatTetherCurrency(amount);
    }
    return formatCurrency(amount, '₺');
  };
  const [pspData, setPspData] = useState<PSPData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [pspFilter, setPspFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [activeTab, handleTabChange] = useTabPersistence<'overview' | 'monthly' | 'trust' | 'analytics'>('overview');
  const [commissionCalculating, setCommissionCalculating] = useState(false);
  const [commissionCalculationStatus, setCommissionCalculationStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [commissionDataCached, setCommissionDataCached] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedPsp, setSelectedPsp] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  
  // Monthly tab state
  const [monthlyData, setMonthlyData] = useState<any[]>([]);
  const [monthlyLoading, setMonthlyLoading] = useState(false);
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<number>(new Date().getMonth() + 1);
  const [expandedPSPs, setExpandedPSPs] = useState<Set<string>>(new Set());
  
  // PHASE 1 OPTIMIZATION: Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10); // Show 10 PSPs per page
  
  // Enhanced date filtering state
  const [dateRange, setDateRange] = useState<'custom' | '7' | '30' | '90' | '365'>('30');
  const [customStartDate, setCustomStartDate] = useState<string>('');
  const [customEndDate, setCustomEndDate] = useState<string>('');
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [detailsData, setDetailsData] = useState<any>(null);
  const [ledgerData, setLedgerData] = useState<DayData[]>([]);
  const [ledgerLoading, setLedgerLoading] = useState(false);
  const [allocationSaving, setAllocationSaving] = useState<{[key: string]: boolean}>({});
  const [allocationSaved, setAllocationSaved] = useState<{[key: string]: boolean}>({});
  const [tempAllocations, setTempAllocations] = useState<{[key: string]: number}>({});
  const [pspOverviewData, setPspOverviewData] = useState<PSPOverviewData[]>([]);
  
  // Bulk allocation modal state
  const [showBulkAllocationModal, setShowBulkAllocationModal] = useState(false);
  const [selectedDayForBulk, setSelectedDayForBulk] = useState<string | null>(null);
  const [bulkAllocations, setBulkAllocations] = useState<{[key: string]: number}>({});
  const [bulkAllocationSaving, setBulkAllocationSaving] = useState(false);
  
  // History tab state
  const [historyData, setHistoryData] = useState<UnifiedHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyPagination, setHistoryPagination] = useState<HistoryPagination | null>(null);
  
  // Edit allocation modal state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingAllocation, setEditingAllocation] = useState<{
    psp: string;
    date: string;
    currentAmount: number;
  } | null>(null);
  const [editAmount, setEditAmount] = useState<string>('');
  const [editSaving, setEditSaving] = useState(false);

  // Edit Devir modal state
  const [showEditDevirModal, setShowEditDevirModal] = useState(false);
  const [editingDevir, setEditingDevir] = useState<{
    psp: string;
    date: string;
    currentAmount: number;
  } | null>(null);
  const [editDevirAmount, setEditDevirAmount] = useState<string>('');
  const [editDevirSaving, setEditDevirSaving] = useState(false);
  const [devirSecretCode, setDevirSecretCode] = useState<string>('');

  // Edit KASA TOP modal state
  const [showEditKasaTopModal, setShowEditKasaTopModal] = useState(false);
  const [editingKasaTop, setEditingKasaTop] = useState<{
    psp: string;
    date: string;
    currentAmount: number;
  } | null>(null);
  const [editKasaTopAmount, setEditKasaTopAmount] = useState<string>('');
  const [editKasaTopSaving, setEditKasaTopSaving] = useState(false);
  const [kasaTopSecretCode, setKasaTopSecretCode] = useState<string>('');
  const [historyFilters, setHistoryFilters] = useState({
    startDate: '',
    endDate: '',
    psp: '',
    type: '', // 'all', 'allocation', 'devir', 'kasa_top'
    page: 1
  });

  // Generate all days of the month for complete daily breakdown
  const generateAllDaysOfMonth = (year: number, month: number) => {
    // month is 1-based (1=January, 6=June, etc.)
    // To get the last day of the current month, use month with day 0
    const daysInMonth = new Date(year, month, 0).getDate(); // month'un 0. gunu = onceki ayin son gunu
    const days = [];
    
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month - 1, day); // month - 1 cunku Date constructor 0-based months kullanir
      // Use local date formatting instead of toISOString() to avoid timezone issues
      const dateString = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      days.push({
        date: dateString,
        day: day,
        dayName: date.toLocaleDateString('tr-TR', { weekday: 'short' }),
        isWeekend: date.getDay() === 0 || date.getDay() === 6
      });
    }
    
    return days;
  };

  // Create complete daily breakdown with all days of the month
  const createCompleteDailyBreakdown = (pspData: any, year: number, month: number) => {
    const allDays = generateAllDaysOfMonth(year, month);
    const transactionDays = pspData.daily_breakdown || [];
    
    // Create a map of existing transaction days for quick lookup
    const transactionMap = new Map();
    transactionDays.forEach((day: any) => {
      transactionMap.set(day.date, day);
    });
    
    // Generate complete breakdown with all days
    return allDays.map(dayInfo => {
      const existingDay = transactionMap.get(dayInfo.date);
      
      if (existingDay) {
        // Return existing transaction data
        return {
          ...existingDay,
          day: dayInfo.day,
          dayName: dayInfo.dayName,
          isWeekend: dayInfo.isWeekend
        };
      } else {
        // Return zero-filled day
        return {
          date: dayInfo.date,
          day: dayInfo.day,
          dayName: dayInfo.dayName,
          isWeekend: dayInfo.isWeekend,
          yatimim: 0,
          cekme: 0,
          toplam: 0,
          komisyon: 0,
          net: 0,
          tahs_tutari: 0,
          kasa_top: 0,
          devir: 0,
          transaction_count: 0
        };
      }
    });
  };

  // Scroll to top on mount to prevent auto-scroll down
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, []);

  // Consolidated data fetching effect
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      // Clear any previous errors when component mounts
      setError(null);
      
      // Always fetch PSP data first
      fetchPSPData();
      
      // Fetch ledger data if on overview tab
      if (activeTab === 'overview') {
        fetchLedgerData();
      }
    }
  }, [isAuthenticated, authLoading, activeTab]);

  // Fetch monthly data when Monthly tab is active
  useEffect(() => {
    if (activeTab === 'monthly' && isAuthenticated && !authLoading) {
      fetchMonthlyData(selectedYear, selectedMonth);
      fetchHistoryData(historyFilters.page);
    }
  }, [activeTab, isAuthenticated, authLoading, selectedYear, selectedMonth, historyFilters.startDate, historyFilters.endDate, historyFilters.psp, historyFilters.type]);

  // Listen for transaction updates to automatically refresh ledger data
  useEffect(() => {
    const handleTransactionsUpdate = (event: any) => {
      // Refresh both PSP data and ledger data when transactions are updated
      if (isAuthenticated && !authLoading) {
        // Force refresh to get latest data after transaction updates
        fetchPSPData(true);
        
        // Also refresh ledger data if we're on overview tab
        if (activeTab === 'overview') {
          fetchLedgerData(true);
        }
      }
    };

    // Add event listener
    window.addEventListener('transactionsUpdated', handleTransactionsUpdate);
    
    // Cleanup
    return () => {
      window.removeEventListener('transactionsUpdated', handleTransactionsUpdate);
    };
  }, [isAuthenticated, authLoading, activeTab]);

  // Cleanup effect to clear cache when component unmounts
  useEffect(() => {
    return () => {
      // Clear cache when component unmounts to prevent stale data
      api.clearCacheForUrl('psp_summary_stats');
      api.clearCacheForUrl('ledger-data');
    };
  }, []);

  const fetchPSPData = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);

      // Clear cache if forcing refresh
      if (forceRefresh) {
        api.clearCacheForUrl('psp_summary_stats');
      }

      const response = await api.get('/transactions/psp_summary_stats');

      if (response.status === 401) {
        // User is not authenticated, redirect will be handled by AuthContext
        return;
      }

      const data = api.parseResponse(response);

      if (response.status === 200 && data) {
        // Handle the correct API response format
        // Backend now returns: [{ psp, total_amount, total_commission, total_net, transaction_count, commission_rate }]
        const pspStats = Array.isArray(data) ? data : [];

        // Transform backend data to frontend format (if needed)
        const transformedData: PSPData[] = pspStats.map((item: any) => ({
          psp: item.psp || 'Unknown',
          total_amount: item.total_amount || 0,
          total_commission: item.total_commission || 0,
          total_net: item.total_net || 0,
          total_allocations: item.total_allocations || 0,
          total_deposits: item.total_deposits || 0,
          total_withdrawals: item.total_withdrawals || 0,
          transaction_count: item.transaction_count || 0,
          commission_rate: item.commission_rate || 0,
        }));

        setPspData(transformedData);
      } else {
        const errorMessage = (data && typeof data === 'object' && 'message' in data) 
          ? (data as any).message 
          : 'Failed to load PSP data';
        setError(errorMessage);
        setPspData([]); // Ensure it's always an array
      }
    } catch (error) {
      setError(`Failed to load PSP data: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setPspData([]); // Ensure it's always an array
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      // Force refresh PSP, ledger, and monthly data
      const refreshPromises = [
        fetchPSPData(true),
        fetchLedgerData(true)
      ];
      
      // Only refresh monthly data if we're on the monthly tab
      if (activeTab === 'monthly') {
        refreshPromises.push(fetchMonthlyData(selectedYear, selectedMonth, true));
      }
      
      await Promise.all(refreshPromises);
    } finally {
      setRefreshing(false);
    }
  };

  const handleExport = () => {
    try {
      // Prepare CSV data for export
      const headers = [
        'Date',
        'PSP',
        'Deposits',
        'Withdrawals',
        'Total',
        'Commission',
        'Net',
        'Allocation',
        'Rollover',
        'Risk Level'
      ];

      const rows: (string | number)[][] = [];
      
      // Add ledger data rows
      ledgerData.forEach((dayData) => {
        Object.entries(dayData.psps).forEach(([psp, pspData]) => {
          const rolloverAmount = (pspData.net || 0) - (pspData.allocation || 0);
          const riskLevel = getRolloverRiskLevel(rolloverAmount, pspData.net || 0);
          
          rows.push([
            dayData.date_str,
            psp,
            pspData.deposit || 0,
            pspData.withdraw || 0,
            pspData.toplam || 0,
            pspData.komisyon || 0,
            pspData.net || 0,
            pspData.allocation || 0,
            rolloverAmount,
            riskLevel
          ]);
        });
      });

      // Create CSV content
      const csvContent = [headers, ...rows].map(row => 
        row.map((cell: string | number) => `"${cell}"`).join(',')
      ).join('\n');

      // Create and download file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ledger_export_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting data:', error);
      alert(t('ledger.export_failed'));
    }
  };

  // Rollover Risk Assessment Functions
  const getRolloverRiskLevel = (rolloverAmount: number, netAmount: number): string => {
    if (netAmount === 0) return 'Normal';
    
    const rolloverRatio = rolloverAmount / netAmount;
    
    if (rolloverRatio > 0.3) return 'Critical';
    if (rolloverRatio > 0.2) return 'High';
    if (rolloverRatio > 0.1) return 'Medium';
    return 'Normal';
  };

  const getRolloverRiskColor = (riskLevel: string): string => {
    switch (riskLevel) {
      case 'Critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'High': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'Medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  const getRolloverRiskIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'Critical': return <AlertTriangle className="h-4 w-4 text-red-600" />;
      case 'High': return <AlertTriangle className="h-4 w-4 text-orange-600" />;
      case 'Medium': return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      default: return <Shield className="h-4 w-4 text-green-600" />;
    }
  };

  const getRolloverWarningMessage = (riskLevel: string, rolloverAmount: number): string => {
    switch (riskLevel) {
      case 'Critical': return `High rollover risk: ₺${rolloverAmount.toLocaleString()} outstanding`;
      case 'High': return `Elevated rollover: ₺${rolloverAmount.toLocaleString()} pending`;
      case 'Medium': return `Moderate rollover: ₺${rolloverAmount.toLocaleString()} to monitor`;
      default: return `Healthy rollover level`;
    }
  };

  // Enhanced Date Utility Functions
  const getDateRangeLabel = (range: string) => {
    switch (range) {
      case '7': return 'Last 7 days';
      case '30': return 'Last 30 days';
      case '90': return 'Last 90 days';
      case '365': return 'Last year';
      case 'custom': return 'Custom range';
      default: return 'Last 30 days';
    }
  };

  const getQuickDateRange = (type: string) => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const thisWeekStart = new Date(today);
    thisWeekStart.setDate(today.getDate() - today.getDay());
    
    const lastWeekStart = new Date(thisWeekStart);
    lastWeekStart.setDate(thisWeekStart.getDate() - 7);
    const lastWeekEnd = new Date(thisWeekStart);
    lastWeekEnd.setDate(thisWeekStart.getDate() - 1);
    
    const thisMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);

    switch (type) {
      case 'today':
        return {
          start: today.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'Today'
        };
      case 'yesterday':
        return {
          start: yesterday.toISOString().split('T')[0],
          end: yesterday.toISOString().split('T')[0],
          label: 'Yesterday'
        };
      case 'thisWeek':
        return {
          start: thisWeekStart.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'This Week'
        };
      case 'lastWeek':
        return {
          start: lastWeekStart.toISOString().split('T')[0],
          end: lastWeekEnd.toISOString().split('T')[0],
          label: 'Last Week'
        };
      case 'thisMonth':
        return {
          start: thisMonthStart.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'This Month'
        };
      case 'lastMonth':
        return {
          start: lastMonthStart.toISOString().split('T')[0],
          end: lastMonthEnd.toISOString().split('T')[0],
          label: 'Last Month'
        };
      default:
        return {
          start: new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'Last 30 days'
        };
    }
  };

  const handleQuickDateSelect = (type: string) => {
    const range = getQuickDateRange(type);
    setCustomStartDate(range.start);
    setCustomEndDate(range.end);
    setDateRange('custom');
    setShowDatePicker(false);
  };

  const formatDateRange = () => {
    if (dateRange === 'custom' && customStartDate && customEndDate) {
      const start = new Date(customStartDate);
      const end = new Date(customEndDate);
      const startStr = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      const endStr = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      return `${startStr} - ${endStr}`;
    }
    return getDateRangeLabel(dateRange);
  };

  // Advanced Risk Analysis Functions

  // Toggle PSP expansion
  const togglePSPExpansion = (pspName: string) => {
    setExpandedPSPs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(pspName)) {
        newSet.delete(pspName);
      } else {
        newSet.add(pspName);
      }
      return newSet;
    });
  };

  const fetchMonthlyData = async (year: number, month: number, forceRefresh = false, includeDaily = true) => {
    try {
      setMonthlyLoading(true);
      setError(null);

      // PHASE 1 OPTIMIZATION: Lazy loading support
      // includeDaily=false: Only summary (~60-70% smaller payload)
      // includeDaily=true: Full daily breakdown (default)
      const cacheBuster = forceRefresh ? `&_t=${Date.now()}` : '';
      const dailyParam = includeDaily ? '&include_daily=true' : '&include_daily=false';
      const url = `/transactions/psp_monthly_stats?year=${year}&month=${month}${dailyParam}${cacheBuster}`;
      
      const response = await api.get(url, undefined, !forceRefresh);

      if (response.status === 401) {
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await api.parseResponse(response);

      // Handle different response formats
      let monthlyDataArray = [];
      if (Array.isArray(data)) {
        // Direct array response
        monthlyDataArray = data;
      } else if (data && Array.isArray(data.data)) {
        // Wrapped in data property
        monthlyDataArray = data.data;
      } else if (data && typeof data === 'object') {
        // Check if the response has PSP data in other formats
        const possibleDataKeys = ['psps', 'psp_data', 'monthly_data', 'results'];
        for (const key of possibleDataKeys) {
          if (Array.isArray(data[key])) {
            monthlyDataArray = data[key];
            break;
          }
        }
      }

      setMonthlyData(monthlyDataArray);
      
      if (monthlyDataArray.length === 0) {
        setError(`No PSP data available for ${new Date(year, month - 1).toLocaleString('default', { month: 'long', year: 'numeric' })}`);
      } else {
        setError(null); // Clear any previous errors
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch monthly data';
      setError(errorMessage);
      setMonthlyData([]); // Clear data on error
    } finally {
      setMonthlyLoading(false);
    }
  };

  const fetchLedgerData = async (forceRefresh = false) => {
    setLedgerLoading(true);
    try {
      // Clear cache if forcing refresh
      if (forceRefresh) {
        api.clearCacheForUrl('ledger-data');
      }
      
      const response = await api.get('/analytics/ledger-data', undefined, !forceRefresh);
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        const ledgerData = data.ledger_data || [];
        
        setLedgerData(ledgerData);
        
        // Initialize tempAllocations with current allocation values
        const initialTempAllocations: {[key: string]: number} = {};
        ledgerData.forEach((day: DayData) => {
          Object.entries(day.psps).forEach(([psp, pspData]) => {
            const key = `${day.date}-${psp}`;
            const typedPspData = pspData as PSPLedgerData;
            initialTempAllocations[key] = typedPspData.allocation || 0;
          });
        });
        setTempAllocations(initialTempAllocations);
        
        // Calculate PSP overview data - güncel pspData'yı parametre olarak geç
        calculatePSPOverviewData(ledgerData, pspData);
        
        // Check for validation errors
        if (data && typeof data === 'object' && 'validation_errors' in data) {
          const validationErrors = (data as any).validation_errors;
          if (Array.isArray(validationErrors) && validationErrors.length > 0) {
            setError(`Data loaded with warnings: ${validationErrors.join(', ')}`);
          } else {
            setError(null);
          }
        } else {
          // Clear any previous errors on successful load
          setError(null);
        }
      } else {
        // Try to get error details from response
        let errorMessage = 'Failed to fetch ledger data';
        try {
          const errorData = await api.parseResponse(response).catch(() => ({}));
          if (errorData && typeof errorData === 'object' && 'error' in errorData) {
            errorMessage = (errorData as any).error || errorMessage;
          } else if (response.status === 404) {
            errorMessage = 'Ledger data endpoint not found. Please check backend configuration.';
          }
        } catch (parseError) {
          // If parsing fails, use status-based message
          if (response.status === 404) {
            errorMessage = 'Ledger data endpoint not found. Please check backend configuration.';
          }
        }
        setError(errorMessage);
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Network error occurred';
      // Check if it's a 404 error
      if (errorMessage.includes('bulunamadı') || errorMessage.includes('404') || errorMessage.includes('Not Found')) {
        setError('Endpoint bulunamadı. Backend servisinin çalıştığından emin olun.');
      } else {
        setError(`Failed to load ledger data: ${errorMessage}`);
      }
      setLedgerData([]); // Clear data on error
    } finally {
      setLedgerLoading(false);
    }
  };

  // useCallback ile sarmalayarak stale closure sorununu çöz
  const calculatePSPOverviewData = useCallback((data: DayData[], currentPspData: PSPData[]) => {
    const pspMap = new Map<string, PSPOverviewData>();

    data.forEach(day => {
      Object.entries(day.psps).forEach(([psp, pspData]) => {
        if (!pspMap.has(psp)) {
          pspMap.set(psp, {
            psp,
            total_deposits: 0,
            total_withdrawals: 0,
            total_net: 0,
            total_allocations: 0,
            total_rollover: 0,
            transaction_count: 0,
            average_transaction: 0,
            last_activity: day.date_str
          });
        }

        const overview = pspMap.get(psp)!;
        overview.total_deposits += pspData.deposit || 0;
        overview.total_withdrawals += pspData.withdraw || 0;
        overview.total_net += pspData.net || 0;
        
        // Use actual transaction count from backend
        overview.transaction_count += pspData.transaction_count || 1;
        
        overview.last_activity = day.date_str; // Keep the most recent date
      });
    });

    // Calculate average transaction amounts and get allocations from PSP data
    pspMap.forEach(overview => {
      // Get total_allocations from PSP data - currentPspData parametresi ile güncel veri kullan
      const pspFromData = currentPspData.find(p => p.psp === overview.psp);
      overview.total_allocations = pspFromData?.total_allocations || 0;
      
      overview.average_transaction = overview.transaction_count > 0 
        ? overview.total_net / overview.transaction_count 
        : 0;
      
      // Calculate rollover as net - allocations (PSP owes company when positive)
      overview.total_rollover = overview.total_net - overview.total_allocations;
    });

    const overviewArray = Array.from(pspMap.values());
    setPspOverviewData(overviewArray);
  }, []);

  const handleAllocationChange = (date: string, psp: string, allocation: number) => {
    const key = `${date}-${psp}`;
    setTempAllocations(prev => ({ ...prev, [key]: allocation }));
  };

  // Bulk allocation functions
  const openBulkAllocationModal = (date: string) => {
    setSelectedDayForBulk(date);
    
    // Initialize bulk allocations with current values for ALL active PSPs
    const initialBulkAllocations: {[key: string]: number} = {};
    
    // Get all unique PSPs from the PSP data (all active PSPs)
    pspData.forEach(psp => {
      const key = `${date}-${psp.psp}`;
      // Check if this PSP has data for this specific day
      const dayData = ledgerData.find(day => day.date === date);
      const dayPspData = dayData?.psps[psp.psp];
      initialBulkAllocations[key] = dayPspData?.allocation || 0;
    });
    
    setBulkAllocations(initialBulkAllocations);
    setShowBulkAllocationModal(true);
  };

  const handleBulkAllocationChange = (psp: string, allocation: number) => {
    if (!selectedDayForBulk) return;
    const key = `${selectedDayForBulk}-${psp}`;
    setBulkAllocations(prev => ({ ...prev, [key]: allocation }));
  };

  const saveBulkAllocations = async () => {
    if (!selectedDayForBulk) return;
    
    setBulkAllocationSaving(true);
    
    try {
      // Save all allocations for the selected day (including PSPs with 0 allocation)
      const savePromises = Object.entries(bulkAllocations).map(async ([key, allocation]) => {
        // Split by the last occurrence of '-' to handle dates with hyphens
        const lastDashIndex = key.lastIndexOf('-');
        const date = key.substring(0, lastDashIndex);
        const psp = key.substring(lastDashIndex + 1);
        
        console.log('🔄 Saving bulk allocation:', { date, psp, allocation });
        // Save even if allocation is 0, to ensure the PSP is recorded for that day
        return saveAllocation(date, psp, allocation);
      });
      
      await Promise.all(savePromises);
      
      // Update temp allocations to reflect the saved values
      setTempAllocations(prev => ({ ...prev, ...bulkAllocations }));
      
      // Close modal
      setShowBulkAllocationModal(false);
      setSelectedDayForBulk(null);
      setBulkAllocations({});
      
      // Refresh data immediately - backend response confirms save was successful
      await Promise.all([
        fetchLedgerData(true),
        fetchPSPData(true)
      ]);
      
    } catch (error) {
      console.error('Error saving bulk allocations:', error);
    } finally {
      setBulkAllocationSaving(false);
    }
  };

  const closeBulkAllocationModal = () => {
    setShowBulkAllocationModal(false);
    setSelectedDayForBulk(null);
    setBulkAllocations({});
  };

  // History tab functions
  const fetchHistoryData = async (page = 1) => {
    console.log('🔍 fetchHistoryData called with page:', page, 'filters:', historyFilters);
    setHistoryLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '50'
      });
      
      if (historyFilters.startDate) params.append('start_date', historyFilters.startDate);
      if (historyFilters.endDate) params.append('end_date', historyFilters.endDate);
      if (historyFilters.psp) params.append('psp', historyFilters.psp);
      if (historyFilters.type) params.append('type', historyFilters.type);
      
      console.log('📡 Fetching history from:', `/analytics/unified-history?${params}`);
      const response = await api.get(`/analytics/unified-history?${params}`);
      console.log('📥 History response:', response.status, response.ok);
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        console.log('📦 Parsed history data:', data);
        if (data && typeof data === 'object' && 'success' in data && data.success) {
          const historyItems = (data as any).data || [];
          console.log('✅ Setting history data:', historyItems.length, 'items');
          setHistoryData(historyItems);
          setHistoryPagination((data as any).pagination || null);
        } else if (data && typeof data === 'object' && 'error' in data) {
          console.error('❌ History data error:', (data as any).error);
          setError((data as any).error || 'Failed to load history data');
        }
      } else {
        const errorData = await api.parseResponse(response).catch(() => ({}));
        console.error('❌ History fetch failed:', errorData);
        setError((errorData as any)?.error || 'Failed to fetch history data');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch history data';
      console.error('❌ History fetch exception:', error);
      setError(errorMessage);
      setHistoryData([]);
      setHistoryPagination(null);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleHistoryFilterChange = (key: string, value: string) => {
    const newFilters = {
      ...historyFilters,
      [key]: value,
      page: 1 // Reset to first page when filters change
    };
    setHistoryFilters(newFilters);
    // Immediately fetch with new filters
    fetchHistoryData(1);
  };

  const handleHistoryPageChange = (page: number) => {
    setHistoryFilters(prev => ({ ...prev, page }));
    fetchHistoryData(page);
  };

  const exportHistoryData = async (format: 'csv' | 'json') => {
    try {
      const params = new URLSearchParams({
        format: format
      });
      
      if (historyFilters.startDate) params.append('start_date', historyFilters.startDate);
      if (historyFilters.endDate) params.append('end_date', historyFilters.endDate);
      if (historyFilters.psp) params.append('psp', historyFilters.psp);
      if (historyFilters.type) params.append('type', historyFilters.type);
      
      const response = await api.get(`/analytics/unified-history/export?${params}`, {
        responseType: 'blob'
      });
      
      if (response.ok) {
        // Create download link
        const url = window.URL.createObjectURL(await response.blob());
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `unified_history_${new Date().toISOString().split('T')[0]}.${format}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error exporting history data:', error);
    }
  };

  // Helper function for bulk allocation saves
  const saveAllocation = async (date: string, psp: string, allocation: number) => {
    let retryCount = 0;
    const maxRetries = 2;
    
    while (retryCount <= maxRetries) {
      try {
        // İlk denemeden sonra token'ı yenile
        if (retryCount > 0) {
          try {
            // ApiClient'ın token'ı temizle ve yeniden al
            (api as any).clearToken?.();
            await api.get('/auth/csrf-token');
            await new Promise(resolve => setTimeout(resolve, 300)); // Reduced delay
          } catch (tokenError) {
            // Token refresh failed, continue anyway
          }
        }
        
        const response = await api.post('/analytics/update-allocation', {
          date,
          psp,
          allocation
        });

        if (response.ok) {
          try {
            const responseData = await api.parseResponse(response);
            return responseData || { success: true };
          } catch (parseError) {
            // Response ok ama parse edilemedi, başarılı kabul et
            return { success: true };
          }
        } else {
          // Backend'den gelen hata mesajını al
          let errorMessage = 'Allocation kaydedilemedi';
          let errorDetails = '';
          
          try {
            // Response'u parse et
            const errorData = await api.parseResponse(response) as any;
            
            // CSRF hatası kontrolü
            const isCsrfError = errorData?.csrf_error || 
                               errorData?.error?.includes('CSRF') || 
                               errorData?.error?.includes('token') || 
                               errorData?.error?.includes('Security token') ||
                               errorData?.message?.includes('CSRF') ||
                               errorData?.message?.includes('token');
            
            if (isCsrfError && retryCount < maxRetries) {
              retryCount++;
              continue; // Tekrar dene
            } else {
              errorMessage = errorData?.error || errorData?.message || errorMessage;
              errorDetails = errorData?.details || errorData?.message || '';
            }
          } catch (parseError) {
            if (retryCount < maxRetries) {
              retryCount++;
              continue;
            }
            errorMessage = `HTTP ${response.status}`;
          }
          
          const fullMessage = errorDetails ? `${errorMessage} - ${errorDetails}` : errorMessage;
          throw new Error(fullMessage);
        }
      } catch (error: any) {
        // CSRF hatası ve retry hakkı varsa tekrar dene
        const isCsrfError = error?.message?.includes('CSRF') || 
                           error?.message?.includes('token') ||
                           error?.message?.includes('Security token');
        
        if (isCsrfError && retryCount < maxRetries) {
          retryCount++;
          await new Promise(resolve => setTimeout(resolve, 300)); // Reduced delay
          continue;
        }
        
        // Network hatası veya diğer hatalar
        if (error.message) {
          throw error;
        } else {
          throw new Error('Ağ hatası veya istek başarısız oldu');
        }
      }
    }
    
    // Tüm retry'lar başarısız oldu
    throw new Error('Güvenlik token hatası - Lütfen sayfayı yenileyin ve tekrar deneyin');
  };

  const testCSRF = async () => {
    try {
      console.log('🧪 Testing CSRF with simple endpoint...');
      const response = await api.post('/analytics/test-csrf', {
        test: 'data',
        timestamp: new Date().toISOString()
      });
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        console.log('✅ CSRF test successful:', data);
        alert(t('ledger.csrf_test_success'));
      } else {
        console.error('❌ CSRF test failed:', response.status);
        alert(t('ledger.csrf_test_failed'));
      }
    } catch (error) {
      console.error('💥 CSRF test error:', error);
      alert(t('ledger.csrf_test_error'));
    }
  };

  // Edit allocation functions
  const openEditModal = (psp: string, date: string, currentAmount: number) => {
    setEditingAllocation({ psp, date, currentAmount });
    setEditAmount(currentAmount.toString());
    setShowEditModal(true);
  };

  const closeEditModal = () => {
    setShowEditModal(false);
    setEditingAllocation(null);
    setEditAmount('');
  };

  const handleEditAllocation = async () => {
    if (!editingAllocation) return;
    
    const newAmount = parseFloat(editAmount);
    if (isNaN(newAmount) || newAmount < 0) {
      alert(t('ledger.enter_valid_amount'));
      return;
    }

    setEditSaving(true);
    try {
      console.log('🔄 TAHS TUT güncelleniyor:', {
        tarih: editingAllocation.date,
        psp: editingAllocation.psp,
        yeniMiktar: newAmount,
        eskiMiktar: editingAllocation.currentAmount
      });
      
      await saveAllocation(editingAllocation.date, editingAllocation.psp, newAmount);
      
      console.log('🔄 Veriler yenileniyor...');
      
      // Refresh all data to show updated allocation
      await Promise.all([
        fetchMonthlyData(selectedYear, selectedMonth, true),
        fetchLedgerData(true),
        fetchHistoryData(historyFilters.page)
      ]);
      
      console.log('✅ TAHS TUT başarıyla güncellendi ve veriler yenilendi');
      
      closeEditModal();
      alert(t('ledger.allocation_updated'));
    } catch (error: any) {
      console.error('❌ TAHS TUT güncelleme hatası:', error);
      const errorMessage = error?.message || t('ledger.failed_update_allocation');
      alert(`${t('ledger.failed_update_allocation')}\n\nDetay: ${errorMessage}`);
    } finally {
      setEditSaving(false);
    }
  };

  // Edit Devir functions
  const openEditDevirModal = (psp: string, date: string, currentAmount: number) => {
    setEditingDevir({ psp, date, currentAmount });
    setEditDevirAmount(currentAmount.toString());
    setDevirSecretCode('');
    setShowEditDevirModal(true);
  };

  const closeEditDevirModal = () => {
    setShowEditDevirModal(false);
    setEditingDevir(null);
    setEditDevirAmount('');
    setDevirSecretCode('');
  };

  const handleEditDevir = async () => {
    if (!editingDevir) return;
    
    // Secret code validation removed - all devirs are now editable
    // if (devirSecretCode !== '4561') {
    //   alert(t('ledger.invalid_secret_devir'));
    //   return;
    // }
    
    const newAmount = parseFloat(editDevirAmount);
    if (isNaN(newAmount)) {
      alert(t('ledger.enter_valid_amount'));
      return;
    }

    setEditDevirSaving(true);
    try {
      // Use the new Devir-specific endpoint
      const requestData = {
        date: editingDevir.date,
        psp: editingDevir.psp,
        devir_amount: newAmount
      };
      console.log('📤 Sending Devir update request:', requestData);
      
      const response = await api.post('/analytics/update-devir', requestData);

      if (response.ok) {
        try {
          const responseData = await api.parseResponse(response);
          console.log('✅ Devir saved successfully:', responseData);
          
          // Refresh all data to show updated Devir
          console.log('🔄 Refreshing data after Devir update...');
          await Promise.all([
            fetchMonthlyData(selectedYear, selectedMonth, true),
            fetchLedgerData(true),
            fetchHistoryData(historyFilters.page)
          ]);
          console.log('✅ Data refresh completed after Devir update');
          
          // Add a small delay to ensure data is properly refreshed
          await new Promise(resolve => setTimeout(resolve, 500));
          
          closeEditDevirModal();
          alert(t('ledger.devir_updated'));
        } catch (parseError) {
          // Response ok ama parse edilemedi, yine de başarılı kabul et ve verileri yenile
          console.warn('⚠️ Devir response parse edilemedi ama işlem başarılı olabilir:', parseError);
          await Promise.all([
            fetchMonthlyData(selectedYear, selectedMonth, true),
            fetchLedgerData(true),
            fetchHistoryData(historyFilters.page)
          ]);
          closeEditDevirModal();
          alert(t('ledger.devir_updated'));
        }
      } else {
        try {
          const errorData = await api.parseResponse(response) as any;
          console.error('❌ Devir save failed:', errorData);
          const errorMessage = errorData?.error || errorData?.message || `HTTP ${response.status}`;
          alert(`${t('ledger.failed_update_devir')}: ${errorMessage}`);
        } catch (parseError) {
          console.error('❌ Devir save failed - parse error:', parseError);
          alert(`${t('ledger.failed_update_devir')}: HTTP ${response.status}`);
        }
      }
    } catch (error: any) {
      console.error('❌ Error updating Devir:', error);
      const errorMessage = error?.message || error?.toString() || 'Network error';
      alert(`${t('ledger.failed_save_devir')}\n\nDetay: ${errorMessage}`);
    } finally {
      setEditDevirSaving(false);
    }
  };

  // KASA TOP edit functions
  const openEditKasaTopModal = (psp: string, date: string, currentAmount: number) => {
    setEditingKasaTop({ psp, date, currentAmount });
    setEditKasaTopAmount(currentAmount.toString());
    setKasaTopSecretCode('');
    setShowEditKasaTopModal(true);
  };

  const closeEditKasaTopModal = () => {
    setShowEditKasaTopModal(false);
    setEditingKasaTop(null);
    setEditKasaTopAmount('');
    setKasaTopSecretCode('');
  };

  const handleEditKasaTop = async () => {
    if (!editingKasaTop) return;
    
    // Validate secret code
    if (kasaTopSecretCode !== '4561') {
      alert(t('ledger.invalid_secret_kasa'));
      return;
    }
    
    const newAmount = parseFloat(editKasaTopAmount);
    if (isNaN(newAmount)) {
      alert(t('ledger.enter_valid_amount'));
      return;
    }

    setEditKasaTopSaving(true);
    try {
      // Use the new KASA TOP-specific endpoint
      const requestData = {
        date: editingKasaTop.date,
        psp: editingKasaTop.psp,
        kasa_top_amount: newAmount
      };
      console.log('📤 Sending KASA TOP update request:', requestData);
      
      const response = await api.post('/analytics/update-kasa-top', requestData);

      if (response.ok) {
        try {
          const responseData = await api.parseResponse(response);
          console.log('✅ KASA TOP saved successfully:', responseData);
          
          // Refresh all data to show updated KASA TOP
          console.log('🔄 Refreshing data after KASA TOP update...');
          await Promise.all([
            fetchMonthlyData(selectedYear, selectedMonth, true),
            fetchLedgerData(true),
            fetchHistoryData(historyFilters.page)
          ]);
          console.log('✅ Data refresh completed after KASA TOP update');
          
          // Add a small delay to ensure data is properly refreshed
          await new Promise(resolve => setTimeout(resolve, 500));
          
          closeEditKasaTopModal();
          alert(t('ledger.kasa_updated'));
        } catch (parseError) {
          // Response ok ama parse edilemedi, yine de başarılı kabul et ve verileri yenile
          console.warn('⚠️ KASA TOP response parse edilemedi ama işlem başarılı olabilir:', parseError);
          await Promise.all([
            fetchMonthlyData(selectedYear, selectedMonth, true),
            fetchLedgerData(true),
            fetchHistoryData(historyFilters.page)
          ]);
          closeEditKasaTopModal();
          alert(t('ledger.kasa_updated'));
        }
      } else {
        try {
          const errorData = await api.parseResponse(response) as any;
          console.error('❌ KASA TOP save failed:', errorData);
          const errorMessage = errorData?.error || errorData?.message || `HTTP ${response.status}`;
          alert(`${t('ledger.failed_update_kasa')}: ${errorMessage}`);
        } catch (parseError) {
          console.error('❌ KASA TOP save failed - parse error:', parseError);
          alert(`${t('ledger.failed_update_kasa')}: HTTP ${response.status}`);
        }
      }
    } catch (error: any) {
      console.error('❌ Error updating KASA TOP:', error);
      const errorMessage = error?.message || error?.toString() || 'Network error';
      alert(`${t('ledger.failed_save_kasa')}\n\nDetay: ${errorMessage}`);
    } finally {
      setEditKasaTopSaving(false);
    }
  };

  const handleSaveAllocation = async (date: string, psp: string) => {
    const key = `${date}-${psp}`;
    const allocation = tempAllocations[key] || 0;
    
    setAllocationSaving(prev => ({ ...prev, [key]: true }));
    setAllocationSaved(prev => ({ ...prev, [key]: false }));

    try {
      const response = await api.post('/analytics/update-allocation', {
        date,
        psp,
        allocation
      });

      if (response.ok) {
        try {
          const responseData = await api.parseResponse(response);
          console.log('✅ Allocation saved successfully:', responseData);
          
          // Optimistic update: Update tempAllocations immediately
          setTempAllocations(prev => ({ ...prev, [key]: allocation }));
          setAllocationSaved(prev => ({ ...prev, [key]: true }));
          
          // Refresh data from backend to get updated rollover calculations
          await Promise.all([
            fetchLedgerData(true),
            fetchPSPData(true)
          ]);
          
          // Clear saved status after 2 seconds
          setTimeout(() => {
            setAllocationSaved(prev => ({ ...prev, [key]: false }));
          }, 2000);
        } catch (parseError) {
          // Response ok ama parse edilemedi, yine de başarılı kabul et ve verileri yenile
          console.warn('⚠️ Allocation response parse edilemedi ama işlem başarılı olabilir:', parseError);
          setTempAllocations(prev => ({ ...prev, [key]: allocation }));
          setAllocationSaved(prev => ({ ...prev, [key]: true }));
          await Promise.all([
            fetchLedgerData(true),
            fetchPSPData(true)
          ]);
          setTimeout(() => {
            setAllocationSaved(prev => ({ ...prev, [key]: false }));
          }, 2000);
        }
      } else {
        // Try to get error details for user feedback
        try {
          const errorData = await api.parseResponse(response) as any;
          const errorMessage = errorData?.error || errorData?.message || `HTTP ${response.status}`;
          setError(`Failed to update allocation: ${errorMessage}`);
        } catch (parseError) {
          setError(`Failed to update allocation: HTTP ${response.status}`);
        }
      }
    } catch (error: any) {
      console.error('❌ Error updating allocation:', error);
      const errorMessage = error?.message || error?.toString() || 'Network error';
      setError(`Error updating allocation: ${errorMessage}`);
    } finally {
      setAllocationSaving(prev => ({ ...prev, [key]: false }));
    }
  };

  const handlePspDetails = async (psp: string) => {
    console.log('handlePspDetails called with PSP:', psp);
    setSelectedPsp(psp);
    setSelectedDate(null);
    setShowDetailsModal(true);
    
    try {
      console.log('Fetching PSP details for:', psp);
      
      // Fetch PSP-specific transaction details (api client handles auth & CSRF automatically)
      const response = await api.get(`/transactions/?psp=${encodeURIComponent(psp)}&per_page=100`);
      
      console.log('API response status:', response.status);
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        console.log('PSP details data:', data);
        setDetailsData({
          type: 'psp',
          psp: psp,
          transactions: data.transactions || [],
          total: data.total || 0
        });
      } else {
        console.error('API response not ok:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error response body:', errorText);
        setDetailsData({
          type: 'psp',
          psp: psp,
          transactions: [],
          total: 0,
          error: `API Error: ${response.status} - ${response.statusText}`
        });
      }
    } catch (error) {
      console.error('Error fetching PSP details:', error);
      setDetailsData({
        type: 'psp',
        psp: psp,
        transactions: [],
        total: 0,
        error: `Network Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  };

  const handleDailyDetails = async (date: string, psp: string) => {
    setSelectedDate(date);
    setSelectedPsp(psp);
    setShowDetailsModal(true);
    
    try {
      // Fetch daily transaction details for specific PSP
      const response = await api.get(`/transactions/?date=${date}&psp=${encodeURIComponent(psp)}&per_page=100`);
      if (response.ok) {
        const data = await api.parseResponse(response);
        setDetailsData({
          type: 'daily',
          date: date,
          psp: psp,
          transactions: data.transactions || [],
          total: data.total || 0
        });
      }
    } catch (error) {
      console.error('Error fetching daily details:', error);
      setDetailsData({
        type: 'daily',
        date: date,
        psp: psp,
        transactions: [],
        total: 0,
        error: 'Failed to load details'
      });
    }
  };

  const closeDetailsModal = () => {
    setShowDetailsModal(false);
    setSelectedPsp(null);
    setSelectedDate(null);
    setDetailsData(null);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getPSPColor = (psp: string) => {
    const colors = [
      'bg-gray-100 text-gray-800',
      'bg-green-100 text-green-800',
      'bg-purple-100 text-purple-800',
      'bg-orange-100 text-orange-800',
      'bg-pink-100 text-pink-800',
      'bg-indigo-100 text-indigo-800',
      'bg-teal-100 text-teal-800',
      'bg-yellow-100 text-yellow-800',
    ];
    const index = psp.length % colors.length;
    return colors[index];
  };

  const getPSPIcon = (psp: string) => {
    const icons = [Building, CreditCard, Activity, Zap, BarChart3, PieChart];
    const index = psp.length % icons.length;
    return icons[index];
  };

  // Ensure pspData is always an array and handle filtering safely
  const filteredData = Array.isArray(pspData)
    ? pspData.filter(entry => {
        const matchesSearch = entry.psp
          .toLowerCase()
          .includes(searchTerm.toLowerCase());
        const matchesPSP = pspFilter === 'all' || entry.psp === pspFilter;

        return matchesSearch && matchesPSP;
      })
    : [];

  const totalEntries = filteredData.length;
  const totalAmount = filteredData.reduce(
    (sum, entry) => sum + entry.total_amount,
    0
  );
  const totalCommission = filteredData.reduce(
    (sum, entry) => sum + entry.total_commission,
    0
  );
  const totalNet = filteredData.reduce(
    (sum, entry) => sum + entry.total_net,
    0
  );
  const totalTransactions = filteredData.reduce(
    (sum, entry) => sum + entry.transaction_count,
    0
  );

  const uniquePSPs = Array.isArray(pspData)
    ? [...new Set(pspData.map(entry => entry.psp))]
    : [];

  // Enhanced loading state
  if (authLoading || loading) {
    return <LedgerPageSkeleton />;
  }

  // Error state
  if (error) {
    return (
      <div className='min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-red-50'>
        <div className='text-center max-w-md mx-auto p-8'>
          <div className='w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6'>
            <AlertCircle className='h-10 w-10 text-red-600' />
          </div>
          <h2 className='text-2xl font-bold text-gray-900 mb-4'>
            Error Loading Data
          </h2>
          <p className='text-gray-600 mb-6'>{error}</p>
          <button 
            onClick={() => fetchPSPData(true)} 
            className='inline-flex items-center gap-2 px-6 py-3 bg-accent-600 text-white rounded-lg hover:bg-accent-700 transition-colors duration-200'
          >
            <RefreshCw className='h-4 w-4' />
            Try Again
          </button>
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
              <Building className="h-8 w-8 text-gray-600" />
              {t('ledger.psp_ledger')}
            </h1>
            <p className="text-sm text-gray-600 mt-1">{t('ledger.psp_transactions_balances')}</p>
          </div>
          <div className="flex items-center gap-3">
            <Button 
              variant="outline"
              size="default"
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 h-10 px-4 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? t('ledger.refreshing') : t('ledger.refresh')}
            </Button>
            <Button 
              variant="outline" 
              size="default"
              onClick={handleExport}
              className="flex items-center gap-2 h-10 px-4 hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm"
            >
              <Download className='h-4 w-4' />
              {t('ledger.export')}
            </Button>
          </div>
        </div>
      </div>

      <div className="p-6">
      {/* Modern Tab Navigation */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-gray-50/80 border border-gray-200/60 rounded-lg shadow-sm">
          <TabsTrigger value="overview" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg">
            <LayoutGrid className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('tabs.overview')}</span>
          </TabsTrigger>
          <TabsTrigger value="monthly" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg">
            <Calendar className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('tabs.monthly')}</span>
          </TabsTrigger>
          <TabsTrigger value="trust" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg">
            <Wallet className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('tabs.trust')}</span>
          </TabsTrigger>
          <TabsTrigger value="analytics" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg">
            <BarChart3 className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('tabs.analytics')}</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab Content */}
        <TabsContent value="overview" className="mt-6">
          {/* Enhanced Stats Cards Section */}
          <div className="mb-6">
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-gray-600" />
                {t('ledger.psp_overview')}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {t('ledger.key_performance_all_psps')}
              </p>
            </div>
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <MetricCard
                title={t('ledger.total_psps')}
                value={formatNumber(pspData.length)}
                subtitle={t('ledger.active_providers')}
                icon={Building}
                color="gray"
                animated={true}
                animationDuration={500}
              />

              {/* Rollover Risk Overview Card */}
              {(() => {
                const riskSummary = ledgerData.reduce((summary, dayData) => {
                  Object.entries(dayData.psps).forEach(([psp, pspData]) => {
                    const rolloverAmount = (pspData.net || 0) - (pspData.allocation || 0);
                    const riskLevel = getRolloverRiskLevel(rolloverAmount, pspData.net || 0);
                    
                    if (riskLevel === 'Critical') summary.critical++;
                    else if (riskLevel === 'High') summary.high++;
                    else if (riskLevel === 'Medium') summary.medium++;
                    else summary.normal++;
                    
                    summary.totalRollover += rolloverAmount;
                  });
                  return summary;
                }, { critical: 0, high: 0, medium: 0, normal: 0, totalRollover: 0 });

                const hasRisk = riskSummary.critical > 0 || riskSummary.high > 0;
                const riskColor = hasRisk ? 'red' : 'green';
                const riskIcon = hasRisk ? AlertTriangle : Shield;
                const riskValue = hasRisk ? `${riskSummary.critical + riskSummary.high}` : '0';
                const riskSubtitle = hasRisk ? `${riskSummary.critical} critical, ${riskSummary.high} high` : 'Healthy levels';
                
                // Calculate average risk percentage
                const totalPSPs = riskSummary.critical + riskSummary.high + riskSummary.medium + riskSummary.normal;
                const avgRisk = totalPSPs > 0 ? (riskSummary.critical + riskSummary.high) / totalPSPs : 0;

                return (
                  <MetricCard
                    title={t('ledger.rollover_risk')}
                    value={riskValue}
                    subtitle={riskSubtitle}
                    icon={riskIcon}
                    color={riskColor}
                    animated={true}
                    animationDuration={500}
                  />
                );
              })()}

              <MetricCard
                title={t('ledger.total_allocations')}
                value={formatCurrency(pspData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : psp.total_allocations), 0), '₺')}
                subtitle={t('ledger.funds_allocated')}
                icon={CreditCard}
                color="orange"
                animated={true}
                animationDuration={500}
              />

              <MetricCard
                title={t('ledger.total_rollover')}
                value={formatCurrency(pspData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.total_allocations - psp.total_net)), 0), '₺')}
                subtitle={t('ledger.available_balance')}
                icon={Activity}
                color="purple"
                animated={true}
                animationDuration={500}
              />
              </div>
            </div>
          </div>

          {/* PSP Overview Cards Section */}
          <div className="mb-6">
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <Building className="h-5 w-5 text-gray-600" />
                {t('ledger.psp_overview_cards')}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {`${pspData.length} ${t('ledger.psp_count')} - ${t('ledger.all_available_data')}`}
              </p>
            </div>
            <div>
            {ledgerLoading ? (
              <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>
                {[1, 2, 3].map((i) => (
                  <div key={i} className='bg-white rounded-lg shadow-sm p-6 space-y-4 animate-pulse'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-gray-200 rounded-lg'></div>
                      <div className='flex-1'>
                        <div className='h-5 bg-gray-200 rounded w-24 mb-2'></div>
                        <div className='h-3 bg-gray-100 rounded w-32'></div>
                      </div>
                    </div>
                    <div className='space-y-3'>
                      <div className='h-16 bg-gray-100 rounded'></div>
                      <div className='h-16 bg-gray-100 rounded'></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>
                {pspData.map((psp, index) => {
                  const PSPSpecificIcon = getPSPIcon(psp.psp) || Building;
                  // Calculate rollover from PSP data
                  const rolloverAmount = psp.total_net - psp.total_allocations;
                  const rolloverPercentage = psp.total_net > 0 ? (rolloverAmount / psp.total_net) * 100 : 0;
                  const isRolloverPositive = rolloverAmount > 0;
                  
                  return (
                    <div key={psp.psp} className='bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 group border border-gray-100 hover:border-blue-200 overflow-hidden'>
                      {/* Header */}
                      <div className='p-6 border-b border-gray-100 bg-gradient-to-br from-white to-gray-50/30'>
                        <div className='flex items-center justify-between'>
                          <div className='flex items-center gap-3'>
                            <div className='w-12 h-12 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow'>
                              <PSPSpecificIcon className='h-6 w-6 text-blue-600 group-hover:scale-110 transition-transform' />
                          </div>
                          <div>
                              <h3 className='text-lg font-bold text-gray-900 group-hover:text-blue-700 transition-colors'>{psp.psp}</h3>
                            <p className='text-xs text-gray-500 font-medium'>{t('ledger.payment_provider')}</p>
                          </div>
                        </div>
                        <div className='text-right'>
                            <div className={`text-lg font-bold ${isRolloverPositive ? 'text-green-600' : 'text-red-600'}`}>
                            {rolloverPercentage.toFixed(1)}%
                          </div>
                          <div className='text-xs text-gray-500 font-medium'>{t('ledger.rollover_rate')}</div>
                          </div>
                        </div>
                      </div>

                      {/* Key Metrics */}
                      <div className='p-6 space-y-4 bg-white'>
                        <div className='grid grid-cols-2 gap-4'>
                          <div className='text-center p-4 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-gray-100 hover:border-blue-200 transition-all group/metric'>
                            <div className='text-xs text-gray-600 mb-2'>{t('ledger.total_deposits')}</div>
                            <div className='text-sm font-semibold text-gray-900'>{formatPSPCurrency(psp.total_deposits, psp.psp)}</div>
                        </div>
                          <div className='text-center p-4 bg-gray-50 rounded-lg'>
                            <div className='text-xs text-gray-600 mb-2'>{t('ledger.total_withdrawals')}</div>
                            <div className='text-sm font-semibold text-gray-900'>{formatPSPCurrency(psp.total_withdrawals, psp.psp)}</div>
                        </div>
                        </div>
                        
                        <div className='text-center p-4 bg-primary-50 rounded-lg border border-primary-100'>
                          <div className='text-xs text-primary-600 mb-2'>{t('ledger.net_amount')}</div>
                          <div className='text-lg font-semibold text-primary-900'>{formatPSPCurrency(psp.total_net, psp.psp)}</div>
                      </div>

                        <div className='grid grid-cols-2 gap-6'>
                          <div className='text-center p-4 bg-gray-50 rounded-lg'>
                            <div className='text-xs text-gray-600 mb-2'>{t('ledger.allocations')}</div>
                            <div className='text-sm font-semibold text-warning-600'>{formatPSPCurrency(psp.total_allocations, psp.psp)}</div>
                        </div>
                          <div className='text-center p-4 bg-gray-50 rounded-lg'>
                            <div className='text-xs text-gray-600 mb-2'>{t('ledger.rollover')}</div>
                            <div className={`text-sm font-semibold ${isRolloverPositive ? 'text-success-600' : 'text-destructive-600'}`}>
                            {formatPSPCurrency(rolloverAmount, psp.psp)}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Footer Stats */}
                      <div className='px-6 py-4 bg-gray-50 rounded-b-lg'>
                        <div className='flex justify-between items-center'>
                        <div className='text-center'>
                          <div className='text-xs text-gray-600'>{t('ledger.total_transactions')}</div>
                            <div className='text-sm font-semibold text-gray-900'>{formatNumber(psp.transaction_count)}</div>
                        </div>
                        <div className='text-center'>
                          <div className='text-xs text-gray-600'>{t('ledger.avg_transaction')}</div>
                            <div className='text-sm font-semibold text-gray-900'>{formatPSPCurrency(psp.transaction_count > 0 ? psp.total_net / psp.transaction_count : 0, psp.psp)}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {pspData.length === 0 && !ledgerLoading && (
              <div className='text-center py-16'>
                <div className='w-20 h-20 bg-gradient-to-br from-blue-50 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-6'>
                  <Building className='h-10 w-10 text-blue-500' />
                </div>
                <h3 className='text-lg font-semibold text-gray-900 mb-2'>{t('ledger.no_psp_data_available')}</h3>
                <p className='text-sm text-gray-600 max-w-md mx-auto mb-6'>
                  {t('ledger.no_psp_data_desc')}
                </p>
                <div className='flex flex-col items-center gap-3 text-xs text-gray-500 max-w-sm mx-auto'>
                  <div className='flex items-center gap-2'>
                    <div className='w-1.5 h-1.5 bg-blue-500 rounded-full'></div>
                    <span>Transaction data appears automatically when processed</span>
                  </div>
                  <div className='flex items-center gap-2'>
                    <div className='w-1.5 h-1.5 bg-blue-500 rounded-full'></div>
                    <span>Use the refresh button to update statistics</span>
                  </div>
                </div>
              </div>
            )}
            </div>
          </div>
        </TabsContent>


        {/* Monthly Tab Content */}
        <TabsContent value="monthly" className="mt-6">
          {/* Monthly PSP Report */}
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
            {/* Header with Month Selection */}
            <div className="bg-slate-100 px-6 py-3 border-b border-slate-300">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-slate-700 rounded-lg flex items-center justify-center">
                    <Calendar className="h-4 w-4 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 tracking-tight">{t('ledger.monthly_psp_report')}</h3>
                    <p className="text-sm text-slate-600">{t('tabs.monthly_desc')}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {/* Year Selection */}
                  <div className="flex items-center gap-2">
                    <label className="text-sm font-medium text-gray-700">Year:</label>
                    <select
                      value={selectedYear}
                      onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                      className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    >
                      {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(year => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Month Selection */}
                  <div className="flex items-center gap-2">
                    <label className="text-sm font-medium text-gray-700">Month:</label>
                    <select
                      value={selectedMonth}
                      onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                      className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    >
                      {Array.from({ length: 12 }, (_, i) => i + 1).map(month => (
                        <option key={month} value={month}>
                          {new Date(2024, month - 1).toLocaleString('default', { month: 'long' })}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Refresh Button */}
                  <Button
                    onClick={() => fetchMonthlyData(selectedYear, selectedMonth, true)}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={monthlyLoading}
                  >
                    <RefreshCw className={`h-4 w-4 ${monthlyLoading ? 'animate-spin' : ''}`} />
                    {monthlyLoading ? 'Refreshing...' : 'Refresh'}
                  </Button>
                </div>
              </div>
            </div>
            
            {/* Monthly Data Table */}
            {monthlyLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="flex items-center gap-3">
                  <RefreshCw className="h-5 w-5 animate-spin text-slate-600" />
                  <span className="text-slate-600">Loading monthly data...</span>
                </div>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <AlertCircle className="h-8 w-8 text-red-500" />
                </div>
                <h3 className="text-lg font-medium text-red-900 mb-2">Error Loading Monthly Data</h3>
                <p className="text-red-600 mb-4">{error}</p>
                <Button
                  onClick={() => fetchMonthlyData(selectedYear, selectedMonth, true)}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Try Again
                </Button>
              </div>
            ) : monthlyData.length === 0 ? (
              <div className="text-center py-12">
                <Calendar className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">{t('ledger.no_psp_data_available')}</h3>
                <p className="text-slate-600 mb-4">{t('ledger.no_psp_data')}</p>
                <p className="text-sm text-slate-500">
                  Selected: {new Date(selectedYear, selectedMonth - 1).toLocaleString('default', { month: 'long', year: 'numeric' })}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-slate-100 border-b border-slate-300">
                      <tr>
                        <th className="text-left py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider w-12"></th>
                        <th className="text-left py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider min-w-[180px]">
                          <div className="flex items-center gap-2">
                            <Building className="h-3.5 w-3.5 text-slate-600" />
                            {t('ledger.psp_count')}
                          </div>
                        </th>
                        <th className="text-right py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider min-w-[120px] tabular-nums">
                          <div className="flex items-center justify-end gap-1.5">
                            <TrendingUp className="h-3.5 w-3.5 text-slate-600" />
                            YATIRIM
                          </div>
                        </th>
                        <th className="text-right py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider min-w-[120px] tabular-nums">
                          <div className="flex items-center justify-end gap-1.5">
                            <TrendingDown className="h-3.5 w-3.5 text-slate-600" />
                            ÇEKME
                          </div>
                        </th>
                        <th className="text-right py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider min-w-[120px] tabular-nums">
                          <div className="flex items-center justify-end gap-1.5">
                            <DollarSign className="h-3.5 w-3.5 text-slate-600" />
                            TOPLAM
                          </div>
                        </th>
                        <th className="text-right py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider min-w-[140px] tabular-nums">
                          <div className="flex items-center justify-end gap-1.5">
                            {commissionCalculating ? (
                              <div className="animate-spin h-3.5 w-3.5 border-2 border-slate-600 border-t-transparent rounded-full"></div>
                            ) : (
                              <Activity className="h-3.5 w-3.5 text-slate-600" />
                            )}
                            <span>KOMİSYON</span>
                          </div>
                        </th>
                        <th className="text-right py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider min-w-[120px] tabular-nums">
                          <div className="flex items-center justify-end gap-1.5">
                            <Target className="h-3.5 w-3.5 text-slate-600" />
                            NET
                          </div>
                        </th>
                        <th className="text-right py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider min-w-[140px] tabular-nums">
                          <div className="flex items-center justify-end gap-1.5">
                            <CreditCard className="h-3.5 w-3.5 text-slate-600" />
                            TAHS TUTARI
                          </div>
                        </th>
                        <th className="text-right py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider min-w-[120px] tabular-nums">
                          <div className="flex items-center justify-end gap-1.5">
                            <BarChart3 className="h-3.5 w-3.5 text-slate-600" />
                            KASA TOP
                          </div>
                        </th>
                        <th className="text-right py-3 px-6 font-semibold text-slate-700 text-xs uppercase tracking-wider min-w-[120px] tabular-nums">
                          <div className="flex items-center justify-end gap-1.5">
                            <RefreshCw className="h-3.5 w-3.5 text-slate-600" />
                            DEVİR
                          </div>
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {/* PHASE 1 OPTIMIZATION: Paginated results */}
                      {monthlyData
                        .filter(psp => psp && psp.psp)
                        .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
                        .map((psp, index) => (
                        <React.Fragment key={psp.psp}>
                          <tr className="hover:bg-slate-50">
                            <td className="py-4 px-6">
                              <button
                                onClick={() => togglePSPExpansion(psp.psp)}
                                className="p-1.5 hover:bg-slate-200 rounded transition-colors"
                                title={expandedPSPs.has(psp.psp) ? "Collapse details" : "Expand details"}
                              >
                                {expandedPSPs.has(psp.psp) ? (
                                  <ChevronDown className="h-3.5 w-3.5 text-slate-600" />
                                ) : (
                                  <ChevronRight className="h-3.5 w-3.5 text-slate-600" />
                                )}
                              </button>
                            </td>
                            <td className="py-4 px-6">
                              <div className="flex items-center gap-2">
                                <div className="w-8 h-8 bg-slate-100 rounded flex items-center justify-center">
                                  <Building className="h-4 w-4 text-slate-600" />
                                </div>
                                <div>
                                  <div className="font-semibold text-slate-900 text-sm">{psp.psp}</div>
                                  <div className="text-xs text-slate-500">{psp.transaction_count || 0} txns</div>
                                </div>
                              </div>
                            </td>
                            <td className="py-4 px-6 text-right tabular-nums">
                              <span className="font-semibold text-slate-900 text-sm">
                                {formatPSPCurrency(psp.yatimim || 0, psp.psp)}
                              </span>
                            </td>
                            <td className="py-4 px-6 text-right tabular-nums">
                              <span className="font-semibold text-slate-900 text-sm">
                                {formatPSPCurrency(psp.cekme || 0, psp.psp)}
                              </span>
                            </td>
                            <td className="py-4 px-6 text-right tabular-nums">
                              <span className="font-semibold text-slate-900 text-sm">
                                {formatPSPCurrency(psp.toplam || 0, psp.psp)}
                              </span>
                            </td>
                            <td className="py-4 px-6 text-right tabular-nums">
                              <div className="flex items-center justify-end gap-1.5">
                                <span className="font-semibold text-slate-900 text-sm">
                                  {formatPSPCurrency(psp.komisyon || 0, psp.psp)}
                                </span>
                                {psp.commission_rate !== undefined && psp.psp.toUpperCase() !== 'TETHER' && (
                                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-slate-200 text-slate-700">
                                    {psp.commission_rate}%
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-4 px-6 text-right tabular-nums">
                              <span className="font-semibold text-slate-900 text-sm">
                                {formatPSPCurrency(psp.net || 0, psp.psp)}
                              </span>
                            </td>
                            <td className="py-4 px-6 text-right tabular-nums">
                              <span className="font-semibold text-slate-900 text-sm">
                                {formatPSPCurrency(psp.tahs_tutari || 0, psp.psp)}
                              </span>
                            </td>
                            <td className="py-4 px-6 text-right tabular-nums">
                              <span className="font-semibold text-slate-900 text-sm">
                                {formatPSPCurrency(psp.kasa_top || 0, psp.psp)}
                              </span>
                            </td>
                            <td className="py-4 px-6 text-right tabular-nums">
                              <span className={`font-semibold text-sm ${(psp.devir || 0) >= 0 ? 'text-slate-900' : 'text-red-700'}`}>
                                {formatPSPCurrency(psp.devir || 0, psp.psp)}
                              </span>
                            </td>
                          </tr>
                          
                          {/* Daily Breakdown Row */}
                          {expandedPSPs.has(psp.psp) && (
                            <tr key={`${psp.psp}-daily`} className="bg-gradient-to-r from-slate-50/50 to-blue-50/30">
                              <td colSpan={10} className="py-6 px-6">
                                <div className="bg-white/80 backdrop-blur-sm rounded-xl border border-slate-200/60 shadow-lg shadow-slate-200/20">
                                  <div className="px-6 py-4 border-b border-slate-200/60 bg-gradient-to-r from-slate-50/80 to-blue-50/40 rounded-t-xl">
                                    <h4 className="text-sm font-bold text-slate-800 flex items-center gap-3">
                                      <div className="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center">
                                        <Calendar className="h-4 w-4 text-white" />
                                      </div>
                                      Daily Transaction Breakdown - {psp.psp}
                                      <span className="ml-auto text-xs font-medium text-slate-600 bg-slate-200/60 px-3 py-1 rounded-full">
                                        {createCompleteDailyBreakdown(psp, selectedYear, selectedMonth).length} days
                                      </span>
                                    </h4>
                                  </div>
                                  <div className="overflow-x-auto">
                                    <table className="w-full">
                                      <thead className="bg-gradient-to-r from-slate-50 to-slate-100/50">
                                        <tr>
                                          <th className="text-left py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">Date</th>
                                          <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">YATIRIM</th>
                                          <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">ÇEKME</th>
                                          <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">TOPLAM</th>
                                          <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">
                                            <div className="flex flex-col items-end">
                                              <span>KOMİSYON</span>
                                              <span className="text-xs font-normal text-slate-500 normal-case">Deposits Only</span>
                                            </div>
                                          </th>
                                          <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">NET</th>
                                          <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">TAHS TUTARI</th>
                                          <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">KASA TOP</th>
                                          <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">DEVİR</th>
                                          <th className="text-center py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">Tx Count</th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-slate-100/60">
                                        {createCompleteDailyBreakdown(psp, selectedYear, selectedMonth).map((daily: any, dailyIndex: number) => (
                                          <tr key={daily.date} className={`hover:bg-slate-50/50 transition-colors duration-150 ${
                                            daily.transaction_count > 0 
                                              ? (dailyIndex % 2 === 0 ? 'bg-white/50' : 'bg-slate-50/30')
                                              : daily.isWeekend
                                                ? 'bg-orange-50/30'
                                                : 'bg-gray-50/20'
                                          }`}>
                                            <td className="py-3 px-4">
                                              <div className="flex items-center gap-2">
                                                <div className={`w-2 h-2 rounded-full ${
                                                  daily.transaction_count > 0 
                                                    ? 'bg-blue-400' 
                                                    : daily.isWeekend 
                                                      ? 'bg-orange-300' 
                                                      : 'bg-gray-300'
                                                }`}></div>
                                                <div className="flex flex-col">
                                                  <span className="font-medium text-slate-800 text-sm">
                                                    {daily.day} {daily.dayName}
                                                  </span>
                                                  <span className="text-xs text-gray-500">
                                                    {new Date(daily.date).toLocaleDateString('tr-TR')}
                                                  </span>
                                                </div>
                                              </div>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                              <span className={`font-mono text-sm font-semibold ${
                                                daily.transaction_count > 0 ? 'text-emerald-700' : 'text-gray-400'
                                              }`}>
                                                {formatPSPCurrency(daily.yatimim || 0, psp.psp)}
                                              </span>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                              <span className={`font-mono text-sm font-semibold ${
                                                daily.transaction_count > 0 ? 'text-red-700' : 'text-gray-400'
                                              }`}>
                                                {formatPSPCurrency(daily.cekme || 0, psp.psp)}
                                              </span>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                              <span className={`font-mono text-sm font-bold ${
                                                daily.transaction_count > 0 ? 'text-slate-800' : 'text-gray-400'
                                              }`}>
                                                {formatPSPCurrency(daily.toplam || 0, psp.psp)}
                                              </span>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                              <div className="flex flex-col items-end">
                                                <div className="flex items-center gap-2">
                                                  <span className={`font-mono text-sm font-semibold ${
                                                    daily.transaction_count > 0 
                                                      ? getCommissionRateColor(psp.commission_rate || 0)
                                                      : 'text-gray-400'
                                                  }`}>
                                                    {formatPSPCurrency(daily.komisyon || 0, psp.psp)}
                                                  </span>
                                                  {psp.psp.toUpperCase() === 'TETHER' ? (
                                                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                                      Internal KASA
                                                    </span>
                                                  ) : psp.commission_rate !== undefined ? (
                                                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${getCommissionRateBgColor(psp.commission_rate)}`}>
                                                      {psp.commission_rate}%
                                                    </span>
                                                  ) : null}
                                                </div>
                                                <span className="text-xs text-slate-500 mt-1">Deposits Only</span>
                                              </div>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                              <span className={`font-mono text-sm font-semibold ${
                                                daily.transaction_count > 0 ? 'text-blue-700' : 'text-gray-400'
                                              }`}>
                                                {formatPSPCurrency(daily.net || 0, psp.psp)}
                                              </span>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                              <div className="flex items-center justify-end gap-2">
                                                <span className={`font-mono text-sm font-semibold ${
                                                  daily.transaction_count > 0 ? 'text-purple-700' : 'text-gray-400'
                                                }`}>
                                                  {formatPSPCurrency(daily.tahs_tutari || 0, psp.psp)}
                                                </span>
                                                <button
                                                  onClick={() => openEditModal(psp.psp, daily.date, daily.tahs_tutari || 0)}
                                                  className="p-1.5 hover:bg-purple-100 rounded-md transition-colors duration-200 group opacity-70 hover:opacity-100"
                                                  title="Edit allocation amount"
                                                >
                                                  <Edit className="h-4 w-4 text-purple-600 group-hover:text-purple-700" />
                                                </button>
                                              </div>
                                            </td>
               <td className="py-3 px-4 text-right">
                 <div className="flex items-center justify-end gap-2">
                   <span className={`font-mono text-sm font-semibold ${
                     daily.transaction_count > 0 ? 'text-indigo-700' : 'text-gray-400'
                   }`}>
                     {formatPSPCurrency(daily.kasa_top || 0, psp.psp)}
                   </span>
                   <button
                     onClick={() => openEditKasaTopModal(psp.psp, daily.date, daily.kasa_top || 0)}
                     className="p-1.5 hover:bg-indigo-100 rounded-md transition-colors duration-200 group opacity-70 hover:opacity-100"
                     title="Edit KASA TOP amount"
                   >
                     <Edit className="h-4 w-4 text-indigo-600 group-hover:text-indigo-700" />
                   </button>
                 </div>
               </td>
                                            <td className="py-3 px-4 text-right">
                                              <div className="flex items-center justify-end gap-2">
                                                <span className={`font-mono text-sm font-semibold ${
                                                  daily.transaction_count > 0 
                                                    ? ((daily.devir || 0) >= 0 ? 'text-emerald-700' : 'text-red-700')
                                                    : 'text-gray-400'
                                                }`}>
                                                  {formatPSPCurrency(daily.devir || 0, psp.psp)}
                                                </span>
                                                <button
                                                  onClick={() => openEditDevirModal(psp.psp, daily.date, daily.devir || 0)}
                                                  className="p-1.5 hover:bg-emerald-100 rounded-md transition-colors duration-200 group opacity-70 hover:opacity-100"
                                                  title="Edit Devir amount"
                                                >
                                                  <Edit className="h-4 w-4 text-emerald-600 group-hover:text-emerald-700" />
                                                </button>
                                              </div>
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                              <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium ${
                                                daily.transaction_count > 0 
                                                  ? 'bg-slate-100 text-slate-700' 
                                                  : 'bg-gray-50 text-gray-400'
                                              }`}>
                                                {daily.transaction_count || 0}
                                              </span>
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                      <tfoot className="bg-gradient-to-r from-slate-100 to-slate-200/60 border-t border-slate-200">
                                        <tr className="font-bold">
                                          <td className="py-4 px-4 text-slate-800">
                                            <div className="flex items-center gap-2">
                                              <div className="w-2 h-2 bg-slate-400 rounded-full"></div>
                                              Daily Totals
                                            </div>
                                          </td>
                                          <td className="py-4 px-4 text-right font-mono text-emerald-800 text-sm">
                                            {formatPSPCurrency(createCompleteDailyBreakdown(psp, selectedYear, selectedMonth).reduce((sum: number, daily: any) => sum + (daily.yatimim || 0), 0), psp.psp)}
                                          </td>
                                          <td className="py-4 px-4 text-right font-mono text-red-800 text-sm">
                                            {formatPSPCurrency(createCompleteDailyBreakdown(psp, selectedYear, selectedMonth).reduce((sum: number, daily: any) => sum + (daily.cekme || 0), 0), psp.psp)}
                                          </td>
                                          <td className="py-4 px-4 text-right font-mono text-slate-800 text-sm">
                                            {formatPSPCurrency(createCompleteDailyBreakdown(psp, selectedYear, selectedMonth).reduce((sum: number, daily: any) => sum + (daily.toplam || 0), 0), psp.psp)}
                                          </td>
                                          <td className="py-4 px-4 text-right font-mono text-amber-800 text-sm">
                                            {formatPSPCurrency(createCompleteDailyBreakdown(psp, selectedYear, selectedMonth).reduce((sum: number, daily: any) => sum + (daily.komisyon || 0), 0), psp.psp)}
                                          </td>
                                          <td className="py-4 px-4 text-right font-mono text-blue-800 text-sm">
                                            {formatPSPCurrency(createCompleteDailyBreakdown(psp, selectedYear, selectedMonth).reduce((sum: number, daily: any) => sum + (daily.net || 0), 0), psp.psp)}
                                          </td>
                                          <td className="py-4 px-4 text-right font-mono text-purple-800 text-sm">
                                            {formatPSPCurrency(createCompleteDailyBreakdown(psp, selectedYear, selectedMonth).reduce((sum: number, daily: any) => sum + (daily.tahs_tutari || 0), 0), psp.psp)}
                                          </td>
                                          <td className="py-4 px-4 text-right font-mono text-indigo-800 text-sm">
                                            {/* KASA TOP: Son günün değerini göster (kümülatif) */}
                                            {formatPSPCurrency(
                                              (() => {
                                                const dailyData = createCompleteDailyBreakdown(psp, selectedYear, selectedMonth);
                                                // Son günün KASA TOP değerini al (kümülatif olduğu için toplamaya gerek yok)
                                                const lastDay = dailyData[dailyData.length - 1];
                                                return lastDay?.kasa_top || 0;
                                              })(),
                                              psp.psp
                                            )}
                                          </td>
                                          <td className="py-4 px-4 text-right font-mono text-slate-800 text-sm">
                                            {/* DEVİR: Son günün değerini göster (kümülatif) */}
                                            {formatPSPCurrency(
                                              (() => {
                                                const dailyData = createCompleteDailyBreakdown(psp, selectedYear, selectedMonth);
                                                // Son günün DEVİR değerini al
                                                const lastDay = dailyData[dailyData.length - 1];
                                                return lastDay?.devir || 0;
                                              })(),
                                              psp.psp
                                            )}
                                          </td>
                                          <td className="py-4 px-4 text-center">
                                            <span className="inline-flex items-center justify-center w-8 h-8 bg-slate-300 rounded-full text-xs font-bold text-slate-800">
                                              {createCompleteDailyBreakdown(psp, selectedYear, selectedMonth).reduce((sum: number, daily: any) => sum + (daily.transaction_count || 0), 0)}
                                            </span>
                                          </td>
                                        </tr>
                                      </tfoot>
                                    </table>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      ))}
                    </tbody>
                    
                  </table>
                  
                  {/* PHASE 1 OPTIMIZATION: Pagination Controls */}
                  {monthlyData.length > itemsPerPage && (
                    <div className="flex items-center justify-between px-6 py-4 bg-slate-50 border-t border-slate-200">
                      <div className="text-sm text-slate-600">
                        Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, monthlyData.length)} of {monthlyData.length} PSPs
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                          disabled={currentPage === 1}
                          variant="outline"
                          size="sm"
                          className="flex items-center gap-1"
                        >
                          <ChevronLeft className="h-4 w-4" />
                          Previous
                        </Button>
                        <div className="flex items-center gap-1">
                          {Array.from({ length: Math.ceil(monthlyData.length / itemsPerPage) }, (_, i) => i + 1).map(page => (
                            <Button
                              key={page}
                              onClick={() => setCurrentPage(page)}
                              variant={currentPage === page ? "default" : "outline"}
                              size="sm"
                              className="w-10"
                            >
                              {page}
                            </Button>
                          ))}
                        </div>
                        <Button
                          onClick={() => setCurrentPage(Math.min(Math.ceil(monthlyData.length / itemsPerPage), currentPage + 1))}
                          disabled={currentPage === Math.ceil(monthlyData.length / itemsPerPage)}
                          variant="outline"
                          size="sm"
                          className="flex items-center gap-1"
                        >
                          Next
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  <table className="w-full">
                    <tfoot className="bg-gradient-to-r from-slate-100 via-slate-200/80 to-slate-100 border-t-2 border-slate-300">
                      <tr className="font-bold">
                        <td className="py-6 px-6"></td>
                        <td className="py-6 px-6">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-slate-600 to-slate-700 rounded-lg flex items-center justify-center shadow-lg">
                              <BarChart3 className="h-5 w-5 text-white" />
                            </div>
                            <div>
                              <div className="text-slate-900 text-sm font-bold">MONTHLY TOTALS</div>
                              <div className="text-xs text-slate-600">{monthlyData.length} PSPs</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-6 px-6 text-right">
                          <div className="flex flex-col items-end">
                            <span className="font-mono text-base font-bold text-emerald-800">
                              {formatCurrency(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.yatimim || 0)), 0))}
                            </span>
                            <span className="text-xs text-emerald-700/70 font-medium">{t('ledger.total_deposits')}</span>
                          </div>
                        </td>
                        <td className="py-6 px-6 text-right">
                          <div className="flex flex-col items-end">
                            <span className="font-mono text-base font-bold text-red-800">
                              {formatCurrency(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.cekme || 0)), 0))}
                            </span>
                            <span className="text-xs text-red-700/70 font-medium">{t('ledger.total_withdrawals')}</span>
                          </div>
                        </td>
                        <td className="py-6 px-6 text-right">
                          <div className="flex flex-col items-end">
                            <span className="font-mono text-base font-bold text-slate-900">
                              {formatCurrency(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.toplam || 0)), 0))}
                            </span>
                            <span className="text-xs text-slate-700/70 font-medium">Net Total</span>
                          </div>
                        </td>
                        <td className="py-6 px-6 text-right">
                          <div className="flex flex-col items-end">
                            <span className="font-mono text-base font-bold text-amber-800">
                              {formatCurrency(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.komisyon || 0)), 0))}
                            </span>
                            <span className="text-xs text-amber-700/70 font-medium">{t('ledger.total_commission')}</span>
                          </div>
                        </td>
                        <td className="py-6 px-6 text-right">
                          <div className="flex flex-col items-end">
                            <span className="font-mono text-base font-bold text-blue-800">
                              {formatCurrency(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.net || 0)), 0))}
                            </span>
                            <span className="text-xs text-blue-700/70 font-medium">Net Amount</span>
                          </div>
                        </td>
                        <td className="py-6 px-6 text-right">
                          <div className="flex flex-col items-end">
                            <span className="font-mono text-base font-bold text-purple-800">
                              {formatCurrency(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.tahs_tutari || 0)), 0))}
                            </span>
                            <span className="text-xs text-purple-700/70 font-medium">{t('ledger.total_allocations')}</span>
                          </div>
                        </td>
                        <td className="py-6 px-6 text-right">
                          <div className="flex flex-col items-end">
                            <span className="font-mono text-base font-bold text-indigo-800">
                              {formatCurrency(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.kasa_top || 0)), 0))}
                            </span>
                            <span className="text-xs text-indigo-700/70 font-medium">{t('ledger.total_revenue')}</span>
                          </div>
                        </td>
                        <td className="py-6 px-6 text-right">
                          <div className="flex flex-col items-end">
                            <span className={`font-mono text-base font-bold ${(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.kasa_top || 0)), 0) - monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.tahs_tutari || 0)), 0)) >= 0 ? 'text-emerald-800' : 'text-red-800'}`}>
                              {formatCurrency(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.kasa_top || 0)), 0) - monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.tahs_tutari || 0)), 0))}
                            </span>
                            <span className={`text-xs font-medium ${(monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.kasa_top || 0)), 0) - monthlyData.reduce((sum, psp) => sum + (psp.psp.toUpperCase() === 'TETHER' ? 0 : (psp.tahs_tutari || 0)), 0)) >= 0 ? 'text-emerald-700/70' : 'text-red-700/70'}`}>
                              Total Rollover
                            </span>
                          </div>
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>

            {/* History Section */}
            <div className="mt-6">
              <UnifiedCard variant="elevated" className="mb-6">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5 text-gray-600" />
                    Audit History
                  </CardTitle>
                  <CardDescription>
                    Complete audit trail of all manual overrides (Allocation, Devir, KASA TOP) with filtering and export capabilities
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Filters and Export Controls */}
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                      <Input
                        type="date"
                        value={historyFilters.startDate}
                        onChange={(e) => handleHistoryFilterChange('startDate', e.target.value)}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                      <Input
                        type="date"
                        value={historyFilters.endDate}
                        onChange={(e) => handleHistoryFilterChange('endDate', e.target.value)}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">{t('ledger.psp_filter')}</label>
                      <Input
                        type="text"
                        placeholder={t('ledger.filter_by_psp')}
                        value={historyFilters.psp}
                        onChange={(e) => handleHistoryFilterChange('psp', e.target.value)}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Type Filter</label>
                      <select
                        value={historyFilters.type}
                        onChange={(e) => handleHistoryFilterChange('type', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">All Types</option>
                        <option value="allocation">Allocation</option>
                        <option value="devir">Devir</option>
                        <option value="kasa_top">KASA TOP</option>
                      </select>
                    </div>
                    <div className="flex items-end gap-2">
                      <Button
                        onClick={() => exportHistoryData('csv')}
                        variant="outline"
                        className="flex items-center gap-2"
                      >
                        <Download className="h-4 w-4" />
                        CSV
                      </Button>
                      <Button
                        onClick={() => exportHistoryData('json')}
                        variant="outline"
                        className="flex items-center gap-2"
                      >
                        <Download className="h-4 w-4" />
                        JSON
                      </Button>
                    </div>
                  </div>

                  {/* History Table */}
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    {historyLoading ? (
                      <div className="flex items-center justify-center py-12">
                        <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                        <span className="ml-2 text-gray-500">Loading history data...</span>
                      </div>
                    ) : (
                      <>
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead className="bg-gray-50 border-b border-gray-100">
                              <tr>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                  Type
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                  Date
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                  {t('ledger.psp_name')}
                                </th>
                                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                  Amount
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                  Created At
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                  Updated At
                                </th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {historyData.length === 0 ? (
                                <tr>
                                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                                    <Clock className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                                    <p>No history found</p>
                                    <p className="text-sm">Try adjusting your filters or check back later</p>
                                  </td>
                                </tr>
                              ) : (
                                historyData.map((entry, index) => (
                                  <tr key={`${entry.id}-${index}`} className="hover:bg-gray-50 transition-colors duration-150">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                        entry.type === 'Allocation' 
                                          ? 'bg-purple-100 text-purple-800' 
                                          : entry.type === 'Devir'
                                          ? 'bg-emerald-100 text-emerald-800'
                                          : 'bg-indigo-100 text-indigo-800'
                                      }`}>
                                        {entry.type}
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                      {new Date(entry.date).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                      <div className="flex items-center gap-2">
                                        <Building className="h-4 w-4 text-gray-400" />
                                        {entry.psp_name}
                                      </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold text-gray-900">
                                      {formatCurrency(entry.amount, '₺')}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                      {new Date(entry.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                      {new Date(entry.updated_at).toLocaleString()}
                                    </td>
                                  </tr>
                                ))
                              )}
                            </tbody>
                          </table>
                        </div>

                        {/* Pagination */}
                        {historyPagination && historyPagination.pages > 1 && (
                          <div className="bg-gray-50 px-6 py-3 border-t border-gray-100">
                            <div className="flex items-center justify-between">
                              <div className="text-sm text-gray-700">
                                Showing {((historyPagination.page - 1) * historyPagination.per_page) + 1} to{' '}
                                {Math.min(historyPagination.page * historyPagination.per_page, historyPagination.total)} of{' '}
                                {historyPagination.total} entries
                              </div>
                              <div className="flex items-center gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleHistoryPageChange(historyPagination.page - 1)}
                                  disabled={!historyPagination.has_prev}
                                >
                                  Previous
                                </Button>
                                <span className="text-sm text-gray-700">
                                  Page {historyPagination.page} of {historyPagination.pages}
                                </span>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleHistoryPageChange(historyPagination.page + 1)}
                                  disabled={!historyPagination.has_next}
                                >
                                  Next
                                </Button>
                              </div>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </CardContent>
              </UnifiedCard>
            </div>
        </TabsContent>

        {/* Trust Tab Content */}
        <TabsContent value="trust" className="mt-6">
          <TrustTabContent />
        </TabsContent>

        {/* Analytics Tab Content */}
        <TabsContent value="analytics" className="mt-6">
          {/* Analytics Header */}
          <div className="flex items-center justify-between">
                  <div>
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <BarChart3 className="h-6 w-6 text-primary-600" />
                Analytics Dashboard
              </h2>
              <p className="text-gray-600 mt-1">Comprehensive insights and performance metrics</p>
                  </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => {
                  fetchPSPData(true);
                  fetchLedgerData(true);
                }}
                variant="outline"
                size="default"
                className="flex items-center gap-2 h-10 px-4 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={ledgerLoading}
              >
                <RefreshCw className={`h-4 w-4 ${ledgerLoading ? 'animate-spin' : ''}`} />
                {ledgerLoading ? 'Refreshing...' : 'Refresh Data'}
              </Button>
                </div>
              </div>

          {/* Key Performance Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title={t('ledger.total_volume')}
              value={formatCurrency(pspData.reduce((sum, psp) => sum + psp.total_amount, 0), '₺')}
              subtitle={t('ledger.all_psps_combined')}
              icon={DollarSign}
              color="indigo"
              animated={true}
              animationDuration={500}
            />
            <MetricCard
              title={t('ledger.active_psps')}
              value={pspData.length.toString()}
              subtitle={t('ledger.payment_providers')}
              icon={Building}
              color="green"
              animated={true}
              animationDuration={500}
            />
            <MetricCard
              title={t('ledger.avg_commission_rate')}
              value={`${(pspData.reduce((sum, psp) => sum + psp.commission_rate, 0) / pspData.length || 0).toFixed(1)}%`}
              subtitle={t('ledger.weighted_average')}
              icon={Target}
              color="orange"
              animated={true}
              animationDuration={500}
            />
            <MetricCard
              title={t('ledger.total_transactions')}
              value={formatNumber(pspData.reduce((sum, psp) => sum + psp.transaction_count, 0))}
              subtitle={t('ledger.all_time')}
              icon={Activity}
              color="purple"
              animated={true}
              animationDuration={500}
            />
              </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* PSP Performance Comparison */}
            <UnifiedCard variant="elevated" className="p-6">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary-600" />
                  {t('ledger.psp_performance_comparison')}
                </CardTitle>
                <CardDescription>
                  {t('ledger.net_amounts_transaction_counts')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={pspData.map(psp => ({
                      name: psp.psp,
                      net: psp.total_net,
                      transactions: psp.transaction_count,
                      commission: psp.total_commission
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis 
                        dataKey="name" 
                        tick={{ fontSize: 12 }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip 
                        formatter={(value, name) => [
                          name === 'net' || name === 'commission' ? formatCurrency(Number(value), '₺') : value,
                          name === 'net' ? 'Net Amount' : name === 'transactions' ? 'Transactions' : 'Commission'
                        ]}
                        labelStyle={{ color: '#374151' }}
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Bar dataKey="net" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
              </div>
            </CardContent>
          </UnifiedCard>

            {/* PSP Market Share */}
            <UnifiedCard variant="elevated" className="p-6">
              <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5 text-primary-600" />
                  {t('ledger.psp_market_share')}
              </CardTitle>
              <CardDescription>
                  {t('ledger.distribution_total_volume')}
              </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <Pie
                        data={pspData.map(psp => ({
                          name: psp.psp,
                          value: psp.total_amount,
                          net: psp.total_net
                        }))}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {pspData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={`hsl(${index * 60}, 70%, 50%)`} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value) => [formatCurrency(Number(value), '₺'), 'Total Amount']}
                        labelStyle={{ color: '#374151' }}
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                    </RechartsPieChart>
                  </ResponsiveContainer>
            </div>
            </CardContent>
          </UnifiedCard>
          </div>

          {/* Daily Trends */}
          <UnifiedCard variant="elevated" className="p-6">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2">
                <LineChart className="h-5 w-5 text-primary-600" />
                Daily Transaction Trends
              </CardTitle>
              <CardDescription>
                Net amounts and transaction counts over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={ledgerData.map(day => ({
                    date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                    net: day.totals.net,
                    transactions: day.totals.total_psp,
                    commission: day.totals.commission
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip 
                      formatter={(value, name) => [
                        name === 'net' || name === 'commission' ? formatCurrency(Number(value), '₺') : value,
                        name === 'net' ? 'Net Amount' : name === 'transactions' ? 'Transactions' : 'Commission'
                      ]}
                      labelStyle={{ color: '#374151' }}
                      contentStyle={{ 
                        backgroundColor: 'white', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                      }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="net" 
                      stackId="1" 
                      stroke="#3b82f6" 
                      fill="#3b82f6" 
                      fillOpacity={0.6}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="commission" 
                      stackId="2" 
                      stroke="#f59e0b" 
                      fill="#f59e0b" 
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </UnifiedCard>

          {/* Allocation vs Rollover Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <UnifiedCard variant="elevated" className="p-6">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary-600" />
                  {t('ledger.allocation_vs_net')}
                </CardTitle>
                <CardDescription>
                  {t('ledger.allocation_vs_net_desc')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart data={pspData.map(psp => ({
                      net: psp.total_net,
                      allocation: psp.total_allocations,
                      psp: psp.psp,
                      rollover: psp.total_net - psp.total_allocations
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis 
                        type="number" 
                        dataKey="net" 
                        name="Net Amount"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => formatCurrency(value, '₺')}
                      />
                      <YAxis 
                        type="number" 
                        dataKey="allocation" 
                        name="Allocation"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => formatCurrency(value, '₺')}
                      />
                      <Tooltip 
                        formatter={(value, name) => [
                          formatCurrency(Number(value), '₺'),
                          name === 'net' ? 'Net Amount' : name === 'allocation' ? 'Allocation' : 'Rollover'
                        ]}
                        labelStyle={{ color: '#374151' }}
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Scatter 
                        dataKey="allocation" 
                        fill="#3b82f6"
                        r={6}
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
              </div>
              </CardContent>
            </UnifiedCard>

            <UnifiedCard variant="elevated" className="p-6">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary-600" />
                  {t('ledger.rollover_analysis')}
                </CardTitle>
                <CardDescription>
                  {t('ledger.rollover_risk_levels')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={pspData.map(psp => {
                      const rollover = psp.total_net - psp.total_allocations;
                      const rolloverPercentage = psp.total_net > 0 ? (rollover / psp.total_net) * 100 : 0;
                      return {
                        name: psp.psp,
                        rollover: rollover,
                        percentage: rolloverPercentage,
                        color: rollover > 0 ? '#ef4444' : '#10b981'
                      };
                    })}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis 
                        dataKey="name" 
                        tick={{ fontSize: 12 }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip 
                        formatter={(value, name) => [
                          name === 'rollover' ? formatCurrency(Number(value), '₺') : `${Number(value).toFixed(1)}%`,
                          name === 'rollover' ? 'Rollover Amount' : 'Rollover %'
                        ]}
                        labelStyle={{ color: '#374151' }}
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Bar dataKey="rollover" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
              </div>
              </CardContent>
            </UnifiedCard>
          </div>

          {/* Commission Analysis Charts */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 lg:gap-6">
            <UnifiedCard variant="elevated" className="p-6">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary-600" />
                  {t('ledger.commission_rates_comparison')}
                </CardTitle>
                <CardDescription>
                  {t('ledger.commission_rates_all_psps')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 sm:h-72 lg:h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={pspData.map(psp => ({
                      psp: psp.psp,
                      rate: psp.commission_rate,
                      deposits: psp.total_deposits,
                      commission: psp.total_commission
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis 
                        dataKey="psp" 
                        tick={{ fontSize: 10 }}
                        angle={-45}
                        textAnchor="end"
                        height={60}
                        interval={0}
                      />
                      <YAxis 
                        tick={{ fontSize: 10 }}
                        tickFormatter={(value) => `${value}%`}
                        width={40}
                      />
                      <Tooltip 
                        formatter={(value, name) => [
                          name === 'rate' ? `${value}%` : formatCurrency(Number(value), '₺'),
                          name === 'rate' ? 'Commission Rate' : name === 'deposits' ? 'Total Deposits' : 'Commission Amount'
                        ]}
                        labelStyle={{ color: '#374151' }}
                        contentStyle={{ 
                          backgroundColor: '#ffffff',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Bar 
                        dataKey="rate" 
                        fill="#f59e0b" 
                        radius={[4, 4, 0, 0]}
                        name="Commission Rate"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </UnifiedCard>

            <UnifiedCard variant="elevated" className="p-6">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-primary-600" />
                  {t('ledger.commission_vs_deposits')}
                </CardTitle>
                <CardDescription>
                  {t('ledger.commission_vs_deposits_desc')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 sm:h-72 lg:h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart data={pspData.map(psp => ({
                      deposits: psp.total_deposits,
                      commission: psp.total_commission,
                      psp: psp.psp,
                      rate: psp.commission_rate
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis 
                        type="number" 
                        dataKey="deposits" 
                        name="Total Deposits"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(value) => formatCurrency(value, '₺')}
                        width={60}
                      />
                      <YAxis 
                        type="number" 
                        dataKey="commission" 
                        name="Commission"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(value) => formatCurrency(value, '₺')}
                        width={60}
                      />
                      <Tooltip 
                        formatter={(value, name) => [
                          name === 'deposits' || name === 'commission' ? formatCurrency(Number(value), '₺') : value,
                          name === 'deposits' ? 'Total Deposits' : name === 'commission' ? 'Commission Amount' : name === 'rate' ? 'Commission Rate' : 'PSP'
                        ]}
                        labelStyle={{ color: '#374151' }}
                        contentStyle={{ 
                          backgroundColor: '#ffffff',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Scatter 
                        dataKey="commission" 
                        fill="#f59e0b" 
                        r={6}
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </UnifiedCard>
          </div>

          {/* Commission Rate Comparison Table */}
          <UnifiedCard variant="elevated" className="p-6">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-primary-600" />
                Commission Rate Comparison
              </CardTitle>
              <CardDescription>
                Detailed comparison of commission rates and their impact
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto -mx-6 px-6">
                <table className="w-full min-w-[600px]">
                  <thead className="bg-gradient-to-r from-slate-50 to-slate-100/50">
                    <tr>
                      <th className="text-left py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">{t('ledger.psp')}</th>
                      <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">{t('ledger.commission_rate')}</th>
                      <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">{t('ledger.total_deposits')}</th>
                      <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">{t('ledger.commission_amount')}</th>
                      <th className="text-right py-3 px-4 font-semibold text-slate-700 text-xs uppercase tracking-wider">Efficiency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100/60">
                    {pspData
                      .sort((a, b) => b.commission_rate - a.commission_rate)
                      .map((psp, index) => {
                        const efficiency = psp.total_deposits > 0 ? (psp.total_commission / psp.total_deposits) * 100 : 0;
                        return (
                          <tr key={psp.psp} className={`hover:bg-slate-50/50 transition-colors duration-150 ${index % 2 === 0 ? 'bg-white/50' : 'bg-slate-50/30'}`}>
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <div className={`w-3 h-3 rounded-full ${getCommissionRateBgColor(psp.commission_rate).split(' ')[0]}`}></div>
                                <span className="font-medium text-slate-800 text-sm">{psp.psp}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4 text-right">
                              {psp.psp.toUpperCase() === 'TETHER' ? (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                  Internal KASA
                                </span>
                              ) : (
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCommissionRateBgColor(psp.commission_rate)}`}>
                                  {psp.commission_rate}%
                                </span>
                              )}
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span className="font-mono text-sm font-semibold text-slate-800">
                                {formatCurrency(psp.total_deposits)}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span className={`font-mono text-sm font-semibold ${getCommissionRateColor(psp.commission_rate)}`}>
                                {formatCurrency(psp.total_commission || 0)}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span className="text-sm font-medium text-slate-600">
                                {efficiency.toFixed(2)}%
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </UnifiedCard>

          {/* Performance Insights */}
          <UnifiedCard variant="elevated" className="p-6">
            <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary-600" />
                Performance Insights
                </CardTitle>
                <CardDescription>
                Key findings and recommendations based on current data
                </CardDescription>
              </CardHeader>
              <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Top Performer */}
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6 border border-green-200">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                      <TrendingUp className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-green-900">Top Performer</h3>
                      <p className="text-sm text-green-700">Highest net amount</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-lg font-bold text-green-900">
                      {pspData.length > 0 ? pspData.reduce((max, psp) => psp.total_net > max.total_net ? psp : max).psp : 'N/A'}
                    </p>
                    <p className="text-sm text-green-700">
                      {pspData.length > 0 ? formatCurrency(pspData.reduce((max, psp) => psp.total_net > max.total_net ? psp : max).total_net, '₺') : '₺0'}
                    </p>
                  </div>
                </div>

                {/* Most Efficient */}
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 border border-blue-200">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                      <Target className="h-5 w-5 text-white" />
                            </div>
                    <div>
                      <h3 className="font-semibold text-blue-900">Most Efficient</h3>
                      <p className="text-sm text-blue-700">Best allocation ratio</p>
                            </div>
                          </div>
                  <div className="space-y-2">
                    <p className="text-lg font-bold text-blue-900">
                      {pspData.length > 0 ? pspData.reduce((best, psp) => {
                        const currentRatio = psp.total_net > 0 ? psp.total_allocations / psp.total_net : 0;
                        const bestRatio = best.total_net > 0 ? best.total_allocations / best.total_net : 0;
                        return currentRatio > bestRatio ? psp : best;
                      }).psp : 'N/A'}
                    </p>
                    <p className="text-sm text-blue-700">
                      {pspData.length > 0 ? `${(pspData.reduce((best, psp) => {
                        const currentRatio = psp.total_net > 0 ? psp.total_allocations / psp.total_net : 0;
                        const bestRatio = best.total_net > 0 ? best.total_allocations / best.total_net : 0;
                        return currentRatio > bestRatio ? psp : best;
                      }).total_net > 0 ? (pspData.reduce((best, psp) => {
                        const currentRatio = psp.total_net > 0 ? psp.total_allocations / psp.total_net : 0;
                        const bestRatio = best.total_net > 0 ? best.total_allocations / best.total_net : 0;
                        return currentRatio > bestRatio ? psp : best;
                      }).total_allocations / pspData.reduce((best, psp) => {
                        const currentRatio = psp.total_net > 0 ? psp.total_allocations / psp.total_net : 0;
                        const bestRatio = best.total_net > 0 ? best.total_allocations / best.total_net : 0;
                        return currentRatio > bestRatio ? psp : best;
                      }).total_net) * 100 : 0).toFixed(1)}%` : '0%'}
                    </p>
                            </div>
                            </div>

                {/* Risk Alert */}
                <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-6 border border-orange-200">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
                      <AlertTriangle className="h-5 w-5 text-white" />
                          </div>
                          <div>
                      <h3 className="font-semibold text-orange-900">Risk Alert</h3>
                      <p className="text-sm text-orange-700">Highest rollover</p>
                          </div>
                        </div>
                  <div className="space-y-2">
                    <p className="text-lg font-bold text-orange-900">
                      {pspData.length > 0 ? pspData.reduce((max, psp) => {
                        const currentRollover = psp.total_allocations - psp.total_net;
                        const maxRollover = max.total_allocations - max.total_net;
                        return currentRollover > maxRollover ? psp : max;
                      }).psp : 'N/A'}
                    </p>
                    <p className="text-sm text-orange-700">
                      {pspData.length > 0 ? formatCurrency(pspData.reduce((max, psp) => {
                        const currentRollover = psp.total_allocations - psp.total_net;
                        const maxRollover = max.total_allocations - max.total_net;
                        return currentRollover > maxRollover ? psp : max;
                      }).total_allocations - pspData.reduce((max, psp) => {
                        const currentRollover = psp.total_allocations - psp.total_net;
                        const maxRollover = max.total_allocations - max.total_net;
                        return currentRollover > maxRollover ? psp : max;
                      }).total_net, '₺') : '₺0'}
                    </p>
                  </div>
                </div>
              </div>
              </CardContent>
            </UnifiedCard>
        </TabsContent>
        </Tabs>
      </div>

      {/* Details Modal */}
      {showDetailsModal && (
        console.log('Rendering details modal with data:', detailsData),
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeDetailsModal();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Escape') closeDetailsModal();
          }}
          tabIndex={-1}
        >
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                  <Building className="h-5 w-5 text-blue-600" />
                </div>
                {detailsData?.type === 'psp' 
                  ? `${t('ledger.psp_details')}: ${detailsData.psp}` 
                  : `${t('ledger.psp_details')}: ${detailsData?.date} - ${detailsData?.psp}`
                }
              </h3>
              <button
                onClick={closeDetailsModal}
                className="h-10 w-10 p-0 hover:bg-gray-100 rounded-xl transition-colors flex items-center justify-center"
              >
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              {detailsData?.error ? (
                <div className="text-center py-8">
                  <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                  <p className="text-red-600">{detailsData.error}</p>
                </div>
              ) : detailsData?.transactions?.length > 0 ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-sm text-gray-600">{t('ledger.total_transactions')}</div>
                      <div className="text-2xl font-bold text-gray-900">{detailsData.transactions.length}</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-sm text-gray-600">{t('ledger.total_amount')}</div>
                      <div className="text-2xl font-bold text-gray-900">
                        {formatCurrency(
                          detailsData.transactions.reduce((sum: number, t: any) => sum + (t.amount || 0), 0),
                          '₺'
                        )}
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-sm text-gray-600">{t('ledger.total_commission')}</div>
                      <div className="text-2xl font-bold text-gray-900">
                        {formatCurrency(
                          detailsData.transactions.reduce((sum: number, t: any) => sum + (t.commission || 0), 0),
                          '₺'
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Date
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Amount
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Commission
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Net Amount
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Category
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {detailsData.transactions.map((transaction: any, index: number) => (
                          <tr key={transaction.id || `${transaction.date || transaction.created_at}-${transaction.amount}-${index}`} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {new Date(transaction.date || transaction.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(transaction.amount || 0, '₺')}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(transaction.commission || 0, '₺')}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(transaction.net_amount || 0, '₺')}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                transaction.category === 'DEP' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {transaction.category === 'DEP' ? 'Deposit' : 'Withdrawal'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No transactions found</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bulk Allocation Modal */}
      {showBulkAllocationModal && selectedDayForBulk && (
        <div 
          className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-300"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeBulkAllocationModal();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Escape') closeBulkAllocationModal();
          }}
          tabIndex={-1}
        >
          <div className="bg-white rounded-3xl shadow-2xl max-w-5xl w-full max-h-[92vh] overflow-hidden animate-in zoom-in-95 duration-300">
            {/* Header */}
            <div className="px-10 py-8 border-b border-gray-100 bg-gradient-to-br from-white via-gray-50/30 to-primary-50/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                  <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-2xl flex items-center justify-center shadow-sm">
                    <Building className="h-8 w-8 text-primary-700" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 tracking-tight">
                      Bulk Allocation
                    </h3>
                    <div className="flex items-center gap-2 mt-2">
                      <Calendar className="h-4 w-4 text-gray-500" />
                      <p className="text-base text-gray-600 font-medium">
                        {ledgerData.find(day => day.date === selectedDayForBulk)?.date_str}
                      </p>
                    </div>
                  </div>
                </div>
                <button
                  onClick={closeBulkAllocationModal}
                  className="w-12 h-12 rounded-xl bg-gray-100/80 hover:bg-gray-200/80 flex items-center justify-center transition-all duration-200 hover:scale-105"
                >
                  <X className="h-6 w-6 text-gray-600" />
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="px-10 py-8 max-h-[60vh] overflow-y-auto">
              <div className="space-y-4">
                {pspData.map((psp, index) => {
                  const key = `${selectedDayForBulk}-${psp.psp}`;
                  const currentAllocation = bulkAllocations[key] || 0;
                  
                  // Get day-specific data if it exists
                  const dayData = ledgerData.find(day => day.date === selectedDayForBulk);
                  const dayPspData = dayData?.psps[psp.psp];
                  
                  // Calculate rollover for this PSP on this day
                  const dayNet = dayPspData?.net || 0;
                  const dayAllocation = dayPspData?.allocation || 0;
                  const dayRollover = dayAllocation - dayNet;
                  
                  // Overall rollover from PSP data
                  const overallRollover = psp.total_allocations - psp.total_net;
                  const hasDayActivity = !!dayPspData;
                  
                  return (
                    <div 
                      key={psp.psp} 
                      className="group bg-white shadow-sm rounded-2xl p-8 hover:shadow-lg hover:shadow-primary-100/20 transition-all duration-300 hover:-translate-y-0.5"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-6">
                            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm transition-all duration-200 ${
                              hasDayActivity 
                                ? 'bg-gradient-to-br from-primary-100 to-primary-200 group-hover:from-primary-200 group-hover:to-primary-300' 
                                : 'bg-gradient-to-br from-gray-100 to-gray-200'
                            }`}>
                              <Building className={`h-7 w-7 transition-colors duration-200 ${
                                hasDayActivity ? 'text-primary-700' : 'text-gray-500'
                              }`} />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-4 mb-3">
                                <h4 className="text-lg font-bold text-gray-900">{psp.psp}</h4>
                                {!hasDayActivity && (
                                  <span className="px-3 py-1.5 text-xs font-semibold bg-gradient-to-r from-orange-100 to-orange-200 text-orange-700 rounded-full border border-orange-200">
                                    No Activity
                                  </span>
                                )}
                                {hasDayActivity && (
                                  <span className="px-3 py-1.5 text-xs font-semibold bg-gradient-to-r from-green-100 to-green-200 text-green-700 rounded-full border border-green-200">
                                    Active
                                  </span>
                                )}
                              </div>
                              <div className="grid grid-cols-2 gap-6">
                                <div className="bg-warning-50/80 rounded-xl p-4 border border-warning-200">
                                  <div className="text-xs font-medium text-warning-600 uppercase tracking-wide mb-1">{t('ledger.allocations')}</div>
                                  <div className="text-lg font-bold text-warning-700">
                                    {formatCurrency(hasDayActivity ? dayAllocation : psp.total_allocations, '₺')}
                                  </div>
                                </div>
                                <div className={`rounded-xl p-4 border ${
                                  (hasDayActivity ? dayRollover : overallRollover) > 0 
                                    ? 'bg-destructive-50/80 border-destructive-200' 
                                    : 'bg-success-50/80 border-success-200'
                                }`}>
                                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">{t('ledger.rollover')}</div>
                                  <div className={`text-lg font-bold ${
                                    (hasDayActivity ? dayRollover : overallRollover) > 0 
                                      ? 'text-destructive-600' 
                                      : 'text-success-600'
                                  }`}>
                                    {formatCurrency(hasDayActivity ? dayRollover : overallRollover, '₺')}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                              New Allocation
                            </label>
                            <div className="flex items-center gap-3">
                              <div className="relative">
                                <input
                                  type="number"
                                  value={currentAllocation}
                                  onChange={(e) => handleBulkAllocationChange(psp.psp, parseFloat(e.target.value) || 0)}
                                  className="w-40 px-5 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-right font-bold text-lg transition-all duration-200 bg-white shadow-sm"
                                  placeholder="0.00"
                                  step="0.01"
                                />
                                <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
                                  <span className="text-sm font-bold text-gray-500">₺</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            
            {/* Footer */}
            <div className="px-10 py-8 border-t border-gray-100 bg-gradient-to-r from-gray-50/80 via-white to-gray-50/80">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-8">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center">
                      <Building className="h-5 w-5 text-primary-700" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-gray-700">
                        {Object.keys(bulkAllocations).length} {t('ledger.psps_selected')}
                      </div>
                      <div className="text-xs text-gray-500">Ready for allocation</div>
                    </div>
                  </div>
                  <div className="h-8 w-px bg-gray-200"></div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                      <DollarSign className="h-5 w-5 text-green-700" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-gray-700">
                        Total Allocation
                      </div>
                      <div className="text-lg font-bold text-green-600">
                        {formatCurrency(
                          Object.values(bulkAllocations).reduce((sum, val) => sum + val, 0), 
                          '₺'
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <button
                    onClick={closeBulkAllocationModal}
                    className="px-8 py-3 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-all duration-200 font-semibold shadow-sm hover:shadow"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveBulkAllocations}
                    disabled={bulkAllocationSaving}
                    className="px-8 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl hover:from-primary-700 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-3 font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                  >
                    {bulkAllocationSaving ? (
                      <>
                        <RefreshCw className="h-5 w-5 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Building className="h-5 w-5" />
                        Apply Allocations
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Allocation Modal */}
      {showEditModal && editingAllocation && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-300">
          <div className="bg-white rounded-lg shadow-2xl max-w-md w-full animate-in zoom-in-95 duration-300">
            {/* Header */}
            <div className="px-8 py-6 border-b border-gray-100 bg-gradient-to-br from-white via-gray-50/30 to-primary-50/20 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-2xl flex items-center justify-center shadow-sm">
                    <Edit className="h-6 w-6 text-primary-700" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 tracking-tight">
                      Edit Allocation
                    </h3>
                    <p className="text-sm text-gray-600 font-medium">
                      {editingAllocation.psp} - {new Date(editingAllocation.date).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeEditModal}
                  className="w-10 h-10 rounded-xl bg-gray-100/80 hover:bg-gray-200/80 flex items-center justify-center transition-all duration-200 hover:scale-105"
                >
                  <XIcon className="h-5 w-5 text-gray-600" />
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="px-8 py-6">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Allocation Amount (₺)
                  </label>
                  <input
                    type="number"
                    value={editAmount}
                    onChange={(e) => setEditAmount(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-200 rounded focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 text-lg font-mono"
                    placeholder="Enter allocation amount"
                    min="0"
                    step="0.01"
                    autoFocus
                    disabled={editSaving}
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    Current amount: {formatCurrency(editingAllocation.currentAmount, '₺')}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Footer */}
            <div className="px-8 py-6 border-t border-gray-100 bg-gray-50/50 rounded-b-lg">
              <div className="flex items-center gap-4">
                <button
                  onClick={closeEditModal}
                  className="px-6 py-3 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-all duration-200 font-semibold shadow-sm hover:shadow"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEditAllocation}
                  disabled={editSaving}
                  className="px-6 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded hover:from-primary-700 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-3 font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                >
                  {editSaving ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    <>
                      <SaveIcon className="h-4 w-4" />
                      Update Allocation
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Devir Modal */}
      {showEditDevirModal && editingDevir && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-300">
          <div className="bg-white rounded-lg shadow-2xl max-w-md w-full animate-in zoom-in-95 duration-300">
            {/* Header */}
            <div className="px-8 py-6 border-b border-gray-100 bg-gradient-to-br from-white via-emerald-50/30 to-emerald-50/20 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-emerald-100 to-emerald-200 rounded-2xl flex items-center justify-center shadow-sm">
                    <Edit className="h-6 w-6 text-emerald-700" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 tracking-tight">
                      Edit Devir Amount
                    </h3>
                    <p className="text-sm text-gray-600 font-medium">
                      {editingDevir.psp} - {new Date(editingDevir.date).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeEditDevirModal}
                  className="w-10 h-10 rounded-xl bg-gray-100/80 hover:bg-gray-200/80 flex items-center justify-center transition-all duration-200 hover:scale-105"
                >
                  <XIcon className="h-5 w-5 text-gray-600" />
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="px-8 py-6">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Devir Amount (₺)
                  </label>
                  <input
                    type="number"
                    value={editDevirAmount}
                    onChange={(e) => setEditDevirAmount(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-200 rounded focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 text-lg font-mono"
                    placeholder="Enter Devir amount"
                    step="0.01"
                    autoFocus
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    Current amount: {formatCurrency(editingDevir.currentAmount, '₺')}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Footer */}
            <div className="px-8 py-6 border-t border-gray-100 bg-gray-50/50 rounded-b-lg">
              <div className="flex items-center gap-4">
                <button
                  onClick={closeEditDevirModal}
                  className="px-6 py-3 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-all duration-200 font-semibold shadow-sm hover:shadow"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEditDevir}
                  disabled={editDevirSaving}
                  className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded hover:from-emerald-700 hover:to-emerald-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-3 font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                >
                  {editDevirSaving ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    <>
                      <SaveIcon className="h-4 w-4" />
                      Update Devir
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit KASA TOP Modal */}
      {showEditKasaTopModal && editingKasaTop && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-300">
          <div className="bg-white rounded-lg shadow-2xl max-w-md w-full animate-in zoom-in-95 duration-300">
            {/* Header */}
            <div className="px-8 py-6 border-b border-gray-100 bg-gradient-to-br from-white via-indigo-50/30 to-indigo-50/20 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-100 to-indigo-200 rounded-2xl flex items-center justify-center shadow-sm">
                    <Edit className="h-6 w-6 text-indigo-700" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 tracking-tight">
                      Edit KASA TOP Amount
                    </h3>
                    <p className="text-sm text-gray-600 font-medium">
                      {editingKasaTop.psp} - {new Date(editingKasaTop.date).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeEditKasaTopModal}
                  className="w-10 h-10 rounded-xl bg-gray-100/80 hover:bg-gray-200/80 flex items-center justify-center transition-all duration-200 hover:scale-105"
                >
                  <XIcon className="h-5 w-5 text-gray-600" />
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="px-8 py-6">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Secret Code
                  </label>
                  <input
                    type="password"
                    value={kasaTopSecretCode}
                    onChange={(e) => setKasaTopSecretCode(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-200 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200 text-lg font-mono"
                    placeholder="Enter secret code"
                    autoFocus
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    KASA TOP Amount (₺)
                  </label>
                  <input
                    type="number"
                    value={editKasaTopAmount}
                    onChange={(e) => setEditKasaTopAmount(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-200 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200 text-lg font-mono"
                    placeholder="Enter KASA TOP amount"
                    step="0.01"
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    Current amount: {formatCurrency(editingKasaTop.currentAmount, '₺')}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Footer */}
            <div className="px-8 py-6 border-t border-gray-100 bg-gray-50/50 rounded-b-lg">
              <div className="flex items-center gap-4">
                <button
                  onClick={closeEditKasaTopModal}
                  className="px-6 py-3 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-all duration-200 font-semibold shadow-sm hover:shadow"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEditKasaTop}
                  disabled={editKasaTopSaving || kasaTopSecretCode !== '4561'}
                  className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded hover:from-indigo-700 hover:to-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-3 font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                >
                  {editKasaTopSaving ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    <>
                      <SaveIcon className="h-4 w-4" />
                      Update KASA TOP
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
