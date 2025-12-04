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
import type { TimeRange, ViewType, ChartPeriod } from '../../types/dashboard.types';

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

  // State management - optimized
  const [timeRange, setTimeRange] = useState<TimeRange>('all');
  const [viewType, setViewType] = useState<ViewType>('net');
  const [chartPeriod, setChartPeriod] = useState<ChartPeriod>('monthly');
  const [showZeroValues, setShowZeroValues] = useState(true);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<Date>(new Date());
  const [selectedDay, setSelectedDay] = useState<Date>(new Date());
  const [selectedDayData, setSelectedDayData] = useState<any>(null);
  const [selectedMonthData, setSelectedMonthData] = useState<any>(null);
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
      if (!financialPerformanceData?.data) return;

      setLoadingDayData(true);
      try {
        if (isCurrentDay()) {
          setSelectedDayData(financialPerformanceData.data.daily);
        } else {
          const dayData = await getDayData(selectedDay);
          setSelectedDayData(dayData);
        }
      } catch (error) {
        logger.error('Error loading day data:', error);
        setSelectedDayData(null);
      } finally {
        setLoadingDayData(false);
      }
    };

    loadDayData();
  }, [selectedDay, financialPerformanceData, isCurrentDay, getDayData]);

  // Load selected month data
  useEffect(() => {
    const loadMonthData = async () => {
      if (!financialPerformanceData?.data) return;

      setLoadingMonthData(true);
      try {
        if (isCurrentMonth()) {
          setSelectedMonthData(financialPerformanceData.data.monthly);
        } else {
          const monthData = await getMonthData(selectedMonth);
          setSelectedMonthData(monthData);
        }
      } catch (error) {
        logger.error('Error loading month data:', error);
        setSelectedMonthData(null);
      } finally {
        setLoadingMonthData(false);
      }
    };

    loadMonthData();
  }, [selectedMonth, financialPerformanceData, isCurrentMonth, getMonthData, viewType]);

  // Memoized calculations
  const quickStats = useMemo(() => {
    return calculateQuickStats(dashboardData, financialPerformanceData?.data || null, t);
  }, [dashboardData, financialPerformanceData, t]);

  const financialBreakdown = useMemo(() => {
    return generateFinancialBreakdown(
      financialPerformanceData?.data || null,
      selectedDayData,
      selectedMonthData,
    );
  }, [financialPerformanceData, selectedDayData, selectedMonthData]);

  const chartData = useMemo(() => {
    if (!dashboardData?.chart_data?.daily_revenue) return [];
    return transformChartData(dashboardData.chart_data.daily_revenue, chartPeriod, showZeroValues);
  }, [dashboardData, chartPeriod, showZeroValues]);

  // Handlers
  const handleRefresh = useCallback(async () => {
    await Promise.all([refreshDashboard(), refreshFinancial()]);
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
  const error = dashboardError || financialError;

  // Loading UI
  if (loading && !dashboardData) {
    return <FullDashboardSkeleton />;
  }

  // Error UI
  if (error && !dashboardData) {
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

  return (
    <main className="flex-1 bg-gray-50 min-h-screen">
      <div className="px-6 lg:px-8 py-6 lg:py-8">
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

          {/* Summary Stats Bar */}
          <SummaryStatsBar
            stats={quickStats}
            loading={loading}
            onStatClick={(index) => {
              const stat = quickStats[index];
              if (stat.label.includes('Cash')) {
                navigate('/analytics/revenue');
              } else if (stat.label.includes('Clients')) {
                navigate('/clients');
              } else if (stat.label.includes('Transactions')) {
                navigate('/transactions');
              }
            }}
          />

          {/* Transactions Chart */}
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
                <RevenueChart data={chartData} type="bar" height={350} />
              </div>
            </CardContent>
          </Card>

          {/* Financial Performance Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Daily Card */}
            <FinancialPerformanceCard
              title={t('dashboard.daily_revenue')}
              icon={Calendar}
              period="Daily"
              data={selectedDayData}
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
              data={selectedMonthData}
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
              data={financialPerformanceData?.data?.annual || null}
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

