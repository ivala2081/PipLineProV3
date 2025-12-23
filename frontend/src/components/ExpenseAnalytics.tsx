import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  PieChart,
  Download,
  RefreshCw,
  DollarSign,
  Activity,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { api } from '../utils/apiClient';
import { useNotifications } from '../hooks/useNotifications';

interface ExpenseAnalyticsProps {
  currency?: 'USD' | 'TRY' | 'USDT';
}

export default function ExpenseAnalytics({ currency = 'USD' }: ExpenseAnalyticsProps) {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { error: showError } = useNotifications();

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/accounting/expenses/analytics?currency=${currency}`);
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          setAnalytics(data.data);
        } else {
          showError(data.error || 'Failed to load analytics');
        }
      }
    } catch (err) {
      console.error('Error loading analytics:', err);
      showError('Failed to load expense analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [currency]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-20 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No analytics data available</p>
          <Button onClick={fetchAnalytics} variant="outline" className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const { summary, monthly_trends, category_breakdown, status_breakdown, top_expenses, current_month } = analytics;
  const currencySymbol = currency === 'USD' ? '$' : currency === 'TRY' ? '₺' : 'USDT';

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900">Expense Analytics</h2>
        <div className="flex gap-2">
          <Button onClick={fetchAnalytics} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Expenses */}
        <Card className="border-gray-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Expenses</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {currencySymbol}{summary.total_expenses.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-gray-500 mt-1">{summary.total_count} transactions</p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <DollarSign className="h-6 w-6 text-gray-700" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Net Amount */}
        <Card className="border-gray-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Net Amount</p>
                <p className={`text-2xl font-bold mt-1 ${summary.net_amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {currencySymbol}{summary.net_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-gray-500 mt-1">Inflow - Outflow</p>
              </div>
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${summary.net_amount >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                {summary.net_amount >= 0 ? (
                  <TrendingUp className={`h-6 w-6 ${summary.net_amount >= 0 ? 'text-green-600' : 'text-red-600'}`} />
                ) : (
                  <TrendingDown className="h-6 w-6 text-red-600" />
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Average Expense */}
        <Card className="border-gray-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Average Expense</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {currencySymbol}{summary.average_expense.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-gray-500 mt-1">Per transaction</p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <Activity className="h-6 w-6 text-gray-700" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pending Payments */}
        <Card className="border-gray-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Payments</p>
                <p className="text-2xl font-bold text-orange-600 mt-1">
                  {summary.pending_count}
                </p>
                <p className="text-xs text-gray-500 mt-1">Awaiting payment</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <AlertCircle className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Current Month Summary */}
      <Card className="border-gray-200">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-gray-900">This Month Summary</CardTitle>
          <CardDescription>Current month expense overview</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-600 mb-1">Total</p>
              <p className="text-xl font-bold text-gray-900">
                {currencySymbol}{current_month.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm text-green-700 mb-1">Inflow</p>
              <p className="text-xl font-bold text-green-900">
                {currencySymbol}{current_month.inflow.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-sm text-red-700 mb-1">Outflow</p>
              <p className="text-xl font-bold text-red-900">
                {currencySymbol}{current_month.outflow.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-700 mb-1">Paid</p>
              <p className="text-xl font-bold text-blue-900">
                {current_month.paid_count}
              </p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
              <p className="text-sm text-orange-700 mb-1">Pending</p>
              <p className="text-xl font-bold text-orange-900">
                {current_month.pending_count}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Monthly Trends & Category Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Monthly Trends */}
        <Card className="border-gray-200">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-gray-600" />
              Monthly Trends
            </CardTitle>
            <CardDescription>Last 6 months expense trends</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {monthly_trends.slice(0, 6).map((month: any) => {
                const maxValue = Math.max(...monthly_trends.map((m: any) => m.total));
                const percentage = (month.total / maxValue) * 100;
                
                return (
                  <div key={month.month} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-gray-700">{month.month}</span>
                      <span className="text-gray-900 font-semibold">
                        {currencySymbol}{month.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-gray-700 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{month.count} transactions</span>
                      <span>↑{month.inflow.toFixed(0)} ↓{month.outflow.toFixed(0)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Category Breakdown */}
        <Card className="border-gray-200">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <PieChart className="h-5 w-5 text-gray-600" />
              Category Breakdown
            </CardTitle>
            <CardDescription>Inflow vs Outflow distribution</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Inflow */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Inflow</span>
                  <span className="text-sm font-bold text-green-600">
                    {currencySymbol}{category_breakdown.inflow.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div 
                    className="bg-green-600 h-4 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${(category_breakdown.inflow / (category_breakdown.inflow + category_breakdown.outflow)) * 100}%` 
                    }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {((category_breakdown.inflow / (category_breakdown.inflow + category_breakdown.outflow)) * 100).toFixed(1)}% of total
                </p>
              </div>

              {/* Outflow */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Outflow</span>
                  <span className="text-sm font-bold text-red-600">
                    {currencySymbol}{category_breakdown.outflow.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div 
                    className="bg-red-600 h-4 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${(category_breakdown.outflow / (category_breakdown.inflow + category_breakdown.outflow)) * 100}%` 
                    }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {((category_breakdown.outflow / (category_breakdown.inflow + category_breakdown.outflow)) * 100).toFixed(1)}% of total
                </p>
              </div>

              {/* Status Distribution */}
              <div className="pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Status Distribution</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                    <p className="text-xs text-green-700 mb-1">Paid</p>
                    <p className="text-lg font-bold text-green-900">{status_breakdown.paid}</p>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg border border-orange-200">
                    <p className="text-xs text-orange-700 mb-1">Pending</p>
                    <p className="text-lg font-bold text-orange-900">{status_breakdown.pending}</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-xs text-gray-700 mb-1">Cancelled</p>
                    <p className="text-lg font-bold text-gray-900">{status_breakdown.cancelled}</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Expenses */}
      <Card className="border-gray-200">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-gray-900">Top 10 Expenses</CardTitle>
          <CardDescription>Highest expense transactions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {top_expenses.map((expense: any, index: number) => (
              <div 
                key={expense.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-sm font-semibold text-gray-700">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{expense.description}</p>
                    {expense.date && (
                      <p className="text-xs text-gray-500">{new Date(expense.date).toLocaleDateString()}</p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-gray-900">
                    {currencySymbol}{expense.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

