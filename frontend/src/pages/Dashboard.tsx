import React, { useState, useEffect, useMemo, useCallback, memo } from 'react';
import ModernDashboard from '../components/modern/ModernDashboard';
import { Button } from '../components/ui/button';
import {
  DollarSign,
  TrendingUp,
  Users,
  CreditCard,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  Activity,
  Calendar,
  PieChart,
  Eye,
  Download,
  RefreshCw,
  LineChart,
  Building2,
  Globe,
  Clock,
  X,
  User,
  Shield,
  Database,
  Wifi,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  Server,
  HardDrive,
  Cpu,
  Network,
  Lock,
  Unlock,
  Activity as ActivityIcon,
  Award,
  Star,
  RefreshCw as RefreshIcon,
  FileText,
  Settings,
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../store';
import {
  fetchDashboardData,
  fetchSecondaryData,
  fetchCommissionAnalytics,
  setActiveTab,
  setTimeRange,
  setRefreshing,
  clearError
} from '../store/slices/dashboardSlice';
import { useExchangeRates } from '../hooks/useExchangeRates';
import ExchangeRatesDisplay from '../components/ExchangeRatesDisplay';
import TopPerformersCard from '../components/TopPerformersCard';
import ExchangeRatesWidget from '../components/ExchangeRatesWidget';
import DashboardTabNavigation from '../components/DashboardTabNavigation';
import usePerformanceMonitor from '../hooks/usePerformanceMonitor';
import { DashboardSkeleton } from '../components/modern/SkeletonLoader';
import StandardMetricsCard from '../components/StandardMetricsCard';
import MetricCard from '../components/MetricCard';
import {
  DashboardPageSkeleton,
  TableSkeleton,
  ChartSkeleton,
  ProgressiveLoader
} from '../components/EnhancedSkeletonLoaders';

import {
  UnifiedButton,
  UnifiedCard,
  UnifiedBadge,
  UnifiedSection,
  UnifiedGrid,
  UnifiedWrapper
} from '../design-system';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { DashboardQuickActions } from '../components/modern/dashboard/DashboardQuickActions';
import { DashboardRevenue } from '../components/modern/dashboard/DashboardRevenue';
import RecentActivityFeed from '../components/modern/RecentActivityFeed';
import CryptoWalletBalancesCard from '../components/CryptoWalletBalancesCard';
import {
  ResponsiveContainer,
  LineChart as RechartsLineChart,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Line,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell
} from 'recharts';

const Dashboard = memo(() => {
  const { t } = useLanguage();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // Early return for loading state - must be done BEFORE calling other hooks
  if (authLoading) {
    return <DashboardPageSkeleton />;
  }

  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  // Performance monitoring
  usePerformanceMonitor('Dashboard');

  // Redux state
  const {
    dashboardData,
    topPerformers,
    revenueTrends,
    systemPerformance,
    dataQuality,
    integrationStatus,
    securityMetrics,
    volumeAnalysis,
    clientAnalytics,
    commissionAnalytics,
    loading,
    error,
    refreshing,
    timeRange,
    activeTab,
    lastFetchTime
  } = useAppSelector(state => state.dashboard);

  // Debug logging

  // Local state for exchange rates modal
  const [showExchangeRatesModal, setShowExchangeRatesModal] = useState(false);

  // PSP Rollover data state
  const [pspRolloverData, setPspRolloverData] = useState<any>(null);
  const [pspRolloverLoading, setPspRolloverLoading] = useState(false);

  // Enhanced loading states
  const [loadingStep, setLoadingStep] = useState(0);

  // Volume chart period selection
  const [volumePeriod, setVolumePeriod] = useState<'daily' | 'weekly' | 'monthly'>('monthly');

  // Function to aggregate daily data into different periods
  const getAggregatedVolumeData = (data: any[], period: string) => {
    if (!data || data.length === 0) return [];

    if (period === 'daily') {
      return data;
    }

    if (period === 'weekly') {
      // Group by week (assuming day is day of year)
      const weeklyData: { [key: string]: { week: number; count: number; volume: number } } = {};

      data.forEach(item => {
        const date = new Date(2025, 0, item.day); // Assuming 2025
        const weekNumber = Math.ceil(item.day / 7);
        const weekKey = `Week ${weekNumber}`;

        if (!weeklyData[weekKey]) {
          weeklyData[weekKey] = { week: weekNumber, count: 0, volume: 0 };
        }
        weeklyData[weekKey].count += item.count;
        weeklyData[weekKey].volume += item.volume;
      });

      return Object.values(weeklyData).sort((a, b) => a.week - b.week);
    }

    if (period === 'monthly') {
      // Group by month
      const monthlyData: { [key: string]: { month: string; count: number; volume: number } } = {};

      data.forEach(item => {
        const date = new Date(2025, 0, item.day); // Assuming 2025
        const monthKey = date.toLocaleDateString('en-US', { month: 'short' });

        if (!monthlyData[monthKey]) {
          monthlyData[monthKey] = { month: monthKey, count: 0, volume: 0 };
        }
        monthlyData[monthKey].count += item.count;
        monthlyData[monthKey].volume += item.volume;
      });

      return Object.values(monthlyData);
    }

    return data;
  };
  const loadingSteps = [
    'Initializing dashboard...',
    'Loading financial data...',
    'Fetching analytics...',
    'Preparing charts...',
    'Finalizing display...'
  ];

  // Exchange Rates Integration
  const currentDate = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const { rates, loading: ratesLoading, error: ratesError, refreshRates } = useExchangeRates(currentDate);

  // Show exchange rate notifications
  useEffect(() => {
    if (ratesError && !ratesLoading) {
      console.warn('Exchange Rate Error:', ratesError);
    }
  }, [ratesError, ratesLoading]);

  useEffect(() => {
    if (rates && Object.keys(rates).length > 0 && !ratesLoading && !ratesError) {
      const rateValues = Object.values(rates);
      if (rateValues.length > 0) {
        const currentRate = rateValues[0];
        const rateAge = new Date().getTime() - new Date(currentRate.updated_at).getTime();
        const ageInMinutes = Math.floor(rateAge / (1000 * 60));

        if (ageInMinutes > 30) {
          console.warn('Exchange Rates Warning:', `Currency rates are ${ageInMinutes} minutes old. Consider refreshing.`);
        }
      }
    }
  }, [rates, ratesLoading, ratesError]);

  const CACHE_DURATION = 60000; // 1 minute cache

  // Fetch PSP rollover data
  const fetchPspRolloverData = useCallback(async () => {
    try {
      setPspRolloverLoading(true);

      const response = await fetch('/api/v1/analytics/psp-rollover-summary', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setPspRolloverData(data.data);
          // Log success message if we have data
          if (data.data?.psps?.length > 0) {

          } else {

          }
        } else {
          console.error('❌ Failed to fetch PSP rollover data:', data.error);
        }
      } else {
        const errorText = await response.text();
        console.error('❌ Failed to fetch PSP rollover data:', response.statusText);
        console.error('❌ Error response body:', errorText);
      }
    } catch (error) {
      console.error('❌ Error fetching PSP rollover data:', error);
      console.error('❌ Error details:', error instanceof Error ? error.message : String(error));
    } finally {
      setPspRolloverLoading(false);
    }
  }, [showUniqueSuccess, showUniqueInfo, showUniqueError]);

  // Memoized handlers
  const handleFetchDashboardData = useCallback(async (forceRefresh = false) => {
    try {
      const now = Date.now();

      // Check if we need to fetch new data
      if (!forceRefresh && (now - lastFetchTime) < CACHE_DURATION) {

        return;
      }

      // OPTIMIZED: Reduced loading steps and delays for faster loading
      setLoadingStep(1);

      // Fetch all essential data in ONE consolidated call
      await dispatch(fetchDashboardData(timeRange));

      setLoadingStep(2);

      // Fetch PSP rollover data in parallel (don't wait for it)
      fetchPspRolloverData();

      setLoadingStep(3);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  }, [dispatch, timeRange, lastFetchTime, fetchPspRolloverData]);

  const handleRefresh = useCallback(async () => {
    try {

      dispatch(setRefreshing(true));
      await handleFetchDashboardData(true);

    } catch (error) {
      console.error('❌ Refresh Failed:', 'Failed to refresh dashboard data');
    } finally {
      dispatch(setRefreshing(false));
    }
  }, [dispatch, handleFetchDashboardData]);

  const handleTabChange = useCallback((tab: 'overview' | 'analytics' | 'performance' | 'monitoring' | 'financial') => {
    dispatch(setActiveTab(tab));
  }, [dispatch]);

  const handleTimeRangeChange = useCallback((range: string) => {
    dispatch(setTimeRange(range));
  }, [dispatch]);

  const handleExchangeRatesRefresh = useCallback(async () => {
    try {

      const now = new Date();
      const currentDate = now.getFullYear() + '-' +
        String(now.getMonth() + 1).padStart(2, '0') + '-' +
        String(now.getDate()).padStart(2, '0');

      const success = await refreshRates({ date: currentDate });

      if (success) {

      } else {
        console.error('❌ Refresh Failed:', 'Failed to update exchange rates. Please try again.');
      }
    } catch (error) {
      console.error('❌ Refresh Error:', 'An error occurred while refreshing exchange rates');
    }
  }, [refreshRates]);

  const handleViewAllRates = useCallback(() => {
    setShowExchangeRatesModal(true);
  }, []);

  const handleCloseRatesModal = useCallback(() => {
    setShowExchangeRatesModal(false);
  }, []);

  // Initial data fetch on component mount - OPTIMIZED
  useEffect(() => {

    if (isAuthenticated && !authLoading) {
      handleFetchDashboardData(true);
      fetchPspRolloverData();
    }
  }, [isAuthenticated, authLoading]); // Only depend on auth state

  const handleClearError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  // View Details handlers
  const handleViewRevenueDetails = useCallback(() => {

    navigate('/revenue-analytics');
  }, [navigate]);

  const handleViewVolumeDetails = useCallback(() => {

    navigate('/analytics');
  }, [navigate]);

  const handleViewClientDetails = useCallback(() => {

    navigate('/clients');
  }, [navigate]);

  const handleViewTransactionDetails = useCallback(() => {

    navigate('/transactions');
  }, [navigate]);

  // Quick Actions handlers
  const handleQuickAction = useCallback((action: string, path: string) => {
    try {
      navigate(path);
    } catch (error) {
      console.error(`Navigation error for ${action}:`, error);
    }
  }, [navigate]);

  // Memoized utility functions
  const formatCurrency = useCallback((amount: number, currency: string = '₺') => {
    // Map internal currency codes to valid ISO 4217 currency codes
    const CURRENCY_MAP: { [key: string]: string } = {
      '₺': 'TRY',  // Turkish Lira symbol -> ISO code
      '$': 'USD',  // US Dollar symbol
      '€': 'EUR',  // Euro symbol  
      '£': 'GBP',  // British Pound symbol
      // Legacy support
      'TL': 'TRY', // Turkish Lira legacy -> ISO code
      'TRY': 'TRY', // Already correct
      'USD': 'USD',
      'EUR': 'EUR',
      'GBP': 'GBP',
    };

    const validCurrency = CURRENCY_MAP[currency] || currency;

    try {
      // Use ISO code for validation but show preferred symbol
      const formatted = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: validCurrency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(amount);

      // Replace currency codes with preferred symbols [[memory:5971629]]
      return formatted
        .replace(/TRY/g, '₺')
        .replace(/USD/g, '$')
        .replace(/EUR/g, '€')
        .replace(/GBP/g, '£');
    } catch (error) {
      // Fallback formatting if currency code is invalid
      console.warn(`Invalid currency code: ${currency}, using fallback formatting`);
      return `${currency}${amount.toLocaleString()}`;
    }
  }, []);

  const formatNumber = useCallback((num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  }, []);

  // Memoized top performers data
  const topPerformersData = useMemo(() => {
    if (!topPerformers) return null;

    return {
      volumeLeaders: {
        title: t('dashboard.top_5_by_volume'),
        description: t('dashboard.highest_deposit_volume'),
        data: topPerformers.volume_leaders,
        icon: <BarChart3 className='h-4 w-4 text-white' />,
        iconBgColor: 'bg-gray-600',
        showVolume: true
      },
      countLeaders: {
        title: t('dashboard.top_5_by_count'),
        description: t('dashboard.most_active_transaction'),
        data: topPerformers.count_leaders,
        icon: <Activity className='h-4 w-4 text-white' />,
        iconBgColor: 'bg-green-600',
        showVolume: false
      }
    };
  }, [topPerformers, t]);

  // REMOVED: Redundant useEffect - data fetching is now handled in the initial mount effect above

  // OPTIMIZED: Commission analytics now comes from consolidated endpoint
  // No need for separate fetch - it's included in fetchDashboardData above
  // useEffect(() => {
  //   if (isAuthenticated && !authLoading) {
  //     dispatch(fetchCommissionAnalytics(timeRange));
  //   }
  // }, [isAuthenticated, authLoading, timeRange, dispatch]);

  // Refresh dashboard data when time range changes - OPTIMIZED
  useEffect(() => {
    if (isAuthenticated && !authLoading) {

      handleFetchDashboardData(true); // Force refresh for time range changes
    }
  }, [timeRange]); // Only depend on timeRange, auth checks handled above

  // Listen for transaction updates to automatically refresh dashboard data
  useEffect(() => {
    const handleTransactionsUpdate = (event: any) => {
      // Refresh dashboard data when transactions are updated
      if (isAuthenticated && !authLoading) {
        handleFetchDashboardData();
      }
    };

    // Add event listener
    window.addEventListener('transactionsUpdated', handleTransactionsUpdate);

    // Cleanup
    return () => {
      window.removeEventListener('transactionsUpdated', handleTransactionsUpdate);
    };
  }, [isAuthenticated, authLoading, handleFetchDashboardData]);

  // Auto-refresh exchange rates every 15 minutes
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      const interval = setInterval(() => {
        const currentDate = new Date().toISOString().slice(0, 10);
        refreshRates({ date: currentDate });
      }, 900000);

      return () => clearInterval(interval);
    }
    return undefined;
  }, [isAuthenticated, authLoading, refreshRates]);

  return (
    <UnifiedWrapper variant="container" spacing="xl" padding="xl">
      {/* Enhanced Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">{t('dashboard.title')}</h1>
            <p className="text-muted-foreground mt-1">{t('dashboard.description')}</p>
          </div>
          <div className='flex items-center gap-3'>
            <UnifiedButton
              onClick={handleRefresh}
              disabled={refreshing}
              variant="secondary"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? t('common.refreshing') : t('common.refresh')}
            </UnifiedButton>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <DashboardTabNavigation
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onRefresh={handleRefresh}
        refreshing={refreshing}
      />

      {/* Progressive Loading State */}
      {refreshing && (
        <div className="my-6">
          <ProgressiveLoader
            steps={loadingSteps}
            currentStep={loadingStep}
          />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="my-6">
          <ErrorState
            title={t('dashboard.error_loading_dashboard')}
            message={error}
            onRetry={() => {
              handleClearError();
              handleFetchDashboardData(true);
            }}
            variant="error"
          />
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">

          {/* Enhanced Stats Cards */}
          {dashboardData && (
            <UnifiedSection title={t('dashboard.key_metrics')} description={t('dashboard.business_overview')}>
              <UnifiedGrid cols={4} gap="lg">
                <MetricCard
                  title={t('dashboard.net_cash')}
                  value={formatCurrency((dashboardData.summary as any).net_cash || dashboardData.summary.total_net, '₺')}
                  icon={DollarSign}
                  color="gray"
                  subtitle={t('dashboard.all_time_net_cash')}
                  animated={true}
                  animationDuration={1200}
                />

                <MetricCard
                  title={t('dashboard.total_transactions')}
                  value={formatNumber(dashboardData.summary.transaction_count)}
                  icon={CreditCard}
                  color="green"
                  subtitle={t('dashboard.total_trans')}
                  animated={true}
                  animationDuration={1200}
                />

                <MetricCard
                  title={t('dashboard.active_clients')}
                  value={formatNumber(dashboardData.summary.active_clients)}
                  icon={Users}
                  color="purple"
                  subtitle={t('dashboard.active_cli')}
                  animated={true}
                  animationDuration={1200}
                />

                <MetricCard
                  title={t('dashboard.total_commissions')}
                  value={formatCurrency(dashboardData.summary.total_commission, '₺')}
                  icon={TrendingUp}
                  color="teal"
                  subtitle={t('dashboard.commission_earned')}
                  animated={true}
                  animationDuration={1200}
                />
              </div>
            </UnifiedSection>
          )}

          {/* Revenue Analytics */}
          <UnifiedSection title={t('dashboard.revenue_analytics')} description={t('dashboard.company_revenue_breakdown')}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <MetricCard
                title={t('dashboard.daily_revenue')}
                value={formatCurrency((dashboardData?.summary as any)?.daily_revenue || 0, '₺')}
                icon={Calendar}
                color="indigo"
                subtitle={t('dashboard.today_revenue')}
                animated={true}
                animationDuration={1200}
              />

              <MetricCard
                title={t('dashboard.weekly_revenue')}
                value={formatCurrency((dashboardData?.summary as any)?.weekly_revenue || 0, '₺')}
                icon={TrendingUp}
                color="green"
                subtitle={t('dashboard.this_week_revenue')}
                animated={true}
                animationDuration={1200}
              />

              <MetricCard
                title={t('dashboard.monthly_revenue')}
                value={formatCurrency((dashboardData?.summary as any)?.monthly_revenue || 0, '₺')}
                icon={BarChart3}
                color="purple"
                subtitle={t('dashboard.this_month_revenue')}
                animated={true}
                animationDuration={1200}
              />

              <MetricCard
                title={t('dashboard.annual_revenue')}
                value={formatCurrency((dashboardData?.summary as any)?.annual_revenue || 0, '₺')}
                icon={DollarSign}
                color="orange"
                subtitle={t('dashboard.this_year_revenue')}
                animated={true}
                animationDuration={1200}
              />
            </div>

            {/* Revenue Trend Chart */}
            <div className="mt-6">
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">{t('dashboard.revenue_trend')}</h3>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <TrendingUp className="h-4 w-4" />
                    <span>{t('dashboard.last_30_days')}</span>
                  </div>
                </div>
                <div className="h-64">
                  {(dashboardData as any)?.revenue_trends && (dashboardData as any).revenue_trends.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsLineChart data={(dashboardData as any).revenue_trends}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis
                          dataKey="date"
                          stroke="#6b7280"
                          fontSize={12}
                          tickLine={false}
                          axisLine={false}
                        />
                        <YAxis
                          stroke="#6b7280"
                          fontSize={12}
                          tickLine={false}
                          axisLine={false}
                          tickFormatter={(value) => `₺${(value / 1000).toFixed(0)}k`}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                          }}
                          formatter={(value: any) => [formatCurrency(value, '₺'), 'Revenue']}
                          labelFormatter={(label) => `Date: ${label}`}
                        />
                        <Line
                          type="monotone"
                          dataKey="revenue"
                          stroke="#3b82f6"
                          strokeWidth={3}
                          dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                          activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
                        />
                      </RechartsLineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      <div className="text-center">
                        <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                        <p className="text-lg font-medium">{t('dashboard.no_revenue_data')}</p>
                        <p className="text-sm text-gray-400 mt-2">{t('dashboard.revenue_trends_appear_here')}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </UnifiedSection>

          {/* Quick Actions */}

          <DashboardQuickActions
            onQuickAction={handleQuickAction}
            onRefresh={handleRefresh}
            refreshing={refreshing}
          />

          {/* Exchange Rates Widget */}
          {/* Exchange Rates Widget */}
          <UnifiedSection title={t('dashboard.exchange_rates')} description={t('dashboard.current_rates')}>
            <ExchangeRatesWidget
              rates={rates}
              loading={ratesLoading}
              error={ratesError}
              onRefresh={handleExchangeRatesRefresh}
              onViewAll={handleViewAllRates}
              formatCurrency={formatCurrency}
            />
          </UnifiedSection>

          {/* Top Performers */}
          {/* Top Performers */}
          <UnifiedSection title={t('dashboard.top_performers')} description={t('dashboard.best_performers')}>
            {topPerformersData ? (
              <UnifiedGrid cols={2} gap="lg">
                <TopPerformersCard
                  {...topPerformersData.volumeLeaders}
                  formatCurrency={formatCurrency}
                />
                <TopPerformersCard
                  {...topPerformersData.countLeaders}
                  formatCurrency={formatCurrency}
                />
              </UnifiedGrid>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <BarChart3 className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">{t('dashboard.loading_top_performers')}</p>
                <p className="text-sm text-gray-400 mt-2">{t('dashboard.please_wait_fetch_data')}</p>
              </div>
            )}
          </UnifiedSection>

          {/* PSP Rollover Cards */}
          {/* PSP Rollover Cards */}
          <UnifiedSection title={t('dashboard.psp_rollover_status')} description={t('dashboard.individual_psp_rollover')}>
            <div className='flex items-center justify-between mb-6'>
              <div className="flex items-center gap-2">
                <UnifiedButton
                  variant="outline"
                  size="sm"
                  onClick={fetchPspRolloverData}
                  disabled={pspRolloverLoading}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className={`h-4 w-4 ${pspRolloverLoading ? 'animate-spin' : ''}`} />
                  {t('common.refresh')}
                </UnifiedButton>
                {pspRolloverData?.psps?.length > 0 && (
                  <span className="text-xs text-green-600 font-medium">
                    ✓ {pspRolloverData.psps.length} {t('dashboard.psps_loaded')}
                  </span>
                )}
              </div>
            </div>

{pspRolloverLoading ? (
              <div className='text-center py-12 text-gray-500'>
                <RefreshCw className='h-12 w-12 mx-auto mb-4 text-gray-300 animate-spin' />
                <p className='text-lg'>{t('dashboard.loading_psp_rollover')}</p>
                <p className='text-sm text-gray-400 mt-2'>{t('dashboard.please_wait_fetch_data')}</p>
              </div>
            ) : pspRolloverData?.psps?.length > 0 ? (
              <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'>
                {pspRolloverData.psps.map((psp: any, index: number) => {
                  const isPositive = psp.total_rollover > 0;
                  const isNegative = psp.total_rollover < 0;
                  const isZero = psp.total_rollover === 0;

                  return (
                    <div
                      key={psp.psp}
                      className={`bg-white rounded-xl shadow-sm border-2 p-6 hover:shadow-md transition-all duration-200 ${isPositive ? 'border-red-200 hover:border-red-300' :
                        isNegative ? 'border-green-200 hover:border-green-300' :
                          'border-gray-200 hover:border-gray-300'
                        }`}
                    >
                      <div className='flex items-start justify-between mb-4'>
                        <div className='flex items-center gap-3'>
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isPositive ? 'bg-red-100' : isNegative ? 'bg-green-100' : 'bg-gray-100'
                            }`}>
                            <span className={`text-sm font-bold ${isPositive ? 'text-red-700' : isNegative ? 'text-green-700' : 'text-gray-700'
                              }`}>
                              {index + 1}
                            </span>
                          </div>
                          <div>
                            <h3 className='font-semibold text-gray-900 text-lg'>{psp.psp || t('dashboard.unknown_psp')}</h3>
                            <p className='text-sm text-gray-500'>{psp.transaction_count} {t('dashboard.transactions')}</p>
                          </div>
                        </div>
                      </div>

                      <div className='space-y-3'>
                        <div className='text-center'>
                          <div className={`text-2xl font-bold mb-1 ${isPositive ? 'text-red-600' : isNegative ? 'text-green-600' : 'text-gray-600'
                            }`}>
                            {formatCurrency(psp.total_rollover, '₺')}
                          </div>
                          <p className={`text-sm font-medium ${isPositive ? 'text-red-700' : isNegative ? 'text-green-700' : 'text-gray-700'
                            }`}>
                            {isPositive ? t('dashboard.amount_owed') : isNegative ? t('dashboard.credit_balance') : t('dashboard.settled')}
                          </p>
                        </div>

                        <div className='pt-3 border-t border-gray-100'>
                          <div className='grid grid-cols-2 gap-4 text-xs'>
                            <div>
                              <p className='text-gray-500'>{t('dashboard.net_amount')}</p>
                              <p className='font-medium text-gray-900'>{formatCurrency(psp.total_net, '₺')}</p>
                            </div>
                            <div>
                              <p className='text-gray-500'>{t('dashboard.allocated')}</p>
                              <p className='font-medium text-gray-900'>{formatCurrency(psp.total_allocations, '₺')}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className='text-center py-12 text-gray-500'>
                <CreditCard className='h-16 w-16 mx-auto mb-4 text-gray-300' />
                <p className='text-lg font-medium'>{t('dashboard.no_psp_rollover_data')}</p>
                <p className='text-sm text-gray-400 mt-2'>{t('dashboard.loading_psp_or_no_trans')}</p>
                <div className='mt-4'>
                  <UnifiedButton
                    variant="outline"
                    size="sm"
                    onClick={fetchPspRolloverData}
                    disabled={pspRolloverLoading}
                    className="flex items-center gap-2 mx-auto"
                  >
                    <RefreshCw className={`h-4 w-4 ${pspRolloverLoading ? 'animate-spin' : ''}`} />
                    {pspRolloverLoading ? t('common.loading') : t('dashboard.retry')}
                  </UnifiedButton>
                </div>
              </div>
            )}
          </UnifiedSection>

{/* Analytics Tab Content */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              {/* Revenue Trends Chart */}
              {/* Revenue Trends Chart */}
              {revenueTrends && (
                <DashboardRevenue
                  revenueTrends={revenueTrends}
                  refreshing={refreshing}
                  onRefresh={() => handleRefresh()}
                  onViewDetails={handleViewRevenueDetails}
                  formatCurrency={formatCurrency}
                />
              )}

              {/* Client Analytics */}
              {clientAnalytics && (
                <UnifiedSection title={t('dashboard.client_analytics')} description={t('dashboard.client_performance_commission')}>
                  <UnifiedGrid cols={2} gap="lg">
                    <div className='bg-white rounded-2xl shadow-sm border border-gray-200 p-6'>
                      <h3 className='text-lg font-semibold text-gray-900 mb-4'>{t('dashboard.top_clients_by_volume')}</h3>
                      <div className='space-y-3'>
                        {clientAnalytics.data.client_analytics?.slice(0, 5).map((client: any, index: number) => (
                          <div key={client.client_name} className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'>
                            <div className='flex items-center gap-3'>
                              <div className='w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center'>
                                <span className='text-sm font-medium text-gray-700'>{index + 1}</span>
                              </div>
                              <div>
                                <p className='font-medium text-gray-900'>{client.client_name}</p>
                                <p className='text-sm text-gray-500'>{client.transaction_count} transactions</p>
                              </div>
                            </div>
                            <span className='font-semibold text-gray-900'>{formatCurrency(client.total_volume, '₺')}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className='bg-white rounded-2xl shadow-sm border border-gray-200 p-6'>
                      <h3 className='text-lg font-semibold text-gray-900 mb-4'>{t('dashboard.psp_performance_analysis')}</h3>
                      <div className='space-y-3'>
                        {commissionAnalytics?.data.psp_commission?.slice(0, 5).map((psp: any, index: number) => (
                          <div key={psp.psp} className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'>
                            <div className='flex items-center gap-3'>
                              <div className='w-8 h-8 bg-green-100 rounded-full flex items-center justify-center'>
                                <span className='text-sm font-medium text-green-700'>{index + 1}</span>
                              </div>
                              <div>
                                <p className='font-medium text-gray-900'>{psp.psp || t('dashboard.unknown_psp')}</p>
                                <p className='text-sm text-gray-500'>{psp.transaction_count} {t('dashboard.transactions')}</p>
                              </div>
                            </div>
                            <div className='text-right'>
                              <span className='font-semibold text-gray-900'>{formatCurrency(psp.total_volume, '₺')}</span>
                              <p className='text-xs text-gray-500'>{psp.commission_rate?.toFixed(2)}% {t('dashboard.rate')}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </UnifiedGrid>
                </UnifiedSection>
              )}
            </div>
          )}

          {/* Performance Tab Content */}
          {
            activeTab === 'performance' && (
              <div className="space-y-6">
                {/* System Performance Metrics */}
                {systemPerformance && (
                  <UnifiedSection title={t('dashboard.system_performance')} description={t('dashboard.real_time_monitoring')}>
                    <UnifiedGrid cols={3} gap="lg">
                      <MetricCard
                        title={t('dashboard.cpu_usage')}
                        value={`${systemPerformance.cpu_usage?.toFixed(1)}%`}
                        subtitle={t('dashboard.system_performance_metric')}
                        icon={Server}
                        color="gray"
                        animated={true}
                        animationDuration={1000}
                      />

                      <MetricCard
                        title={t('dashboard.memory_usage')}
                        value={`${systemPerformance.memory_usage?.toFixed(1)}%`}
                        subtitle={t('dashboard.ram_utilization')}
                        icon={HardDrive}
                        color="green"
                        animated={true}
                        animationDuration={1000}
                      />

                      <MetricCard
                        title={t('dashboard.system_health')}
                        value={systemPerformance.system_health === 'healthy' ? t('dashboard.healthy') : systemPerformance.system_health === 'warning' ? t('dashboard.warning') : t('dashboard.critical')}
                        subtitle={t('dashboard.overall_status')}
                        icon={Network}
                        color={systemPerformance.system_health === 'healthy' ? 'green' : systemPerformance.system_health === 'warning' ? 'orange' : 'red'}
                        animated={false}
                      />
                    </UnifiedGrid>
                  </UnifiedSection>
                )}

                {/* Data Quality Metrics */}
                {dataQuality && (
                  <UnifiedSection title={t('dashboard.data_quality_metrics')} description={t('dashboard.comprehensive_data_quality')}>
                    <UnifiedGrid cols={4} gap="lg">
                      <MetricCard
                        title={t('dashboard.client_completeness')}
                        value={`${dataQuality.client_completeness?.toFixed(1)}%`}
                        icon={Users}
                        color="gray"
                        subtitle={t('dashboard.data_completeness')}
                        animated={true}
                        animationDuration={1000}
                      />

                      <MetricCard
                        title={t('dashboard.amount_completeness')}
                        value={`${dataQuality.amount_completeness?.toFixed(1)}%`}
                        icon={DollarSign}
                        color="green"
                        subtitle={t('dashboard.financial_data')}
                        animated={true}
                        animationDuration={1000}
                      />

                      <MetricCard
                        title={t('dashboard.date_completeness')}
                        value={`${dataQuality.date_completeness?.toFixed(1)}%`}
                        icon={Calendar}
                        color="purple"
                        subtitle={t('dashboard.date_accuracy')}
                        animated={true}
                        animationDuration={1000}
                      />

                      <MetricCard
                        title={t('dashboard.overall_score')}
                        value={`${dataQuality.overall_quality_score?.toFixed(1)}%`}
                        icon={Award}
                        color="orange"
                        subtitle={t('dashboard.quality_rating')}
                        animated={true}
                        animationDuration={1000}
                      />
                    </UnifiedGrid>
                  </UnifiedSection>
                )}
              </div>
            )
          }

          {/* Monitoring Tab Content */}
          {
            activeTab === 'monitoring' && (
              <div className="space-y-6">
                {/* Security Metrics */}
                {securityMetrics && (
                  <UnifiedSection title={t('dashboard.security_monitoring')} description={t('dashboard.security_integration_status')}>
                    <UnifiedGrid cols={2} gap="lg">
                      {/* Security Status */}
                      <MetricCard
                        title={t('dashboard.security_status')}
                        value={securityMetrics.failed_logins.today}
                        subtitle={`${securityMetrics.suspicious_activities.total_alerts} ${t('dashboard.alerts')}, ${securityMetrics.session_management.active_sessions} ${t('dashboard.sessions')}`}
                        icon={Shield}
                        color="red"
                        animated={true}
                        animationDuration={1000}
                      />

                      {/* Integration Status */}
                      <MetricCard
                        title={t('dashboard.integration_status')}
                        value={integrationStatus ? (integrationStatus.bank_connections.status === 'connected' && integrationStatus.psp_connections.status === 'connected' ? t('dashboard.all_connected') : t('dashboard.issues_detected')) : t('dashboard.unknown')}
                        subtitle={integrationStatus ? `${t('dashboard.bank')}: ${integrationStatus.bank_connections.status}, ${t('dashboard.psp')}: ${integrationStatus.psp_connections.status}` : t('dashboard.status_unavailable')}
                        icon={ActivityIcon}
                        color={integrationStatus && integrationStatus.bank_connections.status === 'connected' && integrationStatus.psp_connections.status === 'connected' ? 'green' : 'orange'}
                        animated={false}
                      />
                    </UnifiedGrid>
                  </UnifiedSection>
                )}

                {/* Volume Analysis */}
                {volumeAnalysis && (
                  <UnifiedSection
                    title={t('dashboard.transaction_volume_analysis')}
                    description={volumePeriod === 'daily' ? t('dashboard.daily_transaction_volume') :
                      volumePeriod === 'weekly' ? 'Weekly Transaction Volume' :
                        t('dashboard.monthly_transaction_volume')}
                  >
                    <div className='business-chart'>
                      <div className='business-chart-header'>
                        <div>
                          <h3 className='business-chart-title'>{t('dashboard.transaction_volume_analysis')}</h3>
                          <p className='business-chart-subtitle'>
                            {volumePeriod === 'daily' ? t('dashboard.daily_transaction_volume') :
                              volumePeriod === 'weekly' ? 'Weekly Transaction Volume' :
                                t('dashboard.monthly_transaction_volume')}
                          </p>
                        </div>
                        <div className='business-chart-actions'>
                          {/* Period Selection Buttons */}
                          <div className="flex items-center gap-1 mr-4">
                            <UnifiedButton
                              variant={volumePeriod === 'daily' ? 'primary' : 'outline'}
                              size="sm"
                              onClick={() => setVolumePeriod('daily')}
                              className="px-3"
                            >
                              Daily
                            </UnifiedButton>
                            <UnifiedButton
                              variant={volumePeriod === 'weekly' ? 'primary' : 'outline'}
                              size="sm"
                              onClick={() => setVolumePeriod('weekly')}
                              className="px-3"
                            >
                              Weekly
                            </UnifiedButton>
                            <UnifiedButton
                              variant={volumePeriod === 'monthly' ? 'primary' : 'outline'}
                              size="sm"
                              onClick={() => setVolumePeriod('monthly')}
                              className="px-3"
                            >
                              Monthly
                            </UnifiedButton>
                          </div>
                          <UnifiedButton
                            variant="outline"
                            size="sm"
                            onClick={() => handleRefresh()}
                            disabled={refreshing}
                            className="flex items-center gap-2"
                          >
                            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                            {refreshing ? t('common.refreshing') : t('common.refresh')}
                          </UnifiedButton>
                          <UnifiedButton
                            variant="outline"
                            size="sm"
                            onClick={handleViewVolumeDetails}
                          >
                            <Eye className='w-4 h-4 mr-2' />
                            {t('dashboard.view_details')}
                          </UnifiedButton>
                        </div>
                      </div>
                      <div className='h-80'>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={getAggregatedVolumeData(volumeAnalysis.data.daily_volume, volumePeriod)} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                            <defs>
                              <linearGradient id="volumeBarGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#10B981" stopOpacity={1} />
                                <stop offset="25%" stopColor="#34D399" stopOpacity={0.95} />
                                <stop offset="50%" stopColor="#6EE7B7" stopOpacity={0.9} />
                                <stop offset="75%" stopColor="#A7F3D0" stopOpacity={0.85} />
                                <stop offset="100%" stopColor="#D1FAE5" stopOpacity={0.8} />
                              </linearGradient>
                              <filter id="volumeBarShadow" x="-50%" y="-50%" width="200%" height="200%">
                                <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#10B981" floodOpacity="0.15" />
                              </filter>
                            </defs>
                            <CartesianGrid
                              strokeDasharray="1 1"
                              stroke="#94a3b8"
                              strokeWidth={1}
                              vertical={true}
                              horizontal={true}
                              opacity={1.0}
                            />
                            <XAxis
                              dataKey={volumePeriod === 'daily' ? 'day' : volumePeriod === 'weekly' ? 'week' : 'month'}
                              stroke="#475569"
                              fontSize={12}
                              fontWeight={600}
                              tickLine={false}
                              axisLine={{ stroke: '#e2e8f0', strokeWidth: 1 }}
                              tick={{ fill: '#475569' }}
                              interval="preserveStartEnd"
                            />
                            <YAxis
                              stroke="#475569"
                              fontSize={12}
                              fontWeight={600}
                              tickLine={false}
                              axisLine={{ stroke: '#e2e8f0', strokeWidth: 1 }}
                              tick={{ fill: '#475569' }}
                              tickFormatter={(value) => formatCurrency(value, '₺')}
                              width={80}
                            />
                            <Tooltip
                              content={({ active, payload, label }) => {
                                if (active && payload && payload.length) {
                                  const data = payload[0].payload;
                                  // Parse the date properly - it might be in YYYY-MM-DD format
                                  const dateStr = data.day;
                                  const date = new Date(dateStr + 'T00:00:00'); // Add time to avoid timezone issues

                                  return (
                                    <div className="bg-white border border-slate-200 rounded-xl shadow-xl p-4 min-w-[200px] backdrop-blur-sm">
                                      <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                          <Calendar className="h-4 w-4 text-slate-500" />
                                          <span className="font-semibold text-slate-900">
                                            {date.toLocaleDateString('en-US', {
                                              weekday: 'long',
                                              year: 'numeric',
                                              month: 'long',
                                              day: 'numeric'
                                            })}
                                          </span>
                                        </div>

                                        <div className="border-t border-slate-100 pt-2 space-y-1">
                                          <div className="flex justify-between items-center">
                                            <span className="text-sm text-slate-600">{t('dashboard.volume')}:</span>
                                            <span className="font-semibold text-green-600">
                                              {formatCurrency(data.volume || 0, '₺')}
                                            </span>
                                          </div>

                                          <div className="flex justify-between items-center">
                                            <span className="text-sm text-slate-600">{t('dashboard.transactions')}:</span>
                                            <span className="text-sm font-medium text-slate-700">
                                              {data.transaction_count || 0}
                                            </span>
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                }
                                return null;
                              }}
                              cursor={{ fill: 'rgba(16, 185, 129, 0.05)' }}
                            />
                            <Bar
                              dataKey="volume"
                              fill="url(#volumeBarGradient)"
                              radius={[6, 6, 0, 0]}
                              stroke="none"
                              filter="url(#volumeBarShadow)"
                              style={{
                                filter: 'drop-shadow(0 4px 8px rgba(16, 185, 129, 0.15))',
                              }}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                      <div className='business-chart-legend'>
                        <div className='business-chart-legend-item'>
                          <div className='business-chart-legend-color bg-green-500'></div>
                          <span className='business-chart-legend-label'>{t('dashboard.volume')}</span>
                          <span className='business-chart-legend-value'>₺{volumeAnalysis.data.insights.total_volume?.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  </UnifiedSection>
                )}

                {/* Recent Activity */}
                <UnifiedSection title={t('dashboard.recent_activity')} description={t('dashboard.recent_transaction_activity')}>
                  <RecentActivityFeed 
                    limit={5}
                    onClickTransaction={(transactionId, transaction) => {
                      // Navigate to clients page with client filter to show client information (same as Transactions table in Clients section)
                      if (transaction?.client_name) {
                        navigate(`/clients?tab=transactions&client=${encodeURIComponent(transaction.client_name)}&highlight=${transactionId}`);
                      } else {
                        navigate(`/clients?tab=transactions&highlight=${transactionId}`);
                      }
                    }}
                  />
                </UnifiedSection>

                {/* Crypto Wallet Balances - Between Recent Activity and Revenue */}
                <CryptoWalletBalancesCard />

              </div>
            )
          }

          {/* Financial Analytics Tab Content */}
          {
            activeTab === 'financial' && (
              <div className="space-y-6">
                {/* Financial Summary */}
                {dashboardData && (
                  <UnifiedSection title={t('dashboard.financial_overview')} description={t('dashboard.comprehensive_financial_metrics')}>
                    <UnifiedGrid cols={4} gap="lg">
                      {/* Net Cash */}
                      <MetricCard
                        title={t('dashboard.net_cash')}
                        value={formatCurrency((dashboardData.summary as any).net_cash || dashboardData.summary.total_net, '₺')}
                        subtitle={t('dashboard.all_time')}
                        icon={TrendingUp}
                        color="green"
                        animated={true}
                        animationDuration={1200}
                      />

                      {/* Total Commission */}
                      <MetricCard
                        title={t('dashboard.total_commission')}
                        value={formatCurrency(dashboardData.summary.total_commission, '₺')}
                        subtitle={t('dashboard.earned')}
                        icon={DollarSign}
                        color="gray"
                        animated={true}
                        animationDuration={1200}
                      />

                      {/* Active Clients */}
                      <MetricCard
                        title={t('dashboard.active_clients')}
                        value={dashboardData.summary.active_clients}
                        subtitle={t('dashboard.this_month')}
                        icon={Users}
                        color="purple"
                        animated={true}
                        animationDuration={1200}
                      />

                      {/* Total Transactions */}
                      <MetricCard
                        title={t('dashboard.total_transactions')}
                        value={formatNumber(dashboardData.summary.transaction_count)}
                        subtitle={t('dashboard.all_time')}
                        icon={CreditCard}
                        color="orange"
                        animated={true}
                animationDuration={1200}
              />
            </div>
                  </UnifiedSection>
                )}

                {/* Commission Analysis Chart */}
                {commissionAnalytics && (
                  <UnifiedSection title={t('dashboard.psp_performance_analysis')} description={t('dashboard.client_performance_commission')}>
                    <div className='bg-white rounded-2xl shadow-sm border border-gray-200 p-6'>
                      <div className='flex items-center justify-between mb-4'>
                        <h3 className='text-lg font-semibold text-gray-900'>{t('dashboard.psp_volume_distribution')}</h3>
                        <UnifiedButton
                          variant="outline"
                          size="sm"
                          onClick={() => handleRefresh()}
                          disabled={refreshing}
                          className="flex items-center gap-2"
                        >
                          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                          {refreshing ? t('common.refreshing') : t('common.refresh')}
                        </UnifiedButton>
                      </div>
                      <div className='h-80'>
                        <ResponsiveContainer width="100%" height="100%">
                          <RechartsPieChart>
                            <Pie
                              data={commissionAnalytics.data.psp_commission?.map((item: any, index: number) => ({
                                name: item.psp || 'Unknown PSP',
                                value: item.total_volume,
                                fill: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]
                              }))}
                              cx="50%"
                              cy="50%"
                              outerRadius={100}
                              dataKey="value"
                              label={({ name, percent }: { name: string; percent: number }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            >
                              {commissionAnalytics.data.psp_commission?.map((entry: any, index: number) => (
                                <Cell key={`cell-${index}`} fill={['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]} />
                              ))}
                            </Pie>
                            <Tooltip formatter={(value: number) => [formatCurrency(value, '₺'), t('dashboard.commission')]} />
                          </RechartsPieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </UnifiedSection>
                )}
              </div>
            )
          }

          {/* Loading State */}
          {loading && !dashboardData && (
            <LoadingState message={t('dashboard.loading_dashboard') || 'Loading dashboard...'} />
          )}

          {/* Exchange Rates Modal */}
          {
            showExchangeRatesModal && (
              <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'>
                <div className='bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden'>
                  <div className='flex items-center justify-between p-6 border-b border-gray-200'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-gray-700 rounded-xl flex items-center justify-center shadow-sm'>
                        <Globe className='h-5 w-5 text-white' />
                      </div>
                      <div>
                        <h2 className='text-2xl font-bold text-gray-900'>{t('dashboard.exchange_rates_management')}</h2>
                        <p className='text-sm text-gray-600'>{t('dashboard.view_manage_currency_rates')}</p>
                      </div>
                    </div>
                    <UnifiedButton
                      onClick={handleCloseRatesModal}
                      variant="ghost"
                      size="sm"
                      className='p-2 text-gray-400 hover:text-gray-600'
                    >
                      <X className='h-6 w-6' />
                    </UnifiedButton>
                  </div>
                  <div className='p-6 overflow-y-auto max-h-[calc(90vh-120px)]'>
                    <ExchangeRatesDisplay
                      date={new Date().toISOString().slice(0, 10)}
                      showSource={true}
                      showQuality={true}
                      showManualOverride={true}
                    />
                  </div>
                </div>
              </div>
            )
          }
        </UnifiedWrapper >
      );
});

      Dashboard.displayName = 'Dashboard';

      export default Dashboard;
