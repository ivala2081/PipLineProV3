import { useState, useEffect } from 'react';
import { useTabPersistence } from '../hooks/useTabPersistence';
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Users,
  PieChart,
  Activity,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  Building2,
  Globe,
  FileText,
  AlertCircle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { UnifiedCard, UnifiedButton, UnifiedBadge, UnifiedSection, UnifiedGrid } from '../design-system';
import { AnalyticsPageSkeleton } from '../components/EnhancedSkeletonLoaders';
import { AnimatedValue } from '../components/AnimatedValue';
import { 
  Breadcrumb, 
  DataExport, 
  QuickActions,
  useKeyboardShortcuts,
  COMMON_SHORTCUTS,
  CardSkeleton,
  ChartSkeleton
} from '../components/ui';

interface PspSummary {
  psp: string;
  total_amount: number;
  total_commission: number;
  total_net: number;
  transaction_count: number;
}

interface CategorySummary {
  category: string;
  total_amount: number;
  total_commission: number;
  total_net: number;
  transaction_count: number;
}

interface ClientSummary {
  client_name: string;
  total_amount: number;
  total_commission: number;
  total_net: number;
  transaction_count: number;
}

interface AnalyticsData {
  psp_summary: PspSummary[];
  category_summary: CategorySummary[];
  client_summary: ClientSummary[];
  date_range: {
    start_date: string;
    end_date: string;
  };
}

export default function Analytics() {
  const { t } = useLanguage();
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleExportAnalytics = () => {
    // TODO: Implement analytics data export functionality
    alert(t('analytics.export_coming_soon'));
  };
  const [activeTab, handleTabChange] = useTabPersistence('overview');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  // Keyboard shortcuts
  useKeyboardShortcuts([
    {
      ...COMMON_SHORTCUTS.REFRESH,
      action: () => fetchAnalyticsData()
    },
    {
      key: 'e',
      ctrlKey: true,
      action: () => handleExportAnalytics()
    }
  ]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setRefreshing(true);
      setError(null);

      const response = await fetch('/api/analytics/overview', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      } else if (response.status === 401) {
        setError('Authentication required. Please log in.');
      } else {
        setError('Failed to fetch analytics data');
      }
    } catch (error) {
      console.error('Error fetching analytics data:', error);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return `$${amount.toLocaleString()}`;
  };

  const formatPercentage = (value: number, total: number) => {
    if (total === 0) return '0%';
    return `${((value / total) * 100).toFixed(1)}%`;
  };

  // Generate quick stats from analytics data
  const getQuickStats = () => {
    if (!analyticsData) return [];
    
    const totalAmount = analyticsData.psp_summary.reduce(
      (sum, item) => sum + item.total_amount,
      0
    );
    const totalCommission = analyticsData.psp_summary.reduce(
      (sum, item) => sum + item.total_commission,
      0
    );
    const totalTransactions = analyticsData.psp_summary.reduce(
      (sum, item) => sum + item.transaction_count,
      0
    );
    const activeClients = analyticsData.client_summary.length;

    return [
      {
        label: 'Total Revenue',
        value: formatCurrency(totalAmount),
        change: '+12.5%',
        trend: 'up' as const,
        icon: DollarSign,
        color: 'text-green-600',
        bgColor: 'bg-green-50'
      },
      {
        label: 'Total Commission',
        value: formatCurrency(totalCommission),
        change: '+8.2%',
        trend: 'up' as const,
        icon: TrendingUp,
        color: 'text-gray-600',
        bgColor: 'bg-gray-50'
      },
      {
        label: 'Active Clients',
        value: activeClients.toString(),
        change: '+15.3%',
        trend: 'up' as const,
        icon: Users,
        color: 'text-purple-600',
        bgColor: 'bg-purple-50'
      },
      {
        label: 'Total Transactions',
        value: totalTransactions.toString(),
        change: '+5.7%',
        trend: 'up' as const,
        icon: Activity,
        color: 'text-orange-600',
        bgColor: 'bg-orange-50'
      }
    ];
  };

  if (loading) {
    return <AnalyticsPageSkeleton />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Modern Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                  <BarChart3 className="h-8 w-8 text-gray-600" />
                  {t('analytics.title')}
                </h1>
                <p className="text-gray-600">{t('analytics.description')}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Error State */}
        <div className="p-6">
          <UnifiedCard variant="elevated">
            <CardContent className="p-12 text-center">
              <div className="text-red-500 mb-6">
                <AlertCircle className="h-16 w-16 mx-auto" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Error Loading Analytics
              </h3>
              <p className="text-gray-600 mb-6">{error}</p>
              <UnifiedButton
                variant="primary"
                onClick={fetchAnalyticsData}
                icon={<RefreshCw className="h-4 w-4" />}
                iconPosition="left"
              >
                Try Again
              </UnifiedButton>
            </CardContent>
          </UnifiedCard>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Modern Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                  <BarChart3 className="h-8 w-8 text-gray-600" />
                  {t('analytics.title')}
                </h1>
                <p className="text-gray-600">{t('analytics.description')}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Empty State */}
        <div className="p-6">
          <UnifiedCard variant="elevated">
            <CardContent className="p-12 text-center">
              <div className="text-gray-400 mb-6">
                <BarChart3 className="h-16 w-16 mx-auto" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                No Analytics Data
              </h3>
              <p className="text-gray-600">
                No analytics data is currently available.
              </p>
            </CardContent>
          </UnifiedCard>
        </div>
      </div>
    );
  }

  // Calculate totals for percentages
  const totalAmount = analyticsData.psp_summary.reduce(
    (sum, item) => sum + item.total_amount,
    0
  );
  const totalCommission = analyticsData.psp_summary.reduce(
    (sum, item) => sum + item.total_commission,
    0
  );

  return (
    <div className="p-6">

      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <BarChart3 className="h-8 w-8 text-gray-600" />
              {t('analytics.title')}
            </h1>
            <p className="text-gray-600">{t('analytics.description')}</p>
          </div>
          <div className="flex items-center gap-3">
              <QuickActions actions={[
                {
                  id: 'refresh',
                  label: refreshing ? 'Refreshing...' : 'Refresh Data',
                  icon: <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />,
                  action: () => fetchAnalyticsData(),
                  variant: 'outline'
                },
                {
                  id: 'export',
                  label: 'Export Data',
                  icon: <FileText className="h-4 w-4" />,
                  action: () => handleExportAnalytics(),
                  variant: 'outline'
                }
              ]} />
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
          <TabsTrigger value="performance" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:border data-[state=active]:border-gray-200">
            <TrendingUp className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('tabs.performance')}</span>
          </TabsTrigger>
          <TabsTrigger value="clients" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:border data-[state=active]:border-gray-200">
            <Users className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('navigation.clients')}</span>
          </TabsTrigger>
          <TabsTrigger value="insights" className="group flex items-center gap-2 transition-all duration-300 ease-in-out hover:bg-white/90 hover:shadow-md hover:scale-[1.02] data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:border data-[state=active]:border-gray-200">
            <Target className="h-4 w-4 transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:text-blue-600" />
            <span className="transition-all duration-300 ease-in-out group-hover:font-semibold">{t('tabs.insights')}</span>
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          {/* Quick Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {getQuickStats().map((stat, index) => (
                <UnifiedCard key={index} variant="elevated" showGlass={index < 2} className="relative overflow-hidden">
                  <div className={`absolute top-0 right-0 w-32 h-32 ${stat.bgColor} rounded-full -translate-y-16 translate-x-16`}></div>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`w-12 h-12 ${stat.bgColor} rounded-xl flex items-center justify-center shadow-lg`}>
                        <stat.icon className={`h-6 w-6 ${stat.color}`} />
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${stat.color}`}>
                          {stat.change}
                        </span>
                        {stat.trend === 'up' ? (
                          <ArrowUpRight className="h-4 w-4 text-green-500" />
                        ) : (
                          <ArrowDownRight className="h-4 w-4 text-red-500" />
                        )}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                      <p className="text-3xl font-bold text-gray-900">
                        <AnimatedValue value={stat.value} animated={true} duration={500} />
                      </p>
                    </div>
                  </CardContent>
                </UnifiedCard>
              ))}
            </div>

            {/* Date Range Info */}
            <UnifiedCard variant="outlined">
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Globe className="h-4 w-4 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Data Period</p>
                    <p className="text-sm text-gray-600">
                      {analyticsData.date_range.start_date} to {analyticsData.date_range.end_date}
                    </p>
                  </div>
                </div>
              </CardContent>
            </UnifiedCard>
          </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="mt-6">
          {/* PSP Performance */}
          <UnifiedCard variant="elevated" showGlass={true}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5" />
                  PSP Performance
                </CardTitle>
                <CardDescription>Revenue by Payment Service Provider</CardDescription>
              </CardHeader>
              <CardContent>
                {analyticsData.psp_summary.length > 0 ? (
                  <div className="space-y-4">
                    {analyticsData.psp_summary.map(psp => (
                      <div key={psp.psp} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-900">{psp.psp}</span>
                          <span className="text-sm text-gray-500">{formatCurrency(psp.total_amount)}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-gray-500 to-gray-600 h-2 rounded-full"
                            style={{ width: `${formatPercentage(psp.total_amount, totalAmount)}` }}
                          ></div>
                        </div>
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>{psp.transaction_count} transactions</span>
                          <span>{formatPercentage(psp.total_amount, totalAmount)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <PieChart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No PSP data available</p>
                  </div>
                )}
              </CardContent>
            </UnifiedCard>

            {/* Category Breakdown */}
            <UnifiedCard variant="elevated">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Category Breakdown
                </CardTitle>
                <CardDescription>Revenue by transaction category</CardDescription>
              </CardHeader>
              <CardContent>
                {analyticsData.category_summary.length > 0 ? (
                  <div className="space-y-4">
                    {analyticsData.category_summary.map(category => (
                      <div key={category.category} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <UnifiedBadge 
                              variant={category.category === 'WD' ? 'destructive' : 'success'}
                              size="sm"
                            >
                              {category.category}
                            </UnifiedBadge>
                            <span className="text-sm font-medium text-gray-900">{category.category}</span>
                          </div>
                          <span className="text-sm text-gray-500">{formatCurrency(category.total_amount)}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              category.category === 'WD'
                                ? 'bg-gradient-to-r from-red-500 to-red-600'
                                : 'bg-gradient-to-r from-green-500 to-green-600'
                            }`}
                            style={{ width: `${formatPercentage(category.total_amount, totalAmount)}` }}
                          ></div>
                        </div>
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>{category.transaction_count} transactions</span>
                          <span>{formatPercentage(category.total_amount, totalAmount)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No category data available</p>
                  </div>
                )}
              </CardContent>
            </UnifiedCard>
          </TabsContent>

        {/* Clients Tab */}
        <TabsContent value="clients" className="mt-6">
          <UnifiedCard variant="elevated">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Top Clients
                </CardTitle>
                <CardDescription>Clients with highest transaction volume</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {analyticsData.client_summary.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Client
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Total Amount
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Commission
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Transactions
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Avg Transaction
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {analyticsData.client_summary.slice(0, 10).map((client, index) => (
                          <tr key={client.client_name} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-8 h-8 bg-gradient-to-br from-gray-500 to-gray-600 rounded-full flex items-center justify-center mr-3">
                                  <span className="text-sm font-medium text-white">
                                    #{index + 1}
                                  </span>
                                </div>
                                <div className="text-sm font-medium text-gray-900">
                                  {client.client_name}
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(client.total_amount)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(client.total_commission)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {client.transaction_count}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(client.total_amount / client.transaction_count)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No client data available</p>
                  </div>
                )}
              </CardContent>
            </UnifiedCard>
          </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <UnifiedCard variant="elevated">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Key Insights
                  </CardTitle>
                  <CardDescription>Important findings from your data</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <span className="text-sm font-medium text-green-900">Top Performer</span>
                      </div>
                      <p className="text-sm text-green-700">
                        {analyticsData.psp_summary[0]?.psp || 'N/A'} is your top performing PSP with {formatCurrency(analyticsData.psp_summary[0]?.total_amount || 0)} in revenue.
                      </p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center gap-2 mb-2">
                        <Building2 className="h-5 w-5 text-gray-600" />
                        <span className="text-sm font-medium text-gray-900">Client Growth</span>
                      </div>
                      <p className="text-sm text-gray-700">
                        You have {analyticsData.client_summary.length} active clients contributing to your business.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </UnifiedCard>

              <UnifiedCard variant="elevated">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Summary Report
                  </CardTitle>
                  <CardDescription>Quick overview of your analytics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{t('common.total_revenue')}</span>
                      <span className="text-sm font-semibold text-gray-900">
                        <AnimatedValue value={formatCurrency(totalAmount)} animated={true} duration={500} />
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{t('common.total_commission')}</span>
                      <span className="text-sm font-semibold text-gray-900">
                        <AnimatedValue value={formatCurrency(totalCommission)} animated={true} duration={500} />
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Active Clients</span>
                      <span className="text-sm font-semibold text-gray-900">{analyticsData.client_summary.length}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{t('common.total_transactions')}</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {analyticsData.psp_summary.reduce((sum, item) => sum + item.transaction_count, 0)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </UnifiedCard>
            </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
