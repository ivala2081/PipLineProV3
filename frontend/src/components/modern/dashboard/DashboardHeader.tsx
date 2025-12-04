/**
 * Dashboard Header Component
 * Header section with title, filters, and quick actions
 */

import React from 'react';
import { BarChart3 } from 'lucide-react';
import { useLanguage } from '../../../contexts/LanguageContext';
import { StatusIndicator, DataFreshnessIndicator } from '../../ui/StatusIndicator';
import { QuickActionBar } from '../QuickActionBar';
import type { TimeRange, ViewType } from '../../../types/dashboard.types';

interface DashboardHeaderProps {
  timeRange: TimeRange;
  viewType: ViewType;
  refreshing: boolean;
  isGeneratingReport: boolean;
  lastUpdated: Date | null;
  onTimeRangeChange: (range: TimeRange) => void;
  onViewTypeChange: (view: ViewType) => void;
  onRefresh: () => void;
  onExport: () => void;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  timeRange,
  viewType,
  refreshing,
  isGeneratingReport,
  lastUpdated,
  onTimeRangeChange,
  onViewTypeChange,
  onRefresh,
  onExport,
}) => {
  const { t } = useLanguage();

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-gray-700" />
          {t('dashboard.title') || 'Dashboard'}
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          {t('dashboard.description') || 'Overview of your business performance'}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <StatusIndicator
            status={refreshing ? 'syncing' : 'online'}
            showLabel={false}
            pulse={!refreshing}
            size="sm"
          />
          {lastUpdated && <DataFreshnessIndicator lastUpdated={lastUpdated} />}
        </div>
        <select
          value={timeRange}
          onChange={(e) => onTimeRangeChange(e.target.value as TimeRange)}
          className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 font-medium hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-300 transition-all duration-200"
        >
          <option value="all">All Time</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="6m">Last 6 months</option>
          <option value="1y">Last year</option>
        </select>
        <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => onViewTypeChange('net')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200 ${
              viewType === 'net'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
            }`}
          >
            {t('dashboard.net_revenue') || 'Net'}
          </button>
          <button
            onClick={() => onViewTypeChange('gross')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200 ${
              viewType === 'gross'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
            }`}
          >
            {t('ledger.gross_amount') || 'Gross'}
          </button>
        </div>
        <QuickActionBar
          onExport={onExport}
          onRefresh={onRefresh}
          refreshing={refreshing}
          isGeneratingReport={isGeneratingReport}
        />
      </div>
    </div>
  );
};

