import React from 'react';
import { useDashboardStats, useTopPerformers, useRevenueTrends } from '../hooks/useQueries';
import { TrendingUp, TrendingDown, DollarSign, Users, Activity } from 'lucide-react';

interface DashboardStatsProps {
  range?: string;
}

const DashboardStats: React.FC<DashboardStatsProps> = ({ range = '7d' }) => {
  // Use React Query hooks for data fetching
  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats(range);
  const { data: topPerformers, isLoading: performersLoading } = useTopPerformers(range);
  const { data: revenueTrends, isLoading: trendsLoading } = useRevenueTrends(range);

  // Loading state
  if (statsLoading || performersLoading || trendsLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (statsError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <TrendingDown className="h-5 w-5 text-red-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Error loading dashboard data
            </h3>
            <div className="mt-2 text-sm text-red-700">
              {statsError instanceof Error ? statsError.message : 'An unexpected error occurred'}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Extract data with fallbacks
  const dashboardStats = stats?.data || {};
  const performers = topPerformers?.data || [];
  const trends = revenueTrends?.data || {};

  const metrics = [
    {
      name: 'Total Revenue',
      value: `$${dashboardStats.total_revenue?.toLocaleString() || '0'}`,
      change: trends.revenue_change || 0,
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Active Clients',
      value: dashboardStats.active_clients?.toLocaleString() || '0',
      change: trends.clients_change || 0,
      icon: Users,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
    },
    {
      name: 'Total Transactions',
      value: dashboardStats.total_transactions?.toLocaleString() || '0',
      change: trends.transactions_change || 0,
      icon: Activity,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      name: 'Success Rate',
      value: `${dashboardStats.success_rate?.toFixed(1) || '0'}%`,
      change: trends.success_rate_change || 0,
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          const isPositive = metric.change >= 0;
          
          return (
            <div key={metric.name} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{metric.name}</p>
                  <p className="text-lg font-bold text-gray-900 mt-1">{metric.value}</p>
                </div>
                <div className={`p-3 rounded-full ${metric.bgColor}`}>
                  <Icon className={`h-6 w-6 ${metric.color}`} />
                </div>
              </div>
              
              {/* Change indicator */}
              {metric.change !== 0 && (
                <div className="mt-4 flex items-center">
                  {isPositive ? (
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-500" />
                  )}
                  <span className={`ml-1 text-sm font-medium ${
                    isPositive ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {Math.abs(metric.change).toFixed(1)}%
                  </span>
                  <span className="ml-1 text-sm text-gray-500">from last period</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Top Performers */}
      {performers.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Top Performers</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {performers.slice(0, 5).map((performer: any, index: number) => (
                <div key={performer.id || index} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">
                          {performer.name?.charAt(0) || '?'}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-900">
                        {performer.name || 'Unknown'}
                      </p>
                      <p className="text-sm text-gray-500">
                        {performer.transactions || 0} transactions
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      ${performer.revenue?.toLocaleString() || '0'}
                    </p>
                    <p className="text-sm text-gray-500">
                      {performer.commission_rate || 0}% commission
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardStats;
