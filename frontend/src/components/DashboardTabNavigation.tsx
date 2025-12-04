import React, { memo } from 'react';
import { BarChart3, LineChart, TrendingUp, Shield, DollarSign, RefreshCw } from 'lucide-react';
import { CardTabs, CardTabItem } from './ui/professional-tabs';
import { useLanguage } from '../contexts/LanguageContext';

type TabType = 'overview' | 'analytics' | 'performance' | 'monitoring' | 'financial';

interface DashboardTabNavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  onRefresh: () => void;
  refreshing?: boolean;
}

const DashboardTabNavigation = memo<DashboardTabNavigationProps>(({
  activeTab,
  onTabChange,
  onRefresh,
  refreshing = false
}) => {
  const { t } = useLanguage();
  
  const tabs = [
    {
      id: 'overview' as TabType,
      label: t('tabs.overview'),
      icon: BarChart3,
      description: t('tabs.overview_desc')
    },
    {
      id: 'analytics' as TabType,
      label: t('tabs.analytics'),
      icon: LineChart,
      description: t('tabs.analytics_desc')
    },
    {
      id: 'performance' as TabType,
      label: t('tabs.performance'),
      icon: TrendingUp,
      description: t('tabs.performance_desc')
    },
    {
      id: 'monitoring' as TabType,
      label: t('tabs.monitoring'),
      icon: Shield,
      description: t('tabs.monitoring_desc')
    },
    {
      id: 'financial' as TabType,
      label: t('tabs.financial'),
      icon: DollarSign,
      description: t('tabs.financial_desc')
    }
  ];

  return (
    <CardTabs className="w-full">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        
        return (
          <div key={tab.id} className="flex items-center gap-2">
            <CardTabItem
              id={tab.id}
              label={tab.label}
              icon={Icon}
              active={isActive}
              onClick={() => onTabChange(tab.id)}
              className="relative"
            />
            {isActive && (
              <button
                onClick={onRefresh}
                disabled={refreshing}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-white/60 rounded-lg transition-all duration-200 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                title={refreshing ? t('tabs.refreshing') : `${t('common.refresh')} ${tab.label}`}
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
            )}
          </div>
        );
      })}
    </CardTabs>
  );
});

DashboardTabNavigation.displayName = 'DashboardTabNavigation';

export default DashboardTabNavigation;
