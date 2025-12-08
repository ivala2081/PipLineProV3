import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useTabPersistence } from '../hooks/useTabPersistence';
import { Breadcrumb } from '../components/ui';
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
  Calendar,
  Download,
  Filter,
  Search,
  Eye,
  ArrowLeft,
  LineChart,
  Building2,
  Globe,
  Clock,
  X,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useNavigate } from 'react-router-dom';
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
  Cell,
  Area,
  AreaChart
} from 'recharts';
import { 
  UnifiedSection,
  UnifiedGrid,
  UnifiedCard,
  UnifiedButton,
  UnifiedBadge,
  UnifiedWrapper
} from '../design-system';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

interface Transaction {
  id: number;
  client_name: string;
  amount: number;
  currency: string;
  date: string;
  category: string;
  psp: string;
  commission: number;
  net_amount: number;
  created_at: string;
}

interface RevenueData {
  date: string;
  amount: number;
  deposits: number;
  withdrawals: number;
  commissions: number;
  transaction_count: number;
  client_count: number;
}

interface AnalyticsData {
  daily_revenue: RevenueData[];
  total_revenue: number;
  total_transactions: number;
  total_deposits: number;
  total_withdrawals: number;
  average_daily_revenue: number;
  growth_rate: number;
  top_clients: Array<{
    client_name: string;
    total_amount: number;
    transaction_count: number;
  }>;
  psp_breakdown: Array<{
    psp: string;
    total_amount: number;
    transaction_count: number;
    percentage: number;
  }>;
  category_breakdown: Array<{
    category: string;
    total_amount: number;
    transaction_count: number;
    percentage: number;
  }>;
}

export default function RevenueAnalytics() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, handleTabChange] = useTabPersistence('overview');
  const [timeRange, setTimeRange] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedClient, setSelectedClient] = useState('all');
  const [selectedPSP, setSelectedPSP] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds default

  // Fetch analytics data
  const fetchAnalyticsData = useCallback(async () => {
    try {
      setLoading(true);
      setRefreshing(true);
      setError(null);

      const response = await fetch(`/api/v1/analytics/revenue-detailed?range=${timeRange}`, {
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
        setError('Failed to fetch revenue analytics data');
      }
    } catch (error) {
      console.error('Error fetching revenue analytics data:', error);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  // Auto-refresh functionality
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchAnalyticsData();
      }, refreshInterval);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [autoRefresh, refreshInterval, fetchAnalyticsData]);

  const handleRefresh = useCallback(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  const toggleAutoRefresh = useCallback(() => {
    setAutoRefresh(prev => !prev);
  }, []);

  const handleRefreshIntervalChange = useCallback((interval: string) => {
    const intervalMs = parseInt(interval) * 1000;
    setRefreshInterval(intervalMs);
  }, []);

  const handleBackToDashboard = useCallback(() => {
    navigate('/dashboard');
  }, [navigate]);

  const formatCurrency = useCallback((amount: number, currency: string = '₺') => {
    try {
      const formatted = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency === '₺' ? 'TRY' : currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(amount);
      
      return formatted
        .replace(/TRY/g, '₺')
        .replace(/USD/g, '$')
        .replace(/EUR/g, '€')
        .replace(/GBP/g, '£');
    } catch (error) {
      return `${currency}${amount.toLocaleString()}`;
    }
  }, []);

  const formatNumber = useCallback((num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  }, []);

  // Filter data based on search and filters
  const filteredData = useMemo(() => {
    if (!analyticsData) return null;

    let filtered = { ...analyticsData };

    // Apply client filter
    if (selectedClient !== 'all') {
      filtered.top_clients = filtered.top_clients.filter(
        client => client.client_name.toLowerCase().includes(selectedClient.toLowerCase())
      );
    }

    // Apply PSP filter
    if (selectedPSP !== 'all') {
      filtered.psp_breakdown = filtered.psp_breakdown.filter(
        psp => psp.psp.toLowerCase().includes(selectedPSP.toLowerCase())
      );
    }

    // Apply category filter
    if (selectedCategory !== 'all') {
      filtered.category_breakdown = filtered.category_breakdown.filter(
        cat => cat.category.toLowerCase().includes(selectedCategory.toLowerCase())
      );
    }

    return filtered;
  }, [analyticsData, selectedClient, selectedPSP, selectedCategory]);

  // Chart colors
  const chartColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'];

  if (loading) {
    return (
      <ContentArea spacing="xl">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
            <p className="text-gray-600">Loading revenue analytics...</p>
          </div>
        </div>
      </ContentArea>
    );
  }

  if (error) {
    return (
      <ContentArea spacing="xl">
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <X className="h-8 w-8 text-red-600" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Data</h3>
          <p className="text-gray-600 mb-6">{error}</p>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </ContentArea>
    );
  }

  if (!analyticsData) {
    return (
      <ContentArea spacing="xl">
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="h-8 w-8 text-yellow-600" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Data Available</h3>
          <p className="text-gray-600 mb-6">No analytics data available for the selected time range</p>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </ContentArea>
    );
  }

  return (
    <div className="p-6">

      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-gray-600" />
              Revenue Analytics
            </h1>
            <p className="text-gray-600">Comprehensive revenue analysis with all transaction data</p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={handleBackToDashboard}
              variant="outline"
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Dashboard
            </Button>
            <div className="flex items-center gap-2">
              <Button
                onClick={handleRefresh}
                disabled={refreshing}
                variant="secondary"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>
              
              <div className="flex items-center gap-2 pl-4 border-l border-gray-200">
                <Button
                  onClick={toggleAutoRefresh}
                  variant={autoRefresh ? "primary" : "outline"}
                  size="sm"
                >
                  <Activity className="h-4 w-4 mr-2" />
                  Auto Refresh
                </Button>
                
                {autoRefresh && (
                  <Select value={(refreshInterval / 1000).toString()} onValueChange={handleRefreshIntervalChange}>
                    <SelectTrigger className="w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10s</SelectItem>
                      <SelectItem value="30">30s</SelectItem>
                      <SelectItem value="60">1m</SelectItem>
                      <SelectItem value="300">5m</SelectItem>
                      <SelectItem value="600">10m</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Filters & Controls</h3>
            <Button
              onClick={() => setShowFilters(!showFilters)}
              variant="ghost"
              size="sm"
            >
              <Filter className="h-4 w-4 mr-2" />
              {showFilters ? 'Hide Filters' : 'Show Filters'}
              {showFilters ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
            </Button>
          </div>
          
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">Time Range</label>
                <Select value={timeRange} onValueChange={setTimeRange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Time</SelectItem>
                    <SelectItem value="7d">Last 7 Days</SelectItem>
                    <SelectItem value="30d">Last 30 Days</SelectItem>
                    <SelectItem value="90d">Last 90 Days</SelectItem>
                    <SelectItem value="1y">Last Year</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search clients, PSPs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">Client</label>
                <Select value={selectedClient} onValueChange={setSelectedClient}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Clients</SelectItem>
                    {analyticsData?.top_clients?.map((client, index) => (
                      <SelectItem key={index} value={client.client_name}>
                        {client.client_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">PSP</label>
                <Select value={selectedPSP} onValueChange={setSelectedPSP}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All PSPs</SelectItem>
                    {analyticsData?.psp_breakdown?.map((psp, index) => (
                      <SelectItem key={index} value={psp.psp}>
                        {psp.psp}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="mb-6">
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Key Metrics</h2>
          <p className="text-gray-600">Revenue overview and key performance indicators</p>
        </div>
        <CardGrid cols={4} gap="lg">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{t('common.total_revenue')}</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {formatCurrency(analyticsData?.total_revenue || 0)}
                  </p>
                  <div className="flex items-center mt-2">
                    <ArrowUpRight className="h-4 w-4 text-green-500 mr-1" />
                    <span className="text-sm text-green-600">
                      {analyticsData?.growth_rate ? (analyticsData.growth_rate > 0 ? '+' : '') + analyticsData.growth_rate.toFixed(1) + '%' : '0.0%'}
                    </span>
                  </div>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <DollarSign className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{t('common.total_transactions')}</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {formatNumber(analyticsData.total_transactions)}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    All time
                  </p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <Activity className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{t('common.total_deposits')}</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {formatCurrency(analyticsData?.total_deposits || 0)}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {analyticsData?.total_deposits && analyticsData?.total_revenue ? 
                      ((analyticsData.total_deposits / analyticsData.total_revenue) * 100).toFixed(1) + '% of total' : 
                      '0.0% of total'}
                  </p>
                </div>
                <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-emerald-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{t('common.average_daily')}</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {formatCurrency(analyticsData.average_daily_revenue)}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Revenue per day
                  </p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Calendar className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </CardGrid>
      </div>

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-gray-50/80 border border-gray-200/60 rounded-lg shadow-sm">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              {t('tabs.overview')}
            </TabsTrigger>
            <TabsTrigger value="trends" className="flex items-center gap-2">
              <LineChart className="h-4 w-4" />
              {t('tabs.trends')}
            </TabsTrigger>
            <TabsTrigger value="clients" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              {t('navigation.clients')}
            </TabsTrigger>
            <TabsTrigger value="breakdown" className="flex items-center gap-2">
              <PieChart className="h-4 w-4" />
              {t('tabs.breakdown')}
            </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
            {/* Revenue Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Revenue Trends
                </CardTitle>
                <CardDescription>Daily revenue performance over time (Bar Chart)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analyticsData?.daily_revenue || []} key="revenue-bar-chart" margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                      <defs>
                        <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3B82F6" stopOpacity={1} />
                          <stop offset="25%" stopColor="#60A5FA" stopOpacity={0.95} />
                          <stop offset="50%" stopColor="#93C5FD" stopOpacity={0.9} />
                          <stop offset="75%" stopColor="#BFDBFE" stopOpacity={0.85} />
                          <stop offset="100%" stopColor="#E0F2FE" stopOpacity={0.8} />
                        </linearGradient>
                        <filter id="revenueBarShadow" x="-50%" y="-50%" width="200%" height="200%">
                          <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#3B82F6" floodOpacity="0.15"/>
                        </filter>
                      </defs>
                      <CartesianGrid 
                        strokeDasharray="1 3" 
                        stroke="#f1f5f9" 
                        strokeWidth={1}
                        vertical={false}
                        opacity={0.8}
                      />
                      <XAxis 
                        dataKey="date" 
                        stroke="#475569" 
                        fontSize={12}
                        fontWeight={600}
                        tickLine={false}
                        axisLine={{ stroke: '#e2e8f0', strokeWidth: 1 }}
                        tick={{ fill: '#475569' }}
                        tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
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
                            const dateStr = data.date;
                            const date = new Date(dateStr + 'T00:00:00'); // Add time to avoid timezone issues
                            
                            return (
                              <div className="bg-white border border-slate-200 rounded-lg shadow-2xl p-5 min-w-[220px] backdrop-blur-sm">
                                <div className="space-y-3">
                                  <div className="flex items-center gap-2">
                                    <Calendar className="h-4 w-4 text-slate-600" />
                                    <span className="font-semibold text-slate-900 text-sm">
                                      {date.toLocaleDateString('en-US', { 
                                        weekday: 'long', 
                                        year: 'numeric', 
                                        month: 'long', 
                                        day: 'numeric' 
                                      })}
                                    </span>
                                  </div>
                                  
                                  <div className="border-t border-slate-100 pt-3 space-y-2">
                                    <div className="flex justify-between items-center">
                                      <span className="text-sm font-medium text-slate-700">Net Cash:</span>
                                      <span className={`font-bold text-base ${data.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {formatCurrency(data.amount || 0, '₺')}
                                      </span>
                                    </div>
                                    
                                    <div className="flex justify-between items-center">
                                      <span className="text-sm font-medium text-slate-700">Transactions:</span>
                                      <span className="text-sm font-semibold text-slate-800">
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
                        cursor={{ fill: 'rgba(59, 130, 246, 0.05)' }}
                      />
                      <Bar 
                        dataKey="amount" 
                        fill="url(#revenueGradient)"
                        radius={[6, 6, 0, 0]}
                        stroke="none"
                        filter="url(#revenueBarShadow)"
                        style={{
                          filter: 'drop-shadow(0 4px 8px rgba(59, 130, 246, 0.15))',
                        }}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Top Clients */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Top Clients by Revenue
                </CardTitle>
                <CardDescription>Clients with highest transaction volume</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData?.top_clients?.slice(0, 10).map((client, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-700">#{index + 1}</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{client.client_name}</p>
                          <p className="text-sm text-gray-500">{client.transaction_count} transactions</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">{formatCurrency(client.total_amount)}</p>
                        <p className="text-sm text-gray-500">
                          {analyticsData?.total_revenue ? 
                            ((client.total_amount / analyticsData.total_revenue) * 100).toFixed(1) + '%' : 
                            '0.0%'}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="mt-6">
            {/* Revenue vs Deposits vs Withdrawals */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Revenue Breakdown
                </CardTitle>
                <CardDescription>Daily breakdown of deposits, withdrawals, and net revenue</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analyticsData?.daily_revenue || []} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                      <defs>
                        <linearGradient id="depositsGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#10B981" stopOpacity={1} />
                          <stop offset="25%" stopColor="#34D399" stopOpacity={0.95} />
                          <stop offset="50%" stopColor="#6EE7B7" stopOpacity={0.9} />
                          <stop offset="75%" stopColor="#A7F3D0" stopOpacity={0.85} />
                          <stop offset="100%" stopColor="#D1FAE5" stopOpacity={0.8} />
                        </linearGradient>
                        <linearGradient id="withdrawalsGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#EF4444" stopOpacity={1} />
                          <stop offset="25%" stopColor="#F87171" stopOpacity={0.95} />
                          <stop offset="50%" stopColor="#FCA5A5" stopOpacity={0.9} />
                          <stop offset="75%" stopColor="#FECACA" stopOpacity={0.85} />
                          <stop offset="100%" stopColor="#FEE2E2" stopOpacity={0.8} />
                        </linearGradient>
                        <linearGradient id="netRevenueGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3B82F6" stopOpacity={1} />
                          <stop offset="25%" stopColor="#60A5FA" stopOpacity={0.95} />
                          <stop offset="50%" stopColor="#93C5FD" stopOpacity={0.9} />
                          <stop offset="75%" stopColor="#BFDBFE" stopOpacity={0.85} />
                          <stop offset="100%" stopColor="#E0F2FE" stopOpacity={0.8} />
                        </linearGradient>
                        <filter id="depositsShadow" x="-50%" y="-50%" width="200%" height="200%">
                          <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#10B981" floodOpacity="0.15"/>
                        </filter>
                        <filter id="withdrawalsShadow" x="-50%" y="-50%" width="200%" height="200%">
                          <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#EF4444" floodOpacity="0.15"/>
                        </filter>
                      </defs>
                      <CartesianGrid 
                        strokeDasharray="1 3" 
                        stroke="#f1f5f9" 
                        strokeWidth={1}
                        vertical={false}
                        opacity={0.8}
                      />
                      <XAxis 
                        dataKey="date" 
                        stroke="#475569" 
                        fontSize={12}
                        fontWeight={600}
                        tickLine={false}
                        axisLine={{ stroke: '#e2e8f0', strokeWidth: 1 }}
                        tick={{ fill: '#475569' }}
                        tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
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
                            const dateStr = data.date;
                            const date = new Date(dateStr + 'T00:00:00'); // Add time to avoid timezone issues
                            
                            return (
                              <div className="bg-white border border-slate-200 rounded-lg shadow-2xl p-5 min-w-[220px] backdrop-blur-sm">
                                <div className="space-y-3">
                                  <div className="flex items-center gap-2">
                                    <Calendar className="h-4 w-4 text-slate-600" />
                                    <span className="font-semibold text-slate-900 text-sm">
                                      {date.toLocaleDateString('en-US', { 
                                        weekday: 'long', 
                                        year: 'numeric', 
                                        month: 'long', 
                                        day: 'numeric' 
                                      })}
                                    </span>
                                  </div>
                                  
                                  <div className="border-t border-slate-100 pt-3 space-y-2">
                                    <div className="flex justify-between items-center">
                                      <span className="text-sm font-medium text-slate-700">Net Cash:</span>
                                      <span className={`font-bold text-base ${data.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {formatCurrency(data.amount || 0, '₺')}
                                      </span>
                                    </div>
                                    
                                    <div className="flex justify-between items-center">
                                      <span className="text-sm font-medium text-slate-700">Transactions:</span>
                                      <span className="text-sm font-semibold text-slate-800">
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
                        cursor={{ fill: 'rgba(59, 130, 246, 0.05)' }}
                      />
                      <Bar 
                        dataKey="deposits" 
                        fill="url(#depositsGradient)" 
                        name="Deposits" 
                        radius={[6, 6, 0, 0]}
                        stroke="none"
                        filter="url(#depositsShadow)"
                        style={{
                          filter: 'drop-shadow(0 4px 8px rgba(16, 185, 129, 0.15))',
                        }}
                      />
                      <Bar 
                        dataKey="withdrawals" 
                        fill="url(#withdrawalsGradient)" 
                        name="Withdrawals" 
                        radius={[6, 6, 0, 0]}
                        stroke="none"
                        filter="url(#withdrawalsShadow)"
                        style={{
                          filter: 'drop-shadow(0 4px 8px rgba(239, 68, 68, 0.15))',
                        }}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

        {/* Clients Tab */}
        <TabsContent value="clients" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Client Performance Analysis
                </CardTitle>
                <CardDescription>Detailed client revenue and transaction analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Rank
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Client
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total Revenue
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Transactions
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Avg Transaction
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Market Share
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {analyticsData?.top_clients?.map((client, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                              <span className="text-sm font-medium text-white">#{index + 1}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {client.client_name}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(client.total_amount)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatNumber(client.transaction_count)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(client.total_amount / client.transaction_count)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {analyticsData?.total_revenue ? 
                              ((client.total_amount / analyticsData.total_revenue) * 100).toFixed(1) + '%' : 
                              '0.0%'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

        {/* Breakdown Tab */}
        <TabsContent value="breakdown" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* PSP Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5" />
                    PSP Breakdown
                  </CardTitle>
                  <CardDescription>Revenue distribution by Payment Service Provider</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPieChart>
                        <Pie
                          data={analyticsData?.psp_breakdown?.map((item, index) => ({
                            name: item.psp,
                            value: item.total_amount,
                            fill: chartColors[index % chartColors.length]
                          }))}
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          dataKey="value"
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        >
                          {analyticsData?.psp_breakdown?.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value: number) => [formatCurrency(value, '₺'), 'Revenue']} />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Category Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="h-5 w-5" />
                    Category Breakdown
                  </CardTitle>
                  <CardDescription>Revenue distribution by transaction category</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {analyticsData?.category_breakdown?.map((category, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge 
                              variant={category.category === 'WD' ? 'destructive' : 'default'}
                            >
                              {category.category}
                            </Badge>
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
                            style={{ width: `${category.percentage}%` }}
                          ></div>
                        </div>
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>{category.transaction_count} transactions</span>
                          <span>{category?.percentage ? category.percentage.toFixed(1) + '%' : '0.0%'}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
