import { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { Breadcrumb } from '../components/ui';
import {
  DollarSign,
  Users,
  Activity,
  TrendingUp,
  BarChart3,
  PieChart,
  LineChart,
  Calendar,
  Filter,
  Download,
  Eye,
  RefreshCw,
  Target,
  Zap,
  Award,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUpIcon,
  TrendingDownIcon,
  Minus,
  Building,
  Globe,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
} from 'lucide-react';
import { UnifiedCard, UnifiedButton, UnifiedBadge, UnifiedSection, UnifiedGrid } from '../design-system';
import StandardMetricsCard from '../components/StandardMetricsCard';

// TypeScript interfaces for analytics data
interface DashboardStats {
  total_transactions: number;
  total_revenue: number;
  avg_transaction: number;
  unique_clients: number;
  total_commission: number;
}

interface RevenueTrend {
  date: string;
  revenue: number;
  transactions: number;
}

interface TopPerformer {
  client: string;
  revenue: number;
  transactions: number;
}

interface SystemPerformance {
  cpu_usage: number;
  memory_usage: number;
  memory_available: number;
  disk_usage: number;
  disk_free: number;
  timestamp: string;
}

interface BusinessRecommendation {
  id: number;
  type: string;
  priority: string;
  title: string;
  description: string;
  impact: string;
  effort: string;
  category: string;
}

interface MarketAnalysis {
  market_size_estimate: number;
  market_share: string;
  competition_level: string;
  growth_potential: string;
  customer_segments: number;
  average_client_value: number;
}

interface AnalyticsData {
  dashboard_stats: DashboardStats;
  revenue_trends: RevenueTrend[];
  top_performers: TopPerformer[];
  system_performance: SystemPerformance;
  business_recommendations: BusinessRecommendation[];
  market_analysis: MarketAnalysis;
  metadata: {
    generated_at: string;
    time_range: string;
    cache_duration: number;
    optimization_level: string;
  };
}

export default function BusinessAnalytics() {
  const [selectedMetric, setSelectedMetric] = useState('revenue');
  const [timeRange, setTimeRange] = useState('7d');
  const [showPerformanceMonitor, setShowPerformanceMonitor] = useState(false);
  const [performanceMetrics, setPerformanceMetrics] = useState<any>(null);
  const [optimizationRecommendations, setOptimizationRecommendations] = useState<any[]>([]);
  const [autoOptimizationEnabled, setAutoOptimizationEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const { t } = useLanguage();

  // Fetch consolidated analytics data
  const fetchAnalyticsData = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/v1/analytics/consolidated-dashboard?range=${timeRange}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAnalyticsData(data.data);

        } else {
          console.error('❌ Analytics API error:', data.error);
        }
      } else {
        console.error('❌ Failed to fetch analytics data:', response.status);
      }
    } catch (error) {
      console.error('❌ Error fetching analytics data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load data on component mount and when time range changes
  useEffect(() => {
    fetchAnalyticsData();
  }, [timeRange, refreshKey]);

  // Performance monitoring functions
  const fetchPerformanceMetrics = async () => {
    try {
      const response = await fetch('/api/v1/performance/status');
      if (response.ok) {
        const data = await response.json();
        setPerformanceMetrics(data);
      }
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
    }
  };

  const fetchOptimizationRecommendations = async () => {
    try {
      const response = await fetch('/api/v1/performance/optimization-recommendations');
      if (response.ok) {
        const data = await response.json();
        setOptimizationRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error('Error fetching optimization recommendations:', error);
    }
  };

  const triggerAutoOptimization = async (level = 'moderate') => {
    try {
      const response = await fetch('/api/v1/performance/auto-optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ level }),
      });
      
      if (response.ok) {
        const data = await response.json();

        // Refresh metrics after optimization
        setTimeout(() => {
          fetchPerformanceMetrics();
          fetchOptimizationRecommendations();
        }, 2000);
      }
    } catch (error) {
      console.error('Error triggering auto-optimization:', error);
    }
  };

  // Load performance data on mount
  useEffect(() => {
    fetchPerformanceMetrics();
    fetchOptimizationRecommendations();
  }, []);

  // Enhanced metrics with more business focus
  const metrics = [
    {
      id: 'revenue',
      name: 'Revenue Analytics',
      icon: DollarSign,
      description: 'Revenue trends and analysis',
      color: 'emerald',
      gradient: 'from-emerald-500 to-green-600',
      value: analyticsData?.dashboard_stats?.total_revenue ? `₺${analyticsData.dashboard_stats.total_revenue.toLocaleString()}` : '₺0',
      change: '+15.2%',
      trend: 'up',
    },
    {
      id: 'growth',
      name: 'Growth Metrics',
      icon: TrendingUp,
      description: 'Business growth and expansion metrics',
      color: 'gray',
      gradient: 'bg-gray-500',
      value: '18.2%',
      change: '+2.1%',
      trend: 'up',
    },
    {
      id: 'performance',
      name: 'Performance Analytics',
      icon: Activity,
      description: 'Overall business performance metrics',
      color: 'purple',
      gradient: 'bg-purple-500',
      value: '92.5%',
      change: '+1.8%',
      trend: 'up',
    },
    {
      id: 'forecasting',
      name: 'Forecasting',
      icon: Target,
      description: 'Predictive analytics and forecasting',
      color: 'amber',
      gradient: 'bg-amber-500',
      value: '₺140,000',
      change: '+12.0%',
      trend: 'up',
    },
  ];

  // Enhanced KPI data with real data from API
  const kpiData = [
    {
      title: 'Total Revenue',
      value: analyticsData?.dashboard_stats?.total_revenue ? `₺${analyticsData.dashboard_stats.total_revenue.toLocaleString()}` : '₺0',
      change: '+15.2%',
      trend: 'up',
      icon: DollarSign,
      color: 'bg-emerald-500',
      subtitle: 'Monthly revenue',
    },
    {
      title: 'Active Clients',
      value: analyticsData?.dashboard_stats?.unique_clients?.toString() || '0',
      change: '+8.5%',
      trend: 'up',
      icon: Users,
      color: 'bg-gray-500',
      subtitle: 'Total active clients',
    },
    {
      title: 'Total Transactions',
      value: analyticsData?.dashboard_stats?.total_transactions?.toString() || '0',
      change: '+3.2%',
      trend: 'up',
      icon: Activity,
      color: 'bg-purple-500',
      subtitle: 'Total transactions',
    },
    {
      title: 'Avg Transaction',
      value: analyticsData?.dashboard_stats?.avg_transaction ? `₺${analyticsData.dashboard_stats.avg_transaction.toLocaleString()}` : '₺0',
      change: '+2.1%',
      trend: 'up',
      icon: TrendingUp,
      color: 'bg-amber-500',
      subtitle: 'Average transaction value',
    },
  ];

  // Enhanced comparison data
  const comparisonData = [
    { label: 'Q1 2024', value: 85, target: 100, revenue: '₺85,000', growth: '+5.2%' },
    { label: 'Q2 2024', value: 92, target: 100, revenue: '₺92,000', growth: '+8.2%' },
    { label: 'Q3 2024', value: 88, target: 100, revenue: '₺88,000', growth: '-4.3%' },
    { label: 'Q4 2024', value: 95, target: 100, revenue: '₺95,000', growth: '+8.0%' },
  ];

  // Enhanced timeline data
  const timelineData = [
    {
      date: '2024-01-15',
      title: 'New Client Onboarded',
      description: 'ABC Corporation signed up for premium services',
      type: 'success',
      amount: '₺25,000',
    },
    {
      date: '2024-01-20',
      title: 'Revenue Milestone',
      description: 'Reached ₺100,000 monthly revenue target',
      type: 'success',
      amount: '₺100,000',
    },
    {
      date: '2024-01-25',
      title: 'System Update',
      description: 'Deployed new analytics dashboard features',
      type: 'info',
      amount: null,
    },
    {
      date: '2024-01-28',
      title: 'Client Renewal',
      description: 'XYZ Ltd renewed annual contract',
      type: 'success',
      amount: '₺45,000',
    },
  ];

  // New business metrics
  const businessMetrics = [
    {
      title: 'Market Share',
      value: '12.5%',
      change: '+1.2%',
      trend: 'up',
      icon: Globe,
      color: 'bg-indigo-500',
    },
    {
      title: 'Customer Satisfaction',
      value: '4.8/5.0',
      change: '+0.2',
      trend: 'up',
      icon: Award,
      color: 'bg-pink-500',
    },
    {
      title: 'Response Time',
      value: '2.3h',
      change: '-0.5h',
      trend: 'up',
      icon: Clock,
      color: 'bg-cyan-500',
    },
    {
      title: 'Uptime',
      value: '99.9%',
      change: '+0.1%',
      trend: 'up',
      icon: CheckCircle,
      color: 'bg-green-500',
    },
  ];

  // Enhanced transaction data
  const transactionData = [
    {
      id: 'TXN-001',
      date: '2024-01-25',
      client: 'ABC Corp',
      amount: '₺15,000',
      status: 'completed',
      trend: '+12%',
      category: 'Premium Service',
      paymentMethod: 'Bank Transfer',
    },
    {
      id: 'TXN-002',
      date: '2024-01-24',
      client: 'XYZ Ltd',
      amount: '₺8,500',
      status: 'pending',
      trend: '0%',
      category: 'Standard Service',
      paymentMethod: 'Credit Card',
    },
    {
      id: 'TXN-003',
      date: '2024-01-23',
      client: 'DEF Industries',
      amount: '₺22,000',
      status: 'completed',
      trend: '+18%',
      category: 'Enterprise Service',
      paymentMethod: 'Bank Transfer',
    },
    {
      id: 'TXN-004',
      date: '2024-01-22',
      client: 'GHI Solutions',
      amount: '₺12,500',
      status: 'failed',
      trend: '-5%',
      category: 'Standard Service',
      paymentMethod: 'Credit Card',
    },
  ];

  // Market analysis data from API
  const marketAnalysis = [
    {
      metric: 'Market Size',
      value: analyticsData?.market_analysis?.market_size_estimate ? `₺${(analyticsData.market_analysis.market_size_estimate / 1000000).toFixed(1)}M` : '₺0',
      change: '+8.5%',
      trend: 'up',
      description: 'Total addressable market',
    },
    {
      metric: 'Competition Level',
      value: analyticsData?.market_analysis?.competition_level || 'Medium',
      change: 'Stable',
      trend: 'neutral',
      description: 'Competitive landscape',
    },
    {
      metric: 'Customer Segments',
      value: analyticsData?.market_analysis?.customer_segments?.toString() || '0',
      change: '+12%',
      trend: 'up',
      description: 'Number of customer segments',
    },
    {
      metric: 'Avg Client Value',
      value: analyticsData?.market_analysis?.average_client_value ? `₺${analyticsData.market_analysis.average_client_value.toLocaleString()}` : '₺0',
      change: '+15%',
      trend: 'up',
      description: 'Average customer value',
    },
  ];

  // Business recommendations from API
  const businessRecommendations = analyticsData?.business_recommendations || [];

  const getTrendIcon = (trend: string) => {
    if (trend === 'up') return <ArrowUpRight className="w-4 h-4" />;
    if (trend === 'down') return <ArrowDownRight className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  const getTrendClass = (trend: string) => {
    if (trend === 'up') return 'business-trend-up';
    if (trend === 'down') return 'business-trend-down';
    return 'business-trend-neutral';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'business-badge-success';
      case 'pending':
        return 'business-badge-warning';
      case 'failed':
        return 'business-badge-error';
      default:
        return 'business-badge-info';
    }
  };

  const handleRefresh = () => {
    setIsLoading(true);
    setRefreshKey(prev => prev + 1);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

  const handleExport = () => {
    // Export functionality

  };

  const handleTimeRangeChange = (newRange: string) => {
    setTimeRange(newRange);
    // Trigger data refresh based on new range

  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'P1':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'P2':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'P3':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'High':
        return 'text-green-600 bg-green-50';
      case 'Medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'Low':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'High':
        return 'text-red-600 bg-red-50';
      case 'Medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'Low':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="p-6">

      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <BarChart3 className="h-8 w-8 text-gray-600" />
              Business Analytics
            </h1>
            <p className="text-gray-600">Advanced analytics and business intelligence dashboard</p>
          </div>
          <div className='flex items-center space-x-3'>
            <select 
              value={timeRange} 
              onChange={(e) => handleTimeRangeChange(e.target.value)}
              className='px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-300 w-32'
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="1y">Last year</option>
            </select>
            <button 
              className='business-btn business-btn-secondary'
              onClick={handleExport}
            >
              <Download className='w-4 h-4 mr-2' />
              Export
            </button>
            <button 
              className='business-btn business-btn-primary'
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              {isLoading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>

      {/* Enhanced KPI Grid */}
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6'>
        {kpiData.map((kpi, index) => (
          <StandardMetricsCard
            key={index}
            title={kpi.title}
            value={kpi.value}
            subtitle={kpi.subtitle}
            icon={kpi.icon}
            color={kpi.color.includes('gray') ? 'gray' : 
                  kpi.color.includes('green') ? 'green' : 
                  kpi.color.includes('purple') ? 'purple' : 
                  kpi.color.includes('orange') ? 'orange' : 'gray'}
            variant="default"
          />
        ))}
      </div>

      {/* Business Metrics Grid */}
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6'>
        {businessMetrics.map((metric, index) => (
          <StandardMetricsCard
            key={index}
            title={metric.title}
            value={metric.value}
            icon={metric.icon}
            color={metric.color.includes('gray') ? 'gray' : 
                  metric.color.includes('green') ? 'green' : 
                  metric.color.includes('purple') ? 'purple' : 
                  metric.color.includes('orange') ? 'orange' : 'gray'}
            variant="compact"
          />
        ))}
      </div>

      {/* Analytics Categories and Content */}
      <div className='grid grid-cols-1 lg:grid-cols-3 gap-8'>
        {/* Analytics Categories Sidebar */}
        <div className='lg:col-span-1'>
          <div className='business-card sticky top-6'>
            <div className='business-card-header'>
              <div className='flex items-center gap-3'>
                <div className='w-10 h-10 bg-gray-500 rounded-lg flex items-center justify-center'>
                  <BarChart3 className='w-5 h-5 text-white' />
                </div>
                <h3 className='text-xl font-semibold text-gray-900'>
                  Analytics Categories
                </h3>
              </div>
            </div>
            <div className='business-card-body space-business-sm'>
              {metrics.map(metric => (
                <button
                  key={metric.id}
                  onClick={() => setSelectedMetric(metric.id)}
                  className={`w-full p-4 text-left rounded-lg transition-all duration-200 ${
                    selectedMetric === metric.id
                      ? 'bg-gray-50 border border-gray-200 text-gray-900'
                      : 'hover:bg-gray-50 border border-gray-100 hover:border-gray-200'
                  }`}
                >
                  <div className='flex items-center'>
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center mr-4 ${
                      selectedMetric === metric.id
                        ? 'bg-gray-100'
                        : 'bg-gray-100'
                    }`}>
                      <metric.icon className={`w-5 h-5 ${
                        selectedMetric === metric.id
                          ? 'text-gray-600'
                          : 'text-gray-600'
                      }`} />
                    </div>
                    <div className='flex-1'>
                      <div className={`font-semibold ${
                        selectedMetric === metric.id
                          ? 'text-gray-900'
                          : 'text-gray-900'
                      }`}>
                        {metric.name}
                      </div>
                      <div className={`text-sm ${
                        selectedMetric === metric.id
                          ? 'text-gray-700'
                          : 'text-gray-500'
                      }`}>
                        {metric.description}
                      </div>
                      <div className={`text-sm font-medium mt-1 ${
                        selectedMetric === metric.id
                          ? 'text-gray-700'
                          : 'text-gray-600'
                      }`}>
                        {metric.value} • {metric.change}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Analytics Content */}
        <div className='lg:col-span-2 space-y-6'>
          {/* Revenue Chart */}
          <div className='business-chart'>
            <div className='business-chart-header'>
              <div>
                <h3 className='business-chart-title'>Revenue Trend Analysis</h3>
                <p className='business-chart-subtitle'>Monthly revenue performance over time</p>
              </div>
              <div className='business-chart-actions'>
                <button 
                  className='business-btn business-btn-outline'
                  onClick={handleRefresh}
                  disabled={isLoading}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  {isLoading ? 'Refreshing...' : 'Refresh'}
                </button>
                <button className='business-btn business-btn-outline'>
                  <Eye className='w-4 h-4 mr-2' />
                  View Details
                </button>
              </div>
            </div>
            
            {/* Enhanced Chart Placeholder */}
            <div className='h-64 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200 flex items-center justify-center'>
              <div className='text-center'>
                <div className='w-16 h-16 bg-gray-500 rounded-xl flex items-center justify-center mx-auto mb-4'>
                  <LineChart className='w-8 h-8 text-white' />
                </div>
                <h4 className='text-lg font-semibold text-gray-700 mb-2'>Revenue Chart</h4>
                <p className='text-gray-500'>Interactive revenue trend chart will be displayed here</p>
                <div className='mt-4 flex items-center justify-center gap-4'>
                  <div className='flex items-center gap-2'>
                    <div className='w-3 h-3 bg-gray-500 rounded-full'></div>
                    <span className='text-sm text-gray-600'>Revenue</span>
                  </div>
                  <div className='flex items-center gap-2'>
                    <div className='w-3 h-3 bg-green-500 rounded-full'></div>
                    <span className='text-sm text-gray-600'>Growth</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Chart Legend */}
            <div className='business-chart-legend'>
              <div className='business-chart-legend-item'>
                <div className='business-chart-legend-color bg-gray-500'></div>
                <span className='business-chart-legend-label'>Revenue</span>
                <span className='business-chart-legend-value'>₺125,000</span>
              </div>
              <div className='business-chart-legend-item'>
                <div className='business-chart-legend-color bg-green-500'></div>
                <span className='business-chart-legend-label'>Growth</span>
                <span className='business-chart-legend-value'>+15.2%</span>
              </div>
              <div className='business-chart-legend-item'>
                <div className='business-chart-legend-color bg-purple-500'></div>
                <span className='business-chart-legend-label'>Target</span>
                <span className='business-chart-legend-value'>₺120,000</span>
              </div>
            </div>
          </div>

          {/* Enhanced Performance Comparison */}
          <div className='business-comparison'>
            <div className='business-comparison-header'>
              <div>
                <h3 className='business-chart-title'>Quarterly Performance</h3>
                <p className='business-chart-subtitle'>Performance vs targets by quarter</p>
              </div>
            </div>
            <div className='business-comparison-bars'>
              {comparisonData.map((item, index) => (
                <div key={index} className='business-comparison-bar'>
                  <div className='business-comparison-label'>{item.label}</div>
                  <div className='business-comparison-progress'>
                    <div 
                      className='business-progress-success'
                      style={{ width: `${(item.value / item.target) * 100}%` }}
                    ></div>
                  </div>
                  <div className='business-comparison-value'>{item.value}%</div>
                  <div className='text-sm text-gray-600 w-24'>{item.revenue}</div>
                  <div className={`text-sm font-medium w-16 ${
                    item.growth.startsWith('+') ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {item.growth}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Enhanced Timeline */}
          <div className='business-chart'>
            <div className='business-chart-header'>
              <div>
                <h3 className='business-chart-title'>Recent Activities</h3>
                <p className='business-chart-subtitle'>Latest business events and milestones</p>
              </div>
              <div className='business-chart-actions'>
                <button 
                  className='business-btn business-btn-outline'
                  onClick={handleRefresh}
                  disabled={isLoading}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  {isLoading ? 'Refreshing...' : 'Refresh'}
                </button>
              </div>
            </div>
            <div className='business-timeline'>
              {timelineData.map((item, index) => (
                <div key={index} className='business-timeline-item'>
                  <div className={`business-timeline-marker ${
                    item.type === 'success' ? 'bg-green-500' :
                    item.type === 'info' ? 'bg-gray-500' : 'bg-yellow-500'
                  }`}></div>
                  <div className='business-timeline-content'>
                    <div className='flex items-center justify-between mb-1'>
                      <div className='business-timeline-date'>{item.date}</div>
                      {item.amount && (
                        <span className='text-sm font-medium text-green-600'>{item.amount}</span>
                      )}
                    </div>
                    <div className='business-timeline-title'>{item.title}</div>
                    <div className='business-timeline-description'>{item.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Data Grid */}
      <div className='business-data-grid'>
        <div className='business-data-grid-header'>
          <h3 className='business-data-grid-title'>Transaction Summary</h3>
          <div className='business-data-grid-filters'>
            <button className='business-btn business-btn-outline'>
              <Filter className='w-4 h-4 mr-2' />
              Filter
            </button>
            <button className='business-btn business-btn-outline'>
              <Download className='w-4 h-4 mr-2' />
              Export
            </button>
          </div>
        </div>
        <div className='business-data-grid-content'>
          <table className='business-data-grid-table'>
            <thead className='business-data-table-header'>
              <tr>
                <th className='business-data-table-header-cell'>ID</th>
                <th className='business-data-table-header-cell'>Date</th>
                <th className='business-data-table-header-cell'>Client</th>
                <th className='business-data-table-header-cell'>Amount</th>
                <th className='business-data-table-header-cell'>Status</th>
                <th className='business-data-table-header-cell'>Category</th>
                <th className='business-data-table-header-cell'>Payment</th>
                <th className='business-data-table-header-cell'>Trend</th>
              </tr>
            </thead>
            <tbody className='business-data-table-body'>
              {transactionData.map((transaction, index) => (
                <tr key={index} className='business-data-table-row'>
                  <td className='business-data-table-cell font-mono text-xs'>{transaction.id}</td>
                  <td className='business-data-table-cell'>{transaction.date}</td>
                  <td className='business-data-table-cell font-medium'>{transaction.client}</td>
                  <td className='business-data-table-cell font-semibold'>{transaction.amount}</td>
                  <td className='business-data-table-cell'>
                    <div className='flex items-center gap-2'>
                      {getStatusIcon(transaction.status)}
                      <span className={getStatusBadgeClass(transaction.status)}>
                        {transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
                      </span>
                    </div>
                  </td>
                  <td className='business-data-table-cell text-sm text-gray-600'>{transaction.category}</td>
                  <td className='business-data-table-cell text-sm text-gray-600'>{transaction.paymentMethod}</td>
                  <td className='business-data-table-cell'>
                    <span className={`business-kpi-trend ${getTrendClass(transaction.trend.includes('+') ? 'up' : transaction.trend.includes('-') ? 'down' : 'neutral')}`}>
                      {transaction.trend.includes('+') ? <TrendingUpIcon className='business-trend-icon' /> :
                       transaction.trend.includes('-') ? <TrendingDownIcon className='business-trend-icon' /> :
                       <Minus className='business-trend-icon' />}
                      {transaction.trend}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Market Analysis Section */}
      <div className='business-card'>
        <div className='business-card-header'>
          <div className='flex items-center gap-3'>
            <div className='w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center'>
              <Target className='w-5 h-5 text-white' />
            </div>
            <h3 className='text-xl font-semibold text-gray-900'>Market Analysis</h3>
          </div>
        </div>
                 <div className='business-card-body space-y-4'>
           {marketAnalysis.map((item, index) => (
             <div key={index} className='flex items-center justify-between p-4 rounded-lg bg-gray-50 border border-gray-200'>
               <div>
                 <h4 className='text-lg font-semibold text-gray-800'>{item.metric}</h4>
                 <p className='text-sm text-gray-600'>{item.description}</p>
               </div>
               <div className='flex flex-col items-end'>
                 <div className='text-2xl font-bold text-gray-900'>{item.value}</div>
                 <div className={`text-sm font-medium ${getTrendClass(item.trend)}`}>
                   {getTrendIcon(item.trend)}
                   <span>{item.change}</span>
                 </div>
               </div>
             </div>
           ))}
         </div>
      </div>

             {/* Business Recommendations Section */}
       <div className='business-card'>
         <div className='business-card-header'>
           <div className='flex items-center gap-3'>
             <div className='w-10 h-10 bg-indigo-500 rounded-lg flex items-center justify-center'>
               <Zap className='w-5 h-5 text-white' />
             </div>
             <h3 className='text-xl font-semibold text-gray-900'>Business Recommendations</h3>
           </div>
         </div>
         <div className='business-card-body space-y-4'>
           {businessRecommendations.map((item) => (
             <div key={item.id} className='p-4 rounded-lg bg-gray-50 border border-gray-200'>
               <div className='flex items-start justify-between mb-3'>
                 <div className='flex-1'>
                   <h4 className='text-lg font-semibold text-gray-800 mb-2'>{item.title}</h4>
                   <p className='text-sm text-gray-600 mb-3'>{item.description}</p>
                   <div className='flex items-center gap-4'>
                     <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(item.priority)}`}>
                       {item.priority}
                     </span>
                     <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImpactColor(item.impact)}`}>
                       Impact: {item.impact}
                     </span>
                     <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEffortColor(item.effort)}`}>
                       Effort: {item.effort}
                     </span>
                     <span className='px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800'>
                       {item.category}
                     </span>
                   </div>
                 </div>
                 <button className='business-btn business-btn-outline text-xs'>
                   <Eye className='w-3 h-3 mr-1' />
                   View
                 </button>
               </div>
             </div>
           ))}
         </div>
       </div>

       {/* Summary Dashboard */}
       <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
         <div className='business-card'>
           <div className='business-card-header'>
             <h3 className='text-lg font-semibold text-gray-900'>Quick Actions</h3>
           </div>
           <div className='business-card-body space-y-3'>
             <button className='w-full business-btn business-btn-primary text-left'>
               <Download className='w-4 h-4 mr-2' />
               Generate Report
             </button>
             <button className='w-full business-btn business-btn-outline text-left'>
               <Users className='w-4 h-4 mr-2' />
               Add New Client
             </button>
             <button className='w-full business-btn business-btn-outline text-left'>
               <BarChart3 className='w-4 h-4 mr-2' />
               View Analytics
             </button>
           </div>
         </div>

                   <div className='business-card'>
             <div className='business-card-header'>
               <h3 className='text-lg font-semibold text-gray-900'>System Status</h3>
             </div>
             <div className='business-card-body space-y-3'>
               <div className='flex items-center justify-between'>
                 <span className='text-sm text-gray-600'>CPU Usage</span>
                 <span className={`text-sm font-medium ${
                   (analyticsData?.system_performance?.cpu_usage || 0) > 80 ? 'text-red-600' :
                   (analyticsData?.system_performance?.cpu_usage || 0) > 60 ? 'text-yellow-600' : 'text-green-600'
                 }`}>
                   {analyticsData?.system_performance?.cpu_usage?.toFixed(1) || '0'}%
                 </span>
               </div>
               <div className='flex items-center justify-between'>
                 <span className='text-sm text-gray-600'>Memory Usage</span>
                 <span className={`text-sm font-medium ${
                   (analyticsData?.system_performance?.memory_usage || 0) > 80 ? 'text-red-600' :
                   (analyticsData?.system_performance?.memory_usage || 0) > 60 ? 'text-yellow-600' : 'text-green-600'
                 }`}>
                   {analyticsData?.system_performance?.memory_usage?.toFixed(1) || '0'}%
                 </span>
               </div>
               <div className='flex items-center justify-between'>
                 <span className='text-sm text-gray-600'>Disk Usage</span>
                 <span className={`text-sm font-medium ${
                   (analyticsData?.system_performance?.disk_usage || 0) > 80 ? 'text-red-600' :
                   (analyticsData?.system_performance?.disk_usage || 0) > 60 ? 'text-yellow-600' : 'text-green-600'
                 }`}>
                   {analyticsData?.system_performance?.disk_usage?.toFixed(1) || '0'}%
                 </span>
               </div>
             </div>
           </div>

         <div className='business-card'>
           <div className='business-card-header'>
             <h3 className='text-lg font-semibold text-gray-900'>Recent Updates</h3>
           </div>
           <div className='business-card-body space-y-3'>
             <div className='text-sm'>
               <div className='font-medium text-gray-800'>Dashboard v2.1</div>
               <div className='text-gray-600'>Enhanced analytics features</div>
               <div className='text-xs text-gray-500 mt-1'>2 hours ago</div>
             </div>
             <div className='text-sm'>
               <div className='font-medium text-gray-800'>Payment Gateway</div>
               <div className='text-gray-600'>Improved transaction processing</div>
               <div className='text-xs text-gray-500 mt-1'>1 day ago</div>
             </div>
           </div>
         </div>
       </div>

       {/* Advanced Performance Monitoring Section */}
       <div className='mt-8'>
         <div className='business-card'>
           <div className='business-card-header flex items-center justify-between'>
             <h3 className='text-lg font-semibold text-gray-900 flex items-center gap-2'>
               <Zap className='w-5 h-5 text-gray-600' />
               Performance Monitoring & Auto-Optimization
             </h3>
             <button
               onClick={() => setShowPerformanceMonitor(!showPerformanceMonitor)}
               className='business-btn business-btn-outline text-sm'
             >
               {showPerformanceMonitor ? 'Hide' : 'Show'} Monitor
             </button>
           </div>
           
           {showPerformanceMonitor && (
             <div className='business-card-body'>
               {/* Performance Metrics */}
               {performanceMetrics && (
                 <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6'>
                   <div className='text-center p-4 bg-gray-50 rounded-lg'>
                     <div className='text-2xl font-bold text-gray-600'>
                       {performanceMetrics.cpu_usage?.toFixed(1) || '0'}%
                     </div>
                     <div className='text-sm text-gray-600'>CPU Usage</div>
                   </div>
                   
                   <div className='text-center p-4 bg-green-50 rounded-lg'>
                     <div className='text-2xl font-bold text-green-600'>
                       {performanceMetrics.memory_usage?.toFixed(1) || '0'}%
                     </div>
                     <div className='text-sm text-gray-600'>Memory Usage</div>
                   </div>
                   
                   <div className='text-center p-4 bg-purple-50 rounded-lg'>
                     <div className='text-2xl font-bold text-purple-600'>
                       {performanceMetrics.response_time?.toFixed(0) || '0'}ms
                     </div>
                     <div className='text-sm text-gray-600'>Response Time</div>
                   </div>
                   
                   <div className='text-center p-4 bg-orange-50 rounded-lg'>
                     <div className='text-2xl font-bold text-orange-600'>
                       {performanceMetrics.requests_per_second?.toFixed(1) || '0'}
                     </div>
                     <div className='text-sm text-gray-600'>Requests/sec</div>
                   </div>
                 </div>
               )}

               {/* Auto-Optimization Controls */}
               <div className='border-t pt-6'>
                 <div className='flex items-center justify-between mb-4'>
                   <div>
                     <h4 className='text-md font-semibold text-gray-900'>Auto-Optimization</h4>
                     <p className='text-sm text-gray-600'>Automatically optimize system performance</p>
                   </div>
                   <label className='flex items-center gap-2'>
                     <input
                       type='checkbox'
                       checked={autoOptimizationEnabled}
                       onChange={(e) => setAutoOptimizationEnabled(e.target.checked)}
                       className='rounded'
                     />
                     <span className='text-sm text-gray-700'>Enable Auto-Optimization</span>
                   </label>
                 </div>
                 
                 <div className='grid grid-cols-1 md:grid-cols-3 gap-3'>
                   <button
                     onClick={() => triggerAutoOptimization('mild')}
                     className='business-btn business-btn-outline text-sm'
                   >
                     Mild Optimization
                   </button>
                   <button
                     onClick={() => triggerAutoOptimization('moderate')}
                     className='business-btn business-btn-primary text-sm'
                   >
                     Moderate Optimization
                   </button>
                   <button
                     onClick={() => triggerAutoOptimization('aggressive')}
                     className='business-btn business-btn-outline text-sm border-orange-300 text-orange-700 hover:bg-orange-50'
                   >
                     Aggressive Optimization
                   </button>
                 </div>
               </div>

               {/* Optimization Recommendations */}
               {optimizationRecommendations.length > 0 && (
                 <div className='border-t pt-6 mt-6'>
                   <h4 className='text-md font-semibold text-gray-900 mb-4'>Optimization Recommendations</h4>
                   <div className='space-y-3'>
                     {optimizationRecommendations.map((rec, index) => (
                       <div
                         key={index}
                         className={`p-3 rounded-lg border-l-4 ${
                           rec.priority === 'critical' ? 'border-l-red-500 bg-red-50' :
                           rec.priority === 'high' ? 'border-l-orange-500 bg-orange-50' :
                           rec.priority === 'medium' ? 'border-l-yellow-500 bg-yellow-50' :
                           'border-l-gray-500 bg-gray-50'
                         }`}
                       >
                         <div className='flex items-start justify-between'>
                           <div className='flex-1'>
                             <div className='flex items-center gap-2 mb-1'>
                               <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                 rec.priority === 'critical' ? 'bg-red-100 text-red-800' :
                                 rec.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                 rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                 'bg-gray-100 text-gray-800'
                               }`}>
                                 {rec.priority.toUpperCase()}
                               </span>
                               <span className='text-sm text-gray-500'>{rec.component}</span>
                             </div>
                             <p className='text-sm text-gray-900 mb-2'>{rec.message}</p>
                             <p className='text-xs text-gray-600'><strong>Action:</strong> {rec.action}</p>
                           </div>
                         </div>
                       </div>
                     ))}
                   </div>
                 </div>
               )}
             </div>
           )}
         </div>
       </div>
     </div>
   );
 }
