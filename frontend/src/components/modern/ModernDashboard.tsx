/**
 * Modern Dashboard Component (Refactored)
 * Ana dashboard component - refactored ve optimize edilmiş versiyon
 * Eski: 1932 satır → Yeni: ~400 satır
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../../contexts/LanguageContext';
import { Card, CardContent, CardHeader } from '../ui/card';
import { Button } from '../ui/button';
import { FullDashboardSkeleton } from './DashboardSkeleton';
import { injectShimmerStyles } from './DashboardSkeleton';
import { RevenueChart } from './RevenueChart';
import { SummaryStatsBar } from './SummaryStatsBar';
import { DashboardHeader } from './dashboard/DashboardHeader';
import { FinancialPerformanceCard } from './dashboard/FinancialPerformanceCard';
import { lazy, Suspense } from 'react';
import { useDashboardData } from '../../hooks/useDashboardData';
import { useFinancialPerformance } from '../../hooks/useFinancialPerformance';
import { calculateQuickStats, generateFinancialBreakdown, transformChartData } from '../../utils/dashboardHelpers';
import { ExcelExportService } from '../../services/excelExportService';
import { logger } from '../../utils/logger';
import { SectionHeader } from '../ui/SectionHeader';
import { StatusIndicator } from '../ui/StatusIndicator';
import { Calendar, BarChart3, TrendingUp, LineChart } from 'lucide-react';
import type { TimeRange, ViewType, ChartPeriod, FinancialPeriodData } from '../../types/dashboard.types';

const LazyRecentActivityFeed = lazy(() =>
  import('./RecentActivityFeed').then((module) => ({ default: module.RecentActivityFeed })),
);

interface ModernDashboardProps {
  user?: {
    username?: string;
  };
}

const ModernDashboard: React.FC<ModernDashboardProps> = ({ user }) => {
  const navigate = useNavigate();
  const { t } = useLanguage();

  // Error state for component-level errors
  const [componentError, setComponentError] = useState<Error | null>(null);

  // Debug: Log component mount
  useEffect(() => {
    logger.dashboard('ModernDashboard mounted');
    return () => {
      logger.dashboard('ModernDashboard unmounted');
    };
  }, []);

  // Catch any errors during render
  useEffect(() => {
    const errorHandler = (event: ErrorEvent) => {
      logger.error('Dashboard runtime error:', event.error);
      setComponentError(event.error);
    };

    const unhandledRejectionHandler = (event: PromiseRejectionEvent) => {
      logger.error('Dashboard unhandled promise rejection:', event.reason);
      setComponentError(event.reason instanceof Error ? event.reason : new Error(String(event.reason)));
    };

    window.addEventListener('error', errorHandler);
    window.addEventListener('unhandledrejection', unhandledRejectionHandler);
    return () => {
      window.removeEventListener('error', errorHandler);
      window.removeEventListener('unhandledrejection', unhandledRejectionHandler);
    };
  }, []);

  // State management - optimized
  const [timeRange, setTimeRange] = useState<TimeRange>('all');
  const [viewType, setViewType] = useState<ViewType>('net');
  const [chartPeriod, setChartPeriod] = useState<ChartPeriod>('monthly');
  const [showZeroValues, setShowZeroValues] = useState(true);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<Date>(new Date());
  const [selectedDay, setSelectedDay] = useState<Date>(new Date());
  const [selectedDayData, setSelectedDayData] = useState<FinancialPeriodData | null>(null);
  const [selectedMonthData, setSelectedMonthData] = useState<FinancialPeriodData | null>(null);
  const [loadingDayData, setLoadingDayData] = useState(false);
  const [loadingMonthData, setLoadingMonthData] = useState(false);

  // Custom hooks - data management
  const {
    data: dashboardData,
    loading: loadingDashboard,
    error: dashboardError,
    refresh: refreshDashboard,
    lastUpdated,
  } = useDashboardData({ timeRange, viewType });

  const {
    data: financialPerformanceData,
    loading: loadingFinancial,
    error: financialError,
    refresh: refreshFinancial,
    getDayData,
    getMonthData,
  } = useFinancialPerformance({ timeRange, viewType });

  // Inject shimmer styles
  useEffect(() => {
    injectShimmerStyles();
  }, []);

  // Date navigation functions
  const goToPreviousMonth = useCallback(() => {
    const newMonth = new Date(selectedMonth);
    newMonth.setMonth(newMonth.getMonth() - 1);
    setSelectedMonth(newMonth);
  }, [selectedMonth]);

  const goToNextMonth = useCallback(() => {
    const newMonth = new Date(selectedMonth);
    newMonth.setMonth(newMonth.getMonth() + 1);
    setSelectedMonth(newMonth);
  }, [selectedMonth]);

  const isCurrentMonth = useCallback(() => {
    const now = new Date();
    return selectedMonth.getMonth() === now.getMonth() && selectedMonth.getFullYear() === now.getFullYear();
  }, [selectedMonth]);

  const goToPreviousDay = useCallback(() => {
    const newDay = new Date(selectedDay);
    newDay.setDate(newDay.getDate() - 1);
    setSelectedDay(newDay);
  }, [selectedDay]);

  const goToNextDay = useCallback(() => {
    const newDay = new Date(selectedDay);
    newDay.setDate(newDay.getDate() + 1);
    setSelectedDay(newDay);
  }, [selectedDay]);

  const isCurrentDay = useCallback(() => {
    const now = new Date();
    return (
      selectedDay.getDate() === now.getDate() &&
      selectedDay.getMonth() === now.getMonth() &&
      selectedDay.getFullYear() === now.getFullYear()
    );
  }, [selectedDay]);

  const formatMonthYear = useCallback((date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  }, []);

  const formatDayDate = useCallback((date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }, []);

  // Load selected day data
  useEffect(() => {
    const loadDayData = async () => {
      setLoadingDayData(true);
      try {
        if (isCurrentDay() && financialPerformanceData?.data) {
          // Current day: use cached data
          setSelectedDayData(financialPerformanceData.data.daily);
        } else {
          // Previous/next day: fetch from API
          const dayData = await getDayData(selectedDay);
          // Eger API'den data gelmezse, financialPerformanceData'dan fallback kullan
          if (dayData) {
            setSelectedDayData(dayData);
          } else if (financialPerformanceData?.data?.daily) {
            // Fallback: use cached daily data if available
            setSelectedDayData(financialPerformanceData.data.daily);
          } else {
            // Son fallback: empty data structure
            setSelectedDayData(null);
          }
        }
      } catch (error: any) {
        // CRITICAL FIX: Don't log ERR_EMPTY_RESPONSE as error - backend might be down
        if (error?.message?.includes('ERR_EMPTY_RESPONSE') || error?.message?.includes('Failed to fetch')) {
          logger.warn('Backend not responding for day data (non-critical)');
          // Fallback: use cached data if available
          if (financialPerformanceData?.data?.daily) {
            setSelectedDayData(financialPerformanceData.data.daily);
          } else {
            setSelectedDayData(null);
          }
        } else {
          logger.error('Error loading day data:', error);
          setSelectedDayData(null);
        }
      } finally {
        setLoadingDayData(false);
      }
    };

    loadDayData();
  }, [selectedDay, financialPerformanceData, isCurrentDay, getDayData]);

  // Load selected month data
  useEffect(() => {
    const loadMonthData = async () => {
      setLoadingMonthData(true);
      try {
        if (isCurrentMonth() && financialPerformanceData?.data) {
          // Current month: use cached data
          setSelectedMonthData(financialPerformanceData.data.monthly);
        } else {
          // Previous/next month: fetch from API
          const monthData = await getMonthData(selectedMonth);
          // Eger API'den data gelmezse, financialPerformanceData'dan fallback kullan
          if (monthData) {
            setSelectedMonthData(monthData);
          } else if (financialPerformanceData?.data?.monthly) {
            // Fallback: use cached monthly data if available
            setSelectedMonthData(financialPerformanceData.data.monthly);
          } else {
            // Son fallback: empty data structure
            setSelectedMonthData(null);
          }
        }
      } catch (error: any) {
        // CRITICAL FIX: Don't log ERR_EMPTY_RESPONSE as error - backend might be down
        if (error?.message?.includes('ERR_EMPTY_RESPONSE') || error?.message?.includes('Failed to fetch')) {
          logger.warn('Backend not responding for month data (non-critical)');
          // Fallback: use cached data if available
          if (financialPerformanceData?.data?.monthly) {
            setSelectedMonthData(financialPerformanceData.data.monthly);
          } else {
            setSelectedMonthData(null);
          }
        } else {
          logger.error('Error loading month data:', error);
          setSelectedMonthData(null);
        }
      } finally {
        setLoadingMonthData(false);
      }
    };

    loadMonthData();
  }, [selectedMonth, financialPerformanceData, isCurrentMonth, getMonthData, viewType]);

  // Memoized calculations - with error handling
  const quickStats = useMemo(() => {
    try {
      return calculateQuickStats(dashboardData, financialPerformanceData?.data || null, t);
    } catch (error) {
      logger.error('Error calculating quick stats:', error);
      return [];
    }
  }, [dashboardData, financialPerformanceData, t]);

  // GUARANTEED FIX: Get direct financial data for cards
  const directDailyData = useMemo(() => {
    // Priority 1: selectedDayData (if user navigated to specific day)
    if (selectedDayData && Object.keys(selectedDayData).length > 0) {
      return selectedDayData;
    }
    // Priority 2: dashboardData.financial_performance.daily
    const dashboardDaily = (dashboardData as any)?.financial_performance?.daily;
    if (dashboardDaily && Object.keys(dashboardDaily).length > 0) {
      return dashboardDaily;
    }
    // Priority 3: financialPerformanceData.data.daily
    return financialPerformanceData?.data?.daily || null;
  }, [selectedDayData, dashboardData, financialPerformanceData]);

  const directMonthlyData = useMemo(() => {
    // Priority 1: selectedMonthData (if user navigated to specific month)
    if (selectedMonthData && Object.keys(selectedMonthData).length > 0) {
      return selectedMonthData;
    }
    // Priority 2: dashboardData.financial_performance.monthly
    const dashboardMonthly = (dashboardData as any)?.financial_performance?.monthly;
    if (dashboardMonthly && Object.keys(dashboardMonthly).length > 0) {
      return dashboardMonthly;
    }
    // Priority 3: financialPerformanceData.data.monthly
    return financialPerformanceData?.data?.monthly || null;
  }, [selectedMonthData, dashboardData, financialPerformanceData]);

  const directAnnualData = useMemo(() => {
    // Priority 1: dashboardData.financial_performance.annual
    const dashboardAnnual = (dashboardData as any)?.financial_performance?.annual;
    if (dashboardAnnual && Object.keys(dashboardAnnual).length > 0) {
      return dashboardAnnual;
    }
    // Priority 2: financialPerformanceData.data.annual
    return financialPerformanceData?.data?.annual || null;
  }, [dashboardData, financialPerformanceData]);

  // Debug: Log direct data with DETAILED values (development only)
  logger.debug('[DIRECT DATA CHECK]', {
    selectedDay: selectedDay?.toDateString(),
    selectedMonth: selectedMonth?.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
    
    directDailyData: directDailyData ? {
      total_bank_tl: directDailyData.total_bank_tl,
      total_cc_tl: directDailyData.total_cc_tl,
      total_tether_usd: directDailyData.total_tether_usd,
      conv_usd: directDailyData.conv_usd,
      total_deposits_tl: directDailyData.total_deposits_tl,
      total_withdrawals_tl: directDailyData.total_withdrawals_tl,
      net_cash_tl: directDailyData.net_cash_tl,
      bank_count: directDailyData.bank_count,
      cc_count: directDailyData.cc_count,
      tether_count: directDailyData.tether_count,
    } : 'NULL',
    
    directMonthlyData: directMonthlyData ? {
      total_bank_tl: directMonthlyData.total_bank_tl,
      total_cc_tl: directMonthlyData.total_cc_tl,
      total_tether_usd: directMonthlyData.total_tether_usd,
      conv_usd: directMonthlyData.conv_usd,
      total_deposits_tl: directMonthlyData.total_deposits_tl,
      total_withdrawals_tl: directMonthlyData.total_withdrawals_tl,
      net_cash_tl: directMonthlyData.net_cash_tl,
      bank_count: directMonthlyData.bank_count,
      cc_count: directMonthlyData.cc_count,
      tether_count: directMonthlyData.tether_count,
    } : 'NULL',
    
    directAnnualData: directAnnualData ? {
      total_bank_tl: directAnnualData.total_bank_tl,
      total_cc_tl: directAnnualData.total_cc_tl,
      total_tether_usd: directAnnualData.total_tether_usd,
      conv_usd: directAnnualData.conv_usd,
      total_deposits_tl: directAnnualData.total_deposits_tl,
      total_withdrawals_tl: directAnnualData.total_withdrawals_tl,
      net_cash_tl: directAnnualData.net_cash_tl,
      bank_count: directAnnualData.bank_count,
      cc_count: directAnnualData.cc_count,
      tether_count: directAnnualData.tether_count,
    } : 'NULL',
  });

  const financialBreakdown = useMemo(() => {
    try {
      // CRITICAL FIX: Use dashboardData.financial_performance as PRIMARY source (it has all the data)
      const dashboardFinancialPerf = (dashboardData as any)?.financial_performance;
      const financialData = financialPerformanceData?.data || null;
      
      // Get exchange rate from dashboardData or financialPerformanceData
      const exchangeRate = (dashboardData as any)?.exchange_rates?.USD_TRY || 
                          financialData?.exchange_rate || 
                          48.0;
      
      // Priority 1: Use dashboardData.financial_performance (most reliable, has all data)
      let dataToUse = null;
      if (dashboardFinancialPerf && Object.keys(dashboardFinancialPerf).length > 0) {
        dataToUse = {
          daily: dashboardFinancialPerf.daily || {},
          monthly: dashboardFinancialPerf.monthly || {},
          annual: dashboardFinancialPerf.annual || {},
          exchange_rate: exchangeRate,
        };
      }
      // Priority 2: Use financialPerformanceData if available
      else if (financialData) {
        dataToUse = {
          ...financialData,
          exchange_rate: exchangeRate,
        };
      }
      
      const breakdown = generateFinancialBreakdown(
        dataToUse,
        selectedDayData,
        selectedMonthData,
      );
      
      // Debug: Log breakdown data - ALWAYS log in dev mode for troubleshooting
      if (import.meta.env.DEV) {
        logger.dashboard('Financial breakdown generated', {
          breakdownLength: breakdown.length,
          dataSource: dataToUse ? 'dataToUse' : 'none',
          hasDataToUse: !!dataToUse,
          hasDashboardFinancialPerf: !!dashboardFinancialPerf,
          hasFinancialData: !!financialData,
          hasSelectedDayData: !!selectedDayData,
          hasSelectedMonthData: !!selectedMonthData,
          exchangeRate: exchangeRate,
          dataToUseDaily: dataToUse?.daily ? {
            total_bank_tl: dataToUse.daily.total_bank_tl,
            total_cc_tl: dataToUse.daily.total_cc_tl,
            net_cash_tl: dataToUse.daily.net_cash_tl,
          } : null,
          dataToUseMonthly: dataToUse?.monthly ? {
            total_bank_tl: dataToUse.monthly.total_bank_tl,
            total_cc_tl: dataToUse.monthly.total_cc_tl,
            net_cash_tl: dataToUse.monthly.net_cash_tl,
          } : null,
          dataToUseAnnual: dataToUse?.annual ? {
            total_bank_tl: dataToUse.annual.total_bank_tl,
            total_cc_tl: dataToUse.annual.total_cc_tl,
            net_cash_tl: dataToUse.annual.net_cash_tl,
          } : null,
          selectedDayDataSample: selectedDayData ? {
            total_bank_tl: selectedDayData.total_bank_tl,
            net_cash_tl: selectedDayData.net_cash_tl,
          } : null,
          selectedMonthDataSample: selectedMonthData ? {
            total_bank_tl: selectedMonthData.total_bank_tl,
            net_cash_tl: selectedMonthData.net_cash_tl,
          } : null,
          sampleBreakdown: breakdown.slice(0, 5).map(item => ({
            period: item.timePeriod,
            metric: item.metric,
            amount: item.amount,
          })),
        });
      }
      
      return breakdown;
    } catch (error) {
      logger.error('Error generating financial breakdown:', error);
      return [];
    }
  }, [financialPerformanceData, dashboardData, selectedDayData, selectedMonthData]);

  const chartData = useMemo(() => {
    try {
      if (!dashboardData?.chart_data?.daily_revenue) {
        logger.warn('No chart data available in dashboardData');
        return [];
      }
      const transformed = transformChartData(dashboardData.chart_data.daily_revenue, chartPeriod, showZeroValues);
      if (transformed.length === 0) {
        logger.warn('Transformed chart data is empty');
      }
      return transformed;
    } catch (error) {
      logger.error('Error transforming chart data:', error);
      return [];
    }
  }, [dashboardData, chartPeriod, showZeroValues]);

  // Handlers
  const handleRefresh = useCallback(async () => {
    try {
      setComponentError(null);
      await Promise.all([refreshDashboard(), refreshFinancial()]);
    } catch (error) {
      logger.error('Error refreshing dashboard:', error);
      setComponentError(error instanceof Error ? error : new Error('Refresh failed'));
    }
  }, [refreshDashboard, refreshFinancial]);

  const handleGenerateReport = useCallback(async () => {
    if (!dashboardData) return;

    setIsGeneratingReport(true);
    try {
      await ExcelExportService.generateComprehensiveReport(timeRange);
      logger.info('Report generated successfully');
    } catch (error) {
      logger.error('Error generating report:', error);
    } finally {
      setIsGeneratingReport(false);
    }
  }, [dashboardData, timeRange]);

  // Loading state
  const loading = loadingDashboard || loadingFinancial;

  // Error state
  const error = dashboardError || financialError || (componentError ? componentError.message : null) || null;

  // Component error UI - show if there's a component-level error
  if (componentError) {
    return (
      <main className="flex-1 bg-gradient-to-br from-slate-50 via-white to-slate-100 min-h-screen">
        <div className="px-6 py-8">
          <div className="flex items-center justify-center min-h-[400px]">
            <Card className="w-full max-w-md border-0 shadow-2xl bg-white/80 backdrop-blur-sm">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-2xl">⚠️</span>
                </div>
                <h2 className="text-2xl font-semibold text-slate-900 mb-3">Component Error</h2>
                <p className="text-slate-600 mb-4">{componentError.message}</p>
                <Button
                  onClick={() => {
                    setComponentError(null);
                    window.location.reload();
                  }}
                  className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 hover:scale-105"
                >
                  Reload Page
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    );
  }

  // Debug: Log current state - ALWAYS log in dev mode for troubleshooting
  useEffect(() => {
    if (import.meta.env.DEV) {
      const errorMsg = componentError ? (componentError as Error).message : null;
      logger.dashboard('Dashboard state', {
        loading,
        loadingDashboard,
        loadingFinancial,
        hasDashboardData: !!dashboardData,
        hasFinancialData: !!financialPerformanceData,
        financialDataStructure: financialPerformanceData ? {
          hasDaily: !!financialPerformanceData.data?.daily,
          hasMonthly: !!financialPerformanceData.data?.monthly,
          hasAnnual: !!financialPerformanceData.data?.annual,
          dailySample: financialPerformanceData.data?.daily ? {
            total_bank_tl: financialPerformanceData.data.daily.total_bank_tl,
            net_cash_tl: financialPerformanceData.data.daily.net_cash_tl,
          } : null,
        } : null,
        dashboardDataStructure: dashboardData ? {
          hasFinancialPerf: !!(dashboardData as any)?.financial_performance,
          financialPerfSample: (dashboardData as any)?.financial_performance?.annual ? {
            net_cash_tl: (dashboardData as any).financial_performance.annual.net_cash_tl,
          } : null,
        } : null,
        selectedDayData: selectedDayData ? {
          total_bank_tl: selectedDayData.total_bank_tl,
          net_cash_tl: selectedDayData.net_cash_tl,
        } : null,
        selectedMonthData: selectedMonthData ? {
          total_bank_tl: selectedMonthData.total_bank_tl,
          net_cash_tl: selectedMonthData.net_cash_tl,
        } : null,
        error,
        componentError: errorMsg,
      });
    }
  }, [loading, loadingDashboard, loadingFinancial, dashboardData, financialPerformanceData, selectedDayData, selectedMonthData, error, componentError]);

  // Loading UI - show skeleton while loading (sadece ilk yüklemede)
  if (loading && !dashboardData && !financialPerformanceData) {
    return <FullDashboardSkeleton />;
  }

  // Error UI - only show if we have an error and no data at all
  if (error && !dashboardData && !financialPerformanceData) {
    return (
      <main className="flex-1 bg-gradient-to-br from-slate-50 via-white to-slate-100 min-h-screen">
        <div className="px-6 py-8">
          <div className="flex items-center justify-center min-h-[400px]">
            <Card className="w-full max-w-md border-0 shadow-2xl bg-white/80 backdrop-blur-sm">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-2xl">⚠️</span>
                </div>
                <h2 className="text-2xl font-semibold text-slate-900 mb-3">Error Loading Dashboard</h2>
                <p className="text-slate-600 mb-6">{error}</p>
                <Button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 hover:scale-105"
                >
                  Try Again
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    );
  }

  // Veri yoksa bile dashboard'ı göster (boş verilerle)
  // Kullanıcı en azından UI'ı görebilsin

return (
    <main style={{ flex: 1, backgroundColor: '#f9fafb', minHeight: '100vh' }} className="flex-1 bg-gray-50 min-h-screen">
      <div style={{ padding: '1.5rem 2rem' }} className="px-6 lg:px-8 py-6 lg:py-8">
        <div className="space-y-6">
          {/* Header Section */}
          <DashboardHeader
            timeRange={timeRange}
            viewType={viewType}
            refreshing={loading}
            isGeneratingReport={isGeneratingReport}
            lastUpdated={lastUpdated}
            onTimeRangeChange={setTimeRange}
            onViewTypeChange={setViewType}
            onRefresh={handleRefresh}
            onExport={handleGenerateReport}
          />

          {/* Summary Stats Bar - Her zaman göster */}
          {quickStats.length > 0 && (
            <SummaryStatsBar
              stats={quickStats}
              loading={loading && !dashboardData}
              onStatClick={(index) => {
                if (quickStats[index]) {
                  const stat = quickStats[index];
                  if (stat.label.includes('Cash')) {
                    navigate('/analytics/revenue');
                  } else if (stat.label.includes('Clients')) {
                    navigate('/clients');
                  } else if (stat.label.includes('Transactions')) {
                    navigate('/transactions');
                  }
                }
              }}
            />
          )}

          {/* Transactions Chart - Her zaman göster */}
          <Card className="bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
            <CardHeader className="pb-6">
              <SectionHeader
                title={t('transactions.title')}
                description={t('dashboard.revenue_trend')}
                icon={LineChart}
                size="md"
                badge={<StatusIndicator status="online" label="Live Data" pulse size="sm" />}
                actions={
                  <>
                    {/* Period Selector */}
                    <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                      {(['daily', 'monthly', 'annual'] as const).map((period) => (
                        <button
                          key={period}
                          onClick={() => setChartPeriod(period)}
                          className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200 ${
                            chartPeriod === period
                              ? 'bg-white text-gray-900 shadow-sm'
                              : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
                          }`}
                        >
                          {period.charAt(0).toUpperCase() + period.slice(1)}
                        </button>
                      ))}
                    </div>

                    {/* Show/Hide Zero Values Toggle */}
                    <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                      <button
                        onClick={() => setShowZeroValues(!showZeroValues)}
                        className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200 flex items-center gap-2 ${
                          showZeroValues
                            ? 'bg-white text-gray-900 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
                        }`}
                        title={showZeroValues ? 'Hide days with zero values' : 'Show all days including zeros'}
                      >
                        <span>{showZeroValues ? 'With Zeros' : 'Without Zeros'}</span>
                      </button>
                    </div>
                  </>
                }
              />
            </CardHeader>
            <CardContent>
              <div className="h-96 chart-container">
                {chartData.length > 0 ? (
                  <RevenueChart data={chartData} type="bar" height={350} />
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <p>Chart verisi yükleniyor...</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Financial Performance Cards - GUARANTEED FIX with Direct Data */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Daily Card */}
            <FinancialPerformanceCard
              title={t('dashboard.daily_revenue')}
              icon={Calendar}
              period="Daily"
              data={directDailyData}
              breakdown={financialBreakdown}
              loading={loadingDayData || loading}
              selectedDate={selectedDay}
              isCurrentPeriod={isCurrentDay()}
              onPrevious={goToPreviousDay}
              onNext={goToNextDay}
              onToday={() => setSelectedDay(new Date())}
              formatDate={formatDayDate}
              navigatePath="/analytics/revenue?period=daily"
            />

            {/* Monthly Card */}
            <FinancialPerformanceCard
              title={t('dashboard.monthly_revenue')}
              icon={BarChart3}
              period="Monthly"
              data={directMonthlyData}
              breakdown={financialBreakdown}
              loading={loadingMonthData || loading}
              selectedDate={selectedMonth}
              isCurrentPeriod={isCurrentMonth()}
              onPrevious={goToPreviousMonth}
              onNext={goToNextMonth}
              onToday={() => setSelectedMonth(new Date())}
              formatDate={formatMonthYear}
              navigatePath="/analytics/revenue?period=monthly"
            />

            {/* Total Card */}
            <FinancialPerformanceCard
              title={t('dashboard.performance')}
              icon={TrendingUp}
              period="Total"
              data={directAnnualData}
              breakdown={financialBreakdown}
              loading={loading}
              selectedDate={new Date()}
              isCurrentPeriod={true}
              onPrevious={() => {}}
              onNext={() => {}}
              formatDate={() => 'All Time'}
              navigatePath="/analytics/revenue?period=annual"
            />
          </div>

          {/* Recent Activity Feed */}
          <Suspense
            fallback={
              <Card className="bg-white border border-gray-200 shadow-sm">
                <CardHeader className="pb-4">
                  <div className="h-6 bg-gray-200 rounded w-32 animate-pulse"></div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse"></div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            }
          >
            <LazyRecentActivityFeed
              limit={5}
              onClickTransaction={(transactionId) => {
                navigate(`/transactions?highlight=${transactionId}`);
              }}
            />
          </Suspense>
        </div>
      </div>
    </main>
  );
};

export default React.memo(ModernDashboard);

