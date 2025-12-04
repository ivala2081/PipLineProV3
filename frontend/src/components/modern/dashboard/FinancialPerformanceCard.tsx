/**
 * Financial Performance Card Component
 * Shows financial breakdown for a specific time period
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader } from '../../ui/card';
import { Button } from '../../ui/button';
import { StatusIndicator } from '../../ui/StatusIndicator';
import { SectionHeader } from '../../ui/SectionHeader';
import { FinancialPerformanceCardSkeleton } from '../DashboardSkeleton';
import { ChevronLeft, ChevronRight, LucideIcon, Building2, CreditCard, DollarSign, Activity, TrendingUp, TrendingDown } from 'lucide-react';
import type { FinancialBreakdownItem, FinancialPeriodData } from '../../../types/dashboard.types';
import { useLanguage } from '../../../contexts/LanguageContext';

interface FinancialPerformanceCardProps {
  title: string;
  icon: LucideIcon;
  period: 'Daily' | 'Monthly' | 'Total';
  data: FinancialPeriodData | null;
  breakdown: FinancialBreakdownItem[];
  loading: boolean;
  selectedDate: Date;
  isCurrentPeriod: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onToday?: () => void;
  formatDate: (date: Date) => string;
  navigatePath: string;
}

export const FinancialPerformanceCard: React.FC<FinancialPerformanceCardProps> = ({
  title,
  icon: Icon,
  period,
  data,
  breakdown,
  loading,
  selectedDate,
  isCurrentPeriod,
  onPrevious,
  onNext,
  onToday,
  formatDate,
  navigatePath,
}) => {
  const navigate = useNavigate();
  const { t } = useLanguage();

  // Filter breakdown by period
  const paymentMethods = breakdown.filter(
    (item) => item.timePeriod === period && ['Total Bank', 'CC (Credit Card)', 'Tether', 'Conv'].includes(item.metric),
  );
  const transactionFlow = breakdown.filter(
    (item) => item.timePeriod === period && ['Tot Dep', 'Tot WD', 'Net Cash'].includes(item.metric),
  );

  // GUARANTEED FIX: Prioritize direct data over breakdown
  // Direct data kontrolü - data objesi varsa göster (0 değerleri de geçerli)
  const hasDirectData =
    data &&
    typeof data === 'object' &&
    Object.keys(data).length > 0;
  
  // Breakdown veri kontrolü - fallback olarak
  const hasBreakdownData = breakdown && breakdown.length > 0 && (paymentMethods.length > 0 || transactionFlow.length > 0);
  
  // Priority: Direct data > Breakdown data
  const hasData = hasDirectData || hasBreakdownData;
  
  // GUARANTEED FIX: If we have direct data, use it directly instead of breakdown
  const shouldUseDirectData = hasDirectData;

  // Debug logging (dev mode only)
  if (import.meta.env.DEV && !loading) {
    console.log(`[FinancialPerformanceCard ${period}]`, {
      hasData,
      hasDirectData,
      dataAvailable: !!data,
    });
  }

  return (
    <Card
      className="bg-white border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 group"
    >
      <CardHeader className="pb-4">
        <SectionHeader
          title={title}
          icon={Icon}
          size="md"
          badge={
            <StatusIndicator status="online" label="Live" pulse size="sm" />
          }
        />
      </CardHeader>
      <CardContent>
        {loading ? (
          <FinancialPerformanceCardSkeleton />
        ) : !hasData ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <Icon className="w-12 h-12 mb-3 opacity-50" />
            <p className="text-sm font-medium">No data available</p>
            <p className="text-xs mt-1">for {formatDate(selectedDate)}</p>
          </div>
        ) : paymentMethods.length === 0 && transactionFlow.length === 0 ? (
          // Eger breakdown var ama period'a uygun item yoksa, empty state goster
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <Icon className="w-12 h-12 mb-3 opacity-50" />
            <p className="text-sm font-medium">No data for this period</p>
            <p className="text-xs mt-1">for {formatDate(selectedDate)}</p>
          </div>
        ) : shouldUseDirectData && data ? (
          <>
            {/* Render using direct data */}
            <div className="space-y-4">
              {/* Payment Methods Section - Direct Data */}
              <div className="space-y-2">
                {/* Bank */}
                <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded border border-gray-100 hover:bg-gray-100 hover:border-gray-200 hover:shadow-sm transition-all duration-200 group">
                  <div className="flex items-center gap-3">
                    <Building2 className="w-4 h-4 text-blue-600 group-hover:scale-110 transition-transform duration-200" />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                      Total Bank
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900 group-hover:text-gray-950 transition-colors duration-200">
                      ₺{Math.abs(data.total_bank_tl || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                    </div>
                    {data.bank_count > 0 && (
                      <div className="text-xs text-gray-500">{data.bank_count} txns</div>
                    )}
                  </div>
                </div>

                {/* Credit Card */}
                <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded border border-gray-100 hover:bg-gray-100 hover:border-gray-200 hover:shadow-sm transition-all duration-200 group">
                  <div className="flex items-center gap-3">
                    <CreditCard className="w-4 h-4 text-purple-600 group-hover:scale-110 transition-transform duration-200" />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                      CC (Credit Card)
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900 group-hover:text-gray-950 transition-colors duration-200">
                      ₺{Math.abs(data.total_cc_tl || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                    </div>
                    {data.cc_count > 0 && (
                      <div className="text-xs text-gray-500">{data.cc_count} txns</div>
                    )}
                  </div>
                </div>

                {/* Tether */}
                <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded border border-gray-100 hover:bg-gray-100 hover:border-gray-200 hover:shadow-sm transition-all duration-200 group">
                  <div className="flex items-center gap-3">
                    <DollarSign className="w-4 h-4 text-green-600 group-hover:scale-110 transition-transform duration-200" />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                      Tether
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900 group-hover:text-gray-950 transition-colors duration-200">
                      ${Math.abs(data.total_tether_usd || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                    </div>
                    {data.tether_count > 0 && (
                      <div className="text-xs text-gray-500">{data.tether_count} txns</div>
                    )}
                  </div>
                </div>

                {/* Conv */}
                <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded border border-gray-100 hover:bg-gray-100 hover:border-gray-200 hover:shadow-sm transition-all duration-200 group">
                  <div className="flex items-center gap-3">
                    <Activity className="w-4 h-4 text-blue-600 group-hover:scale-110 transition-transform duration-200" />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                      Conv
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900 group-hover:text-gray-950 transition-colors duration-200">
                      ${Math.abs(data.conv_usd || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>
              </div>

              {/* Transaction Flow Section - Direct Data */}
              <div className="space-y-2 pt-2 border-t-2 border-gray-300">
                {/* Total Deposits */}
                <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded border border-gray-100 hover:bg-gray-100 hover:border-gray-200 hover:shadow-sm transition-all duration-200 group">
                  <div className="flex items-center gap-3">
                    <TrendingUp className="w-4 h-4 text-green-600 group-hover:scale-110 transition-transform duration-200" />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                      Tot Dep
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900 group-hover:text-gray-950 transition-colors duration-200">
                      ₺{Math.abs(data.total_deposits_tl || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>

                {/* Total Withdrawals */}
                <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded border border-gray-100 hover:bg-gray-100 hover:border-gray-200 hover:shadow-sm transition-all duration-200 group">
                  <div className="flex items-center gap-3">
                    <TrendingDown className="w-4 h-4 text-red-600 group-hover:scale-110 transition-transform duration-200" />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                      Tot WD
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900 group-hover:text-gray-950 transition-colors duration-200">
                      ₺{Math.abs(data.total_withdrawals_tl || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>

                {/* Net Cash */}
                <div className={`flex items-center justify-between py-3 px-4 rounded border border-gray-100 hover:border-gray-200 hover:shadow-sm transition-all duration-200 group ${
                  (data.net_cash_tl || 0) >= 0 ? 'bg-green-50' : 'bg-red-50'
                }`}>
                  <div className="flex items-center gap-3">
                    <DollarSign className={`w-4 h-4 group-hover:scale-110 transition-transform duration-200 ${
                      (data.net_cash_tl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`} />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                      Net Cash
                    </span>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-semibold group-hover:text-gray-950 transition-colors duration-200 ${
                      (data.net_cash_tl || 0) >= 0 ? 'text-green-700' : 'text-red-700'
                    }`}>
                      ₺{Math.abs(data.net_cash_tl || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Date Navigation Controls - Direct Data */}
            {period !== 'Total' && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-center w-full">
                  <div className="flex items-center gap-3 w-full max-w-md">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onPrevious();
                      }}
                      className="h-8 w-8 p-0 hover:bg-blue-50 hover:border-blue-300"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="text-sm font-medium text-gray-700 flex-1 text-center">
                      {formatDate(selectedDate)}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNext();
                      }}
                      disabled={isCurrentPeriod}
                      className="h-8 w-8 p-0 hover:bg-blue-50 hover:border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                  {!isCurrentPeriod && onToday && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToday();
                      }}
                      className="h-8 px-3 text-xs hover:bg-blue-50 hover:border-blue-300 ml-4"
                    >
                      {period === 'Daily' ? 'Today' : 'Current Month'}
                    </Button>
                  )}
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            {/* Fallback: Render using breakdown data */}
            <div className="space-y-4">
              {/* Payment Methods Section */}
              <div className="space-y-2">
                {paymentMethods.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded border border-gray-100 hover:bg-gray-100 hover:border-gray-200 hover:shadow-sm transition-all duration-200 group"
                  >
                    <div className="flex items-center gap-3">
                      <item.icon
                        className={`w-4 h-4 ${item.iconColor} group-hover:scale-110 transition-transform duration-200`}
                      />
                      <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                        {item.metric}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900 group-hover:text-gray-950 transition-colors duration-200">
                        {(item.metric === 'Tether' || item.metric === 'Conv' ? '$' : '₺') +
                          (item.amount || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                      </div>
                      {item.count > 0 && (
                        <div className="text-xs text-gray-500">{item.count} txns</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Transaction Flow Section */}
              <div className="space-y-2 pt-2 border-t-2 border-gray-300">
                {transactionFlow.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded border border-gray-100 hover:bg-gray-100 hover:border-gray-200 hover:shadow-sm transition-all duration-200 group"
                  >
                    <div className="flex items-center gap-3">
                      <item.icon
                        className={`w-4 h-4 ${item.iconColor} group-hover:scale-110 transition-transform duration-200`}
                      />
                      <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                        {item.metric}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900 group-hover:text-gray-950 transition-colors duration-200">
                        ₺{(item.amount || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                      </div>
                      {item.count > 0 && (
                        <div className="text-xs text-gray-500">{item.count} txns</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Date Navigation Controls */}
            {period !== 'Total' && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-center w-full">
                  <div className="flex items-center gap-3 w-full max-w-md">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onPrevious();
                      }}
                      className="h-8 w-8 p-0 hover:bg-blue-50 hover:border-blue-300"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="text-sm font-medium text-gray-700 flex-1 text-center">
                      {formatDate(selectedDate)}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNext();
                      }}
                      disabled={isCurrentPeriod}
                      className="h-8 w-8 p-0 hover:bg-blue-50 hover:border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                  {!isCurrentPeriod && onToday && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToday();
                      }}
                      className="h-8 px-3 text-xs hover:bg-blue-50 hover:border-blue-300 ml-4"
                    >
                      {period === 'Daily' ? 'Today' : 'Current Month'}
                    </Button>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

