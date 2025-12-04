/**
 * Dashboard Helper Functions
 * Utility functions for dashboard calculations and data transformations
 */

import React from 'react';
import type {
  FinancialPerformanceData,
  FinancialPeriodData,
  FinancialBreakdownItem,
  QuickStat,
  DashboardData,
} from '../types/dashboard.types';
import {
  DollarSign,
  Users,
  Activity,
  CheckCircle,
  Building2,
  CreditCard,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';

/**
 * Safely get numeric value from any type
 */
export const safeGetValue = (obj: any, key: string, fallback: number = 0): number => {
  const value = obj?.[key];
  return typeof value === 'number' && !isNaN(value) ? value : fallback;
};

/**
 * Calculate quick stats from dashboard data
 */
export const calculateQuickStats = (
  dashboardData: DashboardData | null,
  financialPerformanceData: FinancialPerformanceData | null,
  t: (key: string) => string,
): QuickStat[] => {
  // Dashboard data yoksa bile boş stats göster (UI bozulmasın)
  if (!dashboardData) {
    return [
      {
        label: t('dashboard.net_cash'),
        value: '₺0',
        icon: DollarSign,
        change: '0%',
        trend: 'up' as const,
      },
      {
        label: t('dashboard.active_clients'),
        value: '0',
        icon: Users,
        change: '0%',
        trend: 'up' as const,
      },
      {
        label: t('dashboard.total_transactions'),
        value: '0',
        icon: Activity,
        change: '0%',
        trend: 'up' as const,
      },
      {
        label: t('dashboard.growth_rate'),
        value: '0%',
        icon: CheckCircle,
        change: '0%',
        trend: 'up' as const,
      },
    ];
  }

  // Net cash hesaplama - finansal performans verisinden veya dashboard summary'den
  // CRITICAL FIX: Net cash should be in TL only. USD amounts are already converted to TL in backend.
  let netCashValue = 0;
  
  // Debug: Log available data sources (always log in dev mode)
  console.log('[Net Cash] Checking data sources:', {
    hasSummary: !!dashboardData?.summary,
    summaryNetCash: dashboardData?.summary ? (dashboardData.summary as any).net_cash : undefined,
    summaryType: dashboardData?.summary ? typeof (dashboardData.summary as any).net_cash : 'N/A',
    hasFinancialPerf: !!(dashboardData as any)?.financial_performance,
    financialPerfNetCash: (dashboardData as any)?.financial_performance?.annual?.net_cash_tl,
    financialPerfType: (dashboardData as any)?.financial_performance?.annual?.net_cash_tl ? typeof (dashboardData as any).financial_performance.annual.net_cash_tl : 'N/A',
    hasFinancialData: !!financialPerformanceData,
    financialDataNetCash: financialPerformanceData?.annual?.net_cash_tl,
  });
  
  // Oncelik 1: consolidated dashboard'dan gelen summary.net_cash (en guvenilir kaynak)
  // Bu deger backend'de deposits - withdrawals olarak hesaplanir
  const summaryNetCash = dashboardData?.summary ? (dashboardData.summary as any).net_cash : undefined;
  if (summaryNetCash !== undefined && summaryNetCash !== null && !isNaN(Number(summaryNetCash))) {
    netCashValue = Number(summaryNetCash);
  }
  // Oncelik 2: consolidated dashboard'dan gelen financial_performance verisi
  else {
    const financialPerfNetCash = (dashboardData as any)?.financial_performance?.annual?.net_cash_tl;
    if (financialPerfNetCash !== undefined && financialPerfNetCash !== null && !isNaN(Number(financialPerfNetCash))) {
      netCashValue = Number(financialPerfNetCash);
    }
    // Oncelik 3: financialPerformanceData hook'undan gelen veri
    else {
      const financialDataNetCash = financialPerformanceData?.annual?.net_cash_tl;
      if (financialDataNetCash !== undefined && financialDataNetCash !== null && !isNaN(Number(financialDataNetCash))) {
        netCashValue = Number(financialDataNetCash);
      }
    }
  }
  
  // Debug: Log final value (always log in dev mode)
  console.log('[Net Cash] Final calculated value:', netCashValue, {
    source: summaryNetCash !== undefined ? 'summary.net_cash' : 
            (dashboardData as any)?.financial_performance?.annual?.net_cash_tl !== undefined ? 'financial_performance.annual.net_cash_tl' :
            financialPerformanceData?.annual?.net_cash_tl !== undefined ? 'financialPerformanceData.annual.net_cash_tl' : 'none'
  });

  // Active clients değerini parse et
  const activeClientsValue = dashboardData?.stats?.active_clients?.value || '0';
  const activeClientsNumber = typeof activeClientsValue === 'string' 
    ? parseInt(activeClientsValue.replace(/[,]/g, '')) || 0 
    : activeClientsValue;

  // Total transactions değerini parse et
  const totalTransactionsValue = dashboardData?.stats?.total_transactions?.value || '0';
  const totalTransactionsNumber = typeof totalTransactionsValue === 'string'
    ? parseInt(totalTransactionsValue.replace(/[,]/g, '')) || 0
    : totalTransactionsValue;

  // Growth rate değerini parse et
  const growthRateValue = dashboardData?.stats?.growth_rate?.value || '0%';
  const growthRateNumber = typeof growthRateValue === 'string'
    ? parseFloat(growthRateValue.replace(/[%,]/g, '')) || 0
    : growthRateValue;

  // Change degerlerini backend'den al, yoksa '0%' goster
  // CRITICAL FIX: Net Cash icin net_cash change kullan, total_revenue degil
  const netCashChange = (dashboardData?.stats as any)?.net_cash?.change || dashboardData?.stats?.total_revenue?.change || '0%';
  const activeClientsChange = dashboardData?.stats?.active_clients?.change || '0%';
  const totalTransactionsChange = dashboardData?.stats?.total_transactions?.change || '0%';
  const growthRateChange = dashboardData?.stats?.growth_rate?.change || '0%';

  // Trend yonunu change degerinden belirle
  const getTrend = (change: string): 'up' | 'down' => {
    const numValue = parseFloat(change.replace(/[+%]/g, '')) || 0;
    return numValue >= 0 ? 'up' : 'down';
  };

  return [
    {
      label: t('dashboard.net_cash'),
      value: `₺${netCashValue.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}`,
      icon: DollarSign,
      change: netCashChange,
      trend: getTrend(netCashChange),
    },
    {
      label: t('dashboard.active_clients'),
      value: activeClientsNumber.toLocaleString('tr-TR'),
      icon: Users,
      change: activeClientsChange,
      trend: getTrend(activeClientsChange),
    },
    {
      label: t('dashboard.total_transactions'),
      value: totalTransactionsNumber.toLocaleString('tr-TR'),
      icon: Activity,
      change: totalTransactionsChange,
      trend: getTrend(totalTransactionsChange),
    },
    {
      label: t('dashboard.growth_rate'),
      value: `${growthRateNumber.toFixed(1)}%`,
      icon: CheckCircle,
      change: growthRateChange,
      trend: getTrend(growthRateChange),
    },
  ];
};

/**
 * Generate financial performance breakdown
 */
export const generateFinancialBreakdown = (
  financialData: FinancialPerformanceData | null,
  selectedDayData: FinancialPeriodData | null,
  selectedMonthData: FinancialPeriodData | null,
): FinancialBreakdownItem[] => {
  // Eğer financialData yoksa, boş veri yapısı oluştur
  const emptyPeriodData: FinancialPeriodData = {
    total_bank_usd: 0,
    total_bank_tl: 0,
    total_cc_usd: 0,
    total_cc_tl: 0,
    total_tether_usd: 0,
    total_tether_tl: 0,
    conv_usd: 0,
    conv_tl: 0,
    total_transactions: 0,
    bank_count: 0,
    cc_count: 0,
    tether_count: 0,
    total_deposits_usd: 0,
    total_deposits_tl: 0,
    total_withdrawals_usd: 0,
    total_withdrawals_tl: 0,
    net_cash_usd: 0,
    net_cash_tl: 0,
  };

  // Veri yoksa bile boş breakdown item'ları oluştur (UI bozulmasın)
  if (!financialData) {
    const data = {
      daily: emptyPeriodData,
      monthly: emptyPeriodData,
      annual: emptyPeriodData,
      exchange_rate: 48,
    };
    return createBreakdownItems(data, selectedDayData, selectedMonthData);
  }

  const data = financialData;
  const exchangeRate = data.exchange_rate || 48;

  // Helper function to merge data - use fallback if base data is missing
  const mergePeriodData = (baseData: FinancialPeriodData, fallbackData: any): FinancialPeriodData => {
    if (!fallbackData || Object.keys(fallbackData).length === 0) {
      return baseData;
    }
    
    // CRITICAL FIX: Use fallback ONLY if base value is undefined/null, NOT if it's 0
    // 0 is a valid value (means no transactions)
    return {
      ...baseData,
      // Use fallback value only if base is undefined or null (0 is valid!)
      net_cash_tl: baseData.net_cash_tl !== undefined && baseData.net_cash_tl !== null ? baseData.net_cash_tl : (fallbackData.net_cash_tl ?? 0),
      net_cash_usd: baseData.net_cash_usd !== undefined && baseData.net_cash_usd !== null ? baseData.net_cash_usd : (fallbackData.net_cash_usd ?? 0),
      total_deposits_tl: baseData.total_deposits_tl !== undefined && baseData.total_deposits_tl !== null ? baseData.total_deposits_tl : (fallbackData.total_deposits_tl ?? 0),
      total_deposits_usd: baseData.total_deposits_usd !== undefined && baseData.total_deposits_usd !== null ? baseData.total_deposits_usd : (fallbackData.total_deposits_usd ?? 0),
      total_withdrawals_tl: baseData.total_withdrawals_tl !== undefined && baseData.total_withdrawals_tl !== null ? baseData.total_withdrawals_tl : (fallbackData.total_withdrawals_tl ?? 0),
      total_withdrawals_usd: baseData.total_withdrawals_usd !== undefined && baseData.total_withdrawals_usd !== null ? baseData.total_withdrawals_usd : (fallbackData.total_withdrawals_usd ?? 0),
      // Also merge other fields if available
      total_bank_usd: baseData.total_bank_usd !== undefined && baseData.total_bank_usd !== null ? baseData.total_bank_usd : (fallbackData.total_bank_usd ?? 0),
      total_bank_tl: baseData.total_bank_tl !== undefined && baseData.total_bank_tl !== null ? baseData.total_bank_tl : (fallbackData.total_bank_tl ?? 0),
      total_cc_usd: baseData.total_cc_usd !== undefined && baseData.total_cc_usd !== null ? baseData.total_cc_usd : (fallbackData.total_cc_usd ?? 0),
      total_cc_tl: baseData.total_cc_tl !== undefined && baseData.total_cc_tl !== null ? baseData.total_cc_tl : (fallbackData.total_cc_tl ?? 0),
      total_tether_usd: baseData.total_tether_usd !== undefined && baseData.total_tether_usd !== null ? baseData.total_tether_usd : (fallbackData.total_tether_usd ?? 0),
      total_tether_tl: baseData.total_tether_tl !== undefined && baseData.total_tether_tl !== null ? baseData.total_tether_tl : (fallbackData.total_tether_tl ?? 0),
      conv_usd: baseData.conv_usd !== undefined && baseData.conv_usd !== null ? baseData.conv_usd : (fallbackData.conv_usd ?? 0),
      conv_tl: baseData.conv_tl !== undefined && baseData.conv_tl !== null ? baseData.conv_tl : (fallbackData.conv_tl ?? 0),
      bank_count: baseData.bank_count !== undefined && baseData.bank_count !== null ? baseData.bank_count : (fallbackData.bank_count ?? 0),
      cc_count: baseData.cc_count !== undefined && baseData.cc_count !== null ? baseData.cc_count : (fallbackData.cc_count ?? 0),
      tether_count: baseData.tether_count !== undefined && baseData.tether_count !== null ? baseData.tether_count : (fallbackData.tether_count ?? 0),
      total_transactions: baseData.total_transactions !== undefined && baseData.total_transactions !== null ? baseData.total_transactions : (fallbackData.total_transactions ?? 0),
    };
  };

  // Daily data - selectedDayData varsa onu kullan, yoksa data.daily'yi kullan
  // Eger selectedDayData null ise ama data.daily varsa, data.daily'yi kullan
  let dailyData: FinancialPeriodData;
  if (selectedDayData && Object.keys(selectedDayData).length > 0) {
    dailyData = selectedDayData;
  } else if (data.daily && Object.keys(data.daily).length > 0) {
    dailyData = mergePeriodData(emptyPeriodData, data.daily);
  } else {
    dailyData = emptyPeriodData;
  }

  // Monthly data - selectedMonthData varsa onu kullan, yoksa data.monthly'yi kullan
  // Eger selectedMonthData null ise ama data.monthly varsa, data.monthly'yi kullan
  let monthlyData: FinancialPeriodData;
  if (selectedMonthData && Object.keys(selectedMonthData).length > 0) {
    monthlyData = selectedMonthData;
  } else if (data.monthly && Object.keys(data.monthly).length > 0) {
    monthlyData = mergePeriodData(emptyPeriodData, data.monthly);
  } else {
    monthlyData = emptyPeriodData;
  }

  // Annual data - merge with fallback
  const annualData = data.annual && Object.keys(data.annual).length > 0
    ? mergePeriodData(emptyPeriodData, data.annual)
    : emptyPeriodData;

  const breakdownItems = createBreakdownItems(
    { daily: dailyData, monthly: monthlyData, annual: annualData, exchange_rate: exchangeRate },
    selectedDayData,
    selectedMonthData,
  );
  
  return breakdownItems;
};

/**
 * Helper function to create breakdown items
 */
const createBreakdownItems = (
  data: { daily: FinancialPeriodData; monthly: FinancialPeriodData; annual: FinancialPeriodData; exchange_rate: number },
  selectedDayData: FinancialPeriodData | null,
  selectedMonthData: FinancialPeriodData | null,
): FinancialBreakdownItem[] => {
  const { daily: dailyData, monthly: monthlyData, annual: annualData } = data;

  const breakdown: FinancialBreakdownItem[] = [];

  // Helper to create breakdown item
  const createBreakdownItem = (
    period: 'Daily' | 'Monthly' | 'Total',
    metric: string,
    periodData: FinancialPeriodData,
    icon: React.ComponentType<{ className?: string }>,
    color: string,
    bgColor: string,
  ): FinancialBreakdownItem => {
    const isConv = metric === 'Conv';
    const isTether = metric === 'Tether';
    const isNetCash = metric === 'Net Cash';
    const isTotDep = metric === 'Tot Dep';
    const isTotWD = metric === 'Tot WD';

    let amount = 0;
    let usdAmount = 0;
    let tlAmount = 0;
    let count = 0;

    // CRITICAL FIX: Bank ve CC için TL kullan, Tether ve Conv için USD kullan
    // Backend'den gelen veriler zaten doğru currency'de
    if (metric === 'Total Bank') {
      amount = periodData.total_bank_tl || 0;  // TL cinsinden göster
      usdAmount = periodData.total_bank_usd || 0;
      tlAmount = periodData.total_bank_tl || 0;
      count = periodData.bank_count || 0;
    } else if (metric === 'CC (Credit Card)') {
      amount = periodData.total_cc_tl || 0;  // TL cinsinden göster
      usdAmount = periodData.total_cc_usd || 0;
      tlAmount = periodData.total_cc_tl || 0;
      count = periodData.cc_count || 0;
    } else if (metric === 'Tether') {
      amount = periodData.total_tether_usd || 0;  // USD cinsinden göster
      usdAmount = periodData.total_tether_usd || 0;
      tlAmount = periodData.total_tether_tl || 0;
      count = periodData.tether_count || 0;
    } else if (metric === 'Conv') {
      amount = periodData.conv_usd || 0;  // USD cinsinden göster
      usdAmount = periodData.conv_usd || 0;
      tlAmount = 0;
      count = 0;
    } else if (isTotDep) {
      amount = safeGetValue(periodData, 'total_deposits_tl');  // TL cinsinden göster
      usdAmount = safeGetValue(periodData, 'total_deposits_usd');
      tlAmount = safeGetValue(periodData, 'total_deposits_tl');
      count = 0;
    } else if (isTotWD) {
      amount = safeGetValue(periodData, 'total_withdrawals_tl');  // TL cinsinden göster
      usdAmount = safeGetValue(periodData, 'total_withdrawals_usd');
      tlAmount = safeGetValue(periodData, 'total_withdrawals_tl');
      count = 0;
    } else if (isNetCash) {
      amount = safeGetValue(periodData, 'net_cash_tl');  // TL cinsinden göster
      usdAmount = safeGetValue(periodData, 'net_cash_usd');
      tlAmount = safeGetValue(periodData, 'net_cash_tl');
      count = 0;
    }

    const netCashAmount = isNetCash ? amount : 0;
    const trendColor = netCashAmount >= 0 ? 'text-green-600' : 'text-red-600';
    const finalBgColor = isNetCash ? (netCashAmount >= 0 ? 'bg-green-50' : 'bg-red-50') : bgColor;
    const finalColor = isNetCash ? (netCashAmount >= 0 ? 'green' : 'red') : color;

    return {
      timePeriod: period,
      metric,
      amount,
      usdAmount,
      tlAmount,
      count,
      trend: 0,
      icon,
      description: `${period.toLowerCase()} ${metric.toLowerCase()}`,
      color: finalColor,
      bgColor: finalBgColor,
      iconColor: 'text-gray-800',
      trendColor,
    };
  };

  // Daily metrics
  breakdown.push(createBreakdownItem('Daily', 'Total Bank', dailyData, Building2, 'blue', 'bg-blue-50'));
  breakdown.push(createBreakdownItem('Daily', 'CC (Credit Card)', dailyData, CreditCard, 'purple', 'bg-purple-50'));
  breakdown.push(createBreakdownItem('Daily', 'Tether', dailyData, DollarSign, 'green', 'bg-green-50'));
  breakdown.push(createBreakdownItem('Daily', 'Conv', dailyData, Activity, 'blue', 'bg-blue-50'));
  breakdown.push(createBreakdownItem('Daily', 'Tot Dep', dailyData, TrendingUp, 'green', 'bg-green-50'));
  breakdown.push(createBreakdownItem('Daily', 'Tot WD', dailyData, TrendingDown, 'red', 'bg-red-50'));
  breakdown.push(createBreakdownItem('Daily', 'Net Cash', dailyData, DollarSign, 'green', 'bg-green-50'));

  // Monthly metrics
  breakdown.push(createBreakdownItem('Monthly', 'Total Bank', monthlyData, Building2, 'blue', 'bg-blue-50'));
  breakdown.push(createBreakdownItem('Monthly', 'CC (Credit Card)', monthlyData, CreditCard, 'purple', 'bg-purple-50'));
  breakdown.push(createBreakdownItem('Monthly', 'Tether', monthlyData, DollarSign, 'green', 'bg-green-50'));
  breakdown.push(createBreakdownItem('Monthly', 'Conv', monthlyData, Activity, 'blue', 'bg-blue-50'));
  breakdown.push(createBreakdownItem('Monthly', 'Tot Dep', monthlyData, TrendingUp, 'green', 'bg-green-50'));
  breakdown.push(createBreakdownItem('Monthly', 'Tot WD', monthlyData, TrendingDown, 'red', 'bg-red-50'));
  breakdown.push(createBreakdownItem('Monthly', 'Net Cash', monthlyData, DollarSign, 'green', 'bg-green-50'));

  // Annual metrics
  breakdown.push(createBreakdownItem('Total', 'Total Bank', annualData, Building2, 'blue', 'bg-blue-50'));
  breakdown.push(createBreakdownItem('Total', 'CC (Credit Card)', annualData, CreditCard, 'purple', 'bg-purple-50'));
  breakdown.push(createBreakdownItem('Total', 'Tether', annualData, DollarSign, 'green', 'bg-green-50'));
  breakdown.push(createBreakdownItem('Total', 'Conv', annualData, Activity, 'blue', 'bg-blue-50'));
  breakdown.push(createBreakdownItem('Total', 'Tot Dep', annualData, TrendingUp, 'green', 'bg-green-50'));
  breakdown.push(createBreakdownItem('Total', 'Tot WD', annualData, TrendingDown, 'red', 'bg-red-50'));
  breakdown.push(createBreakdownItem('Total', 'Net Cash', annualData, DollarSign, 'green', 'bg-green-50'));

  return breakdown;
};

/**
 * Transform chart data based on period
 */
export const transformChartData = (
  chartData: Array<{ date: string; amount: number }>,
  period: 'daily' | 'monthly' | 'annual',
  showZeroValues: boolean = true,
): Array<{ date: string; amount: number }> => {
  if (!chartData || chartData.length === 0) return [];

  // Filter zero values if needed
  let filteredData = showZeroValues
    ? chartData
    : chartData.filter((item) => {
        const netCash = (item as any).net_cash || item.amount;
        return netCash !== 0;
      });

  if (period === 'daily') {
    return filteredData;
  }

  if (period === 'monthly') {
    const monthlyMap = new Map<string, { date: string; amount: number }>();

    filteredData.forEach((item) => {
      const date = new Date(item.date);
      const monthKey = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;

      if (monthlyMap.has(monthKey)) {
        monthlyMap.get(monthKey)!.amount += item.amount;
      } else {
        monthlyMap.set(monthKey, {
          date: monthKey,
          amount: item.amount,
        });
      }
    });

    return Array.from(monthlyMap.values()).sort((a, b) => a.date.localeCompare(b.date));
  }

  if (period === 'annual') {
    const yearlyMap = new Map<string, { date: string; amount: number }>();

    filteredData.forEach((item) => {
      const date = new Date(item.date);
      const yearKey = date.getFullYear().toString();

      if (yearlyMap.has(yearKey)) {
        yearlyMap.get(yearKey)!.amount += item.amount;
      } else {
        yearlyMap.set(yearKey, {
          date: yearKey,
          amount: item.amount,
        });
      }
    });

    return Array.from(yearlyMap.values()).sort((a, b) => a.date.localeCompare(b.date));
  }

  return filteredData;
};

